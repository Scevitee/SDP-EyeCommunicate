import sys
from PyQt5.QtWidgets import QApplication
from overlay import Overlay


def ui_launch():
    app = QApplication(sys.argv)

    overlay = Overlay()
    overlay.show()

    overlay.destroyed.connect(app.quit)  # Ensures the program exits when the overlay is closed

    sys.exit(app.exec_())


if __name__ == '__main__':
    ui_launch()
