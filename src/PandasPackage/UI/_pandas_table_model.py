"""
统一的 Pandas 表格模型（带分页与对齐优化）。

目的：
- 消除多个模块中重复的 `PandasTableModel` 定义，降低维护成本。
"""

from qtpy import QtCore
import pandas as pd


class PandasTableModel(QtCore.QAbstractTableModel):
    """用于 pandas DataFrame 的表格模型，支持分页显示。"""

    def __init__(self, dataframe=None, parent=None):
        super(PandasTableModel, self).__init__(parent)
        self._dataframe = dataframe if dataframe is not None else pd.DataFrame()
        # 分页相关属性
        self._page_size = 10  # 默认每页 10 行
        self._current_page = 0
        self._show_all = False  # 是否显示全部

    def rowCount(self, parent=QtCore.QModelIndex()):
        if self._show_all:
            return len(self._dataframe)
        total_rows = len(self._dataframe)
        start_row = self._current_page * self._page_size
        return max(0, min(self._page_size, total_rows - start_row))

    def columnCount(self, parent=QtCore.QModelIndex()):
        return len(self._dataframe.columns)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None

        # 计算实际行索引
        actual_row = (
            index.row() if self._show_all else self._current_page * self._page_size + index.row()
        )

        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            value = self._dataframe.iloc[actual_row, index.column()]
            if pd.isna(value):
                return ""
            return str(value)

        if role == QtCore.Qt.TextAlignmentRole:
            # 数值列右对齐，其他列左对齐
            if pd.api.types.is_numeric_dtype(self._dataframe.iloc[:, index.column()]):
                return QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
            return QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter

        return None

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if role != QtCore.Qt.DisplayRole:
            return None
        if orientation == QtCore.Qt.Horizontal:
            return str(self._dataframe.columns[section])
        # 垂直方向显示真实的 DataFrame 索引
        actual_row = section if self._show_all else self._current_page * self._page_size + section
        return str(self._dataframe.index[actual_row])

    def setDataFrame(self, dataframe):
        """更新模型数据，并回到第一页。"""
        self.beginResetModel()
        self._dataframe = dataframe if dataframe is not None else pd.DataFrame()
        self._current_page = 0
        self.endResetModel()

    def getDataFrame(self):
        return self._dataframe

    def setPageSize(self, size):
        """设置每页行数，-1 表示显示全部。"""
        if size == -1:
            self._show_all = True
        else:
            self._show_all = False
            self._page_size = size
        self._current_page = 0
        self.beginResetModel()
        self.endResetModel()

    def setCurrentPage(self, page):
        """设置当前页。"""
        self._current_page = max(0, int(page))
        self.beginResetModel()
        self.endResetModel()

    def getTotalPages(self):
        """获取总页数。显示全部或空数据时返回 1。"""
        if self._show_all or len(self._dataframe) == 0:
            return 1
        return (len(self._dataframe) - 1) // self._page_size + 1

    def getCurrentPage(self):
        return self._current_page

    def getPageSize(self):
        return self._page_size if not self._show_all else -1


