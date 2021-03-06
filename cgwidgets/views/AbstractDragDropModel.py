# https://doc.qt.io/qt-5/model-view-programming.html#model-view-classes
from qtpy.QtWidgets import (
    QStyledItemDelegate, QApplication, QWidget, QStyle, QStyleOptionViewItem)
from qtpy.QtCore import (
    Qt, QModelIndex, QAbstractItemModel, QItemSelectionModel,
    QSize, QMimeData, QByteArray, QPoint, QRect)
from qtpy.QtGui import QPainter, QColor, QPen, QBrush, QCursor, QPolygonF, QPainterPath

from cgwidgets.settings.colors import iColor
from cgwidgets.utils import attrs

class AbstractDragDropModelItem(object):
    """

    Attributes:
        delegate_widget (QWidget): Widget to be shown when this item is
            selected
        dynamic_widget_base_class (QWidget): Widget to be shown when this item is
            selected if the Tansu is in DYNAMIC mode.
        column_data (dict): Dictionary of key pair values relating to the column name,
            and the value for the item in that column.  Special column names are
                name
                value
                items_list
    """
    def __init__(self, parent=None):
        #self._data = data
        self._column_data = {}
        self._children = []
        self._parent = parent
        self._delegate_widget = None
        self._dynamicWidgetFunction = None

        # flags

        #self._is_selected = False
        self._is_enabled = True
        self._isSelectable = True
        self._isDragEnabled = True
        self._isDropEnabled = True
        self._isEditable = True

        # default parent
        if parent is not None:
            parent.addChild(self)

    # def isSelected(self):
    #     return self._is_selected
    #
    # def setSelected(self, selected):
    #     self._is_selected = selected

    def addChild(self, child):
        self._children.append(child)

    def insertChild(self, position, child):

        if position < 0 or position > len(self._children):
            return False

        self._children.insert(position, child)
        child._parent = self
        return True

    def removeChild(self, position):

        if position < 0 or position > len(self._children):
            return False

        child = self._children.pop(position)
        child._parent = None

        return True

    def columnData(self):
        return self._column_data

    def setColumnData(self, _column_data):
        self._column_data = _column_data

    def childCount(self):
        return len(self._children)

    def children(self):
        return self._children

    def child(self, row):
        try:
            return self._children[row]
        except:
            return None

    def parent(self):
        return self._parent

    def row(self):
        if self._parent is not None:
            return self._parent._children.index(self)

    def log(self, tabLevel=-1):
        output = ""
        tabLevel += 1

        for i in range(tabLevel):
            output += "\t"
        output += "|------" + self._name + "\n"

        for child in self._children:
            output += child.log(tabLevel)

        tabLevel -= 1
        output += "\n"

        return output

    """ DRAG / DROP PROPERTIES """
    def isEnabled(self):
        return self._is_enabled

    def setIsEnabled(self, enable):
        self._is_enabled = enable

    def isSelectable(self):
        if self._isSelectable: return Qt.ItemIsSelectable
        else: return 0

    def setIsSelectable(self, _isSelectable):
        self._isSelectable = _isSelectable

    def isDragEnabled(self):
        if self._isDragEnabled: return Qt.ItemIsDragEnabled
        else: return 0

    def setIsDragEnabled(self, _isDragEnabled):
        self._isDragEnabled = _isDragEnabled

    def isDropEnabled(self):
        if self._isDropEnabled: return Qt.ItemIsDropEnabled
        else: return 0

    def setIsDropEnabled(self, _isDropEnabled):
        self._isDropEnabled = _isDropEnabled

    def isEditable(self):
        if self._isEditable: return Qt.ItemIsEditable
        else: return 0

    def setIsEditable(self, _isEditable):
        self._isEditable = _isEditable


