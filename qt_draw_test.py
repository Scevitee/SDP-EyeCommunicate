from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QHBoxLayout, QLabel
from PyQt5.QtGui import QPainter, QImage, QPen, QColor
from PyQt5.QtCore import Qt, QPoint

class DrawingCanvas(QWidget):
    def __init__(self, color_indicator):
        super().__init__()
        self.image = QImage(400, 400, QImage.Format_RGB32)
        self.image.fill(Qt.white)
        self.undo_stack = []
        self.redo_stack = []
        self.drawing = False
        self.last_point = QPoint()

        # Define colors, thicknesses, and set initial color and thickness
        self.colors = [Qt.black, Qt.red, Qt.green, Qt.blue]
        self.thicknesses = [1, 2, 3, 4, 5]
        self.current_color_index = 0
        self.current_thickness_index = 0
        self.pen_color = self.colors[self.current_color_index]
        self.pen_thickness = self.thicknesses[self.current_thickness_index]
        self.color_indicator = color_indicator
        self.update_color_indicator()  # Set initial color and thickness for the indicator

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawImage(self.rect(), self.image, self.image.rect())

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.save_to_undo()
            self.drawing = True
            self.last_point = self.map_to_image(event.pos())

    def mouseMoveEvent(self, event):
        if (event.buttons() & Qt.LeftButton) and self.drawing:
            painter = QPainter(self.image)
            pen = QPen(self.pen_color, self.pen_thickness, Qt.SolidLine)  # Use selected color and thickness
            painter.setPen(pen)
            current_point = self.map_to_image(event.pos())
            painter.drawLine(self.last_point, current_point)
            self.last_point = current_point
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = False

    def map_to_image(self, point):
        x_ratio = self.image.width() / self.width()
        y_ratio = self.image.height() / self.height()
        return QPoint(int(point.x() * x_ratio), int(point.y() * y_ratio))

    def save_to_undo(self):
        self.undo_stack.append(self.image.copy())
        self.redo_stack.clear()

    def undo(self):
        if self.undo_stack:
            self.redo_stack.append(self.image.copy())
            self.image = self.undo_stack.pop()
            self.update()

    def redo(self):
        if self.redo_stack:
            self.undo_stack.append(self.image.copy())
            self.image = self.redo_stack.pop()
            self.update()

    def clear_canvas(self):
        # Fill the canvas with white (or any background color)
        self.image.fill(Qt.white)
        self.update()  # Refresh the display

    def change_color(self):
        self.pen_color = self.colors[self.current_color_index]
        self.update_color_indicator()  # Update color and thickness indicator

    def next_color(self):
        self.current_color_index = (self.current_color_index + 1) % len(self.colors)
        self.change_color()

    def change_thickness(self):
        self.pen_thickness = self.thicknesses[self.current_thickness_index]
        self.update_color_indicator()  # Update color and thickness indicator

    def next_thickness(self):
        self.current_thickness_index = (self.current_thickness_index + 1) % len(self.thicknesses)
        self.change_thickness()

    def update_color_indicator(self):
        color = QColor(self.pen_color)
        size = self.pen_thickness * 7  # Scale size for better visibility
        self.color_indicator.setStyleSheet(f"background-color: {color.name()}; border-radius: {size // 2}px;")
        self.color_indicator.setFixedSize(size, size)  # Update size to match thickness

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Create color indicator dot
        self.color_indicator = QLabel(self)

        # Initialize canvas with color indicator
        self.canvas = DrawingCanvas(self.color_indicator)

        # Create undo/redo/clear buttons
        undo_button = QPushButton("Undo")
        undo_button.clicked.connect(self.canvas.undo)
        
        redo_button = QPushButton("Redo")
        redo_button.clicked.connect(self.canvas.redo)

        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(self.canvas.clear_canvas)

        # Button and color indicator layout
        button_layout = QHBoxLayout()
        button_layout.addWidget(undo_button)
        button_layout.addWidget(redo_button)
        button_layout.addWidget(clear_button)
        button_layout.addWidget(self.color_indicator)

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.canvas)
        main_layout.addLayout(button_layout)

        # Set main layout
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # Set initial window size
        self.resize(600, 600)

        # Install event filter to capture key events
        self.installEventFilter(self)

    def eventFilter(self, source, event):
        if event.type() == event.KeyPress:
            if event.key() == Qt.Key_P:
                self.canvas.next_color()  # Cycle to the next color
                return True
            elif event.key() == Qt.Key_O:
                self.canvas.next_thickness()  # Cycle to the next thickness
                return True
        return super().eventFilter(source, event)

app = QApplication([])
window = MainWindow()
window.show()
app.exec_()
