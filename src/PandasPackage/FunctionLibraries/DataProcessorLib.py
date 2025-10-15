import pandas as pd
import numpy as np
import traceback
import ast
import sys
import os
from io import StringIO
from uflow.Core import FunctionLibraryBase, IMPLEMENT_NODE
from uflow.Core.Common import *

try:
    from openai import OpenAI

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class UniversalDataProcessorLib(FunctionLibraryBase):
    """Universal Data Processor function library for flexible data processing"""

    def __init__(self, packageName):
        super(UniversalDataProcessorLib, self).__init__(packageName)

    @staticmethod
    @IMPLEMENT_NODE(
        returns=None,
        nodeType=NodeTypes.Pure,
        meta={
            NodeMeta.CATEGORY: "Data Processing",
            NodeMeta.KEYWORDS: ["universal", "processor", "data", "function", "custom"],
        },
    )
    def UniversalDataProcessor(
        data=("DataFramePin", None),
        function_code=(
            "StringPin",
            "# 在这里编写您的数据处理函数\n# 输入: data - 输入数据\n# 输出: 处理后的数据\n\n# 示例:\n# if isinstance(data, pd.DataFrame):\n#     return data.head(10)\n# elif isinstance(data, list):\n#     return [x * 2 for x in data]\n# else:\n#     return data\n\nreturn data",
            {PinSpecifiers.INPUT_WIDGET_VARIANT: "TextEditWidget"},
        ),
        result=(REF, ("DataFramePin", None)),
    ):
        """
        万用数据处理节点 - 通过自定义函数处理任意类型的数据

        输入:
        - data: 任意类型的数据 (DataFrame, list, dict, 基本类型等)
        - function_code: 自定义处理函数的Python代码

        输出:
        - result: 处理后的数据

        使用说明:
        1. 在function_code中编写Python代码
        2. 代码必须返回处理后的数据
        3. 输入数据通过变量'data'访问
        4. 支持pandas、numpy等常用库
        """
        if data is None:
            result(None)
            return

        if not function_code or not function_code.strip():
            result(data)
            return

        try:
            # 创建安全的执行环境
            safe_globals = {
                "__builtins__": {
                    # 允许的基本内置函数
                    "len": len,
                    "str": str,
                    "int": int,
                    "float": float,
                    "bool": bool,
                    "list": list,
                    "dict": dict,
                    "tuple": tuple,
                    "set": set,
                    "max": max,
                    "min": min,
                    "sum": sum,
                    "abs": abs,
                    "round": round,
                    "sorted": sorted,
                    "reversed": reversed,
                    "enumerate": enumerate,
                    "zip": zip,
                    "range": range,
                    "isinstance": isinstance,
                    "type": type,
                    "print": print,
                    "repr": repr,
                    "format": format,
                },
                # 导入常用库
                "pd": pd,
                "np": np,
                "pandas": pd,
                "numpy": np,
                # 输入数据
                "data": data,
            }

            # 限制本地变量
            safe_locals = {}

            # 捕获标准输出
            old_stdout = sys.stdout
            sys.stdout = captured_output = StringIO()

            try:
                # 检查代码中是否有return语句
                if "return" in function_code:
                    # 如果代码中有return语句，将代码包装在函数中执行
                    function_wrapper = f"""
def process_data(data):
{chr(10).join("    " + line for line in function_code.split(chr(10)))}
"""
                    try:
                        exec(function_wrapper, safe_globals)
                        processed_data = safe_globals["process_data"](data)
                    except Exception as e:
                        raise ValueError(f"函数执行错误: {e}")
                else:
                    # 如果没有return语句，尝试获取最后一行表达式的结果
                    lines = function_code.strip().split("\n")
                    last_line = lines[-1].strip()

                    # 检查最后一行是否是表达式
                    try:
                        ast.parse(last_line, mode="eval")
                        # 是表达式，执行并获取结果
                        processed_data = eval(last_line, safe_globals)
                    except SyntaxError:
                        # 不是表达式，执行整个代码块
                        try:
                            exec(function_code, safe_globals, safe_locals)
                            # 尝试获取最后一行表达式的结果
                            processed_data = eval(last_line, safe_globals)
                        except:
                            # 如果都失败了，返回原始数据
                            processed_data = data

                # 获取输出
                output = captured_output.getvalue()
                if output:
                    print(f"函数输出: {output}")

                result(processed_data)

            finally:
                sys.stdout = old_stdout

        except Exception as e:
            error_msg = f"数据处理错误: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)
            # 发生错误时返回原始数据
            result(data)

    @staticmethod
    @IMPLEMENT_NODE(
        returns=None,
        nodeType=NodeTypes.Pure,
        meta={
            NodeMeta.CATEGORY: "AI Code Generation",
            NodeMeta.KEYWORDS: ["ai", "code", "generation", "deepseek", "llm"],
        },
    )
    def AICodeGenerator(
        data=("AnyPin", None),
        prompt=(
            "StringPin",
            "请分析这个数据并生成处理代码",
            {PinSpecifiers.INPUT_WIDGET_VARIANT: "TextEditWidget"},
        ),
        api_key=(
            "StringPin",
            "",
            {PinSpecifiers.INPUT_WIDGET_VARIANT: "TextEditWidget"},
        ),
        base_url=(
            "StringPin",
            "https://api.deepseek.com",
            {PinSpecifiers.INPUT_WIDGET_VARIANT: "TextEditWidget"},
        ),
        model=(
            "StringPin",
            "deepseek-chat",
            {PinSpecifiers.VALUE_LIST: ["deepseek-chat", "deepseek-coder"]},
        ),
        temperature=("FloatPin", 0.3),
        result=(REF, ("StringPin", None)),
    ):
        """
        AI代码生成器 - 使用DeepSeek AI生成数据处理代码

        输入:
        - data: 输入数据 (用于生成数据摘要)
        - prompt: 用户提示词
        - api_key: DeepSeek API密钥 (可从环境变量DEEPSEEK_API_KEY获取)
        - base_url: API基础URL (默认: https://api.deepseek.com)
        - model: 使用的模型 (deepseek-chat, deepseek-coder)
        - temperature: 生成温度 (0-1)

        输出:
        - result: 生成的Python代码

        使用说明:
        1. 输入数据会自动生成摘要供AI参考
        2. 在prompt中描述您想要的数据处理逻辑
        3. AI会生成对应的Python代码
        4. 生成的代码可以直接用于UniversalDataProcessor节点
        5. 支持从环境变量DEEPSEEK_API_KEY自动获取API密钥
        """
        if not OPENAI_AVAILABLE:
            error_msg = "OpenAI库未安装，请运行: pip install openai"
            print(error_msg)
            result("# OpenAI库未安装，请运行: pip install openai")
            return

        # 优先使用环境变量中的API密钥
        final_api_key = api_key.strip() if api_key else ""
        if not final_api_key:
            final_api_key = os.environ.get("DEEPSEEK_API_KEY", "")

        if not final_api_key:
            error_msg = "请提供DeepSeek API密钥或在环境变量中设置DEEPSEEK_API_KEY"
            print(error_msg)
            result("# 请提供DeepSeek API密钥或在环境变量中设置DEEPSEEK_API_KEY")
            return

        if not prompt or not prompt.strip():
            error_msg = "请提供处理提示词"
            print(error_msg)
            result("# 请提供处理提示词")
            return

        try:
            # 生成数据摘要
            data_summary = _generate_data_summary(data)

            # 构建完整的提示词
            full_prompt = f"""
数据摘要:
{data_summary}

用户需求: {prompt}

请生成Python代码来处理这个数据。要求:
1. 只输出可执行的Python代码，无解释、注释或markdown
2. 默认数据变量名为data
3. 根据数据类型选择合适的方法:
   - pd.DataFrame → pandas方法
   - list/tuple → 列表推导式
   - dict → 字典操作
   - np.ndarray → numpy方法
4. 必须返回处理结果
5. 优先使用向量化操作

示例格式:
if isinstance(data, pd.DataFrame):
    return data[data > 0].mean()
elif isinstance(data, (list, tuple)):
    filtered = [x for x in data if x > 0]
    return sum(filtered) / len(filtered) if filtered else 0
"""

            # 创建OpenAI客户端
            client = OpenAI(api_key=final_api_key, base_url=base_url)

            # 调用API
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是Python代码生成器，专门生成数据处理代码。",
                    },
                    {"role": "user", "content": full_prompt},
                ],
                temperature=temperature,
                max_tokens=1000,
                stream=False,
            )

            # 提取生成的代码
            generated_code = response.choices[0].message.content.strip()

            # 清理markdown标记
            generated_code = (
                generated_code.replace("```python", "").replace("```", "").strip()
            )

            print(f"DeepSeek AI生成的代码:\n{generated_code}")
            result(generated_code)

        except Exception as e:
            error_msg = f"DeepSeek AI代码生成错误: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)
            result(f"# DeepSeek AI代码生成错误: {str(e)}")


