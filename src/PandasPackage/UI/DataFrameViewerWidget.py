"""
DataFrame viewer widget for use in DockTools.

Reusable widget extracted from DataFrameDialog with advanced table features.
Uses Qt Model/View architecture for better performance with large datasets.
"""

from qtpy import QtWidgets, QtCore, QtGui
import pandas as pd


class PandasTableModel(QtCore.QAbstractTableModel):
    """Table model for pandas DataFrame with efficient data access and pagination."""

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
        else:
            # 返回当前页的行数
            total_rows = len(self._dataframe)
            start_row = self._current_page * self._page_size
            return min(self._page_size, total_rows - start_row)

    def columnCount(self, parent=QtCore.QModelIndex()):
        return len(self._dataframe.columns)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None

        # 调整索引以访问正确的数据行
        if self._show_all:
            actual_row = index.row()
        else:
            actual_row = self._current_page * self._page_size + index.row()

        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            value = self._dataframe.iloc[actual_row, index.column()]
            if pd.isna(value):
                return ""
            return str(value)

        elif role == QtCore.Qt.TextAlignmentRole:
            # Right align numeric columns
            if pd.api.types.is_numeric_dtype(self._dataframe.iloc[:, index.column()]):
                return QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
            return QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter

        return None

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return str(self._dataframe.columns[section])
            elif orientation == QtCore.Qt.Vertical:
                # 调整行索引显示
                if self._show_all:
                    actual_row = section
                else:
                    actual_row = self._current_page * self._page_size + section
                return str(self._dataframe.index[actual_row])
        return None

    def setDataFrame(self, dataframe):
        """Update the model with a new DataFrame."""
        self.beginResetModel()
        self._dataframe = dataframe if dataframe is not None else pd.DataFrame()
        self._current_page = 0  # 重置到第一页
        self.endResetModel()

    def getDataFrame(self):
        """Get the current DataFrame."""
        return self._dataframe

    def setPageSize(self, size):
        """设置每页行数，-1 表示显示全部"""
        if size == -1:
            self._show_all = True
        else:
            self._show_all = False
            self._page_size = size
        self._current_page = 0
        self.beginResetModel()
        self.endResetModel()

    def setCurrentPage(self, page):
        """设置当前页"""
        self._current_page = page
        self.beginResetModel()
        self.endResetModel()

    def getTotalPages(self):
        """获取总页数"""
        if self._show_all or len(self._dataframe) == 0:
            return 1
        return (len(self._dataframe) - 1) // self._page_size + 1

    def getCurrentPage(self):
        return self._current_page

    def getPageSize(self):
        return self._page_size if not self._show_all else -1


