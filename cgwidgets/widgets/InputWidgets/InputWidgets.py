from qtpy.QtWidgets import (
    QComboBox, QLineEdit, QCompleter, QSizePolicy
)

from qtpy.QtGui import(
    QStandardItem, QStandardItemModel
)
from qtpy.QtCore import (
    QEvent, Qt, QSortFilterProxyModel
)

from qtpy.QtWidgets import QSplitter, QLabel, QFrame, QBoxLayout, QLineEdit
from qtpy.QtCore import Qt

from cgwidgets.widgets import (
    AbstractInputGroupBox,
    AbstractFloatInputWidget,
    AbstractIntInputWidget,
    AbstractStringInputWidget,
    AbstractBooleanInputWidget,
    AbstractVLine
)

from cgwidgets.widgets import TansuModelViewWidget, TansuModelDelegateWidget, TansuModelItem

from cgwidgets.utils import getWidgetAncestor, updateStyleSheet

from cgwidgets.settings.colors import iColor


class UserInputItem(TansuModelItem):
    def getValue(self):
        return self._value

    def setValue(self, value):
        self._value = value


class GroupInputWidget(AbstractInputGroupBox):
    def __init__(self, parent=None, title=None):
        """
    A container for holding user parameters.  The default main
    widget is a TansuWidget which can have the individual widgets
    added to it

    Widgets:
        GroupInputWidget
            | -- main_widget (GroupInputTansuWidget)
                    | -- model
                    | -* (UserInputItem)
    """
        super(GroupInputWidget, self).__init__(parent, title)

        # setup main widget
        self.main_widget = GroupInputTansuWidget(self)

        self.layout().addWidget(self.main_widget)

    def insertInputWidget(self, index, widget, name, value=''):
        """
        Inserts a widget into the Main Widget

        index (int)
        widget (InputWidget)
        name (str)
        type (str):
        """
        #if type:
        name = "{name}  |  {type}".format(name=name, type=widget.TYPE)
        #self.main_widget.insertViewItem(index, name, widget=widget)
        view_item = self.main_widget.insertViewItem(index, name)
        view_item.setValue(value)
        view_item.setDynamicWidgetBaseClass(widget)
        view_item.setDynamicUpdateFunction(widget.updateFunction)

    def removeInputWidget(self, index):
        self.main_widget.removeTab(index)


class GroupInputTansuWidget(TansuModelViewWidget):
    def __init__(self, parent=None):
        super(GroupInputTansuWidget, self).__init__(parent)
        self.model().setItemType(UserInputItem)
        self.setDelegateType(TansuModelViewWidget.DYNAMIC)
        self.setViewPosition(TansuModelViewWidget.WEST)
        self.setMultiSelect(True)
        self.setMultiSelectDirection(Qt.Vertical)


class iGroupInput(object):
    """
    Interface for group input objects.  This is added to all of the input
    widget types so that they will be compatible with the GroupInputWidgets
    """
    def __init__(self):
        self.setTriggerEvent(self.updateItem)

    """ TRIGGER """
    def __trigger_event(self, *args, **kwargs):
        pass

    def setTriggerEvent(self, function):
        """
        Sets the function that should be triggered everytime
        the user finishes editing this widget
        """
        self.__trigger_event = function

    def triggerEvent(self, *args, **kwargs):
        """
        Internal event to run everytime the user triggers an update.  This
        will need to be called on every type of widget.
        """
        self.__trigger_event(*args, **kwargs)

    """ TANSU UPDATE """
    def updateItem(self, *args):
        """
        When the user inputs text, this will update the model item
        """
        try:
            widget = getWidgetAncestor(self, TansuModelDelegateWidget)
            widget.item().setValue(self.text())
        except AttributeError:
            pass

        # add user input event
        self.userInputEvent()

    @staticmethod
    def updateFunction(widget, item):
        """
        When the dynamic widget is created.  This will set
        the display text to the user
        """
        widget.getMainWidget().setText(str(item.getValue()))

    """ setup user input event """
    def __userInputEvent(self):
        return

    def setUserInputEvent(self, function):
        self.__userInputEvent = function

    def userInputEvent(self):
        self.__userInputEvent()


class FloatInputWidget(AbstractFloatInputWidget, iGroupInput):
    def __init__(self, parent=None):
        super(FloatInputWidget, self).__init__(parent)


class IntInputWidget(AbstractIntInputWidget, iGroupInput):
    def __init__(self, parent=None):
        super(IntInputWidget, self).__init__(parent)


