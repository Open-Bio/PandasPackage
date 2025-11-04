"""
Pins 包的聚合入口。

变更：
- 暴露常量以消除魔法字符串：`DATAFRAME_PIN`, `MPL_FIGURE_PIN`
- 直接导出各 Pin 类，方便统一导入与类型检查。
"""

# 允许加载非 uflow 目录中的扩展包
__path__ = __import__("pkgutil").extend_path(__path__, __name__)

# 引入 Pin 类
from .DataFramePin import DataFramePin
from .MatplotlibFigurePin import MatplotlibFigurePin

# 统一的 Pin 类型名称常量（避免在代码中到处写魔法字符串）
DATAFRAME_PIN = "DataFramePin"
MPL_FIGURE_PIN = "MatplotlibFigurePin"

__all__ = [
    "DataFramePin",
    "MatplotlibFigurePin",
    "DATAFRAME_PIN",
    "MPL_FIGURE_PIN",
]