class DataFrameViewerWidget(QtWidgets.QWidget):
    """Widget for displaying DataFrame with search, sorting, and statistics."""

    def __init__(self, parent=None):
        super(DataFrameViewerWidget, self).__init__(parent)
        self.original_dataframe = pd.DataFrame()
        self.setupUI()

    def setupUI(self):
        """Setup the widget UI."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Info bar
        infoLayout = QtWidgets.QHBoxLayout()

        self.infoLabel = QtWidgets.QLabel("No data")
        self.infoLabel.setStyleSheet("font-weight: bold; color: #666;")
        infoLayout.addWidget(self.infoLabel)

        infoLayout.addStretch()

        # 分页控件
        paginationLayout = QtWidgets.QHBoxLayout()
        paginationLayout.addWidget(QtWidgets.QLabel("每页行数:"))

        self.pageSizeCombo = QtWidgets.QComboBox()
        self.pageSizeCombo.addItems(["10", "50", "100", "500", "全部"])
        self.pageSizeCombo.setCurrentIndex(0)  # 默认 10 行
        self.pageSizeCombo.currentIndexChanged.connect(self.onPageSizeChanged)
        paginationLayout.addWidget(self.pageSizeCombo)

        self.prevPageBtn = QtWidgets.QPushButton("◀")
        self.prevPageBtn.setMaximumWidth(30)
        self.prevPageBtn.clicked.connect(self.onPrevPage)
        paginationLayout.addWidget(self.prevPageBtn)

        self.pageLabel = QtWidgets.QLabel("1/1")
        paginationLayout.addWidget(self.pageLabel)

        self.nextPageBtn = QtWidgets.QPushButton("▶")
        self.nextPageBtn.setMaximumWidth(30)
        self.nextPageBtn.clicked.connect(self.onNextPage)
        paginationLayout.addWidget(self.nextPageBtn)

        infoLayout.addLayout(paginationLayout)

        # Search box
        self.searchBox = QtWidgets.QLineEdit()
        self.searchBox.setPlaceholderText("Search...")
        self.searchBox.setMaximumWidth(150)
        self.searchBox.textChanged.connect(self.onSearchChanged)
        infoLayout.addWidget(QtWidgets.QLabel("Search:"))
        infoLayout.addWidget(self.searchBox)

        layout.addLayout(infoLayout)

        # Table view with model
        self.model = PandasTableModel()
        self.proxyModel = QtCore.QSortFilterProxyModel()
        self.proxyModel.setSourceModel(self.model)
        self.proxyModel.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)

        self.tableView = QtWidgets.QTableView()
        self.tableView.setModel(self.proxyModel)
        self.tableView.setSortingEnabled(True)
        self.tableView.setAlternatingRowColors(True)
        self.tableView.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.tableView.horizontalHeader().setStretchLastSection(True)
        self.tableView.verticalHeader().setDefaultSectionSize(24)

        layout.addWidget(self.tableView)

        # Statistics panel (collapsible)
        self.statsGroup = QtWidgets.QGroupBox("Statistics")
        self.statsGroup.setCheckable(True)
        self.statsGroup.setChecked(False)
        statsLayout = QtWidgets.QVBoxLayout()

        self.statsText = QtWidgets.QTextEdit()
        self.statsText.setReadOnly(True)
        self.statsText.setMaximumHeight(150)
        statsLayout.addWidget(self.statsText)

        self.statsGroup.setLayout(statsLayout)
        self.statsGroup.toggled.connect(self.onStatsToggled)
        layout.addWidget(self.statsGroup)

    def setDataFrame(self, dataframe):
        """Set the DataFrame to display."""
        if dataframe is None or dataframe.empty:
            self.original_dataframe = pd.DataFrame()
            self.model.setDataFrame(self.original_dataframe)
            self.infoLabel.setText("No data")
            self.statsText.clear()
            return

        self.original_dataframe = dataframe.copy()
        self.model.setDataFrame(self.original_dataframe)

        # Update info
        rows, cols = dataframe.shape
        memory_usage = dataframe.memory_usage(deep=True).sum() / 1024 / 1024  # MB
        self.infoLabel.setText(
            f"Shape: {rows:,} rows × {cols} columns | "
            f"Memory: {memory_usage:.2f} MB"
        )

        # Auto-resize columns
        self.tableView.resizeColumnsToContents()

        # Update statistics if panel is open
        if self.statsGroup.isChecked():
            self.updateStatistics()

        # 更新分页 UI
        self.updatePaginationUI()

    def onPageSizeChanged(self, index):
        """处理每页行数变化"""
        page_sizes = [10, 50, 100, 500, -1]  # -1 表示全部
        page_size = page_sizes[index]
        self.model.setPageSize(page_size)
        self.updatePaginationUI()

    def onPrevPage(self):
        """上一页"""
        current = self.model.getCurrentPage()
        if current > 0:
            self.model.setCurrentPage(current - 1)
            self.updatePaginationUI()

    def onNextPage(self):
        """下一页"""
        current = self.model.getCurrentPage()
        total = self.model.getTotalPages()
        if current < total - 1:
            self.model.setCurrentPage(current + 1)
            self.updatePaginationUI()

    def updatePaginationUI(self):
        """更新分页 UI 状态"""
        current = self.model.getCurrentPage()
        total = self.model.getTotalPages()
        
        self.pageLabel.setText(f"{current + 1}/{total}")
        
        # 显示全部时禁用翻页按钮
        show_all = self.model.getPageSize() == -1
        self.prevPageBtn.setEnabled(not show_all and current > 0)
        self.nextPageBtn.setEnabled(not show_all and current < total - 1)

    def getDataFrame(self):
        """Get the current DataFrame."""
        return self.original_dataframe

    def onSearchChanged(self, text):
        """Handle search text changes."""
        # Apply filter to all columns
        self.proxyModel.setFilterFixedString(text)

    def onStatsToggled(self, checked):
        """Handle statistics panel toggle."""
        if checked:
            self.updateStatistics()

    def updateStatistics(self):
        """Update the statistics panel."""
        if self.original_dataframe.empty:
            self.statsText.setText("No data to analyze")
            return

        try:
            # Generate statistics
            stats = self.original_dataframe.describe(include='all').to_string()
            self.statsText.setText(stats)
        except Exception as e:
            self.statsText.setText(f"Error generating statistics: {e}")

    def clear(self):
        """Clear the viewer."""
        self.setDataFrame(pd.DataFrame())
