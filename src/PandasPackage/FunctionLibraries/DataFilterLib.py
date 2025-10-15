import pandas as pd
from uflow.Core import FunctionLibraryBase, IMPLEMENT_NODE
from uflow.Core.Common import *


class DataFilterLib(FunctionLibraryBase):
    """Data Filter function library for filtering DataFrame rows and columns"""

    def __init__(self, packageName):
        super(DataFilterLib, self).__init__(packageName)

    ###################     ROW FILTER NODES      ################################################################
    @staticmethod
    @IMPLEMENT_NODE(
        returns=None,
        nodeType=NodeTypes.Pure,
        meta={
            NodeMeta.CATEGORY: "Data Filtering",
            NodeMeta.KEYWORDS: ["filter", "condition", "row", "data"],
        },
    )
    def FilterByCondition(
        data=("DataFramePin", None),
        column_name=(
            "StringPin",
            "",
            {PinSpecifiers.INPUT_WIDGET_VARIANT: "DynamicColumnSelectorWidget"},
        ),
        operator=(
            "StringPin",
            "<",
            {PinSpecifiers.VALUE_LIST: ["<", ">", "<=", ">=", "==", "!="]},
        ),
        threshold=("FloatPin", 0.0),
        result=(REF, ("DataFramePin", None)),
    ):
        """Filter DataFrame rows by condition (e.g., df[df['pvalue'] < 0.05])."""
        if data is None or data.empty:
            result(pd.DataFrame())
            return

        if column_name not in data.columns:
            raise ValueError(f"Column '{column_name}' not found in DataFrame")

        # Apply the condition based on operator
        if operator == "<":
            filtered_df = data[data[column_name] < threshold]
        elif operator == ">":
            filtered_df = data[data[column_name] > threshold]
        elif operator == "<=":
            filtered_df = data[data[column_name] <= threshold]
        elif operator == ">=":
            filtered_df = data[data[column_name] >= threshold]
        elif operator == "==":
            filtered_df = data[data[column_name] == threshold]
        elif operator == "!=":
            filtered_df = data[data[column_name] != threshold]
        else:
            raise ValueError(f"Unsupported operator '{operator}'")

        result(filtered_df)

    @staticmethod
    @IMPLEMENT_NODE(
        returns=None,
        nodeType=NodeTypes.Pure,
        meta={
            NodeMeta.CATEGORY: "Data Filtering",
            NodeMeta.KEYWORDS: ["filter", "list", "isin", "row", "data"],
        },
    )
    def FilterByList(
        data=("DataFramePin", None),
        column_name=(
            "StringPin",
            "",
            {PinSpecifiers.INPUT_WIDGET_VARIANT: "DynamicColumnSelectorWidget"},
        ),
        value_list=(
            "StringPin",
            "",
            {PinSpecifiers.INPUT_WIDGET_VARIANT: "TextEditWidget"},
        ),
        inverse=("BoolPin", False),
        result=(REF, ("DataFramePin", None)),
    ):
        """Filter DataFrame rows by list of values (e.g., df[df['gene'].isin(gene_list)])."""
        if data is None or data.empty:
            result(pd.DataFrame())
            return

        if column_name not in data.columns:
            raise ValueError(f"Column '{column_name}' not found in DataFrame")

        # Parse the comma-separated value list
        if not value_list.strip():
            raise ValueError("Value list is empty")

        # Split by comma and strip whitespace
        values = [v.strip() for v in value_list.split(",") if v.strip()]

        if not values:
            raise ValueError("No valid values found in list")

        # Apply the filter
        if inverse:
            # Filter out rows where column value is in the list
            filtered_df = data[~data[column_name].isin(values)]
        else:
            # Filter rows where column value is in the list
            filtered_df = data[data[column_name].isin(values)]

        result(filtered_df)
