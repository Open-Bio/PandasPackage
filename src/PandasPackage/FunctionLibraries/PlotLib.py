import numpy as np
import pandas as pd
from uflow.Core import FunctionLibraryBase, IMPLEMENT_NODE
from uflow.Core.Common import *

try:
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend for creating figures
    import matplotlib.pyplot as plt
    import matplotlib.font_manager as fm
    import platform
    
    # 全局设置matplotlib中文字体
    def setup_chinese_font():
        """设置matplotlib中文字体，支持Windows、macOS和Linux"""
        system = platform.system()
        
        # 根据操作系统选择中文字体
        if system == 'Windows':
            # Windows系统常用中文字体
            font_candidates = ['Microsoft YaHei', 'SimHei', 'SimSun', 'KaiTi']
        elif system == 'Darwin':  # macOS
            # macOS系统常用中文字体
            font_candidates = ['PingFang SC', 'STHeiti', 'Arial Unicode MS', 'Heiti SC']
        else:  # Linux
            # Linux系统常用中文字体
            font_candidates = ['WenQuanYi Micro Hei', 'WenQuanYi Zen Hei', 'Noto Sans CJK SC', 'DejaVu Sans']
        
        # 获取系统中所有可用字体
        available_fonts = [f.name for f in fm.fontManager.ttflist]
        
        # 尝试设置中文字体
        font_set = False
        for font_name in font_candidates:
            if font_name in available_fonts:
                plt.rcParams['font.sans-serif'] = [font_name] + plt.rcParams['font.sans-serif']
                font_set = True
                print(f"Matplotlib中文字体已设置为: {font_name}")
                break
        
        if not font_set:
            # 如果没有找到合适的中文字体，尝试查找任何包含中文字符的字体
            chinese_fonts = [f.name for f in fm.fontManager.ttflist 
                           if any(keyword in f.name.lower() for keyword in ['chinese', 'cjk', 'han', 'hei', 'song', 'kai'])]
            if chinese_fonts:
                plt.rcParams['font.sans-serif'] = [chinese_fonts[0]] + plt.rcParams['font.sans-serif']
                print(f"Matplotlib中文字体已设置为: {chinese_fonts[0]} (自动检测)")
            else:
                print("Warning: 未找到合适的中文字体，中文可能显示为方块")
        
        # 解决负号显示问题
        plt.rcParams['axes.unicode_minus'] = False
    
    # 初始化时设置中文字体
    setup_chinese_font()
    
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

    @staticmethod
    @IMPLEMENT_NODE(
        returns=None,
        nodeType=NodeTypes.Pure,
        meta={
            NodeMeta.CATEGORY: "Visualization",
            NodeMeta.KEYWORDS: ["plot", "data", "hardcoded", "demo", "dataframe", "figure"],
        },
    )
    def GenerateDataAndPlot(
        data=(REF, ("DataFramePin", None)),
        figure=(REF, ("MatplotlibFigurePin", None)),
    ):
        """
        硬编码的数据和图表生成节点 - 同时输出DataFrame数据和对应的matplotlib图表
        
        输出:
        - data: 包含示例数据的DataFrame（销售数据示例）
        - figure: 基于该数据生成的matplotlib图表
        
        这个节点用于演示如何同时输出数据和图表，生成一个包含销售数据的DataFrame
        以及基于该数据的可视化图表。
        """
        try:
            # 创建硬编码的示例数据
            sample_data = {
                '月份': ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'],
                '销售额': [120, 135, 148, 160, 175, 190, 205, 220, 210, 195, 180, 165],
                '成本': [80, 85, 90, 95, 100, 105, 110, 115, 112, 108, 102, 98],
                '利润': [40, 50, 58, 65, 75, 85, 95, 105, 98, 87, 78, 67],
                '订单数': [45, 52, 58, 63, 68, 72, 76, 80, 78, 74, 70, 65]
            }
            df = pd.DataFrame(sample_data)
            
            # 输出DataFrame数据
            data(df)
            
            # 生成图表
            if not MATPLOTLIB_AVAILABLE:
                print("Warning: matplotlib is not installed, only data will be output")
                figure(None)
                return
            
            # 创建一个包含多个子图的Figure
            fig, axes = plt.subplots(2, 2, figsize=(12, 10))
            fig.suptitle('销售数据分析报告', fontsize=16, fontweight='bold')
            
            # 子图1: 销售额趋势线图
            axes[0, 0].plot(df['月份'], df['销售额'], marker='o', linewidth=2, markersize=8, color='#2E86AB', label='销售额')
            axes[0, 0].set_title('月度销售额趋势', fontsize=12, fontweight='bold')
            axes[0, 0].set_xlabel('月份')
            axes[0, 0].set_ylabel('销售额 (万元)')
            axes[0, 0].grid(True, alpha=0.3)
            axes[0, 0].legend()
            axes[0, 0].tick_params(axis='x', rotation=45)
            
            # 子图2: 销售额和成本对比柱状图
            x_pos = range(len(df['月份']))
            width = 0.35
            axes[0, 1].bar([x - width/2 for x in x_pos], df['销售额'], width, label='销售额', color='#06A77D', alpha=0.8)
            axes[0, 1].bar([x + width/2 for x in x_pos], df['成本'], width, label='成本', color='#F18F01', alpha=0.8)
            axes[0, 1].set_title('销售额与成本对比', fontsize=12, fontweight='bold')
            axes[0, 1].set_xlabel('月份')
            axes[0, 1].set_ylabel('金额 (万元)')
            axes[0, 1].set_xticks(x_pos)
            axes[0, 1].set_xticklabels(df['月份'], rotation=45)
            axes[0, 1].legend()
            axes[0, 1].grid(True, alpha=0.3, axis='y')
            
            # 子图3: 利润柱状图
            colors_profit = ['#2E86AB' if x > 80 else '#F18F01' if x > 60 else '#C73E1D' for x in df['利润']]
            axes[1, 0].bar(df['月份'], df['利润'], color=colors_profit, alpha=0.8, edgecolor='black', linewidth=1)
            axes[1, 0].set_title('月度利润', fontsize=12, fontweight='bold')
            axes[1, 0].set_xlabel('月份')
            axes[1, 0].set_ylabel('利润 (万元)')
            axes[1, 0].tick_params(axis='x', rotation=45)
            axes[1, 0].grid(True, alpha=0.3, axis='y')
            
            # 子图4: 订单数散点图（带趋势线）
            axes[1, 1].scatter(df['月份'], df['订单数'], s=100, c=df['订单数'], cmap='viridis', alpha=0.7, edgecolors='black', linewidth=1)
            # 添加趋势线
            z = np.polyfit(range(len(df)), df['订单数'], 1)
            p = np.poly1d(z)
            axes[1, 1].plot(df['月份'], p(range(len(df))), "r--", alpha=0.5, linewidth=2, label='趋势线')
            axes[1, 1].set_title('订单数分布', fontsize=12, fontweight='bold')
            axes[1, 1].set_xlabel('月份')
            axes[1, 1].set_ylabel('订单数')
            axes[1, 1].tick_params(axis='x', rotation=45)
            axes[1, 1].legend()
            axes[1, 1].grid(True, alpha=0.3)
            
            # 调整布局
            plt.tight_layout()
            
            # 输出Figure对象
            figure(fig)
            
        except Exception as e:
            print(f"Error generating data and plot: {e}")
            import traceback
            traceback.print_exc()
            # 确保即使出错也输出空的DataFrame
            data(pd.DataFrame())
            figure(None)

    @staticmethod
    @IMPLEMENT_NODE(
        returns=None,
        nodeType=NodeTypes.Pure,
        meta={
            NodeMeta.CATEGORY: "Visualization",
            NodeMeta.KEYWORDS: ["plot", "data", "hardcoded", "multi", "4outputs", "dataframe", "figure"],
        },
    )
    def GenerateMultiDataAndPlots(
        sales_data=(REF, ("DataFramePin", None)),
        product_data=(REF, ("DataFramePin", None)),
        sales_figure=(REF, ("MatplotlibFigurePin", None)),
        product_figure=(REF, ("MatplotlibFigurePin", None)),
    ):
        """
        硬编码的多数据和图表生成节点 - 同时输出2个DataFrame数据和2个matplotlib图表（共4个输出）
        
        输出:
        - sales_data: 销售数据DataFrame
        - product_data: 产品数据DataFrame
        - sales_figure: 销售数据可视化图表
        - product_figure: 产品数据可视化图表
        
        这个节点用于演示如何同时输出多个数据和图表，展示更复杂的数据流场景。
        """
        try:
            # 创建第一个硬编码数据集：销售数据
            sales_sample = {
                '月份': ['1月', '2月', '3月', '4月', '5月', '6月'],
                '销售额': [120, 135, 148, 160, 175, 190],
                '成本': [80, 85, 90, 95, 100, 105],
                '利润': [40, 50, 58, 65, 75, 85]
            }
            df_sales = pd.DataFrame(sales_sample)
            
            # 创建第二个硬编码数据集：产品数据
            product_sample = {
                '产品名称': ['产品A', '产品B', '产品C', '产品D', '产品E'],
                '销量': [450, 320, 280, 380, 290],
                '单价': [120, 180, 150, 200, 165],
                '总销售额': [54000, 57600, 42000, 76000, 47850],
                '库存': [120, 85, 150, 95, 110]
            }
            df_product = pd.DataFrame(product_sample)
            
            # 输出两个DataFrame数据
            sales_data(df_sales)
            product_data(df_product)
            
            # 生成第一个图表：销售数据图表
            if MATPLOTLIB_AVAILABLE:
                # 销售数据图表 - 包含2个子图
                fig_sales, axes_sales = plt.subplots(1, 2, figsize=(14, 5))
                fig_sales.suptitle('销售数据分析', fontsize=14, fontweight='bold')
                
                # 子图1: 销售额和成本对比
                x_pos = range(len(df_sales['月份']))
                width = 0.35
                axes_sales[0].bar([x - width/2 for x in x_pos], df_sales['销售额'], width, 
                                 label='销售额', color='#2E86AB', alpha=0.8)
                axes_sales[0].bar([x + width/2 for x in x_pos], df_sales['成本'], width, 
                                 label='成本', color='#F18F01', alpha=0.8)
                axes_sales[0].set_title('销售额与成本对比', fontsize=11, fontweight='bold')
                axes_sales[0].set_xlabel('月份')
                axes_sales[0].set_ylabel('金额 (万元)')
                axes_sales[0].set_xticks(x_pos)
                axes_sales[0].set_xticklabels(df_sales['月份'])
                axes_sales[0].legend()
                axes_sales[0].grid(True, alpha=0.3, axis='y')
                
                # 子图2: 利润趋势
                axes_sales[1].plot(df_sales['月份'], df_sales['利润'], marker='o', 
                                  linewidth=2.5, markersize=10, color='#06A77D', 
                                  markerfacecolor='white', markeredgewidth=2)
                axes_sales[1].fill_between(df_sales['月份'], df_sales['利润'], 
                                          alpha=0.3, color='#06A77D')
                axes_sales[1].set_title('利润趋势', fontsize=11, fontweight='bold')
                axes_sales[1].set_xlabel('月份')
                axes_sales[1].set_ylabel('利润 (万元)')
                axes_sales[1].grid(True, alpha=0.3)
                
                plt.tight_layout()
                sales_figure(fig_sales)
            else:
                print("Warning: matplotlib is not installed, sales figure will be None")
                sales_figure(None)
            
            # 生成第二个图表：产品数据图表
            if MATPLOTLIB_AVAILABLE:
                # 产品数据图表 - 包含2个子图
                fig_product, axes_product = plt.subplots(1, 2, figsize=(14, 5))
                fig_product.suptitle('产品数据分析', fontsize=14, fontweight='bold')
                
                # 子图1: 产品销量柱状图
                colors_bar = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8']
                bars = axes_product[0].bar(df_product['产品名称'], df_product['销量'], 
                                          color=colors_bar, alpha=0.8, edgecolor='black', linewidth=1.5)
                axes_product[0].set_title('各产品销量', fontsize=11, fontweight='bold')
                axes_product[0].set_xlabel('产品名称')
                axes_product[0].set_ylabel('销量')
                axes_product[0].grid(True, alpha=0.3, axis='y')
                # 添加数值标签
                for bar in bars:
                    height = bar.get_height()
                    axes_product[0].text(bar.get_x() + bar.get_width()/2., height,
                                        f'{int(height)}', ha='center', va='bottom', fontweight='bold')
                
                # 子图2: 总销售额饼图
                axes_product[1].pie(df_product['总销售额'], labels=df_product['产品名称'], 
                                    autopct='%1.1f%%', startangle=90, colors=colors_bar,
                                    textprops={'fontsize': 9, 'fontweight': 'bold'})
                axes_product[1].set_title('总销售额占比', fontsize=11, fontweight='bold')
                
                plt.tight_layout()
                product_figure(fig_product)
            else:
                print("Warning: matplotlib is not installed, product figure will be None")
                product_figure(None)
            
        except Exception as e:
            print(f"Error generating multi data and plots: {e}")
            import traceback
            traceback.print_exc()
            # 确保即使出错也输出空的DataFrame
            sales_data(pd.DataFrame())
            product_data(pd.DataFrame())
            sales_figure(None)
            product_figure(None)

