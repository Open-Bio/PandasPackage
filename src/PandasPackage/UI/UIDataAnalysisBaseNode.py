import os
import pandas as pd
from uflow.UI.Canvas.UINodeBase import UINodeBase
from uflow.UI.Canvas.NodeActionButton import NodeActionButtonBase
from uflow.UI.Canvas.UICommon import NodeActionButtonInfo
from ..UI.DataFrameDialog import DataFrameDialog, MultiDataFrameDialog
from ..UI.FigureDialog import FigureDialog
from ..UI.MixedDataViewerDialog import MixedDataViewerDialog
from ..UI.PropertiesDialog import PropertiesDialog


class ViewDataFrameNodeActionButton(NodeActionButtonBase):
    """Custom action button for DataFrame viewing with visual feedback."""

    def __init__(self, svgFilePath, action, uiNode):
        super(ViewDataFrameNodeActionButton, self).__init__(svgFilePath, action, uiNode)
        self.svgIcon.setElementId("Expand")

    def mousePressEvent(self, event):
        super(ViewDataFrameNodeActionButton, self).mousePressEvent(event)
        # Update icon based on the state that will be AFTER viewDataFrame toggles it
        # Since viewDataFrame will toggle isDialogVisible, we set the opposite
        if self.parentItem().isDialogVisible:
            self.svgIcon.setElementId("Collapse")  # Will be closed after toggle
        else:
            self.svgIcon.setElementId("Expand")  # Will be opened after toggle


class PropertiesDialogManager:
    """Global manager for properties dialogs to prevent conflicts."""

    _instance = None
    _active_dialogs = {}
    _current_dialog = None  # Track the currently visible dialog

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PropertiesDialogManager, cls).__new__(cls)
        return cls._instance

    def get_or_create_dialog(self, node, parent):
        """Get existing dialog for node or create new one."""
        node_id = id(node)
        if node_id not in self._active_dialogs:
            dialog = PropertiesDialog(parent=parent)
            dialog.finished.connect(lambda: self._on_dialog_closed(node_id))
            self._active_dialogs[node_id] = dialog
        return self._active_dialogs[node_id]

    def show_dialog_for_node(self, node, parent, setNodeCallback):
        """Show dialog for specific node, hiding any currently visible dialog."""
        # Hide current dialog if it exists
        if self._current_dialog and self._current_dialog.isVisible():
            self._current_dialog.hide()

        # Get or create dialog for this node
        dialog = self.get_or_create_dialog(node, parent)
        dialog.setNode(node, setNodeCallback)
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()

        # Update current dialog reference
        self._current_dialog = dialog

        return dialog

    def _on_dialog_closed(self, node_id):
        """Handle dialog being closed."""
        if node_id in self._active_dialogs:
            dialog = self._active_dialogs[node_id]
            if self._current_dialog is dialog:
                self._current_dialog = None
            del self._active_dialogs[node_id]

    def close_all_dialogs(self):
        """Close all active property dialogs."""
        for dialog in list(self._active_dialogs.values()):
            dialog.close()
        self._active_dialogs.clear()
        self._current_dialog = None


