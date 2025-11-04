# Input widgets for pins

from qtpy import QtCore
from qtpy.QtWidgets import *
from qtpy import QtGui
import pandas as pd
import time

from uflow.UI.Widgets.InputWidgets import InputWidgetSingle
from uflow.Core.Common import *
from ..Pins import DATAFRAME_PIN
from qtpy.QtWidgets import QTextEdit


class DynamicColumnSelectorWidget(InputWidgetSingle):
    """
    Dynamic column selector widget that shows DataFrame columns in a dropdown
    Similar to EnumInputWidget but with dynamic column list and performance optimizations
    """

    def __init__(self, parent=None, **kwargs):
        super(DynamicColumnSelectorWidget, self).__init__(parent=parent, **kwargs)

        # Store owning node reference for accessing DataFrame pins
        self.owningNode = None
        if "owningNode" in kwargs:
            self.owningNode = kwargs["owningNode"]

        # Create EnumComboBox for dropdown selection
        from uflow.UI.Widgets.EnumComboBox import EnumComboBox

        self.enumBox = EnumComboBox([])
        self.enumBox.setEditable(True)  # Allow manual input
        # Don't connect changeCallback directly - we'll handle it manually
        # self.enumBox.changeCallback.connect(self.dataSetCallback)
        self.setWidget(self.enumBox)

        # Performance optimization flags
        self._columns_cached = []
        self._last_update_time = 0
        self._update_threshold = 0.5  # Minimum time between updates (seconds)
        self._is_updating = False

        # Debounce timer for input changes
        self._debounce_timer = QtCore.QTimer()
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.timeout.connect(self._onDebounceTimeout)
        self._debounce_delay = 300  # 300ms debounce delay

        # Connect signals for manual refresh and user selection
        self.enumBox.activated.connect(self._onDropdownActivated)
        self.enumBox.lineEdit().textChanged.connect(self._onTextChanged)
        # Connect for user selection changes (not column list updates)
        self.enumBox.currentTextChanged.connect(self._onUserSelectionChanged)

        # Don't auto-update on init to improve performance
        # self.updateColumnList()

    def _onDropdownActivated(self, index):
        """Handle dropdown activation - trigger manual refresh"""
        if not self._is_updating:
            self.updateColumnList()

    def _onTextChanged(self, text):
        """Handle text changes with debouncing"""
        # Stop previous timer
        self._debounce_timer.stop()

        # Start new timer
        self._debounce_timer.start(self._debounce_delay)

    def _onDebounceTimeout(self):
        """Handle debounced text change"""
        # Only update if we're not already updating
        if not self._is_updating:
            self.updateColumnList()

    def _onUserSelectionChanged(self, text):
        """Handle user selection changes - trigger dataSetCallback"""
        # Only call dataSetCallback for actual user selections, not programmatic updates
        if not self._is_updating:
            self.dataSetCallback(text)

    def updateColumnList(self):
        """Update the dropdown list with current DataFrame columns (with performance optimizations)"""
        try:
            # Check if we should skip this update
            current_time = time.time()
            if current_time - self._last_update_time < self._update_threshold:
                return

            self._is_updating = True
            self._last_update_time = current_time

            columns = self.getDataFrameColumns()

            # Only update if columns have actually changed
            if columns != self._columns_cached:
                # Store current selection before updating
                current_selection = self.enumBox.currentText()

                self._columns_cached = columns.copy() if columns else []

                # Update the combobox model
                model = QtGui.QStandardItemModel()
                for i, column in enumerate(columns):
                    item = QtGui.QStandardItem(column)
                    model.setItem(i, 0, item)

                # Block signals during model update to prevent recursion
                self.enumBox.blockSignals(True)
                self.enumBox.setModel(model)
                self.enumBox.setModelColumn(0)

                # Restore previous selection if it still exists in the new list
                if current_selection and current_selection in columns:
                    self.enumBox.setCurrentText(current_selection)
                elif columns:  # If previous selection not found, set to first column
                    self.enumBox.setCurrentText(columns[0])

                self.enumBox.blockSignals(False)

        except Exception as e:
            print(f"Error updating column list: {e}")
        finally:
            self._is_updating = False

    def getDataFrameColumns(self):
        """Extract column names from connected DataFrame pins without triggering execution"""
        try:
            if not self.owningNode:
                return []

            # Get the raw node from UI node
            rawNode = (
                self.owningNode._rawNode
                if hasattr(self.owningNode, "_rawNode")
                else self.owningNode
            )

            # 查找 DataFrame 输入引脚（使用常量，避免魔法字符串）
            for pin in rawNode.inputs.values():
                if pin.dataType == DATAFRAME_PIN and pin.hasConnections():
                    # Use currentData() instead of getData() to avoid triggering execution
                    df = pin.currentData()
                    if df is not None and not df.empty:
                        return list(df.columns)

            return []
        except Exception as e:
            print(f"Error extracting DataFrame columns: {e}")
            return []

    def blockWidgetSignals(self, bLock=False):
        self.enumBox.blockSignals(bLock)

    def setWidgetValue(self, val):
        self.enumBox.setCurrentText(str(val))

    def showEvent(self, event):
        """Update column list when widget is shown (with performance check)"""
        super(DynamicColumnSelectorWidget, self).showEvent(event)
        # Only update if we haven't updated recently
        current_time = time.time()
        if current_time - self._last_update_time > self._update_threshold:
            self.updateColumnList()

    def forceRefresh(self):
        """Force refresh the column list (for manual refresh)"""
        self._last_update_time = 0  # Reset timer
        self.updateColumnList()


