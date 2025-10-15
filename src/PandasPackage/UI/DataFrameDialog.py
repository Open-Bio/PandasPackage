"""
DataFrame preview dialog with advanced table features.

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


class DataFrameDialog(QtWidgets.QDialog):
    """Dialog for displaying DataFrame with pagination, sorting, and filtering."""

    def __init__(self, dataframe=None, pin_name="data", parent=None):
        super(DataFrameDialog, self).__init__(parent)
        self.pin_name = pin_name
        self.original_dataframe = dataframe if dataframe is not None else pd.DataFrame()
        self.settings = QtCore.QSettings("uflow", "DataFrameDialog")
        self.setupUI()
        self.setDataFrame(self.original_dataframe)
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

    def restoreWindowGeometry(self):
        """Restore window position and size from settings."""
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        else:
            # First time: center on screen
            self.centerOnScreen()

    def centerOnScreen(self):
        """Center the dialog on the screen."""
        screen = QtWidgets.QApplication.primaryScreen()
        if screen:
            screenGeometry = screen.availableGeometry()
            x = (screenGeometry.width() - self.width()) // 2
            y = (screenGeometry.height() - self.height()) // 2
            self.move(x, y)

    def closeEvent(self, event):
        """Save window geometry when closing."""
        self.settings.setValue("geometry", self.saveGeometry())
        super(DataFrameDialog, self).closeEvent(event)

    def accept(self):
        """Save geometry before accepting."""
        self.settings.setValue("geometry", self.saveGeometry())
        super(DataFrameDialog, self).accept()

    def reject(self):
        """Save geometry before rejecting."""
        self.settings.setValue("geometry", self.saveGeometry())
        super(DataFrameDialog, self).reject()


class MultiDataFrameDialog(QtWidgets.QDialog):
    """Dialog for displaying multiple DataFrames in tabs."""

    def __init__(self, dataframes_dict, parent=None):
        """
        Args:
            dataframes_dict: dict of {pin_name: dataframe}
        """
        super(MultiDataFrameDialog, self).__init__(parent)
        self.dataframes = dataframes_dict
        self.settings = QtCore.QSettings("uflow", "MultiDataFrameDialog")
        self.setupUI()
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

    def restoreWindowGeometry(self):
        """Restore window position and size from settings."""
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        else:
            # First time: center on screen
            self.centerOnScreen()

    def centerOnScreen(self):
        """Center the dialog on the screen."""
        screen = QtWidgets.QApplication.primaryScreen()
        if screen:
            screenGeometry = screen.availableGeometry()
            x = (screenGeometry.width() - self.width()) // 2
            y = (screenGeometry.height() - self.height()) // 2
            self.move(x, y)

    def closeEvent(self, event):
        """Save window geometry when closing."""
        self.settings.setValue("geometry", self.saveGeometry())
        super(MultiDataFrameDialog, self).closeEvent(event)

    def accept(self):
        """Save geometry before accepting."""
        self.settings.setValue("geometry", self.saveGeometry())
        super(MultiDataFrameDialog, self).accept()

    def reject(self):
        """Save geometry before rejecting."""
        self.settings.setValue("geometry", self.saveGeometry())
        super(MultiDataFrameDialog, self).reject()
