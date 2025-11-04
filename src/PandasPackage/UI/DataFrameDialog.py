"""
DataFrame preview dialog with advanced table features.

Uses Qt Model/View architecture for better performance with large datasets.
"""

from qtpy import QtWidgets, QtCore, QtGui
import pandas as pd
from ._dialog_persistence import PersistentGeometryDialogMixin
from ._pandas_table_model import PandasTableModel


class DataFrameDialog(PersistentGeometryDialogMixin, QtWidgets.QDialog):
    """Dialog for displaying DataFrame with pagination, sorting, and filtering."""

    def __init__(self, dataframe=None, pin_name="data", parent=None):
        super(DataFrameDialog, self).__init__(parent)
        self.pin_name = pin_name
        self.original_dataframe = dataframe if dataframe is not None else pd.DataFrame()
        # 保留原 settings，Mixin 会优先使用此实例
        self.settings = QtCore.QSettings("uflow", "DataFrameDialog")
        self.setupUI()
        self.setDataFrame(self.original_dataframe)
        # 统一通过 Mixin 恢复几何信息
        self.restoreWindowGeometry()

    def setupUI(self):
        """Setup the dialog UI."""
        self.setWindowTitle(f"DataFrame Viewer - {self.pin_name}")
        self.setMinimumSize(800, 600)

        layout = QtWidgets.QVBoxLayout(self)

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
        self.searchBox.setPlaceholderText("Search in table...")
        self.searchBox.setMaximumWidth(200)
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

        # Bottom buttons
        buttonLayout = QtWidgets.QHBoxLayout()

        self.exportButton = QtWidgets.QPushButton("Export to CSV...")
        self.exportButton.clicked.connect(self.exportToCSV)
        buttonLayout.addWidget(self.exportButton)

        buttonLayout.addStretch()

        self.closeButton = QtWidgets.QPushButton("Close")
        self.closeButton.clicked.connect(self.accept)
        buttonLayout.addWidget(self.closeButton)

        layout.addLayout(buttonLayout)

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
            f"Shape: {rows:,} rows × {cols} columns | Memory: {memory_usage:.2f} MB"
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
            stats = self.original_dataframe.describe(include="all").to_string()
            self.statsText.setText(stats)
        except Exception as e:
            self.statsText.setText(f"Error generating statistics: {e}")

    def exportToCSV(self):
        """Export the DataFrame to CSV file."""
        if self.original_dataframe.empty:
            QtWidgets.QMessageBox.warning(self, "No Data", "No data to export")
            return

        fileName, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Export to CSV", "", "CSV Files (*.csv);;All Files (*)"
        )

        if fileName:
            try:
                self.original_dataframe.to_csv(fileName, index=True)
                QtWidgets.QMessageBox.information(
                    self, "Success", f"Data exported to {fileName}"
                )
            except Exception as e:
                QtWidgets.QMessageBox.critical(
                    self, "Export Error", f"Failed to export: {e}"
                )

    # 几何信息保存/恢复逻辑由 Mixin 统一处理


class MultiDataFrameDialog(PersistentGeometryDialogMixin, QtWidgets.QDialog):
    """Dialog for displaying multiple DataFrames in tabs."""

    def __init__(self, dataframes_dict, parent=None):
        """
        Args:
            dataframes_dict: dict of {pin_name: dataframe}
        """
        super(MultiDataFrameDialog, self).__init__(parent)
        self.dataframes = dataframes_dict
        # 保留原 settings，Mixin 会优先使用此实例
        self.settings = QtCore.QSettings("uflow", "MultiDataFrameDialog")
        self.setupUI()
        # 统一通过 Mixin 恢复几何信息
        self.restoreWindowGeometry()

    def setupUI(self):
        """Setup the dialog UI."""
        self.setWindowTitle("DataFrame Viewer - Multiple Pins")
        self.setMinimumSize(900, 700)

        layout = QtWidgets.QVBoxLayout(self)

        # Tab widget for multiple DataFrames
        self.tabWidget = QtWidgets.QTabWidget()

        for pin_name, dataframe in self.dataframes.items():
            # Create a widget for each DataFrame
            widget = QtWidgets.QWidget()
            tabLayout = QtWidgets.QVBoxLayout(widget)

            # Info label
            infoLabel = QtWidgets.QLabel()
            if dataframe is not None and not dataframe.empty:
                rows, cols = dataframe.shape
                memory_usage = dataframe.memory_usage(deep=True).sum() / 1024 / 1024
                infoLabel.setText(
                    f"Shape: {rows:,} rows × {cols} columns | Memory: {memory_usage:.2f} MB"
                )
            else:
                infoLabel.setText("No data")
            infoLabel.setStyleSheet("font-weight: bold; color: #666; padding: 5px;")
            tabLayout.addWidget(infoLabel)

            # Table view
            model = PandasTableModel(dataframe)
            proxyModel = QtCore.QSortFilterProxyModel()
            proxyModel.setSourceModel(model)

            tableView = QtWidgets.QTableView()
            tableView.setModel(proxyModel)
            tableView.setSortingEnabled(True)
            tableView.setAlternatingRowColors(True)
            tableView.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
            tableView.horizontalHeader().setStretchLastSection(True)
            tableView.resizeColumnsToContents()

            tabLayout.addWidget(tableView)

            # Add tab
            self.tabWidget.addTab(widget, pin_name)

        layout.addWidget(self.tabWidget)

        # Close button
        buttonLayout = QtWidgets.QHBoxLayout()
        buttonLayout.addStretch()

        closeButton = QtWidgets.QPushButton("Close")
        closeButton.clicked.connect(self.accept)
        buttonLayout.addWidget(closeButton)

        layout.addLayout(buttonLayout)

    # 几何信息保存/恢复逻辑由 Mixin 统一处理
