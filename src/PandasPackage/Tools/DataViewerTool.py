from qtpy import QtWidgets, QtGui
import pandas as pd

from uflow.UI.Tool.Tool import DockTool
from ..UI.DataFrameViewerWidget import DataFrameViewerWidget


class DataViewerTool(DockTool):
    """Data viewer tool for displaying DataFrame data in a table format.

    Features:
    - Advanced table view with sorting and filtering
    - Search functionality
    - Statistics panel
    - Supports multiple instances (not singleton)
    - Freely dockable and floatable
    """

    def __init__(self):
        super(DataViewerTool, self).__init__()

        # Setup scrollable area for better layout
        self.scrollArea = QtWidgets.QScrollArea(self)
        self.scrollArea.setWidgetResizable(True)
        self.setWidget(self.scrollArea)

        # Create the viewer widget
        self.viewerWidget = DataFrameViewerWidget()
        self.scrollArea.setWidget(self.viewerWidget)

        # Setup toolbar buttons
        self.setupToolbarButtons()

        # Set window title
        self.setWindowTitle(self.uniqueName())

    def setupToolbarButtons(self):
        """Setup toolbar buttons for the tool."""
        # Export button
        self.exportButton = QtWidgets.QToolButton()
        self.exportButton.setText("Export CSV")
        self.exportButton.setToolTip("Export current data to CSV file")
        # 使用Qt内置图标
        self.exportButton.setIcon(
            self.style().standardIcon(QtWidgets.QStyle.SP_DialogSaveButton)
        )
        self.exportButton.clicked.connect(self.exportToCSV)
        self.addButton(self.exportButton)

        # Clear button
        self.clearButton = QtWidgets.QToolButton()
        self.clearButton.setText("Clear")
        self.clearButton.setToolTip("Clear the viewer")
        # 使用Qt内置图标
        self.clearButton.setIcon(
            self.style().standardIcon(QtWidgets.QStyle.SP_DialogDiscardButton)
        )
        self.clearButton.clicked.connect(self.clear)
        self.addButton(self.clearButton)

    def setDataFrame(self, df):
        """Set the DataFrame to display in the viewer."""
        if self.viewerWidget:
            self.viewerWidget.setDataFrame(df)

    def getDataFrame(self):
        """Get the current DataFrame."""
        if self.viewerWidget:
            return self.viewerWidget.getDataFrame()
        return pd.DataFrame()

    def clear(self):
        """Clear the viewer."""
        if self.viewerWidget:
            self.viewerWidget.clear()

    def exportToCSV(self):
        """Export the current DataFrame to CSV file."""
        df = self.getDataFrame()
        if df.empty:
            QtWidgets.QMessageBox.warning(self, "No Data", "No data to export")
            return

        fileName, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Export to CSV", "", "CSV Files (*.csv);;All Files (*)"
        )

        if fileName:
            try:
                df.to_csv(fileName, index=True)
                QtWidgets.QMessageBox.information(
                    self, "Success", f"Data exported to {fileName}"
                )
            except Exception as e:
                QtWidgets.QMessageBox.critical(
                    self, "Export Error", f"Failed to export: {e}"
                )

    @staticmethod
    def getIcon():
        return QtGui.QIcon(":brick.png")

    @staticmethod
    def toolTip():
        return "Data table viewer for DataFrame preview with advanced features"

    @staticmethod
    def isSingleton():
        # Allow multiple instances for comparing different DataFrames
        return False

    @staticmethod
    def name():
        return str("DataViewer")
