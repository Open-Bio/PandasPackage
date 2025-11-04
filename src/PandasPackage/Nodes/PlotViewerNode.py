from uflow.Core import NodeBase
from uflow.Core.NodeBase import NodePinsSuggestionsHelper
from uflow.Core.Common import *
from qtpy import QtWidgets


class PlotViewerNode(NodeBase):
    """Node for viewing matplotlib Figure objects in a dockable tool."""

    def __init__(self, name):
        super(PlotViewerNode, self).__init__(name)
        self.inExec = self.createInputPin(
            DEFAULT_IN_EXEC_NAME, "ExecPin", None, self.compute
        )
        self.figureInput = self.createInputPin(
            "figure", "MatplotlibFigurePin", structure=StructureType.Multi
        )
        self.outExec = self.createOutputPin(DEFAULT_OUT_EXEC_NAME, "ExecPin")

    @staticmethod
    def pinTypeHints():
        helper = NodePinsSuggestionsHelper()
        helper.addInputDataType("ExecPin")
        helper.addInputDataType("MatplotlibFigurePin")
        helper.addOutputDataType("ExecPin")
        helper.addInputStruct(StructureType.Multi)
        helper.addOutputStruct(StructureType.Single)
        return helper

    @staticmethod
    def category():
        return "Data Viewers"

    @staticmethod
    def keywords():
        return ["plot", "viewer", "matplotlib", "figure", "visualization"]

    @staticmethod
    def description():
        return "Preview matplotlib Figure objects in an interactive plot viewer."

    def compute(self, *args, **kwargs):
        if self.figureInput.dirty:
            inputData = self.figureInput.getData()

            # Get or create the plot viewer tool
            viewer = self._wrapper.canvasRef().uflowInstance.invokeDockToolByName(
                "PandasPackage", "PlotViewer"
            )

            # Check if viewer was created successfully
            if viewer is None:
                print("Warning: Failed to create PlotViewer tool")
                self.outExec.call()
                return

            # Handle multiple figures (use the first one)
            if isinstance(inputData, list):
                if inputData:
                    viewer.setFigure(inputData[0])
                else:
                    viewer.setFigure(None)
            elif inputData is not None:
                # Handle single Figure
                viewer.setFigure(inputData)
            else:
                # Empty or invalid data
                viewer.setFigure(None)

            QtWidgets.QApplication.processEvents()
        self.outExec.call()

