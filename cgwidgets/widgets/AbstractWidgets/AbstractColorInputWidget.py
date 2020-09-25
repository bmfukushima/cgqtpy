"""
TODO:
    Linear Gradients
        * Setup linear gradients triggers
        * Update values in labels widget
                - Set the manipulated thingy to the selected text color?
                    No idea how to do this...
                       unless you use multiple labels...
    Display Label
        * Show current values
        * background
                - semi transparent?
                - middle gray?
    Annoying
        * Flickering on Linear Gradient drag
        * Foreground gradient is causing alpha overlay issue...
            - Force the for ground into one gradient?
"""

import sys
import math
import re

# from qtpy.QtWidgets import *
# from qtpy.QtCore import *
# from qtpy.QtGui import *

from qtpy.QtWidgets import (
    QApplication,
    QStackedWidget, QStackedLayout, QVBoxLayout, QWidget,
    QGraphicsView, QGraphicsScene, QGraphicsEllipseItem, QGraphicsItemGroup,
    QGraphicsLineItem, QLabel, QBoxLayout, QFrame, QLineEdit
)
from qtpy.QtCore import (Qt, QPoint, QPointF)
from qtpy.QtGui import (
    QColor, QLinearGradient, QGradient, QBrush
)

from cgwidgets.utils import installLadderDelegate, getWidgetAncestor, updateStyleSheet
from cgwidgets.widgets import AbstractLine, AbstractInputGroup
from cgwidgets.settings.colors import iColor


class AbstractColorGradientMainWidget(QStackedWidget):
    """
    Displays the color swatch to the user.  This color swatch will have a cross
    hair where the user can select the color that they want to use

    Attributes:
        linear_crosshair_direction (Qt.Direction): Direction that the crosshair
            will travel when doing a 1D selection (HSV/RGB)
        color (QColor): The current color that is being returned
            TODO
                setColor needs to have a userTrigger on it to do some operation...

    Widgets
        | -- color_picker (ColorGradientWidget)
                | -- VBox
                        TODO:
                            (Change to box? So you can set orientation?)
                        | -- QGraphicsView
                        | -- QGraphicsLabel
                TODO:
                        Add labels to bottom
                        display_values_widget
        | -- display_color_widget (ColorDisplayLabel)
                TODO:
                    Add the RGBA | HSV values to the label
                    Potentially make this into a Layout?
    """
    def __init__(self, parent=None):
        super(AbstractColorGradientMainWidget, self).__init__(parent=parent)
        # setup attrs
        self._border_width = 10
        self._linear_crosshair_direction = Qt.Horizontal

        # create widgets
        self.color_picker_widget = ColorGradientWidget()
        self.display_color_widget = ColorDisplayLabel()

        self.addWidget(self.display_color_widget)
        self.addWidget(self.color_picker_widget)

        default_color = QColor()
        default_color.setRgbF(0.5, 0.5, 1.0, 1.0)
        self.setColor(default_color)

    """ API """
    def setRGBACrosshairPosition(self, pos):
        """
        Interface to set the cross hair position on the scene

        Args:
            pos (QPoint):
        """
        scene = self.getScene()
        scene.setRGBACrosshairPos(pos)

    def setRGBACrosshairPositionFromColor(self, color):
        """
        Sets the crosshair position to color provided.

        color (QColor):
            color to search for in the crosshair position
        """
        scene = self.getScene()
        xpos = (color.hueF() * scene.width())
        ypos = math.fabs((color.valueF() * scene.height()) - scene.height())

        pos = QPoint(xpos, ypos)
        self.setRGBACrosshairPosition(pos)

    def setColor(self, color):
        """
        Sets the current color of this widget to the one provided.  This will
        update the display border, as well as the crosshair position in the
        gradient widget.
        Args:
            color (QColor): color to be set to
        """
        self._color = color
        self.updateDisplayBorder()
        self.setRGBACrosshairPositionFromColor(color)

        # update display args
        widget_dict = self.color_picker_widget.display_values_widget.getWidgetDict()
        new_color_args = {
            "hue" : color.hueF(),
            "value" : color.valueF(),
            "saturation" : color.saturationF(),
            "red" : color.redF(),
            "green" : color.greenF(),
            "blue" : color.blueF()
        }

        for color_arg in widget_dict:
            # get value widget
            widget = widget_dict[color_arg]
            value_widget = widget.value_widget

            # set new value
            value = new_color_args[color_arg]
            widget.setValue(value)

    def getColor(self):
        if not hasattr(self, '_color'):
            self._color = QColor()
        return self._color

    def setLinearCrosshairDirection(self, direction=Qt.Horizontal):
        self._linear_crosshair_direction = direction
        self.getScene().setLinearCrosshairDirection(direction)

    def getLinearCrosshairDirection(self):
        return self._linear_crosshair_direction

    """ UTILS """
    def getScene(self):
        return self.color_picker_widget.scene

    def updateDisplayBorder(self, color=None):
        """
        Updates the border color that is displayed to the user
        Args:
            color (QColor): color to set the border to, if no color is provided,
                this by default will use the getColor() method
        """
        # get color
        if not color:
            color = self.getColor()

        # set up style sheet
        kwargs = {
            "color" : repr(color.getRgb()),
            "border_width" : self.border_width
        }
        self.setStyleSheet(
            """
            AbstractColorGradientMainWidget{{
            border: {border_width} solid rgba{color}
            }}
            """.format(**kwargs)
        )

    """ PROPERTIES"""

    @property
    def border_width(self):
        return self._border_width

    @border_width.setter
    def border_width(self, border_width):
        self._border_width = border_width


