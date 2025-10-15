"""
DataFrame viewer widget for use in DockTools.

Reusable widget extracted from DataFrameDialog with advanced table features.
Uses Qt Model/View architecture for better performance with large datasets.
"""

from qtpy import QtWidgets, QtCore, QtGui
import pandas as pd


class PandasTableModel(QtCore.QAbstractTableModel):
    """Table model for pandas DataFrame with efficient data access."""

    def __init__(self, dataframe=None, parent=None):
        super(PandasTableModel, self).__init__(parent)
        self._dataframe = dataframe if dataframe is not None else pd.DataFrame()

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self._dataframe)

    def columnCount(self, parent=QtCore.QModelIndex()):
        return len(self._dataframe.columns)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None

        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            value = self._dataframe.iloc[index.row(), index.column()]
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
                return str(self._dataframe.index[section])
        return None

    def setDataFrame(self, dataframe):
        """Update the model with a new DataFrame."""
        self.beginResetModel()
        self._dataframe = dataframe if dataframe is not None else pd.DataFrame()
        self.endResetModel()

    def getDataFrame(self):
        """Get the current DataFrame."""
        return self._dataframe


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