class UIDataAnalysisBaseNode(UINodeBase):
    """Base UI class for all DataAnalysis nodes with popup data viewer.

    Provides two buttons:
    - View button: Toggle auto-updating data viewer dialog (supports DataFrame and Figure)
    - Refresh button: Forces node recomputation
    """

    def __init__(self, raw_node):
        super(UIDataAnalysisBaseNode, self).__init__(raw_node)

        # Collect all viewable pins (DataFramePin and MatplotlibFigurePin)
        self.dataFramePins = []
        self.figurePins = []

        # Check output pins first
        for pin in self._rawNode.outputs.values():
            if pin.dataType == "DataFramePin":
                self.dataFramePins.append(pin)
            elif pin.dataType == "MatplotlibFigurePin":
                self.figurePins.append(pin)

        # If no output pins, check input pins
        if not self.dataFramePins and not self.figurePins:
            for pin in self._rawNode.inputs.values():
                if pin.dataType == "DataFramePin":
                    self.dataFramePins.append(pin)
                elif pin.dataType == "MatplotlibFigurePin":
                    self.figurePins.append(pin)

        # Track dialog state (like OpenCV's displayImage)
        self.viewerDialog = None
        self.isDialogVisible = False

        # Track properties dialog state
        self.propertiesDialog = None
        self.isPropertiesDialogVisible = False
        self.dialogManager = PropertiesDialogManager()

        # If node has viewable pins, add view and refresh buttons
        if self.dataFramePins or self.figurePins:
            # Create view action and button (toggle dialog)
            self.actionViewData = self._menu.addAction("ViewData")
            self.actionViewData.setToolTip("Toggle data viewer dialog")
            self.actionViewData.triggered.connect(self.viewData)

            viewIconPath = os.path.join(
                os.path.dirname(__file__), "resources", "view.svg"
            )

            self.actionViewData.setData(
                NodeActionButtonInfo(viewIconPath, ViewDataFrameNodeActionButton)
            )

            # Create refresh action and button
            self.actionRefreshData = self._menu.addAction("RefreshNode")
            self.actionRefreshData.setToolTip("Refresh node computation")
            self.actionRefreshData.triggered.connect(self.refreshData)

            refreshIconPath = os.path.join(
                os.path.dirname(__file__), "resources", "reload.svg"
            )

            self.actionRefreshData.setData(
                NodeActionButtonInfo(refreshIconPath, NodeActionButtonBase)
            )

        # Connect to computed signal for auto-update (like OpenCV)
        self._rawNode.computed.connect(self.onNodeComputed)

    def viewData(self):
        """Toggle data viewer dialog (like OpenCV's viewImage)."""
        if not self.dataFramePins and not self.figurePins:
            return

        # Toggle state
        self.isDialogVisible = not self.isDialogVisible

        if self.isDialogVisible:
            # Open/show dialog
            self.showViewerDialog()
        else:
            # Close dialog
            self.closeViewerDialog()
        
        # Force refresh data when toggling (like OpenCV's refreshImage)
        self.refreshData()

    def showViewerDialog(self):
        """Show the appropriate viewer dialog based on available pin types."""
        from qtpy import QtWidgets

        # Collect data from all pins
        dataframes_dict = {}
        figures_dict = {}
        pins_data_dict = {}

        for pin in self.dataFramePins:
            df = pin.getData()
            # Include even empty DataFrames (they can be displayed)
            if df is not None:
                dataframes_dict[pin.name] = df
                pins_data_dict[pin.name] = ("DataFramePin", df)

        for pin in self.figurePins:
            fig = pin.getData()
            # Only include non-None figures (None means no plot generated yet)
            if fig is not None:
                figures_dict[pin.name] = fig
                pins_data_dict[pin.name] = ("MatplotlibFigurePin", fig)

        # Only show warning if we have pins but no data
        # If there are no pins at all, don't show warning (node doesn't support preview)
        has_any_pins = len(self.dataFramePins) > 0 or len(self.figurePins) > 0
        
        if not pins_data_dict:
            if has_any_pins:
                # We have pins but no data - node may not have executed yet
                # Still show dialog but with empty/placeholder content
                # This allows user to see the dialog and wait for data
                pass
            else:
                # No pins at all - this shouldn't happen if we got here, but handle gracefully
                QtWidgets.QMessageBox.information(
                    None, "No Data", "No data available to display."
                )
                self.isDialogVisible = False
                return

        # Determine which dialog to use based on pin types
        has_dataframes = len(dataframes_dict) > 0
        has_figures = len(figures_dict) > 0
        total_pins = len(pins_data_dict)
        
        # If no data but we have pins, create empty dialog with placeholder
        if not pins_data_dict and has_any_pins:
            # Create a mixed dialog with empty data to show placeholder
            empty_pins_dict = {}
            # Add placeholder entries for pins without data
            for pin in self.dataFramePins:
                empty_pins_dict[pin.name] = ("DataFramePin", pd.DataFrame())
            for pin in self.figurePins:
                empty_pins_dict[pin.name] = ("MatplotlibFigurePin", None)
            self.viewerDialog = MixedDataViewerDialog(empty_pins_dict, parent=None)
        elif has_dataframes and has_figures:
            # Mixed types - use MixedDataViewerDialog
            self.viewerDialog = MixedDataViewerDialog(pins_data_dict, parent=None)
        elif has_figures and not has_dataframes:
            # Only figures
            if total_pins == 1:
                # Single figure - use simple dialog
                pin_name, (_, figure) = list(pins_data_dict.items())[0]
                self.viewerDialog = FigureDialog(figure, pin_name, parent=None)
            else:
                # Multiple figures - use mixed dialog
                self.viewerDialog = MixedDataViewerDialog(pins_data_dict, parent=None)
        elif has_dataframes and not has_figures:
            # Only dataframes - use existing DataFrame dialogs
            if total_pins == 1:
                # Single DataFrame - use simple dialog
                pin_name, dataframe = list(dataframes_dict.items())[0]
                self.viewerDialog = DataFrameDialog(dataframe, pin_name, parent=None)
            else:
                # Multiple DataFrames - use tabbed dialog
                self.viewerDialog = MultiDataFrameDialog(dataframes_dict, parent=None)
        else:
            # Should not reach here if we handled empty case above
            # But handle gracefully just in case
            pass

        # Connect dialog close to update state
        self.viewerDialog.finished.connect(self.onDialogClosed)

        # Show as non-modal (allows interaction with graph while open)
        self.viewerDialog.show()

    def closeViewerDialog(self):
        """Close the viewer dialog."""
        if self.viewerDialog:
            self.viewerDialog.close()
            self.viewerDialog = None

    def onDialogClosed(self):
        """Handle dialog being closed by user."""
        self.isDialogVisible = False
        self.viewerDialog = None

    def updateDialogData(self):
        """Update dialog with latest data (called when node computes)."""
        if not self.viewerDialog or not self.isDialogVisible:
            return

        # Collect fresh data
        dataframes_dict = {}
        figures_dict = {}
        pins_data_dict = {}

        for pin in self.dataFramePins:
            df = pin.getData()
            if df is not None:
                dataframes_dict[pin.name] = df
                pins_data_dict[pin.name] = ("DataFramePin", df)

        for pin in self.figurePins:
            fig = pin.getData()
            if fig is not None:
                figures_dict[pin.name] = fig
                pins_data_dict[pin.name] = ("MatplotlibFigurePin", fig)

        # Update dialog based on type
        if isinstance(self.viewerDialog, DataFrameDialog):
            # Single DataFrame dialog
            if dataframes_dict:
                pin_name, dataframe = list(dataframes_dict.items())[0]
                self.viewerDialog.setDataFrame(dataframe)
        elif isinstance(self.viewerDialog, FigureDialog):
            # Single Figure dialog
            if figures_dict:
                pin_name, figure = list(figures_dict.items())[0]
                self.viewerDialog.setFigure(figure)
        elif isinstance(self.viewerDialog, MultiDataFrameDialog):
            # Multi DataFrame dialog - need to recreate (simpler than updating tabs)
            # Close current and open new one
            self.closeViewerDialog()
            self.showViewerDialog()
        elif isinstance(self.viewerDialog, MixedDataViewerDialog):
            # Mixed dialog - update all pins
            self.viewerDialog.updateAllPins(pins_data_dict)

    def refreshData(self):
        """Refresh button handler - force node recomputation."""
        if self.dataFramePins or self.figurePins:
            self._rawNode.processNode()

    def onNodeComputed(self, *args, **kwargs):
        """Called automatically when node finishes computing (like OpenCV's updateImage).

        Auto-updates the viewer dialog if it's open.
        """
        if self.isDialogVisible:
            self.updateDialogData()

    def togglePropertiesDialog(self):
        """Toggle properties dialog visibility."""
        # Check if this node's dialog is currently visible
        if (
            self.propertiesDialog
            and self.propertiesDialog.isVisible()
            and self.dialogManager._current_dialog is self.propertiesDialog
        ):
            # Dialog is visible, close it
            self.closePropertiesDialog()
        else:
            # Dialog is not visible, show it
            self.showPropertiesDialog()

    def showPropertiesDialog(self):
        """Show the properties dialog."""
        # Use global manager to show dialog and hide any currently visible one
        self.propertiesDialog = self.dialogManager.show_dialog_for_node(
            self, self.canvasRef(), self.createPropertiesWidget
        )
        self.isPropertiesDialogVisible = True

    def closePropertiesDialog(self):
        """Close the properties dialog."""
        if self.propertiesDialog:
            self.propertiesDialog.close()
        self.isPropertiesDialogVisible = False

    def onPropertiesDialogClosed(self):
        """Handle properties dialog being closed by user."""
        self.isPropertiesDialogVisible = False
        # Don't set self.propertiesDialog = None here as it's managed by the global manager

    def mouseDoubleClickEvent(self, event):
        """Handle double click on node to toggle properties dialog."""
        # Check if the click is on the node name widget (which handles its own double-click for editing)
        if self.nodeNameWidget.geometry().contains(event.pos()):
            # Let the node name widget handle the double-click for text editing
            super(UIDataAnalysisBaseNode, self).mouseDoubleClickEvent(event)
            return

        # Check if the click is on any action buttons
        for button in self._actionButtons:
            if button.geometry().contains(event.pos()):
                # Let the action button handle the double-click
                super(UIDataAnalysisBaseNode, self).mouseDoubleClickEvent(event)
                return

        # For other areas of the node, toggle properties dialog
        self.togglePropertiesDialog()
        # Don't call super() here to prevent further event propagation
        event.accept()

    def kill(self, *args, **kwargs):
        """Override kill method to clean up dialogs."""
        # Close properties dialog if open
        if self.propertiesDialog:
            self.propertiesDialog.close()
        # Call parent kill method
        super(UIDataAnalysisBaseNode, self).kill(*args, **kwargs)