class ColorGradientWidget(QWidget):
    """
    MainWindow
        --> Layout
            --> GraphicsView (GLWidget)
                --> GraphicsScene
    """
    def __init__(self, parent=None):
        super(ColorGradientWidget, self).__init__(parent)

        QVBoxLayout(self)
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)

        self.scene = ColorGraphicsScene(self)
        self.view = ColorGraphicsView(self.scene)
        # TODO Display values while manipulating
        self.display_values_widget = DisplayValuesGroupWidget(self)

        self.layout().addWidget(self.view)
        self.layout().addWidget(self.display_values_widget)
        self.setStyleSheet("border:None")

    def mousePressEvent(self, *args, **kwargs):
        return QWidget.mousePressEvent(self, *args, **kwargs)

    def leaveEvent(self, *args, **kwargs):
        color_widget = getWidgetAncestor(self, AbstractColorGradientMainWidget)
        color_widget.setCurrentIndex(0)
        return QWidget.leaveEvent(self, *args, **kwargs)


class ColorGraphicsView(QGraphicsView):
    """
    Attributes:
        previous_size (geometry) hold the previous position
            so that a resize event can recalculate the cross hair
            based off of this geometry
    """
    def __init__(self, parent=None):
        super(ColorGraphicsView, self).__init__(parent)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    """ UTILS """
    def __hideRGBACrosshair(self, hide=True):
        """
        Determines if the cross hair for the RGBA picker should be shown/hidden

        Args:
            hide (bool): if true, hides the RGBA color picker, if false, shows the
                RGBA color picker
        """
        if hide is True:
            self.scene().rgba_crosshair_item.hide()
        else:
            self.scene().rgba_crosshair_item.show()

    def __hideLinearCrosshair(self, hide=True):
        """
        Determines if the cross hair for the RGBA picker should be shown/hidden

        Args:
            hide (bool): if true, hides the RGBA color picker, if false, shows the
                RGBA color picker
        """
        if hide is True:
            self.scene().linear_crosshair_item.hide()
        else:
            self.scene().linear_crosshair_item.show()

    def __updateRGBACrosshairOnResize(self):
        """
        Updates the RGBA crosshair to the correct position.
        """

        rgba_crosshair_pos = self.scene().getRGBACrosshairPos()
        old_width = self.getPreviousSize().width()
        old_height = self.getPreviousSize().height()
        crosshair_xpos = rgba_crosshair_pos.x() / old_width
        crosshair_ypos = rgba_crosshair_pos.y() / old_height

        # get new crosshair position
        xpos = crosshair_xpos * self.geometry().width()
        ypos = crosshair_ypos * self.geometry().height()
        new_pos = QPoint(xpos, ypos)
        self.scene().updateRGBACrosshair(new_pos)

    def __updateLinearCrosshairOnResize(self, direction):
        """
        Updates the linear crosshair on resize.

        This is currently piggy backing on the direction setting
        mechanism.  As by default that will redraw the crosshair
        """
        # get pos
        rgba_crosshair_pos = self.scene().getLinearCrosshairPos()
        old_width = self.getPreviousSize().width()
        old_height = self.getPreviousSize().height()
        crosshair_xpos = rgba_crosshair_pos.x() / old_width
        crosshair_ypos = rgba_crosshair_pos.y() / old_height

        # update linear crosshair position
        xpos = crosshair_xpos * self.geometry().width()
        ypos = crosshair_ypos * self.geometry().height()
        new_pos = QPoint(xpos, ypos)
        self.scene().setLinearCrosshairPos(new_pos)

        # update the cross hair size
        #direction = self.scene().getLinearCrosshairDirection()
        self.scene().setLinearCrosshairDirection(direction)

    """ EVENTS """
    def mousePressEvent(self, event, *args, **kwargs):
        """
        TODO
            Determine which gradient should be used by the user...
                - ALT / ALT+SHIFT COMBOS?
                - Can I reuse the LMB/MMB/RMB defaults?
            RGBA --> LMB
            HSV
            RGB
        Attrs:
            _picking (bool): tells the widget that the user is now attempting
                to pick a value
            _in_gradient_widget (bool) tells the widget that the cursor is
                in the gradient widget
        """
        modifiers = QApplication.keyboardModifiers()
        button = event.button()
        # move rgba

        # HSV
        self._picking = True
        self._in_gradient_widget = True

        # setup default crosshair
        self.__hideRGBACrosshair(True)
        self.__hideLinearCrosshair(False)

        # HSV
        if not modifiers:
            if button == Qt.LeftButton:
                self.__hideRGBACrosshair(False)
                self.__hideLinearCrosshair(True)
                self.scene().gradient_type = ColorGraphicsScene.RGBA
            elif button == Qt.MiddleButton:
                self.scene().gradient_type = ColorGraphicsScene.VALUE
            elif button == Qt.RightButton:
                self.scene().gradient_type = ColorGraphicsScene.SATURATION

        #RGB
        elif modifiers == Qt.AltModifier:
            if button == Qt.LeftButton:
                self.scene().gradient_type = ColorGraphicsScene.RED
            elif button == Qt.MiddleButton:
                self.scene().gradient_type = ColorGraphicsScene.GREEN
            elif button == Qt.RightButton:
                self.scene().gradient_type = ColorGraphicsScene.BLUE

        self.scene().drawGradient()
        self.setCursor(Qt.BlankCursor)

        return QGraphicsView.mousePressEvent(self, event,*args, **kwargs)

    def mouseMoveEvent(self, event, *args, **kwargs):
        modifiers = QApplication.keyboardModifiers()

        # TODO Setup value getters/setters
        """
        This move event will determine if the values should be updated
        this will need to update the hsv/rgba moves aswell
        """

        if self._picking:
            self._getColor(event)
            # if self.scene().gradient_type == ColorGraphicsScene.RGBA:
            #     self._getRGBAValue(event)

        return QGraphicsView.mouseMoveEvent(self, event, *args, **kwargs)

    def mouseReleaseEvent(self, *args, **kwargs):
        # reset everything back to default state
        # reset gradient
        self.__hideRGBACrosshair(False)
        self.__hideLinearCrosshair(True)
        self.scene().gradient_type = ColorGraphicsScene.RGBA
        self.scene().drawGradient()
        # reset picking attrs
        self._picking = False
        self.unsetCursor()
        return QGraphicsView.mouseReleaseEvent(self, *args, **kwargs)

    def resizeEvent(self, *args, **kwargs):
        """
        allow widget to resize with the rectangle...
        """
        # there has to be a better way to set this...

        # =======================================================================
        # resize widget
        # =======================================================================
        rect = self.geometry()
        self.scene().setSceneRect(
            rect.topLeft().x(),
            rect.topLeft().y(),
            rect.width(),
            rect.height()
        )

        # update gradient
        self.scene().drawGradient()

        # update crosshair
        # RGBA Crosshair
        self.__updateRGBACrosshairOnResize()

        # Linear crosshair
        main_widget = getWidgetAncestor(self, AbstractColorGradientMainWidget)
        direction = main_widget.getLinearCrosshairDirection()
        self.__updateLinearCrosshairOnResize(direction)

        self.setPreviousSize(rect)
        return QGraphicsView.resizeEvent(self, *args, **kwargs)

    """ SELECTION """
    def _getColor(self, event):
        """
        Gets the color from the user selection and sends it to the
        setColor on the main widget ( AbstractColorGradientMainWidget )

        """
        # get attrs
        color_display_widget = getWidgetAncestor(self.scene(), AbstractColorGradientMainWidget)
        selection_type = self.scene().gradient_type

        if  selection_type == ColorGraphicsScene.RGBA:
            # RGBA (HUE / VALUE)
            color = self._getRGBAValue(event)
            color_display_widget.setColor(color)
            return
        else:

            self.scene().setLinearCrosshairPos(event.pos())
            #self.__hideLinearCrosshair(True)
            orig_color = color_display_widget.getColor()
            pos = event.globalPos()
            new_color = self._pickColor(pos)
            #self.__hideLinearCrosshair(False)

            # saturation
            if selection_type == ColorGraphicsScene.SATURATION:
                hue = orig_color.hueF()
                sat = new_color.valueF()
                value = orig_color.valueF()
                orig_color.setHsvF(hue, sat, value)
            # value
            elif selection_type == ColorGraphicsScene.VALUE:
                hue = orig_color.hueF()
                sat = orig_color.saturationF()
                value = new_color.valueF()
                orig_color.setHsvF(hue, sat, value)
            # red
            elif selection_type == ColorGraphicsScene.RED:
                red = new_color.redF()
                orig_color.setRedF(red)
            # green
            elif selection_type == ColorGraphicsScene.GREEN:
                green = new_color.greenF()
                orig_color.setGreenF(green)
            # blue
            elif selection_type == ColorGraphicsScene.BLUE:
                blue = new_color.blueF()
                orig_color.setBlueF(blue)

            color_display_widget.setColor(orig_color)
            return

    def _getRGBAValue(self, event):
        """
        Gets the RGBA color

        Returns (QColor)
        """
        # get color
        scene = self.scene()
        pos = event.globalPos()
        color = self._pickColor(pos)
        scene.updateRGBACrosshair(event.pos())

        # check mouse position...
        top_left = self.mapToGlobal(self.pos())
        top = top_left.y()
        left = top_left.x()
        right = left + self.geometry().width()
        bot = top + self.geometry().height()

        if pos.y() < top or pos.y() > bot or pos.x() < left or pos.x() > right:
            if self._in_gradient_widget == True:
                self.setCursor(Qt.CrossCursor)
                self._in_gradient_widget = False
        else:
            if self._in_gradient_widget == False:
                self.setCursor(Qt.BlankCursor)
                self._in_gradient_widget = True

        return color

    def _pickColor(self, pos):
        """
        picks the the current color displayed on screen at
        the current location of the cursor
        """
        desktop = QApplication.desktop().winId()
        screen = QApplication.primaryScreen()
        pixmap = screen.grabWindow(
            desktop,
            pos.x(), pos.y(),
            1, 1
        )
        img = pixmap.toImage()
        color = QColor(img.pixel(0, 0))
        if color.valueF() == 0:
            pos = QPoint(pos.x() + 1, pos.y() + 1)
            return self._pickColor(pos)
        return color

    """ PROPERTIES """
    def setPreviousSize(self, geometry):
        self.previous_size = geometry

    def getPreviousSize(self):
        if not hasattr(self, 'previous_size'):
            self.previous_size = self.geometry()
        return self.previous_size


