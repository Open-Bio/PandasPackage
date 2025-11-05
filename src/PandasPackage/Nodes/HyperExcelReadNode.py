import os
import re
import pandas as pd
from uflow.Core import NodeBase
from uflow.Core.NodeBase import NodePinsSuggestionsHelper
from uflow.Core.Common import *
from uflow import getPinDefaultValueByType


class HyperExcelRead(NodeBase):
    """Node that reads all sheets from an Excel file and creates dynamic output pins for each sheet."""

    def __init__(self, name):
        super(HyperExcelRead, self).__init__(name)
        
        # Input pins
        self.pathPin = self.createInputPin(
            "path", 
            "StringPin", 
            defaultValue="",
            callback=self.onPathChanged,
            structure=StructureType.Single,
        )
        # Set FilePathWidget for path pin
        self.pathPin.annotationDescriptionDict = {
            PinSpecifiers.INPUT_WIDGET_VARIANT: "FilePathWidget"
        }
        
        self.headerPin = self.createInputPin(
            "header",
            "IntPin",
            defaultValue=0,
            callback=self.compute,
            structure=StructureType.Single,
        )
        self.inExec = self.createInputPin(
            DEFAULT_IN_EXEC_NAME, "ExecPin", None, self.compute
        )
        
        # Output pins - create a default DataFramePin output for preview functionality
        self.outExec = self.createOutputPin(DEFAULT_OUT_EXEC_NAME, "ExecPin")
        self.defaultOutput = self.createOutputPin(
            "data",
            "DataFramePin",
            defaultValue=pd.DataFrame(),
            structure=StructureType.Single,
        )
        
        # Track sheet names and pins mapping
        self._sheetNames = []  # List of sheet names in order
        self._sheetPinMap = {}  # Map from sheet name to pin name
        self._lastPath = ""  # Track last processed path
        
        # Disable cache to ensure fresh reads
        self.bCacheEnabled = False

    def _sanitizePinName(self, sheet_name):
        """Convert sheet name to a valid pin name by replacing invalid characters.
        
        Args:
            sheet_name: Original sheet name from Excel
            
        Returns:
            str: Sanitized pin name
        """
        if not sheet_name or not isinstance(sheet_name, str):
            return "sheet"
        
        # Replace invalid characters with underscore
        # Keep alphanumeric, underscore, and common safe characters
        sanitized = re.sub(r'[^\w\-]', '_', sheet_name)
        
        # Remove leading/trailing underscores and dots
        sanitized = sanitized.strip('_.')
        
        # Ensure it's not empty
        if not sanitized:
            sanitized = "sheet"
        
        # Ensure it doesn't start with a number
        if sanitized[0].isdigit():
            sanitized = "sheet_" + sanitized
        
        return sanitized

    def _updateOutputPins(self, sheet_names):
        """Update output pins based on sheet names.
        
        Args:
            sheet_names: List of sheet names from Excel file
        """
        # Get current output pin names (excluding ExecPin)
        current_pin_names = {
            pin.name for pin in self.outputs.values() 
            if pin.dataType == "DataFramePin"
        }
        
        # Remove default "data" pin if sheets are detected
        if sheet_names:
            default_pin = self.getPinByName("data")
            if default_pin and default_pin.dataType == "DataFramePin":
                default_pin.kill()
                # Remove from current_pin_names set
                current_pin_names.discard("data")
        else:
            # No sheets, ensure default "data" pin exists
            default_pin = self.getPinByName("data")
            if not default_pin or default_pin.dataType != "DataFramePin":
                # Create default "data" pin if it doesn't exist
                self.defaultOutput = self.createOutputPin(
                    "data",
                    "DataFramePin",
                    defaultValue=pd.DataFrame(),
                    structure=StructureType.Single,
                )
                current_pin_names.add("data")
        
        # Get new pin names for sheets
        new_pin_names = set()
        sheet_to_pin_map = {}
        
        for sheet_name in sheet_names:
            pin_name = self._sanitizePinName(sheet_name)
            # Ensure uniqueness
            pin_name = self.getUniqPinName(pin_name)
            new_pin_names.add(pin_name)
            sheet_to_pin_map[sheet_name] = pin_name
        
        # Remove pins that are no longer needed (excluding default "data" pin)
        pins_to_remove = current_pin_names - new_pin_names - {"data"}
        for pin_name in pins_to_remove:
            pin = self.getPinByName(pin_name)
            if pin and pin.dataType == "DataFramePin":
                pin.kill()
        
        # Create new pins that don't exist yet
        for sheet_name in sheet_names:
            pin_name = sheet_to_pin_map[sheet_name]
            if pin_name not in current_pin_names:
                self.createOutputPin(
                    pin_name,
                    "DataFramePin",
                    defaultValue=pd.DataFrame(),
                    structure=StructureType.Single,
                )
        
        # Update tracking
        self._sheetNames = list(sheet_names)
        self._sheetPinMap = sheet_to_pin_map
        
        # Update node structure
        self.autoAffectPins()
        
        # Notify UI to update
        wrapper = self.getWrapper()
        if wrapper:
            wrapper.onPinsUpdated()

    def onPathChanged(self, *args, **kwargs):
        """Callback when path input changes. Updates output pins based on Excel file structure."""
        try:
            path = self.pathPin.getData()
            
            # Check if path is valid and changed
            if not path or not isinstance(path, str) or not path.strip():
                # Clear output pins if path is empty
                if self._sheetNames:
                    self._updateOutputPins([])
                self._lastPath = ""
                return
            
            path = path.strip()
            
            # Skip if path hasn't changed
            if path == self._lastPath:
                return
            
            # Check if file exists
            if not os.path.exists(path):
                self.setError(f"File not found: {path}")
                if self._sheetNames:
                    self._updateOutputPins([])
                self._lastPath = ""
                return
            
            # Try to read Excel file structure
            try:
                excel_file = pd.ExcelFile(path)
                sheet_names = excel_file.sheet_names
                
                if not sheet_names:
                    self.setError(f"No sheets found in Excel file: {path}")
                    self._updateOutputPins([])
                else:
                    self.clearError()
                    self._updateOutputPins(sheet_names)
                    self._lastPath = path
                    
            except Exception as e:
                self.setError(f"Error reading Excel file: {str(e)}")
                if self._sheetNames:
                    self._updateOutputPins([])
                self._lastPath = ""
                
        except Exception as e:
            self.setError(f"Error processing path: {str(e)}")
            if self._sheetNames:
                self._updateOutputPins([])
            self._lastPath = ""

    def compute(self, *args, **kwargs):
        """Read all sheets from Excel file and set data to corresponding output pins."""
        try:
            path = self.pathPin.getData()
            header = self.headerPin.getData()
            
            if header is None:
                header = 0
            
            # Validate path
            if not path or not isinstance(path, str) or not path.strip():
                # Set empty DataFrames to all output pins
                for sheet_name in self._sheetNames:
                    pin_name = self._sheetPinMap.get(sheet_name)
                    if pin_name:
                        pin = self.getPinByName(pin_name)
                        if pin:
                            pin.setData(pd.DataFrame())
                self.outExec.call()
                return
            
            path = path.strip()
            
            # Check if file exists
            if not os.path.exists(path):
                self.setError(f"File not found: {path}")
                # Set empty DataFrames to all output pins
                for sheet_name in self._sheetNames:
                    pin_name = self._sheetPinMap.get(sheet_name)
                    if pin_name:
                        pin = self.getPinByName(pin_name)
                        if pin:
                            pin.setData(pd.DataFrame())
                self.outExec.call()
                return
            
            # Read all sheets
            try:
                excel_file = pd.ExcelFile(path)
                
                # Ensure pins are up to date
                current_sheet_names = excel_file.sheet_names
                if set(current_sheet_names) != set(self._sheetNames):
                    self._updateOutputPins(current_sheet_names)
                
                # Read each sheet and set to corresponding pin
                for sheet_name in self._sheetNames:
                    pin_name = self._sheetPinMap.get(sheet_name)
                    if pin_name:
                        try:
                            df = pd.read_excel(path, sheet_name=sheet_name, header=header)
                            pin = self.getPinByName(pin_name)
                            if pin:
                                pin.setData(df)
                        except Exception as e:
                            # If a specific sheet fails, set empty DataFrame
                            self.setError(f"Error reading sheet '{sheet_name}': {str(e)}")
                            pin = self.getPinByName(pin_name)
                            if pin:
                                pin.setData(pd.DataFrame())
                
                self.clearError()
                
            except Exception as e:
                self.setError(f"Error reading Excel file: {str(e)}")
                # Set empty DataFrames to all output pins
                for sheet_name in self._sheetNames:
                    pin_name = self._sheetPinMap.get(sheet_name)
                    if pin_name:
                        pin = self.getPinByName(pin_name)
                        if pin:
                            pin.setData(pd.DataFrame())
                            
        except Exception as e:
            self.setError(f"Error in compute: {str(e)}")
            # Set empty DataFrames to all output pins
            for sheet_name in self._sheetNames:
                pin_name = self._sheetPinMap.get(sheet_name)
                if pin_name:
                    pin = self.getPinByName(pin_name)
                    if pin:
                        pin.setData(pd.DataFrame())
        
        self.outExec.call()

    def serialize(self):
        """Serialize node state including sheet pin mappings."""
        default = super(HyperExcelRead, self).serialize()
        default["sheetNames"] = self._sheetNames
        default["sheetPinMap"] = self._sheetPinMap
        default["lastPath"] = self._lastPath
        return default

    def postCreate(self, jsonTemplate=None):
        """Restore node state from serialized data."""
        try:
            super(HyperExcelRead, self).postCreate(jsonTemplate)
            
            if jsonTemplate is None:
                return
            
            # Restore sheet names and pin mappings
            if "sheetNames" in jsonTemplate and "sheetPinMap" in jsonTemplate:
                sheet_names = jsonTemplate.get("sheetNames", [])
                sheet_pin_map = jsonTemplate.get("sheetPinMap", {})
                
                if sheet_names:
                    # Restore pin mappings
                    self._sheetNames = sheet_names
                    self._sheetPinMap = sheet_pin_map
                    
                    # Create pins that might not exist yet
                    for sheet_name in sheet_names:
                        pin_name = sheet_pin_map.get(sheet_name)
                        if pin_name:
                            existing_pin = self.getPinByName(pin_name)
                            if not existing_pin:
                                self.createOutputPin(
                                    pin_name,
                                    "DataFramePin",
                                    defaultValue=pd.DataFrame(),
                                    structure=StructureType.Single,
                                )
                    
                    # Only call autoAffectPins if graph is valid
                    if self.graph() is not None:
                        self.autoAffectPins()
            
            # Restore last path
            if "lastPath" in jsonTemplate:
                self._lastPath = jsonTemplate["lastPath"]
            
            # Restore pin values from template
            for outJson in jsonTemplate.get("outputs", []):
                pin = self.getPinByName(outJson["name"])
                if pin:
                    pin.deserialize(outJson)
        except Exception as e:
            # Silently handle errors during deserialization to avoid issues
            # during application shutdown/cleanup
            pass

    @staticmethod
    def pinTypeHints():
        """Return pin type hints for node suggestions."""
        helper = NodePinsSuggestionsHelper()
        helper.addInputDataType("ExecPin")
        helper.addInputDataType("StringPin")
        helper.addInputDataType("IntPin")
        helper.addOutputDataType("ExecPin")
        helper.addOutputDataType("DataFramePin")
        helper.addInputStruct(StructureType.Single)
        helper.addOutputStruct(StructureType.Single)
        return helper

    @staticmethod
    def category():
        """Return node category."""
        return "Data Input"

    @staticmethod
    def keywords():
        """Return search keywords."""
        return ["excel", "read", "hyper", "all", "sheets", "multiple"]

    @staticmethod
    def description():
        """Return node description."""
        return "Read all sheets from an Excel file. Dynamically creates output pins for each sheet."