class StringInputWidget(AbstractStringInputWidget, iGroupInput):
    def __init__(self, parent=None):
        super(StringInputWidget, self).__init__(parent)


class BooleanInputWidget(AbstractBooleanInputWidget, iGroupInput):
    def __init__(self, parent=None, is_clicked=False):
        super(BooleanInputWidget, self).__init__(parent, is_clicked=is_clicked)
        self.setTriggerEvent(self.updateItem)
        self.setupStyleSheet()

    def updateItem(self, *args):
        """
        When the user clicks on this
        """
        widget = getWidgetAncestor(self, TansuModelDelegateWidget)
        widget.item().setValue(self.is_clicked)
        self.is_clicked = self.is_clicked

        # add user input event
        self.userInputEvent()

    @staticmethod
    def updateFunction(widget, item):
        """
        When the dynamic widget is created.  This will set
        the display text to the user
        """
        # get default value
        # this is because the default value is set as '' during the constructor in
        # GroupInputWidget --> insertInputWidget
        if not item.getValue():
            value = False
        else:
            value = item.getValue()
        widget.getMainWidget().is_clicked = value
        updateStyleSheet(widget.getMainWidget())


class ListInputWidget(QComboBox, iGroupInput):
    pass


class UserInputWidget(QFrame):
    """
    name (str): the name displayed to the user
    input_widget (InputWidgetInstance): The instance of the input widget type
        that is displayed to the user for manipulation
    input_widget_base_class (InputWidgetClass): The type of input widget that this is
        displaying to the user
            Options are:
                BooleanInputWidget
                StringInputWidget
                IntInputWidget
                FloatInputWidget
                ListInputWidget
    """
    def __init__(self, parent=None, name="None", note="None", widget_type=StringInputWidget):
        super(UserInputWidget, self).__init__(parent)
        QBoxLayout(QBoxLayout.LeftToRight, self)

        # set up attrs
        self.setInputBaseClass(widget_type)

        # setup layout
        self._label = QLabel(name)
        self._separator = AbstractVLine()
        self._input_widget = widget_type()

        self.layout().addWidget(self._label)
        self.layout().addWidget(self._separator)
        self.layout().addWidget(self._input_widget)

        # set up display
        self._label.setToolTip(note)
        self.setupStyleSheet()

    def setupStyleSheet(self):
        style_sheet = iColor.createDefaultStyleSheet(self)
        self.setStyleSheet(style_sheet)
        self._label.setStyleSheet(
            self._label.styleSheet() + 'color: rgba{rgba_text_color}'.format(
                rgba_text_color=iColor.rgba_text_color))

    def setToolTip(self, tool_tip):
        self._label.setToolTip(tool_tip)

    def setName(self, name):
        self._label.setText(name)

    def getName(self):
        return self._label.text()

    def setInputWidget(self, _input_widget):
        self._input_widget = _input_widget

    def getInputWidget(self):
        return self._input_widget

    def setInputBaseClass(self, _input_widget_base_class):
        self._input_widget_base_class = _input_widget_base_class

    def getInputBaseClass(self):
        return self._input_widget_base_class

    def setUserInputEvent(self, function):
        self._input_widget.setUserInputEvent(function)


if __name__ == "__main__":
    import sys
    from qtpy.QtWidgets import QApplication, QWidget, QVBoxLayout
    from qtpy.QtGui import QCursor
    app = QApplication(sys.argv)
    w = QWidget()
    l = QVBoxLayout(w)

    gw = GroupInputWidget('cool stuff')

    gw.insertInputWidget(0, FloatInputWidget, 'Float')
    gw.insertInputWidget(0, FloatInputWidget, 'Int')
    gw.insertInputWidget(0, BooleanInputWidget, 'Boolean')
    gw.insertInputWidget(0, StringInputWidget, 'String')

    print (gw.main_widget.model())
    #gw.insertInputWidget(0, ListInputWidget, 'List')
    #gw.layout().itemAt(0).populate(['a','b','c','d'])
    #input_widget1.setUseLadder(True)
    gw.display_background = False
    l.addWidget(gw)
    #w = BooleanInputWidget()
    # w = ListInputWidget()
    # w.populate(['a','b','c','d'])
    #w.setInputBaseClass(ListInputWidget)
    w.resize(500, 500)
    w.show()
    w.move(QCursor.pos())

    sys.exit(app.exec_())