def _generate_data_summary(data):
    """生成数据摘要"""
    if data is None:
        return "数据为空 (None)"

    try:
        if isinstance(data, pd.DataFrame):
            summary = f"DataFrame形状: {data.shape}\n"
            summary += f"列名: {list(data.columns)}\n"
            summary += f"数据类型:\n{data.dtypes}\n"
            summary += f"前5行数据:\n{data.head()}\n"
            summary += f"基本统计:\n{data.describe()}"
            return summary

        elif isinstance(data, (list, tuple)):
            summary = f"列表/元组长度: {len(data)}\n"
            summary += f"数据类型: {type(data).__name__}\n"
            if len(data) > 0:
                summary += f"第一个元素类型: {type(data[0]).__name__}\n"
                summary += f"前5个元素: {data[:5]}\n"
                if len(data) > 5:
                    summary += f"后5个元素: {data[-5:]}\n"
            return summary

        elif isinstance(data, dict):
            summary = f"字典长度: {len(data)}\n"
            summary += f"键: {list(data.keys())}\n"
            summary += f"值类型: {[type(v).__name__ for v in data.values()]}\n"
            summary += f"前5个键值对: {dict(list(data.items())[:5])}"
            return summary

        elif isinstance(data, np.ndarray):
            summary = f"NumPy数组形状: {data.shape}\n"
            summary += f"数据类型: {data.dtype}\n"
            summary += f"前5个元素: {data.flat[:5]}\n"
            summary += (
                f"统计信息: min={data.min()}, max={data.max()}, mean={data.mean()}"
            )
            return summary

        else:
            summary = f"数据类型: {type(data).__name__}\n"
            summary += f"值: {str(data)[:200]}{'...' if len(str(data)) > 200 else ''}"
            return summary

    except Exception as e:
        return f"数据摘要生成失败: {str(e)}\n数据类型: {type(data).__name__}"
