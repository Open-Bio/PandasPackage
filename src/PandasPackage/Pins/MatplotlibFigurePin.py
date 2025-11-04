import json
from uflow.Core import PinBase
from uflow.Core.Common import *


class NoneEncoder(json.JSONEncoder):
    """JSON encoder that returns None for Figure objects (non-serializable)"""

    def default(self, obj):
        return None


class NoneDecoder(json.JSONDecoder):
    """JSON decoder that returns None for Figure objects (non-serializable)"""

    def __init__(self, *args, **kwargs):
        super(NoneDecoder, self).__init__(object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, objDict):
        return None


class MatplotlibFigurePin(PinBase):
    """Matplotlib Figure pin for passing matplotlib Figure objects between nodes

    This pin type is designed for data visualization workflows where matplotlib
    Figure objects need to be passed between nodes. Due to the complexity and
    non-serializable nature of Figure objects, this pin is marked as non-storable.

    Features:
    - Supports matplotlib.figure.Figure objects
    - Purple color (150, 100, 200) for easy identification
    - Not serializable (for performance reasons)
    - Returns None when no data is present

    Example usage:
        # In a node's __init__:
        self.inputFig = self.createInputPin('figure', 'MatplotlibFigurePin')
        self.outputFig = self.createOutputPin('result', 'MatplotlibFigurePin')

        # In compute():
        fig = self.inputFig.getData()
        # Process the Figure
        self.outputFig.setData(fig)
    """

    def __init__(self, name, parent, direction, **kwargs):
        super(MatplotlibFigurePin, self).__init__(name, parent, direction, **kwargs)
        self.setDefaultValue(None)
        # Disable storage to avoid serialization issues with Figure objects
        self.disableOptions(PinOptions.Storable)

    @staticmethod
    def jsonEncoderClass():
        """Return JSON encoder class (returns None for Figures)"""
        return NoneEncoder

    @staticmethod
    def jsonDecoderClass():
        """Return JSON decoder class (returns None for Figures)"""
        return NoneDecoder

    @staticmethod
    def IsValuePin():
        """Indicates this is a value pin (not an execution pin)"""
        return True

    @staticmethod
    def supportedDataTypes():
        """Return tuple of supported data types that can connect to this pin"""
        return ("MatplotlibFigurePin",)

    @staticmethod
    def pinDataTypeHint():
        """Return pin type identifier and default value"""
        return "MatplotlibFigurePin", None

    @staticmethod
    def color():
        """Return RGBA color for the pin (purple for visualization)"""
        return (150, 100, 200, 255)

    @staticmethod
    def internalDataStructure():
        """Return the internal Python type this pin handles"""
        try:
            import matplotlib.figure
            return matplotlib.figure.Figure
        except ImportError:
            # Fallback if matplotlib is not available
            return type(None)

    @staticmethod
    def processData(data):
        """Process and validate incoming data

        Args:
            data: Input data to be processed

        Returns:
            matplotlib.figure.Figure: Valid Figure object or None

        Raises:
            TypeError: If data is not a Figure or None
        """
        if data is None:
            return None
        
        try:
            import matplotlib.figure
            if isinstance(data, matplotlib.figure.Figure):
                return data
            else:
                raise TypeError(
                    f"Invalid data type for MatplotlibFigurePin: expected matplotlib.figure.Figure, "
                    f"got {type(data).__name__}. Please ensure the connected node "
                    f"outputs a valid Figure object."
                )
        except ImportError:
            raise ImportError(
                "matplotlib is not installed. Please install it with: pip install matplotlib"
            )
