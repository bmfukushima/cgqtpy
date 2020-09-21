from qtpy.QtWidgets import QSplitter, QLabel
from qtpy.QtCore import Qt

from cgwidgets.widgets import (
    AbstractInputGroupBox,
    AbstractFloatInputWidget,
    AbstractIntInputWidget,
    AbstractStringInputWidget,
    AbstractBooleanInputWidget
)

from cgwidgets.widgets import TansuModelViewWidget, TansuModelDelegateWidget


class GroupInputWidget(AbstractInputGroupBox):
    """
    A container for holding user parameters.  The default main
    widget is a TansuWidget which can have the individual widgets
    added to ti
    """
    def __init__(self, parent=None, title=None):
        super(GroupInputWidget, self).__init__(parent, title)

        # setup main widget
        self.main_widget = GroupInputTansuWidget(self)

        self.layout().addWidget(self.main_widget)

    def insertInputWidget(self, index, widget, name, type=None):
        """
        Inserts a widget into the Main Widget

        index (int)
        widget (InputWidget)
        name (str)
        type (str):
        """
        if type:
            name = "{name}  |  {type}".format(name=name, type=str(type))
        self.main_widget.insertViewItem(index, name, widget=widget)

    def removeInputWidget(self, index):
        self.main_widget.removeTab(index)


class GroupInputTansuWidget(TansuModelViewWidget):
    def __init__(self, parent=None):
        super(GroupInputTansuWidget, self).__init__(parent)
        self.setViewPosition(TansuModelViewWidget.WEST)
        self.setMultiSelect(True)
        self.setMultiSelectDirection(Qt.Vertical)
        self.setDelegateType(TansuModelViewWidget.DYNAMIC)

    def createTansuModelDelegateWidget(self, name, widget):
        """
        Creates a new tab widget widget...
        TODO:
            Move to base tansu?
        """
        display_widget = TansuModelDelegateWidget(self, name)
        display_widget.setMainWidget(widget)

        return display_widget


class FloatInputWidget(AbstractFloatInputWidget):
    def __init__(self, parent=None):
        super(FloatInputWidget, self).__init__(parent)


class IntInputWidget(AbstractIntInputWidget):
    def __init__(self, parent=None):
        super(IntInputWidget, self).__init__(parent)


class StringInputWidget(AbstractStringInputWidget):
    def __init__(self, parent=None):
        super(StringInputWidget, self).__init__(parent)


class BooleanInputWidget(AbstractBooleanInputWidget):
    def __init__(self, parent=None):
        super(BooleanInputWidget, self).__init__(parent)


if __name__ == "__main__":
    import sys
    from qtpy.QtWidgets import QApplication, QWidget, QVBoxLayout
    from qtpy.QtGui import QCursor
    app = QApplication(sys.argv)
    w = QWidget()
    l = QVBoxLayout(w)
    def triggerEvent(value):
        print (value)
    input_widget1 = FloatInputWidget()
    input_widget1.setTriggerEvent(triggerEvent)
    input_widget2 = FloatInputWidget()
    input_widget3 = FloatInputWidget()
    gw = GroupInputWidget('cool stuff')
    gw.insertInputWidget(0, input_widget1, 'test 1')
    gw.insertInputWidget(0, input_widget2, 'test 2')
    gw.insertInputWidget(0, input_widget3, 'test 3')

    #input_widget1.setUseLadder(True)
    gw.display_background = False
    l.addWidget(gw)
    w.resize(500, 500)
    w.show()
    w.move(QCursor.pos())

    sys.exit(app.exec_())