class ColorGraphicsScene(QGraphicsScene):
    """
    The widget that is responsible for displaying the color gradient to the user
    """

    RED = 'red'
    GREEN = 'green'
    BLUE = 'blue'
    ALPHA = 'alpha'
    HUE = 'hue'
    SATURATION = 'saturation'
    VALUE = 'value'
    RGBA = 'rgba'

    def __init__(self, parent=None):
        super(ColorGraphicsScene, self).__init__(parent)
        # setup default attrs
        self.CROSSHAIR_RADIUS = 10
        self._rgba_crosshair_pos = QPoint(0, 0)
        self._linear_crosshair_pos = QPoint(0, 0)
        self._linear_crosshair_size = 15

        # create scene
        self.setSceneRect(0, 0, 500, 500)
        self.gradient_type = ColorGraphicsScene.RGBA
        # TODO MOVE THIS SOMEWHERE USEFUL?
        self.drawRGBACrosshair()
        self.drawLinearCrosshair()

    """ DRAW GRADIENTS """
    def create1DGradient(
        self,
        direction=Qt.Horizontal,
        color1=(0, 0, 0, 1),
        color2=(1, 1, 1, 1)
    ):
        """
        Creates 1D Linear gradient to be displayed to the user.

        Args:
            direction (Qt.Direction): The direction the gradient should go
            color1 (QColor): The first color in the gradient, the default value is black.
            color2 (QColor): The second color in the gradient, the default value is white.

        Returns (QBrush)
        """
        # create QColor Floats
        colorA = QColor()
        colorA.setRgbF(*color1)
        colorB = QColor()
        colorB.setRgbF(*color2)

        # set direction
        if direction == Qt.Horizontal:
            gradient = QLinearGradient(0, 0, self.width(), 0)
        elif direction == Qt.Vertical:
            gradient = QLinearGradient(0, 0, 0, self.height())

        # create brush
        gradient.setSpread(QGradient.RepeatSpread)
        gradient.setColorAt(0, colorA)
        gradient.setColorAt(1, colorB)
        gradient_brush = QBrush(gradient)
        return gradient_brush

    def drawGradient(self):
        """
        Primary drawing function of the gradient.
        This wil look at the property "gradient_type" and set the
        gradient according to that.
        """
        self.setForegroundBrush(QBrush())
        if self.gradient_type == ColorGraphicsScene.RED:
            background_gradient = self.create1DGradient(color2=(1, 0, 0, 1))
        elif self.gradient_type == ColorGraphicsScene.GREEN:
            background_gradient = self.create1DGradient(color2=(0, 1, 0, 1))
        elif self.gradient_type == ColorGraphicsScene.BLUE:
            background_gradient = self.create1DGradient(color2=(0, 0, 1, 1))
        elif self.gradient_type == ColorGraphicsScene.ALPHA:
            background_gradient = self.create1DGradient()
        elif self.gradient_type == ColorGraphicsScene.HUE:
            background_gradient = self.create1DGradient()
        elif self.gradient_type == ColorGraphicsScene.SATURATION:
            background_gradient = self.create1DGradient()
        elif self.gradient_type == ColorGraphicsScene.VALUE:
            background_gradient = self.create1DGradient()
        elif self.gradient_type == ColorGraphicsScene.RGBA:
            background_gradient = self._drawRGBAGradient()
            # black_gradient = QLinearGradient(0, 0, 0, self.height())
            # black_gradient.setSpread(QGradient.RepeatSpread)
            # black_gradient.setColorAt(0, QColor(0, 0, 0, 0))
            # black_gradient.setColorAt(1, QColor(value, value, value, 255))
            foreground_gradient = self.create1DGradient(
                direction=Qt.Vertical,
                color1=(0, 0, 0, 0),
                color2=(1, 1, 1, 1),
            )
            self.setForegroundBrush(foreground_gradient)

        self.setBackgroundBrush(background_gradient)

    def _drawRGBAGradient(self):
        """
        draws the background color square for the main widget
        """

        # get Value from main widget
        value = 1
        sat = 1

        color_gradient = QLinearGradient(0, 0, self.width(), 0)

        num_colors = 6
        color_gradient.setSpread(QGradient.RepeatSpread)
        for x in range(num_colors):
            pos = (1 / num_colors) * (x)
            color = QColor()
            color.setHsvF(x * (1/num_colors), sat, value)
            color_gradient.setColorAt(pos, color)

        # how to add FG here?

        color_gradient_brush = QBrush(color_gradient)
        return color_gradient_brush

    """ PROPERTIES """
    @property
    def gradient_type(self):
        return self._gradient_type

    @gradient_type.setter
    def gradient_type(self, gradient_type):
        self._gradient_type = gradient_type

    """ CROSSHAIR"""
    def drawLinearCrosshair(self):
        """
        Creates the initial linear crosshair.  Note that this is hard coded to setup
        to be drawn horizontally.  You can update the direction with
        setLinearCrosshairDirection(Qt.Direction) on the
        AbstractColorGradientMainWidget.
        """
        # vertical line
        self.linear_topline_item = LineSegment(width=2)
        self.linear_botline_item = LineSegment(width=2)

        # horizontal line
        self.linear_leftline_item = LineSegment(width=2)
        self.linear_rightline_item = LineSegment(width=2)

        # create linear cross hair items group
        self.linear_crosshair_item = QGraphicsItemGroup()
        self.linear_crosshair_item.addToGroup(self.linear_botline_item)
        self.linear_crosshair_item.addToGroup(self.linear_rightline_item)
        self.linear_crosshair_item.addToGroup(self.linear_topline_item)
        self.linear_crosshair_item.addToGroup(self.linear_leftline_item)

        # add group item
        self.setLinearCrosshairDirection(Qt.Horizontal)
        self.addItem(self.linear_crosshair_item)

    def getLinearCrosshairPos(self):
        return self._linear_crosshair_pos

    def setLinearCrosshairPos(self, pos):
        """
        Places the crosshair at a specific  location in the widget.  This is generally
        used when updating color values, and passing them back to the color widget.
        """
        main_widget = getWidgetAncestor(self, AbstractColorGradientMainWidget)
        direction = main_widget.getLinearCrosshairDirection()
        if direction == Qt.Horizontal:
            pos = QPoint(pos.x(), 0)
            self.linear_crosshair_item.setPos(pos.x(), 0)
            self._linear_crosshair_pos = pos
        elif direction == Qt.Vertical:
            pos = QPoint(0, pos.y())
            self.linear_crosshair_item.setPos(0, pos.y())
            self._linear_crosshair_pos = pos

    def setLinearCrosshairDirection(self, direction):
        """
        Sets the direction of travel of the linear crosshair.  This will also update
        the display of the crosshair
        """
        # set direction
        self._linear_crosshair_direction = direction
        #self._linear_crosshair_size

        # update display
        if direction == Qt.Horizontal:
            self.linear_topline_item.setLine(-5, 0, 5, 0)
            self.linear_botline_item.setLine(-5, self.height(), 5, self.height())

            self.linear_leftline_item.setLine(-5, 0, -5, self.height())
            self.linear_rightline_item.setLine(5, 0, 5, self.height())

        elif direction == Qt.Vertical:
            self.linear_topline_item.setLine(0, -5, self.width(), -5)
            self.linear_botline_item.setLine(0, 5, self.width(), 5)

            self.linear_leftline_item.setLine(0, -5, 0, 5)
            self.linear_rightline_item.setLine(self.width(), -5, self.width(), 5)

    def getLinearCrosshairDirection(self):
        return self._linear_crosshair_direction

    """ RGBA """
    def drawRGBACrosshair(self):
        """
        rgba_topline_item
        rgba_botline_item
        rgba_leftline_item
        rgba_rightline_item:
        rgba_crosshair_item_circle: center portion of crosshair

        """
        # vertical line
        self.rgba_topline_item = LineSegment()
        self.rgba_topline_item.setLine(0, 0, 0, self.height())
        self.rgba_botline_item = LineSegment()
        self.rgba_botline_item.setLine(0, 0, 0, self.height())

        # horizontal line
        self.rgba_leftline_item = LineSegment()
        self.rgba_leftline_item.setLine(0, 0, self.width(), 0)
        self.rgba_rightline_item = LineSegment()
        self.rgba_rightline_item.setLine(0, 0, self.width(), 0)

        # crosshair circle
        self.rgba_crosshair_item_circle = QGraphicsEllipseItem()
        self.rgba_crosshair_item_circle.setRect(
            -(self.CROSSHAIR_RADIUS * 0.5),
            -(self.CROSSHAIR_RADIUS * 0.5),
            self.CROSSHAIR_RADIUS,
            self.CROSSHAIR_RADIUS
        )

        # add items
        self.rgba_crosshair_item = QGraphicsItemGroup()

        self.rgba_crosshair_item.addToGroup(self.rgba_crosshair_item_circle)
        self.rgba_crosshair_item.addToGroup(self.rgba_topline_item)
        self.rgba_crosshair_item.addToGroup(self.rgba_botline_item)
        self.rgba_crosshair_item.addToGroup(self.rgba_leftline_item)
        self.rgba_crosshair_item.addToGroup(self.rgba_rightline_item)

        self.addItem(self.rgba_crosshair_item)

    def getRGBACrosshairPos(self):
        return self._rgba_crosshair_pos

    def setRGBACrosshairPos(self, pos):
        self._rgba_crosshair_pos = pos

    def updateRGBACrosshair(self, pos):
        """
        Places the crosshair at a specific  location in the widget.  This is generally
        used when updating color values, and passing them back to the color widget.
        """
        crosshair_radius = self.CROSSHAIR_RADIUS * 0.5
        xpos = pos.x()
        ypos = pos.y()

        # update items positions
        self.rgba_crosshair_item_circle.setPos(pos)
        self.rgba_topline_item.setLine(xpos, 0, xpos, ypos - crosshair_radius)
        self.rgba_botline_item.setLine(xpos, ypos + crosshair_radius, xpos, self.height())
        self.rgba_leftline_item.setLine(0, ypos, xpos - crosshair_radius, ypos)
        self.rgba_rightline_item.setLine(xpos + crosshair_radius, ypos, self.width(), ypos)

        self.setRGBACrosshairPos(pos)


