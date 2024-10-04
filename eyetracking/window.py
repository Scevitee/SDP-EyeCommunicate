from PyQt5 import QtWidgets
from PyQt5.Qlwidgets import QApplication, QMainWindow
import sys

def window():
    app = QApplication(sys.argv)
    win = QMainWindow()
    win.setGeometry(0, 0, width, height)
    win.setWindowTitle("Calibration")

    win.show()
    sys.exit(app.exe_())

window()
