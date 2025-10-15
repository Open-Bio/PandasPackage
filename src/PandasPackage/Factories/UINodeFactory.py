from ..UI.UIDataAnalysisBaseNode import UIDataAnalysisBaseNode
from ..UI.UIDataViewerNode import UIDataViewerNode


def createUINode(raw_instance):
    # Use custom UI for DataViewerNode (extends base functionality)
    if raw_instance.__class__.__name__ == "DataViewerNode":
        return UIDataViewerNode(raw_instance)

    # Default: all DataAnalysis nodes get base class with auto refresh button
    return UIDataAnalysisBaseNode(raw_instance)
