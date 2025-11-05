from ..UI.UIDataAnalysisBaseNode import UIDataAnalysisBaseNode


class UIHyperExcelReadNode(UIDataAnalysisBaseNode):
    """UI wrapper for HyperExcelReadNode that handles dynamic pin updates."""

    def __init__(self, raw_node):
        super(UIHyperExcelReadNode, self).__init__(raw_node)

    def onPinsUpdated(self):
        """Called when the node updates its output pins dynamically.
        
        This method creates UI wrappers for newly created pins and updates
        the node shape to reflect the changes.
        """
        # Create UI wrappers for all pins (will skip if already exists)
        for pin in self._rawNode.getOrderedPins():
            self._createUIPinWrapper(pin)
        
        # Update node shape to reflect new pin layout
        self.updateNodeShape()
        self.updateNodeHeaderColor()
        
        # Update data frame pins list for viewer functionality
        self.dataFramePins = []
        for pin in self._rawNode.outputs.values():
            if pin.dataType == "DataFramePin":
                self.dataFramePins.append(pin)

    def postCreate(self, jsonTemplate=None):
        """Handle post-creation setup, including dynamic pins."""
        super(UIHyperExcelReadNode, self).postCreate(jsonTemplate)
        
        # Ensure all pins have UI wrappers
        self.onPinsUpdated()

