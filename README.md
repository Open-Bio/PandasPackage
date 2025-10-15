# uflowDataAnalysis

uflow数据分析包，提供表格数据的读写和预览功能。

## 功能特性

### 数据输入节点

- **ReadCSV** - 读取CSV文件
- **ReadExcel** - 读取Excel文件
- **ReadTXT** - 读取文本文件（支持自定义分隔符）
- **ReadTSV** - 读取TSV文件

### 数据输出节点

- **WriteCSV** - 写入CSV文件
- **WriteExcel** - 写入Excel文件
- **WriteTXT** - 写入文本文件
- **WriteTSV** - 写入TSV文件

### 数据查看

- **DataViewerNode** - 数据预览节点
- **DataViewerTool** - 数据表格查看工具

## 使用方法

1. 在uflow中，新包会自动出现在节点库中
2. 从"Data Input"类别拖拽读取节点到画布
3. 从"Data Output"类别拖拽写入节点到画布
4. 使用DataViewerNode预览数据
5. 通过DataViewerTool查看详细的数据表格

## 依赖

- pandas
- openpyxl
- xlrd

## 数据类型

包使用DataFramePin类型在节点间传递pandas DataFrame对象，支持所有pandas DataFrame的功能。