class LineSegment(QGraphicsLineItem):
    """
    Abstract line segment to be used fro the crosshair
    """
    def __init__(self, parent=None, width=1):
        super(LineSegment, self).__init__(parent)
        pen = self.pen()
        pen.setWidth(width)
        self.setPen(pen)


""" DISPLAY LABELS"""
class ColorDisplayLabel(QLabel):
    #  ==========================================================================
    # Display color swatch to the user
    #  ==========================================================================
    def __init__(self, parent=None):
        super(ColorDisplayLabel, self).__init__(parent=parent)
        updated_args = {'rgba_background': iColor['rgba_gray_2']}
        style_sheet = iColor.createDefaultStyleSheet(self, updated_args)

        self.setStyleSheet(style_sheet)

    def enterEvent(self, *args, **kwargs):
        color_display_widget = getWidgetAncestor(self, AbstractColorGradientMainWidget)
        color_display_widget.setCurrentIndex(1)
        return QLabel.enterEvent(self, *args, **kwargs)


class DisplayValuesGroupWidget(QFrame):
    """
    Widget that will contain all of the display values for the user.

    Args:
        direction (QBoxLayout.Direction): direction that this widget should be
            set up in.  LeftToRight | RightToLeft | TopToBottom | BottomToTop

    Attributes:
        widget_dict (dict): of DisplayLabels whose keys will be the title
            of the widget.  These will correspond with the
            ColorGraphicsScene.TYPE.  However, there will be no option
            for RGBA / rgba.  So don't use that...

    Widgets
        | -- QBoxLayout
                | -* DisplayLabel

    """
    def __init__(self, parent=None, direction=QBoxLayout.LeftToRight):
        super(DisplayValuesGroupWidget, self).__init__(parent)
        QBoxLayout(direction, self)
        self._widget_dict = {}
        for title in ['hue', 'saturation', 'value']:
            label = DisplayLabel(self, title=title)
            self.layout().addWidget(label)
            self._widget_dict[title] = label

        for title in ['red', 'green', 'blue']:
            label = DisplayLabel(self, title=title)
            self.layout().addWidget(label)
            self._widget_dict[title] = label

        self.updateStyleSheet()

    def getWidgetDict(self):
        return self._widget_dict

    def updateStyleSheet(self):
        # QLabel{{
        #     color: rgba{rgba_text}
        # }}
        # DisplayValuesGroupWidget{{
        #     background-color: rgba{rgba_gray_0}
        # }}
        self.setStyleSheet("""
        background-color: rgba{rgba_gray_0}

        """.format(**iColor.style_sheet_args))


