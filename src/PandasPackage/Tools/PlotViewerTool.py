from qtpy import QtWidgets, QtGui

from uflow.UI.Tool.Tool import DockTool
from ..UI.PlotViewerWidget import PlotViewerWidget


class PlotViewerTool(DockTool):
    """Plot viewer tool for displaying matplotlib Figure objects.

    Features:
    - Interactive matplotlib plots with zoom and pan
    - Save plots to various formats (PNG, PDF, SVG)
    - Supports multiple instances (not singleton)
    - Freely dockable and floatable
    """

    def __init__(self):
        super(PlotViewerTool, self).__init__()

        # Setup scrollable area for better layout
        self.scrollArea = QtWidgets.QScrollArea(self)
        self.scrollArea.setWidgetResizable(True)
        self.setWidget(self.scrollArea)

        # Create the viewer widget
        self.viewerWidget = PlotViewerWidget()
        self.scrollArea.setWidget(self.viewerWidget)

        # Set window title
        self.setWindowTitle(self.uniqueName())

    def setFigure(self, figure):
        """Set the matplotlib Figure to display in the viewer.
        
        Args:
            figure: matplotlib.figure.Figure object or None
        """
        if self.viewerWidget:
            self.viewerWidget.setFigure(figure)

    def getFigure(self):
        """Get the current Figure."""
        if self.viewerWidget:
            return self.viewerWidget.getFigure()
        return None

    def clear(self):
        """Clear the viewer."""
        if self.viewerWidget:
            self.viewerWidget.clear()

    @staticmethod
    def getIcon():
        return QtGui.QIcon(":brick.png")

    @staticmethod
    def toolTip():
        return "Interactive matplotlib plot viewer with zoom, pan, and save capabilities"

    @staticmethod
    def isSingleton():
        # Allow multiple instances for comparing different plots
        return False

    @staticmethod
    def name():
        return str("PlotViewer")

