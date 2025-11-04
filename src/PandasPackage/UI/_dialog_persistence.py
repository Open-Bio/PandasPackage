from qtpy import QtWidgets, QtCore


class PersistentGeometryDialogMixin:
    """
    持久化对话框几何信息的 Mixin。

    设计目标：
    - 统一管理窗口位置与大小的保存/恢复逻辑，消除各个对话框中重复代码。
    - 尽量与现有行为兼容：如果子类已有 `self.settings`（QSettings 实例），优先使用；
      否则按类名构造默认 QSettings("uflow", <ClassName>)。
    - 提供通用的 `restoreWindowGeometry`、`centerOnScreen`，并在 `closeEvent/accept/reject`
      中统一保存 geometry。
    """

    def _settings(self) -> QtCore.QSettings:
        """获取用于持久化的 QSettings。
        优先返回子类设置的 `self.settings`；否则按类名构造默认实例。
        """
        if hasattr(self, "settings") and isinstance(self.settings, QtCore.QSettings):
            return self.settings
        # 兼容：默认按类名分组，避免相互覆盖
        return QtCore.QSettings("uflow", type(self).__name__)

    def restoreWindowGeometry(self):
        """恢复窗口位置与大小；若无历史记录，则居中显示。"""
        geometry = self._settings().value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        else:
            self.centerOnScreen()

    def centerOnScreen(self):
        """将窗口移动到屏幕中心（仅在首次显示时使用）。"""
        screen = QtWidgets.QApplication.primaryScreen()
        if screen:
            screenGeometry = screen.availableGeometry()
            x = (screenGeometry.width() - self.width()) // 2
            y = (screenGeometry.height() - self.height()) // 2
            self.move(x, y)

    def _saveGeometry_(self):
        """统一保存窗口几何信息。"""
        self._settings().setValue("geometry", self.saveGeometry())

    def closeEvent(self, event):
        """在关闭时保存geometry，并调用父类逻辑。"""
        self._saveGeometry_()
        super(PersistentGeometryDialogMixin, self).closeEvent(event)

    def accept(self):
        """在接受时保存geometry，并调用父类逻辑。"""
        self._saveGeometry_()
        super(PersistentGeometryDialogMixin, self).accept()

    def reject(self):
        """在拒绝时保存geometry，并调用父类逻辑。"""
        self._saveGeometry_()
        super(PersistentGeometryDialogMixin, self).reject()


