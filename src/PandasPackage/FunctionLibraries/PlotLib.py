import numpy as np
import pandas as pd
from uflow.Core import FunctionLibraryBase, IMPLEMENT_NODE
from uflow.Core.Common import *

try:
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend for creating figures
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


class PlotLib(FunctionLibraryBase):
    """Plot function library for creating matplotlib visualizations"""

    def __init__(self, packageName):
        super(PlotLib, self).__init__(packageName)

    @staticmethod
    @IMPLEMENT_NODE(
        returns=None,
        nodeType=NodeTypes.Pure,
        meta={
            NodeMeta.CATEGORY: "Visualization",
            NodeMeta.KEYWORDS: ["plot", "test", "matplotlib", "demo", "hardcoded"],
        },
    )
    def TestPlot(
        figure=(REF, ("MatplotlibFigurePin", None)),
    ):
        """
        测试绘图节点 - 硬编码生成一个示例matplotlib图
        
        输出:
        - figure: 包含示例图表的matplotlib Figure对象
        
        这个节点用于测试MatplotlibFigurePin的功能，生成一个包含多个子图的示例图表。
        """
        if not MATPLOTLIB_AVAILABLE:
            print("Warning: matplotlib is not installed")
            figure(None)
            return

        try:
            # 创建一个包含多个子图的Figure
            fig, axes = plt.subplots(2, 2, figsize=(10, 8))
            fig.suptitle('Test Plot - Matplotlib Figure Pin Demo', fontsize=14, fontweight='bold')

            # 子图1: 线性图
            x1 = np.linspace(0, 10, 100)
            y1 = np.sin(x1)
            axes[0, 0].plot(x1, y1, 'b-', linewidth=2, label='sin(x)')
            axes[0, 0].set_title('Line Plot')
            axes[0, 0].set_xlabel('X')
            axes[0, 0].set_ylabel('Y')
            axes[0, 0].grid(True, alpha=0.3)
            axes[0, 0].legend()

            # 子图2: 散点图
            x2 = np.random.randn(100)
            y2 = np.random.randn(100)
            colors = np.random.rand(100)
            sizes = 1000 * np.random.rand(100)
            axes[0, 1].scatter(x2, y2, c=colors, s=sizes, alpha=0.6, cmap='viridis')
            axes[0, 1].set_title('Scatter Plot')
            axes[0, 1].set_xlabel('X')
            axes[0, 1].set_ylabel('Y')
            axes[0, 1].grid(True, alpha=0.3)

            # 子图3: 柱状图
            categories = ['A', 'B', 'C', 'D', 'E']
            values = [23, 45, 56, 78, 32]
            axes[1, 0].bar(categories, values, color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8'])
            axes[1, 0].set_title('Bar Chart')
            axes[1, 0].set_xlabel('Category')
            axes[1, 0].set_ylabel('Value')
            axes[1, 0].grid(True, alpha=0.3, axis='y')

            # 子图4: 饼图
            sizes = [15, 30, 45, 10]
            labels = ['Type A', 'Type B', 'Type C', 'Type D']
            colors_pie = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A']
            axes[1, 1].pie(sizes, labels=labels, colors=colors_pie, autopct='%1.1f%%', startangle=90)
            axes[1, 1].set_title('Pie Chart')

            # 调整布局
            plt.tight_layout()

            # 输出Figure对象
            figure(fig)

        except Exception as e:
            print(f"Error creating test plot: {e}")
            import traceback
            traceback.print_exc()
            figure(None)

    @staticmethod
    @IMPLEMENT_NODE(
        returns=None,
        nodeType=NodeTypes.Pure,
        meta={
            NodeMeta.CATEGORY: "Visualization",
            NodeMeta.KEYWORDS: ["plot", "dataframe", "pandas", "chart"],
        },
    )
    def PlotDataFrame(
        data=("DataFramePin", None),
        x_column=("StringPin", ""),
        y_column=("StringPin", ""),
        plot_type=("StringPin", "line", {PinSpecifiers.VALUE_LIST: ["line", "bar", "scatter", "hist"]}),
        figure=(REF, ("MatplotlibFigurePin", None)),
    ):
        """
        从DataFrame创建图表
        
        输入:
        - data: 输入的DataFrame
        - x_column: X轴列名（可选，为空时使用索引）
        - y_column: Y轴列名（必需）
        - plot_type: 图表类型 (line, bar, scatter, hist)
        
        输出:
        - figure: matplotlib Figure对象
        """
        if not MATPLOTLIB_AVAILABLE:
            print("Warning: matplotlib is not installed")
            figure(None)
            return

        if data is None or data.empty:
            print("Warning: DataFrame is empty or None")
            figure(None)
            return

        try:
            fig, ax = plt.subplots(figsize=(8, 6))

            if plot_type == "line":
                if x_column and x_column in data.columns:
                    ax.plot(data[x_column], data[y_column] if y_column else data.iloc[:, 0])
                else:
                    ax.plot(data[y_column] if y_column else data.iloc[:, 0])
                ax.set_title(f'Line Plot: {y_column}')
            elif plot_type == "bar":
                if x_column and x_column in data.columns:
                    ax.bar(data[x_column], data[y_column] if y_column else data.iloc[:, 0])
                else:
                    ax.bar(range(len(data)), data[y_column] if y_column else data.iloc[:, 0])
                ax.set_title(f'Bar Chart: {y_column}')
            elif plot_type == "scatter":
                if x_column and x_column in data.columns:
                    ax.scatter(data[x_column], data[y_column] if y_column else data.iloc[:, 0])
                else:
                    ax.scatter(range(len(data)), data[y_column] if y_column else data.iloc[:, 0])
                ax.set_title(f'Scatter Plot: {y_column}')
            elif plot_type == "hist":
                column_data = data[y_column] if y_column and y_column in data.columns else data.iloc[:, 0]
                ax.hist(column_data, bins=20)
                ax.set_title(f'Histogram: {y_column if y_column else "first column"}')

            ax.set_xlabel(x_column if x_column else 'Index')
            ax.set_ylabel(y_column if y_column else data.columns[0])
            ax.grid(True, alpha=0.3)
            plt.tight_layout()

            figure(fig)

        except Exception as e:
            print(f"Error creating plot from DataFrame: {e}")
            import traceback
            traceback.print_exc()
            figure(None)

