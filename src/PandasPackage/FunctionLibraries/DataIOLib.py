import os
import pandas as pd
from uflow.Core import FunctionLibraryBase, IMPLEMENT_NODE
from uflow.Core.Common import *


class DataIOLib(FunctionLibraryBase):
    """Data IO function library for reading and writing various data formats"""

    def __init__(self, packageName):
        super(DataIOLib, self).__init__(packageName)

    ###################     READ NODES      ################################################################
    @staticmethod
    @IMPLEMENT_NODE(
        returns=None,
        meta={
            NodeMeta.CATEGORY: "Data Input",
            NodeMeta.KEYWORDS: ["csv", "read", "data"],
        },
    )
    def ReadCSV(
        path=("StringPin", "", {PinSpecifiers.INPUT_WIDGET_VARIANT: "FilePathWidget"}),
        separator=("StringPin", ","),
        encoding=("StringPin", "utf-8"),
        header=("IntPin", 0),
        data=(REF, ("DataFramePin", None)),
    ):
        """Read data from CSV file."""
        if not path or not path.strip():
            raise ValueError("File path is empty")
        df = pd.read_csv(path, sep=separator, encoding=encoding, header=header)
        data(df)

    @staticmethod
    @IMPLEMENT_NODE(
        returns=None,
        meta={
            NodeMeta.CATEGORY: "Data Input",
            NodeMeta.KEYWORDS: ["excel", "read", "data"],
        },
    )
    def ReadExcel(
        path=("StringPin", "", {PinSpecifiers.INPUT_WIDGET_VARIANT: "FilePathWidget"}),
        sheet_name=("StringPin", "0"),
        header=("IntPin", 0),
        data=(REF, ("DataFramePin", None)),
    ):
        """Read data from Excel file."""
        if not path or not path.strip():
            raise ValueError("File path is empty")
        df = pd.read_excel(path, sheet_name=sheet_name, header=header)
        data(df)

    @staticmethod
    @IMPLEMENT_NODE(
        returns=None,
        meta={
            NodeMeta.CATEGORY: "Data Input",
            NodeMeta.KEYWORDS: ["txt", "text", "read", "data"],
        },
    )
    def ReadTXT(
        path=("StringPin", "", {PinSpecifiers.INPUT_WIDGET_VARIANT: "FilePathWidget"}),
        separator=("StringPin", "\t"),
        encoding=("StringPin", "utf-8"),
        header=("IntPin", 0),
        data=(REF, ("DataFramePin", None)),
    ):
        """Read data from text file."""
        if not path or not path.strip():
            raise ValueError("File path is empty")
        df = pd.read_csv(path, sep=separator, encoding=encoding, header=header)
        data(df)

    @staticmethod
    @IMPLEMENT_NODE(
        returns=None,
        meta={
            NodeMeta.CATEGORY: "Data Input",
            NodeMeta.KEYWORDS: ["tsv", "read", "data"],
        },
    )
    def ReadTSV(
        path=("StringPin", "", {PinSpecifiers.INPUT_WIDGET_VARIANT: "FilePathWidget"}),
        encoding=("StringPin", "utf-8"),
        header=("IntPin", 0),
        data=(REF, ("DataFramePin", None)),
    ):
        """Read data from TSV file."""
        if not path or not path.strip():
            raise ValueError("File path is empty")
        df = pd.read_csv(path, sep="\t", encoding=encoding, header=header)
        data(df)

    ###################     WRITE NODES      ################################################################
    @staticmethod
    @IMPLEMENT_NODE(
        returns=None,
        nodeType=NodeTypes.Callable,
        meta={
            NodeMeta.CATEGORY: "Data Output",
            NodeMeta.KEYWORDS: ["csv", "write", "data"],
        },
    )
    def WriteCSV(
        path=("StringPin", "", {PinSpecifiers.INPUT_WIDGET_VARIANT: "FilePathWidget"}),
        data=("DataFramePin", None),
        separator=("StringPin", ","),
        encoding=("StringPin", "utf-8"),
        index=("BoolPin", False),
    ):
        """Write data to CSV file."""
        if not path or not path.strip():
            raise ValueError("File path is empty")
        if data is None or data.empty:
            raise ValueError("DataFrame is empty or None")
        data.to_csv(path, sep=separator, encoding=encoding, index=index)

    @staticmethod
    @IMPLEMENT_NODE(
        returns=None,
        nodeType=NodeTypes.Callable,
        meta={
            NodeMeta.CATEGORY: "Data Output",
            NodeMeta.KEYWORDS: ["excel", "write", "data"],
        },
    )
    def WriteExcel(
        path=("StringPin", "", {PinSpecifiers.INPUT_WIDGET_VARIANT: "FilePathWidget"}),
        data=("DataFramePin", None),
        sheet_name=("StringPin", "Sheet1"),
        index=("BoolPin", False),
    ):
        """Write data to Excel file."""
        if not path or not path.strip():
            raise ValueError("File path is empty")
        if data is None or data.empty:
            raise ValueError("DataFrame is empty or None")
        data.to_excel(path, sheet_name=sheet_name, index=index)

    @staticmethod
    @IMPLEMENT_NODE(
        returns=None,
        nodeType=NodeTypes.Callable,
        meta={
            NodeMeta.CATEGORY: "Data Output",
            NodeMeta.KEYWORDS: ["txt", "text", "write", "data"],
        },
    )
    def WriteTXT(
        path=("StringPin", "", {PinSpecifiers.INPUT_WIDGET_VARIANT: "FilePathWidget"}),
        data=("DataFramePin", None),
        separator=("StringPin", "\t"),
        encoding=("StringPin", "utf-8"),
        index=("BoolPin", False),
    ):
        """Write data to text file."""
        if not path or not path.strip():
            raise ValueError("File path is empty")
        if data is None or data.empty:
            raise ValueError("DataFrame is empty or None")
        data.to_csv(path, sep=separator, encoding=encoding, index=index)

    @staticmethod
    @IMPLEMENT_NODE(
        returns=None,
        nodeType=NodeTypes.Callable,
        meta={
            NodeMeta.CATEGORY: "Data Output",
            NodeMeta.KEYWORDS: ["tsv", "write", "data"],
        },
    )
    def WriteTSV(
        path=("StringPin", "", {PinSpecifiers.INPUT_WIDGET_VARIANT: "FilePathWidget"}),
        data=("DataFramePin", None),
        encoding=("StringPin", "utf-8"),
        index=("BoolPin", False),
    ):
        """Write data to TSV file."""
        if not path or not path.strip():
            raise ValueError("File path is empty")
        if data is None or data.empty:
            raise ValueError("DataFrame is empty or None")
        data.to_csv(path, sep="\t", encoding=encoding, index=index)
