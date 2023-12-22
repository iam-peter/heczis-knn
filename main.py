import sys
import time

import numpy as np
import matplotlib.pyplot as plt

from matplotlib.backends.backend_qtagg import FigureCanvas
from matplotlib.backends.backend_qtagg import \
    NavigationToolbar2QT as NavigationToolbar
from matplotlib.backends.qt_compat import QtWidgets
from matplotlib.figure import Figure

from scipy.spatial import KDTree

from PySide6.QtCore import *
from PySide6.QtWidgets import *

class ApplicationWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.centralWidget = QWidget()
        self.setCentralWidget(self.centralWidget)

        mainLayout = QHBoxLayout(self.centralWidget)

        figureLayout = QVBoxLayout()

        self.canvas = FigureCanvas(Figure(figsize=(5, 5)))

        figureLayout.addWidget(NavigationToolbar(self.canvas, self))
        figureLayout.addWidget(self.canvas)

        mainLayout.addLayout(figureLayout)

        # Store the current query position
        self.position = QPointF()

        self.settingLayout = QFormLayout()

        self.xSpinBox = QDoubleSpinBox()
        self.xSpinBox.valueChanged.connect(self.positionChanged)

        self.ySpinBox = QDoubleSpinBox()
        self.ySpinBox.valueChanged.connect(self.positionChanged)

        self.resetButton = QPushButton('Reset')

        self.modeComboBox = QComboBox()
        self.modeComboBox.addItems(["K Neighbors", "Radius Neighbors"])
        self.modeComboBox.currentIndexChanged.connect(self.modeChanged)

        self.kSpinBox = QSpinBox()
        self.kSpinBox.setValue(8)
        self.kSpinBox.valueChanged.connect(self.updateNeighborVisualization)

        self.radiusSpinBox = QDoubleSpinBox()
        self.radiusSpinBox.setValue(12)
        self.radiusSpinBox.valueChanged.connect(self.updateNeighborVisualization)

        self.settingLayout.addRow('X', self.xSpinBox)
        self.settingLayout.addRow('Y', self.ySpinBox)
        self.settingLayout.addRow(self.resetButton)
        self.settingLayout.addRow('Mode', self.modeComboBox)
        self.settingLayout.addRow('K', self.kSpinBox) # 4
        self.settingLayout.addRow('Radius', self.radiusSpinBox) # 5

        self.settingLayout.setRowVisible(5, False)

        mainLayout.addLayout(self.settingLayout)

        self._static_ax = self.canvas.figure.subplots()

        f = open('Simulated_Data_ML.csv', 'r', encoding='utf-8-sig')
        self.data = np.loadtxt(f,
                               dtype=np.dtype([('p1', np.float64), ('p2', np.float64), ('label', np.uintc)]),
                               delimiter=',', skiprows=1)

        self.kdTree = KDTree(self.data[['p1', 'p2']].tolist())

        self._static_ax.scatter(self.data['p1'], self.data['p2'], c=self.data['label'], alpha=0.5)
        self._static_ax.grid(True)

        self._lines = []

        self.circle = self._static_ax.add_patch(plt.Circle((60, 60), radius=self.radiusSpinBox.value(), fill=False, edgecolor='k'))
        self.circle.set_visible(False)

        self.canvas.mpl_connect('button_press_event', self.onClick)

    def onClick(self, event):
        self.position = QPointF(event.xdata, event.ydata)
        self.xSpinBox.blockSignals(True)
        self.ySpinBox.blockSignals(True)
        self.xSpinBox.setValue(self.position.x())
        self.ySpinBox.setValue(self.position.y())
        self.xSpinBox.blockSignals(False)
        self.ySpinBox.blockSignals(False)

        self.updateNeighborVisualization()

    def modeChanged(self):
        if self.modeComboBox.currentIndex() == 0: # K Neighbors
            self.settingLayout.setRowVisible(4, True)
            self.settingLayout.setRowVisible(5, False)
        else:
            self.settingLayout.setRowVisible(4, False)
            self.settingLayout.setRowVisible(5, True)

        self.updateNeighborVisualization()

    def positionChanged(self):
        self.position = QPointF(self.xSpinBox.value(), self.ySpinBox.value())

        self.updateNeighborVisualization()

    def updateNeighborVisualization(self):
        # Clear previous lines
        [[l.remove() for l in lines] for lines in self._lines]
        self._lines.clear()
        # Clear previous points
        if hasattr(self, '_points'):
            self._points.remove()
            delattr(self, "_points")

        self.circle.set_visible(False)

        # Early return if point is not contained in figure
        if not self._static_ax.viewLim.contains(self.position.x(), self.position.y()):
            return

        if self.modeComboBox.currentIndex() == 0: # K Neighbors
            print("K Neighbors")

            distances, indices = self.kdTree.query([self.position.x(), self.position.y()], k=self.kSpinBox.value())

            for index in indices:
                self._lines.append(self._static_ax.plot([self.data['p1'][index], self.position.x()],
                                                        [self.data['p2'][index], self.position.y()],
                                                        'k+-', alpha=0.3))

        else: # Radius Neighbors
            print("Radius Neighbors")

            indices = self.kdTree.query_ball_point([self.position.x(), self.position.y()], r=self.radiusSpinBox.value())

            x = []
            y = []

            for index in indices:
                x.append(self.data['p1'][index])
                y.append(self.data['p2'][index])

            self._points = self._static_ax.scatter(x, y, c='r', alpha=0.5)

            self.circle.set_visible(True)
            self.circle.set_radius(self.radiusSpinBox.value())
            self.circle.set_center([self.position.x(), self.position.y()])


        self.canvas.draw()


if __name__ == "__main__":
    # Check whether there is already a running QApplication (e.g., if running
    # from an IDE).
    qapp = QtWidgets.QApplication.instance()
    if not qapp:
        qapp = QtWidgets.QApplication(sys.argv)

    app = ApplicationWindow()
    app.resize(800, 600)
    app.show()
    app.activateWindow()
    app.raise_()
    qapp.exec()