class AbstractDragDropModel(QAbstractItemModel):
    """
    Abstract model that is used for the Tansu.  This supports tables, lists, and
    trees.  However not yet...
    TODO:
        - multi column support

    Attributes:
        item_type (Item): Data item to be stored on each index.  By default this
            set to the AbstractDragDropModelItem
    """
    ITEM_HEIGHT = 35
    ITEM_WIDTH = 100

    def __init__(self, parent=None, root_item=None):
        super(AbstractDragDropModel, self).__init__(parent)
        # set up default item type
        self._item_type = AbstractDragDropModelItem
        self._item_height = AbstractDragDropModel.ITEM_HEIGHT
        self._item_width = AbstractDragDropModel.ITEM_WIDTH

        # set up root item
        if not root_item:
            root_item = AbstractDragDropModelItem()
            root_item.setColumnData({"name":"root"})
        self._root_item = root_item
        self._root_drop_enabled = True

        # setup default attrs
        self._header_data = ['name']

        # flags
        self._isSelectable = True
        self._isEnableable = True
        self._isDragEnabled = True
        self._isDropEnabled = True
        self._isEditable = True
        self._isDeleteEnabled = True

        #
        self._dropping = False

    """ UTILS """
    def setItemEnabled(self, item, enabled):
        item.setIsEnabled(enabled)
        self.itemEnabledEvent(item, enabled)

    def deleteItem(self, item, event_update=False):
        # run deletion event
        if event_update:
            self.itemDeleteEvent(item)

        # get old parents
        old_parent_item = item.parent()
        old_parent_index = self.getParentIndexFromItem(item)

        # remove item
        self.beginRemoveRows(old_parent_index, item.row(), item.row() + 1)
        old_parent_item.children().remove(item)
        self.endRemoveRows()

        # TODO remove item

    def rowCount(self, parent):
        """
        INPUTS: QModelIndex
        OUTPUT: int
        """
        if not parent.isValid():
            parent_item = self._root_item
        else:
            parent_item = parent.internalPointer()

        return parent_item.childCount()

    def columnCount(self, parent):
        """
        INPUTS: QModelIndex
       OUTPUT: int
       """
        return len(self._header_data)

    def data(self, index, role):
        """
        This is the main display class for the model.  Setting different
        display roles inside of this class will determine how the views
        will handle the model data

        INPUTS: QModelIndex, int
        OUTPUT: QVariant, strings are cast to QString which is a QVariant
        """
        if not index.isValid():
            return None

        item = index.internalPointer()

        if role == Qt.DisplayRole or role == Qt.EditRole:
            for i in range(self.columnCount(item)):
                if index.column() == i:
                    try:
                        return_val = item.columnData()[self._header_data[i]]
                    except KeyError:
                        return_val = None
                    return return_val

        # change style for disabled items
        if role == Qt.FontRole:
            #font = self.font()
            font = QApplication.font()
            font.setStrikeOut(not item.isEnabled())
            self.layoutChanged.emit()
            return font
            #self.setFont(0, font)
        # todo disabled item color
        if role == Qt.ForegroundRole:
            if item.isEnabled():
                color = QColor(*iColor["rgba_text"])
            else:
                color = QColor(*iColor["rgba_text_disabled"])
            return color

        elif role == Qt.BackgroundRole:
            return QColor(255,0,0,255)

        if role == Qt.SizeHintRole:
            return QSize(self.item_width, self.item_height)

        # if role == Qt.BackgroundRole:
        #     return None

    def setData(self, index, value, role=Qt.EditRole):
        """
        INPUTS: QModelIndex, QVariant, int (flag)
        """
        if index.isValid():
            if role == Qt.EditRole:
                item = index.internalPointer()
                arg = self._header_data[index.column()]
                item.columnData()[arg] = value
                return True
        return False

    def headerData(self, column, orientation, role):
        """
        Sets the header data for each column
        INPUTS: int, Qt::Orientation, int
        OUTPUT: QVariant, strings are cast to QString which is a QVariant
        """
        if role == Qt.DisplayRole:
            return self._header_data[column]

    def setHeaderData(self, _header_data):
        self._header_data = _header_data

    def parent(self, index):
        """
        INPUTS: QModelIndex
        OUTPUT: QModelIndex
        Should return the parent of the item with the given QModelIndex"""
        item = self.getItem(index)
        parent_item = item.parent()

        if parent_item == self._root_item:
            return QModelIndex()

        if parent_item == None:
            return QModelIndex()

        return self.createIndex(parent_item.row(), 0, parent_item)

    def index(self, row, column, parent):
        """
        Returns the QModelIndex associated with a row/column/parent provided

        Args:
                row (int)
                column (int)
                parent (QModelIndex)

        Returns (QModelIndex)
        """
        parent_item = self.getItem(parent)
        child_item = parent_item.child(row)

        if child_item:
            return self.createIndex(row, column, child_item)
        else:
            return QModelIndex()

    def getItem(self, index):
        """
        Returns the item held by the index provided
        Args:
            index (QModelIndex)
        Returns (AbstractDragDropModelItem)
        """
        if index.isValid():
            item = index.internalPointer()
            if item:
                return item

        return self._root_item

    def getItemName(self, item):
        name = item.columnData()[self._header_data[0]]
        return name

    """ Create index/items"""
    def setItemType(self, item_type):
        self._item_type = item_type

    def itemType(self):
        return self._item_type

    def createNewItem(self, *args, **kwargs):
        """
        Creates a new item of the specified type
        """
        item_type = self.itemType()
        new_item = item_type(*args, **kwargs)

        return new_item

    def insertNewIndex(self, row, name="None", parent=QModelIndex()):
        self.insertRow(row, parent)
        new_index = self.index(row, 0, parent)
        item = new_index.internalPointer()
        item.setColumnData({self._header_data[0]:name})

        return new_index

    """ INSERT INDEXES """
    def insertRows(self, position, num_rows, parent=QModelIndex()):
        """
        INPUTS: int, int, QModelIndex
        """
        parent_item = self.getItem(parent)
        self.beginInsertRows(parent, position, position + num_rows - 1)

        for row in range(num_rows):
            childCount = parent_item.childCount()
            childNode = self.createNewItem()
            success = parent_item.insertChild(position, childNode)

        self.endInsertRows()

        return success

    def removeRows(self, position, num_rows, parent=QModelIndex()):
        """INPUTS: int, int, QModelIndex"""
        # pre flight
        if self._dropping is True:
            self._dropping = False
            return True

        # get parent
        parent_item = self.getItem(parent)

        # remove rows
        self.beginRemoveRows(parent, position, position + num_rows - 1)
        for row in range(num_rows):
            success = parent_item.removeChild(position)
        self.endRemoveRows()

        return success

    def getRootItem(self):
        return self._root_item

    def setRootItem(self, root_item):
        self._root_item = root_item

    """ PROPERTIES """
    @property
    def item_height(self):
        return self._item_height

    @item_height.setter
    def item_height(self, _item_height):
        self._item_height = _item_height

    @property
    def item_width(self):
        return self._item_width

    @item_width.setter
    def item_width(self, _item_width):
        self._item_width = _item_width

    """ DRAG / DROP PROPERTIES """
    def isSelectable(self):
        if self._isSelectable:
            return Qt.ItemIsSelectable
        else:
            return 0

    def setIsSelectable(self, _isSelectable):
        self._isSelectable = _isSelectable

    def isDeleteEnabled(self):
        return self._isDeleteEnabled

    def setIsDeleteEnabled(self, _isDeleteEnabled):
        self._isDeleteEnabled = _isDeleteEnabled

    def isDragEnabled(self):
        if self._isDragEnabled:
            return Qt.ItemIsDragEnabled
        else:
            return 0

    def setIsDragEnabled(self, _isDragEnabled):
        self._isDragEnabled = _isDragEnabled

    def isDropEnabled(self):
        if self._isDropEnabled:
            return Qt.ItemIsDropEnabled
        else:
            return 0

    def setIsDropEnabled(self, _isDropEnabled):
        self._isDropEnabled = _isDropEnabled

    def isEnableable(self):
        return self._isEnableable

    def setIsEnableable(self, _isEnableable):
        self._isEnableable = _isEnableable

    def isRootDropEnabled(self):
        return self._root_drop_enabled

    def setIsRootDropEnabled(self, _root_drop_enabled):
        self._root_drop_enabled = _root_drop_enabled

    def isEditable(self):
        if self._isEditable:
            return Qt.ItemIsEditable
        else:
            return 0

    def setIsEditable(self, _isEditable):
        self._isEditable = _isEditable

    """ DRAG / DROP"""
    def getParentIndexFromItem(self, item):
        """
        Returns the parent index of an item.  This is especially
        useful when doing drag/drop operations

        Args:
            item (item): item whose parent a QModelIndex should be returned for

        Returns (QModelIndex)
        """
        parent_item = item.parent()
        if parent_item == self.getRootItem():
            parent_index = QModelIndex()
        elif not parent_item:
            parent_index = QModelIndex()
        else:
            parent_index = self.createIndex(parent_item.row(), 0, parent_item)
        return parent_index

    def supportedDropActions(self):
        return Qt.MoveAction

    def flags(self, index):
        #https://doc.qt.io/qt-5/qt.html#ItemFlag-enum
        item = index.internalPointer()

        if item:
            # determine flag values
            if self.isSelectable(): selectable = item.isSelectable()
            else: selectable = 0

            if self.isDropEnabled(): drop_enabled = item.isDropEnabled()
            else: drop_enabled = 0

            if self.isDragEnabled(): drag_enabled = item.isDragEnabled()
            else: drag_enabled = 0

            if self.isEditable(): editable = item.isEditable()
            else: editable = 0

            # return flag values
            return (
                Qt.ItemIsEnabled
                | selectable
                | drag_enabled
                | drop_enabled
                | editable
            )

        # set up drag/drop on root node
        if self.isRootDropEnabled(): return Qt.ItemIsEnabled | Qt.ItemIsDropEnabled
        else: return Qt.ItemIsEnabled

    def mimeTypes(self):
        return ['application/x-qabstractitemmodeldatalist']

    def mimeData(self, indexes):
        self.indexes = [index.internalPointer() for index in indexes if index.column() == 0]
        mimedata = QMimeData()
        mimedata.setData('application/x-qabstractitemmodeldatalist', QByteArray())

        # run virtual function
        self.dragStartEvent(self.indexes)
        return mimedata

    def dropMimeData(self, data, action, row, column, parent):
        # bypass remove rows
        self._dropping = True

        # get parent item
        parent_item = parent.internalPointer()
        if not parent_item:
            parent_item = self.getRootItem()

        # iterate through index list
        indexes = self.indexes
        for item in indexes:
            # drop on item
            if row < 0:
                row = 0

            # drop between items
            else:
                # apply offset if dropping below the current location (due to deletion)
                if row > item.row():
                    row -= 1

            # remove item
            self.deleteItem(item, event_update=False)

            # insert item
            self.beginInsertRows(parent, row, row + 1)
            parent_item.insertChild(row, item)
            self.endInsertRows()

        # run virtual function
        self.dropEvent(row, indexes, parent_item)

        return False

    """ VIRTUAL FUNCTIONS """
    def setItemDeleteEvent(self, function):
        self.__itemDeleteEvent = function

    def itemDeleteEvent(self, item):
        self.__itemDeleteEvent(item)

    def __itemDeleteEvent(self, item):
        pass

    def setDragStartEvent(self, function):
        self.__startDragEvent = function

    def dragStartEvent(self, indexes):
        self.__startDragEvent(indexes)

    def __startDragEvent(self, indexes):
        pass

    def setDropEvent(self, function):
        self.__dropEvent = function

    def dropEvent(self, row, indexes, parent):
        """
        Virtual function that is run after the mime data has been dropped.

        Args:
            indexes (list): of AbstractDragDropModelItems
            parent (AbstractDragDropModelItem): item that was dropped on
        """
        self.__dropEvent(row, indexes, parent)

    def __dropEvent(self, row, indexes, parent):
        pass

    def setItemEnabledEvent(self, function):
        self.__itemEnabledEvent = function

    def itemEnabledEvent(self, item, enabled):
        """
        Virtual function is run when an item is enabled/disabled using
        the 'D' key.

        Args:
            item (AbstractDragDropModelItem): item that has been manipulated
            enabled (boolean): whether or not the item was enabled/disabled

        Note:
            This will run through a for each loop and run for every single item in
            the current selection
        """
        self.__itemEnabledEvent(item, enabled)

    def __itemEnabledEvent(self, item, enabled):
        # print(item.columnData()['name'], enabled)
        pass

    def setTextChangedEvent(self, function):
        self.__textChangedEvent = function

    def textChangedEvent(self, item, old_value, new_value):
        """
        Virtual function that is run after the mime data has been dropped.

        Args:
            item (AbstractDragDropModelItem): item that has been manipulated
            old_value (str):
            new_value (str):
        """
        self.__textChangedEvent(item, old_value, new_value)

    def __textChangedEvent(self, item, old_value, new_value):
        print(item, item)
        pass

