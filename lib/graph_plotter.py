"""A graph plotting module using Matplotlib to generate graphs from 
collected data stored in CSV files and PyQt5 to create the window framework.\n
NOTE: Module is in beta stage and will require redevelopment for improved efficiency at a later date."""

import csv
import os, sys

try:
    import numpy as np

    from PyQt5 import QtGui, QtCore, QtWidgets, uic
    from matplotlib.backends.backend_qt5agg import (FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
    from matplotlib.figure import Figure
except ModuleNotFoundError as e:
    print("The following module could not be found:", e)
    quit()

path = os.path.dirname(os.path.realpath(__file__))
Ui_MainWindow, QMainWindow = uic.loadUiType(f'{path}\\window.ui')

app = QtWidgets.QApplication(sys.argv)


class PlotGraph(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None, *args, **kwargs):
        super(PlotGraph, self).__init__(parent)
        self.setupUi(self)
        self.mplfigs.itemClicked.connect(self.change_graph)
        self.figure_dict = {}

        # Lists for data records
        self.time = []
        self.newtons = []
        self.trigger = 0.5

        if __name__ == '__main__':
            # Loop over all result records generated
            file_in_dir = [name for name in os.listdir('../results')]
            for i in range(0, len(file_in_dir)):
                name = file_in_dir[i][:-4]

                self.figure_dict[name] = file_in_dir[i]
                self.mplfigs.addItem(name)


    def plot(self, datafile):
        """Local function called internally. Plot the selected graph chosen from the records dictionary (right-panel)."""

        self.time.clear(); self.newtons.clear()
        with open(f"../results/{datafile}" if __name__ == '__main__' else f"./results/{datafile}", newline='') as data_file:
            reader = csv.DictReader(data_file)
            for row in reader:
                if not row['average'] == '':
                    self.average = float(row['average'])
                
                if not row['peak'] == '':
                    self.peak = float(row['peak'])

                if not row['time'] == '' or not row['newtons'] == '':
                    self.time.append(row['time'])
                    self.newtons.append(row['newtons'])


        self.time = [float(x) for x in self.time]; self.newtons = [float(x) for x in self.newtons]
        self.bounds = [n for n in self.newtons if n > self.trigger * 0.9]
        
        self.refined_average = 0
        for j in self.bounds:
            self.refined_average += j
        
        self.refined_average = round(self.refined_average / len(self.bounds), 2)

        self.figure = Figure()
        self.ax = self.figure.add_subplot(111)
        self.ax.set_xlabel("Time (ms)"); self.ax.set_ylabel("Newtons (N)"); self.ax.set_title(datafile)
        
        self.ax.plot(self.time, self.newtons)
        self.ax.plot(self.time[self.newtons.index(self.peak)], self.peak, '.', label="Peak | " + str(self.peak))
        self.ax.plot([min(self.time), max(self.time)], [self.average]*2, '--', label="Average | " + str(round(self.average, 2)))
        self.ax.plot([min(self.time), max(self.time)], [self.refined_average]*2, '--', label="Average ±10% | " + str(self.refined_average))

        handles, labels = self.ax.get_legend_handles_labels()
        self.ax.legend(handles, labels)

        if not __name__ == '__main__':
            self.mplfigs.addItem(datafile[:-4])

            self.add_graph(self.figure)


    def add_graph(self, figure):
        """Local function called internally. Draw new canvas and create new navigation toolbar."""

        self.canvas = FigureCanvas(figure)
        self.mplvl.addWidget(self.canvas)
        self.canvas.draw()

        # Toolbar
        self.toolbar = NavigationToolbar(self.canvas, self, coordinates=True)
        self.addToolBar(self.toolbar)


    def change_graph(self, item):
        """Local function called internally. Load the chosen graph from the records dictionary.\n
        Function will call rm_mpl() and then plot() passing the selected record."""

        text = item.text()
        try:
            self.rm_mpl()
        except:
            pass
       
        if __name__ == '__main__':
            self.plot(self.figure_dict[text])
            self.add_graph(self.figure)


    def rm_mpl(self):
        """Local function called internally. Remove the canvas and navigation toolbar to be recreated."""

        self.mplvl.removeWidget(self.canvas)
        self.canvas.close()
        self.mplvl.removeWidget(self.toolbar)
        self.toolbar.close()


if __name__ == '__main__':
    main = PlotGraph()
    main.show()

    sys.exit(app.exec())