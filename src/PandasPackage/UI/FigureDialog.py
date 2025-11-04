"""
Single Figure preview dialog for matplotlib Figure objects.

Simplified dialog for displaying a single Figure with interactive features.
"""

from qtpy import QtWidgets, QtCore, QtGui
from .PlotViewerWidget import PlotViewerWidget
from ._dialog_persistence import PersistentGeometryDialogMixin

try:
    import matplotlib.figure
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


class FigureDialog(PersistentGeometryDialogMixin, QtWidgets.QDialog):
    """用于展示单个 matplotlib Figure 的对话框。

    变更点：
    - 继承 PersistentGeometryDialogMixin 统一管理窗口几何信息保存/恢复。
    - 在 closeEvent 中先清理 PlotViewerWidget（断开 matplotlib 回调），再交由 Mixin 保存 geometry。
    """

    def __init__(self, figure=None, pin_name="figure", parent=None):
        super(FigureDialog, self).__init__(parent)
        self.pin_name = pin_name
        self.current_figure = figure
        # 仍保留原 settings，Mixin 会优先使用此实例，确保兼容旧的持久化位置
        self.settings = QtCore.QSettings("uflow", "FigureDialog")
        self.setupUI()
        if figure is not None:
            self.setFigure(figure)
        # 统一通过 Mixin 恢复几何信息
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

    def closeEvent(self, event):
        """关闭时先清理 PlotViewerWidget，再交由 Mixin 保存窗口几何信息。"""
        # 先确保嵌入的 PlotViewerWidget 断开回调并清理
        try:
            if hasattr(self, "plotViewer") and self.plotViewer:
                self.plotViewer.clear()
        except Exception:
            pass
        # 调用 Mixin 的 closeEvent（通过 super）统一保存 geometry
        super(FigureDialog, self).closeEvent(event)


