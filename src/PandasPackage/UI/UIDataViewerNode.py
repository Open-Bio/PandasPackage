from ..UI.UIDataAnalysisBaseNode import UIDataAnalysisBaseNode


class UIDataViewerNode(UIDataAnalysisBaseNode):
    """Custom UI for DataViewerNode.

    Inherits refresh button from UIDataAnalysisBaseNode.
    Can be extended with additional viewer-specific functionality.
    """

    def __init__(self, raw_node):
        super(UIDataViewerNode, self).__init__(raw_node)
        # Additional viewer-specific initialization can go here

    def onNodeComputed(self, *args, **kwargs):
        """Called automatically when node finishes computing.

        The compute() method already updates the DataViewerTool,
        so we don't need to do anything extra here.
        """
        pass
