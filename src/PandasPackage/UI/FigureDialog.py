"""
Single Figure preview dialog for matplotlib Figure objects.

Simplified dialog for displaying a single Figure with interactive features.
"""

from qtpy import QtWidgets, QtCore, QtGui
from .PlotViewerWidget import PlotViewerWidget

try:
    import matplotlib.figure
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


class FigureDialog(QtWidgets.QDialog):
    """Dialog for displaying a single matplotlib Figure."""

    def __init__(self, figure=None, pin_name="figure", parent=None):
        super(FigureDialog, self).__init__(parent)
        self.pin_name = pin_name
        self.current_figure = figure
        self.settings = QtCore.QSettings("uflow", "FigureDialog")
        self.setupUI()
        if figure is not None:
            self.setFigure(figure)
        self.restoreWindowGeometry()

    def setupUI(self):
        """Setup the dialog UI."""
        self.setWindowTitle(f"Figure Viewer - {self.pin_name}")
        self.setMinimumSize(800, 600)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Use PlotViewerWidget for consistent display
        self.plotViewer = PlotViewerWidget()
        layout.addWidget(self.plotViewer)

        # Bottom buttons
        buttonLayout = QtWidgets.QHBoxLayout()
        buttonLayout.addStretch()

        self.closeButton = QtWidgets.QPushButton("Close")
        self.closeButton.clicked.connect(self.accept)
        buttonLayout.addWidget(self.closeButton)

        layout.addLayout(buttonLayout)

    def setFigure(self, figure):
        """Set the matplotlib Figure to display."""
        self.current_figure = figure
        if self.plotViewer:
            self.plotViewer.setFigure(figure)

    def getFigure(self):
        """Get the current Figure."""
        return self.current_figure

    def restoreWindowGeometry(self):
        """Restore window position and size from settings."""
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        else:
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
        # Ensure the embedded PlotViewerWidget disconnects callbacks and clears
        try:
            if hasattr(self, "plotViewer") and self.plotViewer:
                self.plotViewer.clear()
        except Exception:
            pass
        self.settings.setValue("geometry", self.saveGeometry())
        super(FigureDialog, self).closeEvent(event)

    def accept(self):
        """Save geometry before accepting."""
        self.settings.setValue("geometry", self.saveGeometry())
        super(FigureDialog, self).accept()

    def reject(self):
        """Save geometry before rejecting."""
        self.settings.setValue("geometry", self.saveGeometry())
        super(FigureDialog, self).reject()


