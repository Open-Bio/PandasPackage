import pandas as pd
import json
from uflow.Core import PinBase
from uflow.Core.Common import *


class NoneEncoder(json.JSONEncoder):
    """JSON encoder that returns None for DataFrame objects (non-serializable)"""

    def default(self, obj):
        return None


class NoneDecoder(json.JSONDecoder):
    """JSON decoder that returns None for DataFrame objects (non-serializable)"""

    def __init__(self, *args, **kwargs):
        super(NoneDecoder, self).__init__(object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, objDict):
        return None


class DataFramePin(PinBase):
    """DataFrame pin for passing pandas DataFrame objects between nodes

    This pin type is designed for data analysis workflows where tabular data
    needs to be passed between nodes. Due to the size and complexity of DataFrames,
    this pin is marked as non-storable (won't be saved with the graph).

    Features:
    - Supports pandas DataFrame objects
    - Green color (50, 200, 100) for easy identification
    - Not serializable (for performance reasons)
    - Returns empty DataFrame when no data is present

    Example usage:
        # In a node's __init__:
        self.inputDF = self.createInputPin('df', 'DataFramePin')
        self.outputDF = self.createOutputPin('result', 'DataFramePin')

        # In compute():
        df = self.inputDF.getData()
        result = df.copy()  # Process the DataFrame
        self.outputDF.setData(result)
    """

    def __init__(self, name, parent, direction, **kwargs):
        super(DataFramePin, self).__init__(name, parent, direction, **kwargs)
        self.setDefaultValue(pd.DataFrame())
        # Disable storage to avoid serialization issues with large DataFrames
        self.disableOptions(PinOptions.Storable)

    @staticmethod
    def jsonEncoderClass():
        """Return JSON encoder class (returns None for DataFrames)"""
        return NoneEncoder

    @staticmethod
    def jsonDecoderClass():
        """Return JSON decoder class (returns None for DataFrames)"""
        return NoneDecoder

    @staticmethod
    def IsValuePin():
        """Indicates this is a value pin (not an execution pin)"""
        return True

    @staticmethod
    def supportedDataTypes():
        """Return tuple of supported data types that can connect to this pin"""
        return ("DataFramePin",)

    @staticmethod
    def pinDataTypeHint():
        """Return pin type identifier and default value"""
        return "DataFramePin", pd.DataFrame()

    @staticmethod
    def color():
        """Return RGBA color for the pin (green for data)"""
        return (50, 200, 100, 255)

    @staticmethod
    def internalDataStructure():
        """Return the internal Python type this pin handles"""
        return pd.DataFrame

    @staticmethod
    def processData(data):
        """Process and validate incoming data

        Args:
            data: Input data to be processed

        Returns:
            pd.DataFrame: Valid DataFrame object

        Raises:
            TypeError: If data is not a DataFrame or None
        """
        if data is None:
            return DataFramePin.pinDataTypeHint()[1]
        if isinstance(data, pd.DataFrame):
            return data
        else:
            raise TypeError(
                f"Invalid data type for DataFramePin: expected pandas.DataFrame, "
                f"got {type(data).__name__}. Please ensure the connected node "
                f"outputs a valid DataFrame object."
            )

    def getInputWidgetVariant(self):
        """Define custom input widget variant for DataFramePin

        This allows pins to specify custom UI widgets through annotations.
        """
        if self.annotationDescriptionDict is not None:
            if PinSpecifiers.INPUT_WIDGET_VARIANT in self.annotationDescriptionDict:
                return self.annotationDescriptionDict[
                    PinSpecifiers.INPUT_WIDGET_VARIANT
                ]
        return self._inputWidgetVariant