class DisplayLabel(AbstractInputGroup):
    """
    Attributes:
        name (str)
        value (str)
        selected (bool)

    Widgets:
        | -- QBoxLayout
                | -- label_widget (QLabel)
                | -- divider_widget (AbstractLine)
                | -- value_widget (QLabel)
    """
    def __init__(self, parent=None, title='None', value='None'):
        super(DisplayLabel, self).__init__(parent, title)
        # setup attrs
        self._value = value
        self._is_selected = False
        self.setSelected(True)

        # setup GUI
        self.value_widget = QLineEdit()
        self.value_widget.setStyleSheet("color: rgba{rgba_text}".format(**iColor.style_sheet_args))
        self.value_widget.setAlignment(Qt.AlignLeft)
        #self.value_widget.setAlignment(Qt.AlignCenter)
        self.insertWidget(1, self.value_widget)

    """ PROPERTIES """
    def setValue(self, value):
        self._value = value
        self.value_widget.setText(str(value))
        self.value_widget.setCursorPosition(0)

    def getValue(self):
        return self._value


class DisplayLabelA(QWidget):
    """

    Attributes:
        title (str)
        value (str)
        is_selected (bool)
        direction (QBoxLayout.LeftToRight)

    Widgets:
        | -- QBoxLayout
                | -- label_widget (QLabel)
                | -- divider_widget (AbstractLine)
                | -- value_widget (QLabel)
    """
    def __init__(self, parent=None, title='None', value='None', direction=QBoxLayout.LeftToRight):
        super(DisplayLabelA, self).__init__(parent)
        # setup attrs
        self._direction = direction
        self._title = title
        self._value = value
        self._is_selected = False

        # set up gui
        QBoxLayout(direction, self)
        self.title_widget = QLabel(title)
        self.divider_widget = QFrame()
        self.value_widget = QLabel(value)

        self.layout().addWidget(self.title_widget)
        self.layout().addWidget(self.divider_widget)
        self.layout().addWidget(self.value_widget)

        # finalize attrs
        self.setDirection(direction)
        self.divider_widget.setLineWidth(1)

    """ PROPERTIES """
    def setTitle(self, title):
        self._title = title
        self.title_widget.setText(str(title))

    def getTitle(self):
        return self._title

    def setValue(self, value):
        self._value = value
        self.value_widget.setText(str(value))

    def getValue(self):
        return self._value

    def isSelected(self):
        return self._is_selected

    def setSelected(self, is_selected):
        self._is_selected = is_selected

    def getDirection(self):
        return self._direction

    def setDirection(self, direction):
        """
        Sets the layout direction of this widget.

        Args:
            direction (Qt.Direction): Which way this widget should be laid out.
        """
        # set attrs
        self._direction = direction

        # set widget directions
        self.layout().setDirection(direction)
        if direction == Qt.Vertical:
            self.setFrameShape(QFrame.HLine)
        elif direction == Qt.Horizontal:
            self.setFrameShape(QFrame.VLine)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    color_widget = AbstractColorGradientMainWidget()
    #color_widget.setLinearCrosshairDirection(Qt.Vertical)
    color_widget.show()
    sys.exit(app.exec_())







