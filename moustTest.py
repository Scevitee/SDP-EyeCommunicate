import sys
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QPainter, QCursor, QMouseEvent
import pyautogui


class MouseControlApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mouse Control Application")
        self.resize(400, 300)
        self.setMouseTracking(True)  # Enable tracking mouse movement without clicking
        self.setCursor(QCursor(Qt.CrossCursor))  # Set custom cursor (cross)
        self.setFocusPolicy(Qt.StrongFocus)  # Ensure widget can receive keyboard events

    def mousePressEvent(self, event):
        """Detect mouse clicks and simulate actual clicks."""
        if event.button() == Qt.LeftButton:
            # Simulate a left-click at the current custom mouse position
            print(f"Simulating left-click at {self.custom_mouse_position}")
            pyautogui.click(self.custom_mouse_position.x(), self.custom_mouse_position.y())

        elif event.button() == Qt.RightButton:
            # Simulate a right-click at the current custom mouse position
            print(f"Simulating right-click at {self.custom_mouse_position}")
            pyautogui.rightClick(self.custom_mouse_position.x(), self.custom_mouse_position.y())

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            print(f"Left button released at {event.pos()}")

    def mouseMoveEvent(self, event: QMouseEvent):
        print(f"Mouse moved to {event.pos()}")

        

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            print("Escape pressed. Exiting.")
            self.close()
        else:
            # Get the current cursor position
            pos = QCursor.pos()
            # Determine the increment
            step = 10  # Pixels to move per key press
            if event.key() == Qt.Key_Left:
                pos.setX(pos.x() - step)
            elif event.key() == Qt.Key_Right:
                pos.setX(pos.x() + step)
            elif event.key() == Qt.Key_Up:
                pos.setY(pos.y() - step)
            elif event.key() == Qt.Key_Down:
                pos.setY(pos.y() + step)
            # Move the cursor to the new position
            QCursor.setPos(pos)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawText(
            self.rect(),
            Qt.AlignCenter,
            "Use arrow keys to move the mouse.\nPress ESC to exit.",
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MouseControlApp()
    window.show()
    sys.exit(app.exec())