class TextEditWidget(InputWidgetSingle):
    """
    Multi-line text input widget for comma-separated value lists
    """

    def __init__(self, parent=None, **kwargs):
        super(TextEditWidget, self).__init__(parent=parent, **kwargs)

        # Create QTextEdit for multi-line input
        self.textEdit = QTextEdit(self)
        self.textEdit.setMaximumHeight(100)  # Limit height for better UI
        self.textEdit.setPlaceholderText(
            "Enter comma-separated values (e.g., value1, value2, value3)"
        )
        self.setWidget(self.textEdit)

        # Connect text change signal
        self.textEdit.textChanged.connect(self._onTextChanged)

    def _onTextChanged(self):
        """Handle text changes and call dataSetCallback"""
        text = self.textEdit.toPlainText()
        self.dataSetCallback(text)

    def blockWidgetSignals(self, bLock=False):
        self.textEdit.blockSignals(bLock)

    def setWidgetValue(self, val):
        self.textEdit.setPlainText(str(val))


class PathInputWidget(InputWidgetSingle):
    """
    使用系统原生对话框的路径输入控件
    
    为 StringPin 提供路径输入功能，使用系统原生文件对话框而不是 Qt 自定义 UI 对话框。
    支持文件选择、目录选择和通用路径选择三种模式。
    
    继承层次：
    InputWidgetSingle <- PathInputWidget
    
    关键方法：
    - __init__: 创建控件并连接信号
    - getPath: 打开系统原生文件对话框
    - setWidgetValue: 设置控件的显示值
    - blockWidgetSignals: 阻止信号（避免循环更新）
    """

    def __init__(self, mode="all", parent=None, **kwds):
        """
        初始化路径输入控件
        
        参数：
            mode (str): 路径选择模式
                - "file": 文件选择模式
                - "directory": 目录选择模式  
                - "all": 通用路径选择模式
            parent: 父控件
            **kwds: 关键字参数，包含：
                - dataSetCallback: 数据变化时的回调函数
                - defaultValue: 默认值
        
        作用：
        - 创建文本输入框和浏览按钮
        - 连接信号到回调函数
        - 设置初始状态
        
        效果：
        - 创建一个文本框和 "..." 按钮
        - 用户点击按钮时打开系统原生文件对话框
        - 选择路径后更新文本框内容
        """
        super(PathInputWidget, self).__init__(parent=parent, **kwds)
        self.mode = mode
        
        # 创建内容容器
        self.content = QWidget()
        self.content.setContentsMargins(0, 0, 0, 0)
        
        # 创建水平布局
        self.pathLayout = QHBoxLayout(self.content)
        self.pathLayout.setContentsMargins(0, 0, 0, 0)
        
        # 创建文本输入框
        self.le = QLineEdit()
        self.le.setContextMenuPolicy(QtCore.Qt.NoContextMenu)
        self.pathLayout.addWidget(self.le)
        
        # 创建浏览按钮
        self.pbGetPath = QPushButton("...")
        self.pbGetPath.clicked.connect(self.getPath)
        self.pathLayout.addWidget(self.pbGetPath)
        
        # 设置控件
        self.setWidget(self.content)
        
        # 连接文本变化信号到回调函数
        # 当用户修改文本时，会调用 dataSetCallback
        self.le.textChanged.connect(lambda val: self.dataSetCallback(val))

    def getPath(self):
        """
        打开系统原生文件对话框选择路径
        
        关键区别：直接使用 QFileDialog 的静态方法，使用系统原生对话框
        而不是自定义的 FileDialog 类，提供更好的系统集成和用户体验。
        
        支持的模式：
        - file: 文件选择对话框
        - directory: 目录选择对话框
        - all: 默认使用文件选择对话框
        """
        if self.mode == "file":
            # 文件选择对话框
            path, _ = QFileDialog.getOpenFileName(
                self, 
                "选择文件", 
                "", 
                "所有文件 (*.*)"
            )
        elif self.mode == "directory":
            # 目录选择对话框
            path = QFileDialog.getExistingDirectory(
                self, 
                "选择目录"
            )
        else:
            # 默认使用文件选择
            path, _ = QFileDialog.getOpenFileName(
                self, 
                "选择文件", 
                "", 
                "所有文件 (*.*)"
            )
        
        # 如果用户选择了路径，更新文本框
        if path:
            self.le.setText(path)

    def blockWidgetSignals(self, bLocked):
        """
        阻止控件信号
        
        参数：
            bLocked (bool): True 表示阻止信号，False 表示恢复信号
        
        作用：
        - 在程序设置控件值时阻止信号
        - 避免触发不必要的回调（防止循环更新）
        
        使用场景：
        - 从外部更新控件值时（如从文件加载）
        - 避免信号循环（setValue -> signal -> setValue -> ...）
        """
        self.le.blockSignals(bLocked)

    def setWidgetValue(self, val):
        """
        设置控件的显示值
        
        参数：
            val: 要显示的值（字符串或可转换为字符串的类型）
        
        作用：
        - 更新文本框的内容
        - 反映引脚的当前值
        
        触发时机：
        - 引脚值被程序修改时
        - 从文件加载图时
        - 引脚连接断开并恢复默认值时
        
        效果：
        - 文本框显示选中的路径
        """
        self.le.setText(str(val))


