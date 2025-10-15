import os
from uflow.Core.PackageBase import PackageBase


class PandasPackage(PackageBase):
    """Data Analysis uflow package"""

    def __init__(self):
        super(PandasPackage, self).__init__()
        self.analyzePackage(os.path.dirname(__file__))

    def PinsInputWidgetFactory(self):
        """Register input widget factory for custom widgets"""
        from .Factories.PinInputWidgetFactory import getInputWidget

        return getInputWidget
