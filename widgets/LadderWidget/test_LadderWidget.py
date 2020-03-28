import unittest
import sys

from qtpy.QtWidgets import QLabel, QApplication
from qtpy.QtCore import QEvent, Qt
from qtpy.QtTest import QTest

from cgwidgets.widgets.LadderWidget import LadderWidget
from cgwidgets.delegates.LadderDelegate.test_LadderDelegate import iTest


class TestLadderWidget(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        TestLadderWidget.widget = LadderWidget()

    def setUp(self):
        self.ladder0 = LadderWidget()
        self.ladder1 = LadderWidget(
            value_list=[0.0001, 0.001, 0.01, 0.1],
            widget=QLabel(),
            user_input=QEvent.MouseButtonPress
        )

    def test_popUp(self):
        QTest.mouseClick(self.ladder0, Qt.LeftButton)
        QTest.mouseClick(self.ladder1, Qt.LeftButton)

    def test_setValue(self):
        iTest().setValue(self, 5, TestLadderWidget.widget.ladder)
        iTest().setValue(self, -5, TestLadderWidget.widget.ladder)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    unittest.main()