"""
Properties dialog for displaying node properties in a floating window.

Based on DataFrameDialog.py design pattern, provides non-modal property editing
with window state persistence and support for multiple instances.
"""

from qtpy import QtWidgets, QtCore, QtGui
from uflow.UI.Widgets.PropertiesFramework import PropertiesWidget


class PropertiesDialog(QtWidgets.QDialog):
    """Non-modal dialog for displaying node properties with floating window support."""

    def __init__(self, node=None, parent=None):
        super(PropertiesDialog, self).__init__(parent)
        self.node = node
        self.settings = QtCore.QSettings("uflow", "PropertiesDialog")
        self.setupUI()
        self.restoreWindowGeometry()

    def setupUI(self):
        """Setup the dialog UI."""
        self.setWindowTitle("Node Properties")
        self.setMinimumSize(400, 300)
        self.setModal(False)  # Non-modal dialog

        layout = QtWidgets.QVBoxLayout(self)

        # Create scroll area for properties widget
        self.scrollArea = QtWidgets.QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.scrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)

        # Create properties widget
        self.propertiesWidget = PropertiesWidget()
        self.scrollArea.setWidget(self.propertiesWidget)
        layout.addWidget(self.scrollArea)

        # Bottom buttons
        buttonLayout = QtWidgets.QHBoxLayout()

        self.closeButton = QtWidgets.QPushButton("Close")
        self.closeButton.clicked.connect(self.accept)
        buttonLayout.addWidget(self.closeButton)

        layout.addLayout(buttonLayout)

    def setNode(self, node, propertiesFillDelegate):
        """Set the node to display properties for."""
        self.node = node
        if node:
            self.setWindowTitle(f"Properties - {node.getName()}")
            # Clear existing properties and fill with new node's properties
            self.propertiesWidget.clear()
            if propertiesFillDelegate:
                propertiesFillDelegate(self.propertiesWidget)
        else:
            self.setWindowTitle("Node Properties")
            self.propertiesWidget.clear()

    def clear(self):
        """Clear the properties display."""
        self.propertiesWidget.clear()
        self.node = None
        self.setWindowTitle("Node Properties")

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
        super(PropertiesDialog, self).closeEvent(event)

    def accept(self):
        """Save geometry before accepting."""
        self.settings.setValue("geometry", self.saveGeometry())
        super(PropertiesDialog, self).accept()

    def reject(self):
        """Save geometry before rejecting."""
        self.settings.setValue("geometry", self.saveGeometry())
        super(PropertiesDialog, self).reject()
