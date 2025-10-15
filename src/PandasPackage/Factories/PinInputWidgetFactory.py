# Input widgets for pins

from qtpy import QtCore
from qtpy.QtWidgets import *
from qtpy import QtGui
import pandas as pd
import time

from uflow.UI.Widgets.InputWidgets import InputWidgetSingle
from uflow.Core.Common import *
from qtpy.QtWidgets import QTextEdit


class DynamicColumnSelectorWidget(InputWidgetSingle):
    """
    Dynamic column selector widget that shows DataFrame columns in a dropdown
    Similar to EnumInputWidget but with dynamic column list and performance optimizations
    """

    def __init__(self, parent=None, **kwargs):
        super(DynamicColumnSelectorWidget, self).__init__(parent=parent, **kwargs)

        # Store owning node reference for accessing DataFrame pins
        self.owningNode = None
        if "owningNode" in kwargs:
            self.owningNode = kwargs["owningNode"]

        # Create EnumComboBox for dropdown selection
        from uflow.UI.Widgets.EnumComboBox import EnumComboBox

        self.enumBox = EnumComboBox([])
        self.enumBox.setEditable(True)  # Allow manual input
        # Don't connect changeCallback directly - we'll handle it manually
        # self.enumBox.changeCallback.connect(self.dataSetCallback)
        self.setWidget(self.enumBox)

        # Performance optimization flags
        self._columns_cached = []
        self._last_update_time = 0
        self._update_threshold = 0.5  # Minimum time between updates (seconds)
        self._is_updating = False

        # Debounce timer for input changes
        self._debounce_timer = QtCore.QTimer()
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.timeout.connect(self._onDebounceTimeout)
        self._debounce_delay = 300  # 300ms debounce delay

        # Connect signals for manual refresh and user selection
        self.enumBox.activated.connect(self._onDropdownActivated)
        self.enumBox.lineEdit().textChanged.connect(self._onTextChanged)
        # Connect for user selection changes (not column list updates)
        self.enumBox.currentTextChanged.connect(self._onUserSelectionChanged)

        # Don't auto-update on init to improve performance
        # self.updateColumnList()

    def _onDropdownActivated(self, index):
        """Handle dropdown activation - trigger manual refresh"""
        if not self._is_updating:
            self.updateColumnList()

    def _onTextChanged(self, text):
        """Handle text changes with debouncing"""
        # Stop previous timer
        self._debounce_timer.stop()

        # Start new timer
        self._debounce_timer.start(self._debounce_delay)

    def _onDebounceTimeout(self):
        """Handle debounced text change"""
        # Only update if we're not already updating
        if not self._is_updating:
            self.updateColumnList()

    def _onUserSelectionChanged(self, text):
        """Handle user selection changes - trigger dataSetCallback"""
        # Only call dataSetCallback for actual user selections, not programmatic updates
        if not self._is_updating:
            self.dataSetCallback(text)

    def updateColumnList(self):
        """Update the dropdown list with current DataFrame columns (with performance optimizations)"""
        try:
            # Check if we should skip this update
            current_time = time.time()
            if current_time - self._last_update_time < self._update_threshold:
                return

            self._is_updating = True
            self._last_update_time = current_time

            columns = self.getDataFrameColumns()

            # Only update if columns have actually changed
            if columns != self._columns_cached:
                # Store current selection before updating
                current_selection = self.enumBox.currentText()

                self._columns_cached = columns.copy() if columns else []

                # Update the combobox model
                model = QtGui.QStandardItemModel()
                for i, column in enumerate(columns):
                    item = QtGui.QStandardItem(column)
                    model.setItem(i, 0, item)

                # Block signals during model update to prevent recursion
                self.enumBox.blockSignals(True)
                self.enumBox.setModel(model)
                self.enumBox.setModelColumn(0)

                # Restore previous selection if it still exists in the new list
                if current_selection and current_selection in columns:
                    self.enumBox.setCurrentText(current_selection)
                elif columns:  # If previous selection not found, set to first column
                    self.enumBox.setCurrentText(columns[0])

                self.enumBox.blockSignals(False)

        except Exception as e:
            print(f"Error updating column list: {e}")
        finally:
            self._is_updating = False

    def getDataFrameColumns(self):
        """Extract column names from connected DataFrame pins without triggering execution"""
        try:
            if not self.owningNode:
                return []

            # Get the raw node from UI node
            rawNode = (
                self.owningNode._rawNode
                if hasattr(self.owningNode, "_rawNode")
                else self.owningNode
            )

            # Look for DataFrame input pins
            for pin in rawNode.inputs.values():
                if pin.dataType == "DataFramePin" and pin.hasConnections():
                    # Use currentData() instead of getData() to avoid triggering execution
                    df = pin.currentData()
                    if df is not None and not df.empty:
                        return list(df.columns)

            return []
        except Exception as e:
            print(f"Error extracting DataFrame columns: {e}")
            return []

    def blockWidgetSignals(self, bLock=False):
        self.enumBox.blockSignals(bLock)

    def setWidgetValue(self, val):
        self.enumBox.setCurrentText(str(val))

    def showEvent(self, event):
        """Update column list when widget is shown (with performance check)"""
        super(DynamicColumnSelectorWidget, self).showEvent(event)
        # Only update if we haven't updated recently
        current_time = time.time()
        if current_time - self._last_update_time > self._update_threshold:
            self.updateColumnList()

    def forceRefresh(self):
        """Force refresh the column list (for manual refresh)"""
        self._last_update_time = 0  # Reset timer
        self.updateColumnList()


class TextEditWidget(InputWidgetSingle):
    """
    Multi-line text input widget for comma-separated value lists
    """

    def __init__(self, parent=None, **kwargs):
        super(TextEditWidget, self).__init__(parent=parent, **kwargs)

        # Create QTextEdit for multi-line input
        self.textEdit = QTextEdit(self)
        self.textEdit.setMaximumHeight(100)  # Limit height for better UI
        self.textEdit.setPlaceholderText(
            "Enter comma-separated values (e.g., value1, value2, value3)"
        )
        self.setWidget(self.textEdit)

        # Connect text change signal
        self.textEdit.textChanged.connect(self._onTextChanged)

    def _onTextChanged(self):
        """Handle text changes and call dataSetCallback"""
        text = self.textEdit.toPlainText()
        self.dataSetCallback(text)

    def blockWidgetSignals(self, bLock=False):
        self.textEdit.blockSignals(bLock)

    def setWidgetValue(self, val):
        self.textEdit.setPlainText(str(val))


def getInputWidget(dataType, dataSetter, defaultValue, widgetVariant, **kwargs):
    """
    Factory function for creating input widgets
    """
    if widgetVariant == "DynamicColumnSelectorWidget":
        return DynamicColumnSelectorWidget(
            dataSetCallback=dataSetter, defaultValue=defaultValue, **kwargs
        )
    elif widgetVariant == "TextEditWidget":
        return TextEditWidget(
            dataSetCallback=dataSetter, defaultValue=defaultValue, **kwargs
        )
    return None
