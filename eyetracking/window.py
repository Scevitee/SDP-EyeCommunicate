import sys
from pathlib import Path

from PySide6.Qtquick import QQuickView
from PySide6.QtCore import QStringListModel, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QmlElement

def window():
    app = QGuiApplication(sys.argv)
    win = QMainWindow()
    win.setGeometry(0, 0, width, height)
    win.setWindowTitle("Calibration")

    qml_file = Path(__file__).parent / "Screen01.ui.qml"

    win.show()
    sys.exit(app.exe_())

window()

