"""
Properties dialog for displaying node properties in a floating window.

Based on DataFrameDialog.py design pattern, provides non-modal property editing
with window state persistence and support for multiple instances.
"""

from qtpy import QtWidgets, QtCore, QtGui
from uflow.UI.Widgets.PropertiesFramework import PropertiesWidget
from ._dialog_persistence import PersistentGeometryDialogMixin


class PropertiesDialog(PersistentGeometryDialogMixin, QtWidgets.QDialog):
    """非模态属性对话框，支持悬浮显示与几何信息持久化（通过 Mixin 统一实现）。"""

    def __init__(self, node=None, parent=None):
        super(PropertiesDialog, self).__init__(parent)
        self.node = node
        # 保留原 settings，Mixin 会优先使用此实例
        self.settings = QtCore.QSettings("uflow", "PropertiesDialog")
        self.setupUI()
        # 统一通过 Mixin 恢复几何信息
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

    # 恢复/保存几何信息与关闭、接受、拒绝的逻辑由 Mixin 统一处理
