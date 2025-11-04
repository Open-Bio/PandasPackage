"""
Mixed data viewer dialog supporting both DataFrame and Matplotlib Figure objects.

Uses tabs to organize multiple pins, with each tab displaying the appropriate
viewer based on data type (DataFrame -> table, Figure -> plot).
"""

from qtpy import QtWidgets, QtCore, QtGui
import pandas as pd
from .DataFrameDialog import PandasTableModel
from .PlotViewerWidget import PlotViewerWidget
from ._dialog_persistence import PersistentGeometryDialogMixin
from ..Pins import DATAFRAME_PIN, MPL_FIGURE_PIN

try:
    import matplotlib.figure
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


class MixedDataViewerDialog(PersistentGeometryDialogMixin, QtWidgets.QDialog):
    """用于展示多个不同类型（DataFrame 与 Figure）数据的多标签对话框。

    变更点：
    - 继承 PersistentGeometryDialogMixin，统一管理窗口几何信息保存/恢复。
    - 使用集中常量 `DATAFRAME_PIN` 与 `MPL_FIGURE_PIN`，避免魔法字符串。
    """

    def __init__(self, pins_data_dict, parent=None):
        """
        Args:
            pins_data_dict: dict of {pin_name: (pin_type, data)}
                pin_type: "DataFramePin" or "MatplotlibFigurePin"
                data: pandas.DataFrame or matplotlib.figure.Figure
        """
        super(MixedDataViewerDialog, self).__init__(parent)
        self.pins_data = pins_data_dict
        # 保留原 settings，Mixin 会优先使用此实例
        self.settings = QtCore.QSettings("uflow", "MixedDataViewerDialog")
        self.setupUI()
        self.restoreWindowGeometry()

    def setupUI(self):
        """Setup the dialog UI."""
        self.setWindowTitle("Data Viewer - Multiple Pins")
        self.setMinimumSize(900, 700)

        layout = QtWidgets.QVBoxLayout(self)

        # Tab widget for multiple pins
        self.tabWidget = QtWidgets.QTabWidget()

        # Store references to viewer widgets for updates
        self.viewer_widgets = {}

        for pin_name, (pin_type, data) in self.pins_data.items():
            widget = self._createTabWidget(pin_name, pin_type, data)
            self.tabWidget.addTab(widget, pin_name)
            self.viewer_widgets[pin_name] = (pin_type, widget)

        layout.addWidget(self.tabWidget)

        # Close button
        buttonLayout = QtWidgets.QHBoxLayout()
        buttonLayout.addStretch()

        closeButton = QtWidgets.QPushButton("Close")
        closeButton.clicked.connect(self.accept)
        buttonLayout.addWidget(closeButton)

        layout.addLayout(buttonLayout)

    def _createTabWidget(self, pin_name, pin_type, data):
        """Create a widget for a single pin based on its type."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        if pin_type == DATAFRAME_PIN:
            # Create DataFrame viewer
            widget = self._createDataFrameTab(pin_name, data)
        elif pin_type == MPL_FIGURE_PIN:
            # Create Figure viewer
            widget = self._createFigureTab(pin_name, data)
        else:
            # Unknown type - show error message
            errorLabel = QtWidgets.QLabel(f"Unknown pin type: {pin_type}")
            errorLabel.setAlignment(QtCore.Qt.AlignCenter)
            errorLabel.setStyleSheet("color: #f00; font-size: 14px;")
            layout.addWidget(errorLabel)

        return widget

    def _createDataFrameTab(self, pin_name, dataframe):
        """Create a tab widget for DataFrame display."""
        widget = QtWidgets.QWidget()
        tabLayout = QtWidgets.QVBoxLayout(widget)
        tabLayout.setContentsMargins(5, 5, 5, 5)

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
        model = PandasTableModel(dataframe if dataframe is not None else pd.DataFrame())
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

        # Store model reference for updates
        widget._model = model
        widget._proxyModel = proxyModel
        widget._tableView = tableView

        return widget

    def _createFigureTab(self, pin_name, figure):
        """Create a tab widget for Figure display."""
        widget = QtWidgets.QWidget()
        tabLayout = QtWidgets.QVBoxLayout(widget)
        tabLayout.setContentsMargins(0, 0, 0, 0)

        # Use PlotViewerWidget for consistent display
        plotViewer = PlotViewerWidget()
        plotViewer.setFigure(figure)
        tabLayout.addWidget(plotViewer)

        # Store viewer reference for updates
        widget._plotViewer = plotViewer

        return widget

    def setPinData(self, pin_name, pin_type, data):
        """Update data for a specific pin."""
        if pin_name not in self.viewer_widgets:
            return

        pin_type_old, widget = self.viewer_widgets[pin_name]

        # Check if type changed (shouldn't happen, but handle gracefully)
        if pin_type_old != pin_type:
            # Need to recreate the tab
            index = self.tabWidget.indexOf(widget)
            if index >= 0:
                self.tabWidget.removeTab(index)
                new_widget = self._createTabWidget(pin_name, pin_type, data)
                self.tabWidget.insertTab(index, new_widget, pin_name)
                self.viewer_widgets[pin_name] = (pin_type, new_widget)
            return

        # Update existing widget
        if pin_type == DATAFRAME_PIN:
            if hasattr(widget, '_model'):
                widget._model.setDataFrame(data if data is not None else pd.DataFrame())
                widget._tableView.resizeColumnsToContents()
        elif pin_type == MPL_FIGURE_PIN:
            if hasattr(widget, '_plotViewer'):
                widget._plotViewer.setFigure(data)

    def updateAllPins(self, pins_data_dict):
        """Update all pins with new data."""
        for pin_name, (pin_type, data) in pins_data_dict.items():
            self.setPinData(pin_name, pin_type, data)

    def restoreWindowGeometry(self):
        """Restore window position and size from settings."""
        # 统一通过 Mixin 恢复几何信息
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
        """关闭时先清理 Figure 相关 viewer，再交由 Mixin 保存几何信息。"""
        # 主动清理 matplotlib viewer，断开回调，防止关闭后仍触发事件
        try:
            for pin_name, (pin_type, widget) in list(self.viewer_widgets.items()):
                if pin_type == MPL_FIGURE_PIN and hasattr(widget, '_plotViewer'):
                    try:
                        widget._plotViewer.clear()
                    except Exception:
                        pass
        except Exception:
            pass
        # 交由 Mixin 统一保存 geometry
        super(MixedDataViewerDialog, self).closeEvent(event)

    # 接受/拒绝的保存逻辑由 Mixin 统一处理，无需重复实现

