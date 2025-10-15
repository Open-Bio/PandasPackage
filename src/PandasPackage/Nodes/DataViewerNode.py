from uflow.Core import NodeBase
from uflow.Core.NodeBase import NodePinsSuggestionsHelper
from uflow.Core.Common import *
from qtpy import QtWidgets
import pandas as pd


class DataViewerNode(NodeBase):
    def __init__(self, name):
        super(DataViewerNode, self).__init__(name)
        self.inExec = self.createInputPin(
            DEFAULT_IN_EXEC_NAME, "ExecPin", None, self.compute
        )
        self.dataInput = self.createInputPin(
            "data", "DataFramePin", structure=StructureType.Multi
        )
        self.outExec = self.createOutputPin(DEFAULT_OUT_EXEC_NAME, "ExecPin")

    @staticmethod
    def pinTypeHints():
        helper = NodePinsSuggestionsHelper()
        helper.addInputDataType("ExecPin")
        helper.addInputDataType("DataFramePin")
        helper.addOutputDataType("ExecPin")
        helper.addInputStruct(StructureType.Multi)
        helper.addOutputStruct(StructureType.Single)
        return helper

    @staticmethod
    def category():
        return "Data Viewers"

    @staticmethod
    def keywords():
        return ["data", "viewer", "preview", "table"]

    @staticmethod
    def description():
        return "Preview DataFrame data in a table viewer."

    def compute(self, *args, **kwargs):
        if self.dataInput.dirty:
            inputData = self.dataInput.getData()

            # Get or create the data viewer tool
            viewer = self._wrapper.canvasRef().uflowInstance.invokeDockToolByName(
                "PandasPackage", "DataViewer"
            )

            # Check if viewer was created successfully
            if viewer is None:
                print("Warning: Failed to create DataViewer tool")
                self.outExec.call()
                return

            if isinstance(inputData, list):
                # Handle multiple DataFrames
                if inputData:
                    # Use the first DataFrame for preview
                    viewer.setDataFrame(inputData[0])
            elif isinstance(inputData, pd.DataFrame):
                # Handle single DataFrame
                viewer.setDataFrame(inputData)
            else:
                # Empty or invalid data
                viewer.setDataFrame(pd.DataFrame())

            QtWidgets.QApplication.processEvents()
        self.outExec.call()