def getInputWidget(
    dataType, dataSetter, defaultValue, widgetVariant=DEFAULT_WIDGET_VARIANT, **kwds
):
    """
    引脚输入控件工厂函数
    
    参数：
        dataType (str): 引脚的数据类型名称
        dataSetter (callable): 设置引脚数据的回调函数
        defaultValue: 引脚的默认值
        widgetVariant: 控件变体（用于同一类型的不同显示方式）
        **kwds: 其他关键字参数
    
    返回：
        InputWidget: 对应的输入控件实例，如果不支持则返回 None
    
    作用：
        根据控件变体返回合适的输入控件：
        - DynamicColumnSelectorWidget: 动态列选择器（用于 DataFrame 列选择）
        - TextEditWidget: 多行文本编辑器（用于逗号分隔值列表）
        - PathInputWidget: 路径输入控件（使用系统原生对话框）
            - FilePathWidget: 文件路径选择
            - PathWidget: 通用路径选择
            - FolderPathWidget: 文件夹路径选择
    
    添加新控件：
        if widgetVariant == 'MyCustomWidget':
            return MyCustomInputWidget(dataSetCallback=dataSetter, defaultValue=defaultValue, **kwds)
    
    效果：
        - 为 PandasPackage 的特定需求提供自定义输入控件
        - 文件路径控件使用系统原生对话框，提供更好的用户体验
        - 动态列选择器提供智能的 DataFrame 列名建议
    """
    # 使用注册表替代 if/elif 链，提高可扩展性
    registry = {
        "DynamicColumnSelectorWidget": lambda: DynamicColumnSelectorWidget(
            dataSetCallback=dataSetter, defaultValue=defaultValue, **kwds
        ),
        "TextEditWidget": lambda: TextEditWidget(
            dataSetCallback=dataSetter, defaultValue=defaultValue, **kwds
        ),
        "FilePathWidget": lambda: PathInputWidget(
            mode="file", dataSetCallback=dataSetter, defaultValue=defaultValue, **kwds
        ),
        "PathWidget": lambda: PathInputWidget(
            mode="all", dataSetCallback=dataSetter, defaultValue=defaultValue, **kwds
        ),
        "FolderPathWidget": lambda: PathInputWidget(
            mode="directory", dataSetCallback=dataSetter, defaultValue=defaultValue, **kwds
        ),
    }

    factory = registry.get(widgetVariant)
    return factory() if factory else None
