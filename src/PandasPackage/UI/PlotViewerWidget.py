"""
Matplotlib plot viewer widget for use in DockTools.

Reusable widget for displaying matplotlib Figure objects with interactive features.
Uses matplotlib's Qt backend for embedding plots in Qt applications.
"""

from qtpy import QtWidgets, QtCore, QtGui
try:
    import matplotlib
    # Auto-detect Qt version (Qt6/PySide6 uses QtAgg, Qt5 uses Qt5Agg)
    # qtpy automatically handles Qt5/Qt6 compatibility
    try:
        # Try Qt6 backend first (for PySide6)
        from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
        from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
    except ImportError:
        # Fallback to Qt5 backend
        matplotlib.use('Qt5Agg')
        from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
        from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
    from matplotlib.figure import Figure
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


class PlotViewerWidget(QtWidgets.QWidget):
    """Widget for displaying matplotlib Figure with toolbar and controls."""

    def __init__(self, parent=None):
        super(PlotViewerWidget, self).__init__(parent)
        
        if not MATPLOTLIB_AVAILABLE:
            self.setupNoMatplotlibUI()
            return
            
        self.current_figure = None
        self.setupUI()

    def setupUI(self):
        """Setup the widget UI."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Info bar
        infoLayout = QtWidgets.QHBoxLayout()

        self.infoLabel = QtWidgets.QLabel("No plot")
        self.infoLabel.setStyleSheet("font-weight: bold; color: #666;")
        infoLayout.addWidget(self.infoLabel)

        infoLayout.addStretch()

        # Save button
        self.saveButton = QtWidgets.QPushButton("Save")
        self.saveButton.setToolTip("Save current plot to file")
        self.saveButton.clicked.connect(self.savePlot)
        infoLayout.addWidget(self.saveButton)

        # Clear button
        self.clearButton = QtWidgets.QPushButton("Clear")
        self.clearButton.setToolTip("Clear the viewer")
        self.clearButton.clicked.connect(self.clear)
        infoLayout.addWidget(self.clearButton)

        layout.addLayout(infoLayout)

        # Matplotlib canvas (will be created when figure is set)
        self.canvas = None
        self.toolbar = None

        # Placeholder label
        self.placeholderLabel = QtWidgets.QLabel("No plot to display")
        self.placeholderLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.placeholderLabel.setStyleSheet("color: #999; font-size: 14px;")
        layout.addWidget(self.placeholderLabel)

    def setupNoMatplotlibUI(self):
        """Setup UI when matplotlib is not available."""
        layout = QtWidgets.QVBoxLayout(self)
        errorLabel = QtWidgets.QLabel(
            "matplotlib is not installed.\n"
            "Please install it with: pip install matplotlib"
        )
        errorLabel.setAlignment(QtCore.Qt.AlignCenter)
        errorLabel.setStyleSheet("color: #f00; font-size: 14px;")
        layout.addWidget(errorLabel)

    def setFigure(self, figure):
        """Set the matplotlib Figure to display.
        
        Args:
            figure: matplotlib.figure.Figure object or None
        """
        if not MATPLOTLIB_AVAILABLE:
            return

        if figure is None:
            self.clear()
            return

        try:
            import matplotlib.figure
            if not isinstance(figure, matplotlib.figure.Figure):
                self.infoLabel.setText(f"Invalid figure type: {type(figure).__name__}")
                return

            # Safely disconnect any existing callbacks and make current toolbar inert
            self._safe_teardown()

            # Remove old canvas and toolbar if they exist
            if self.canvas is not None:
                self.layout().removeWidget(self.canvas)
                self.canvas.setParent(None)
                self.canvas.deleteLater()
                self.canvas = None
            if self.toolbar is not None:
                self.layout().removeWidget(self.toolbar)
                self.toolbar.setParent(None)
                self.toolbar.deleteLater()
                self.toolbar = None
            if self.placeholderLabel is not None:
                self.layout().removeWidget(self.placeholderLabel)
                self.placeholderLabel.setParent(None)
                self.placeholderLabel = None

            # Store reference to prevent garbage collection
            self.current_figure = figure

            # Create new canvas with the figure
            self.canvas = FigureCanvas(figure)
            
            # Create navigation toolbar
            self.toolbar = NavigationToolbar(self.canvas, self)

            # Add to layout
            layout = self.layout()
            layout.addWidget(self.toolbar)
            layout.addWidget(self.canvas)

            # Update info
            num_axes = len(figure.axes)
            self.infoLabel.setText(
                f"Figure: {figure.get_size_inches()[0]:.1f}\" × {figure.get_size_inches()[1]:.1f}\" | "
                f"Axes: {num_axes}"
            )

            # Refresh the canvas
            self.canvas.draw()
            QtWidgets.QApplication.processEvents()

        except Exception as e:
            self.infoLabel.setText(f"Error displaying figure: {e}")

    def getFigure(self):
        """Get the current Figure."""
        return self.current_figure

    def savePlot(self):
        """Save the current plot to a file."""
        if self.current_figure is None:
            QtWidgets.QMessageBox.warning(self, "No Plot", "No plot to save")
            return

        fileName, selectedFilter = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Save Plot",
            "",
            "PNG Files (*.png);;PDF Files (*.pdf);;SVG Files (*.svg);;All Files (*)"
        )

        if fileName:
            try:
                self.current_figure.savefig(fileName, dpi=300, bbox_inches='tight')
                QtWidgets.QMessageBox.information(
                    self, "Success", f"Plot saved to {fileName}"
                )
            except Exception as e:
                QtWidgets.QMessageBox.critical(
                    self, "Save Error", f"Failed to save plot: {e}"
                )

    def clear(self):
        """Clear the viewer."""
        if not MATPLOTLIB_AVAILABLE:
            return

        # Safely disconnect and teardown first to avoid callbacks firing after deletion
        self._safe_teardown()

        # Remove canvas and toolbar
        if self.canvas is not None:
            self.layout().removeWidget(self.canvas)
            self.canvas.setParent(None)
            self.canvas.deleteLater()
            self.canvas = None
        if self.toolbar is not None:
            self.layout().removeWidget(self.toolbar)
            self.toolbar.setParent(None)
            self.toolbar.deleteLater()
            self.toolbar = None

        # Restore placeholder
        if self.placeholderLabel is None:
            layout = self.layout()
            self.placeholderLabel = QtWidgets.QLabel("No plot to display")
            self.placeholderLabel.setAlignment(QtCore.Qt.AlignCenter)
            self.placeholderLabel.setStyleSheet("color: #999; font-size: 14px;")
            layout.addWidget(self.placeholderLabel)

        self.current_figure = None
        self.infoLabel.setText("No plot")

    def _safe_teardown(self):
        """Disconnect Matplotlib callbacks and make toolbar inert before deletion."""
        # Stop Qt interactions on the canvas
        if getattr(self, "canvas", None) is not None:
            try:
                self.canvas.setMouseTracking(False)
                self.canvas.setEnabled(False)
            except Exception:
                pass
            # Disconnect all Matplotlib callbacks registered on this canvas
            try:
                registry = getattr(self.canvas, "callbacks", None)
                if registry is not None and hasattr(registry, "callbacks"):
                    for _event, mapping in list(registry.callbacks.items()):
                        for cid in list(mapping.keys()):
                            try:
                                self.canvas.mpl_disconnect(cid)
                            except Exception:
                                pass
            except Exception:
                pass

        # Make toolbar inert to avoid late set_message updates touching deleted QLabel
        if getattr(self, "toolbar", None) is not None:
            try:
                self.toolbar.setVisible(False)
            except Exception:
                pass
            try:
                self.toolbar.set_message = lambda *a, **k: None
            except Exception:
                pass
            try:
                if hasattr(self.toolbar, "destroy"):
                    self.toolbar.destroy()
            except Exception:
                pass

    def closeEvent(self, event):
        # Ensure teardown happens if the widget is closed via parent/dialog
        try:
            self.clear()
        except Exception:
            pass
        super(PlotViewerWidget, self).closeEvent(event)
