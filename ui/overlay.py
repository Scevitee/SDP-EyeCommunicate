import sys
from PyQt5.QtCore import Qt, QPoint, QSize, pyqtSignal, QEvent
from PyQt5.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QMessageBox, QDialog, QSizePolicy
)
from PyQt5.QtGui import QPainter, QColor, QImage, QPen, QIcon, QKeyEvent


class Overlay(QWidget):
    def __init__(self):
        super().__init__()

        # Define initial and compact size dimensions
        self.default_size = (500, 500)
        self.button_size = 40
        self.compact_height = self.button_size + 20
        self.compact_width = (self.button_size + 10) * 5  # Adjusted for additional button

        # Start in expanded mode
        self.is_pinned = False

        # Set up the window properties
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(100, 100, *self.default_size)
        self.setMinimumSize(50, 50)

        # Set up main vertical layout
        self.layout = QVBoxLayout(self)

        # Set up label
        self.label = QLabel('This is the alpha version of the UI overlay', self)
        self.label.setStyleSheet("color: white; font-size: 20px;")
        self.layout.addWidget(self.label)

        # Set up a horizontal layout for the buttons
        self.button_layout = QHBoxLayout()

        # Add a pin button
        self.toggle_button = QPushButton(self)
        pin_icon = QIcon("assets/pin_icon.png")  # Replace with your actual icon path
        self.toggle_button.setIcon(pin_icon)
        self.toggle_button.setIconSize(QSize(self.button_size, self.button_size))
        self.toggle_button.setFixedSize(self.button_size, self.button_size)
        self.toggle_button.clicked.connect(self.toggle_pin)
        self.button_layout.addWidget(self.toggle_button)

        # Add a close/power button
        self.close_button = QPushButton(self)
        power_icon = QIcon("assets/power_icon.png")  # Replace with your actual icon path
        self.close_button.setIcon(power_icon)
        self.close_button.setIconSize(QSize(self.button_size, self.button_size))
        self.close_button.setFixedSize(self.button_size, self.button_size)
        self.close_button.clicked.connect(self.show_confirmation_dialog)
        self.button_layout.addWidget(self.close_button)

        # Add a settings button
        self.settings_button = QPushButton(self)
        settings_icon = QIcon("assets/settings_icon.png")  # Replace with your actual icon path
        self.settings_button.setIcon(settings_icon)
        self.settings_button.setIconSize(QSize(self.button_size, self.button_size))
        self.settings_button.setFixedSize(self.button_size, self.button_size)
        self.settings_button.clicked.connect(self.open_settings)
        self.button_layout.addWidget(self.settings_button)

        # Add a drawing button
        self.drawing_button = QPushButton(self)
        draw_icon = QIcon("assets/draw_icon.png")  # Replace with your actual icon path
        self.drawing_button.setIcon(draw_icon)
        self.drawing_button.setIconSize(QSize(self.button_size, self.button_size))
        self.drawing_button.setFixedSize(self.button_size, self.button_size)
        self.drawing_button.clicked.connect(self.open_drawing_canvas)
        self.button_layout.addWidget(self.drawing_button)

        # Add a keyboard button
        self.keyboard_button = QPushButton(self)
        keyboard_icon = QIcon("assets/keyboard_icon.png")  # Replace with your actual icon path
        self.keyboard_button.setIcon(keyboard_icon)
        self.keyboard_button.setIconSize(QSize(self.button_size, self.button_size))
        self.keyboard_button.setFixedSize(self.button_size, self.button_size)
        self.keyboard_button.clicked.connect(self.open_keyboard)
        self.button_layout.addWidget(self.keyboard_button)

        # Add the horizontal button layout
        self.layout.addLayout(self.button_layout)
        self.setLayout(self.layout)

        # Variables for dragging
        self.is_dragging = False
        self.drag_start_position = QPoint(0, 0)

    def paintEvent(self, event):
        # Semi-transparent background
        painter = QPainter(self)
        painter.setBrush(QColor(0, 0, 0, 160))
        painter.drawRect(self.rect())

    def toggle_pin(self):
        if self.is_pinned:
            self.resize(*self.default_size)
            self.label.show()
            self.is_pinned = False
        else:
            self.resize(self.compact_width, self.compact_height)
            self.label.hide()
            self.is_pinned = True

    def show_confirmation_dialog(self):
        confirmation_dialog = QMessageBox(self)
        confirmation_dialog.setWindowTitle("Confirm Exit")
        confirmation_dialog.setText("Are you sure you want to close the application?")
        confirmation_dialog.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        result = confirmation_dialog.exec_()
        if result == QMessageBox.Yes:
            sys.exit(0)

    def open_settings(self):
        self.settings_window = SettingsWindow(self)
        self.settings_window.show()

    def open_drawing_canvas(self):
        self.drawing_window = DrawingWindow(self)
        self.drawing_window.show()

    def open_keyboard(self):
        """Open the virtual keyboard window."""
        self.keyboard_window = KeyboardWindow(self)
        self.keyboard_window.show()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_dragging = True
            self.drag_start_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.is_dragging:
            self.move(event.globalPos() - self.drag_start_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_dragging = False
            event.accept()

from PyQt5.QtWidgets import QApplication

class KeyboardWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Virtual Keyboard")
        self.setGeometry(300, 300, 800, 300)

        # Main layout for the keyboard
        layout = QVBoxLayout(self)

        # Rows of keys
        key_rows = [
            ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P'],
            ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L'],
            ['Z', 'X', 'C', 'V', 'B', 'N', 'M', 'Space']
        ]

        for row in key_rows:
            row_layout = QHBoxLayout()
            for key in row:
                button = QPushButton(key)
                button.setFixedSize(60, 60)
                button.clicked.connect(lambda _, k=key: self.key_pressed(k))
                row_layout.addWidget(button)
            layout.addLayout(row_layout)

        self.setLayout(layout)

    def key_pressed(self, key):
        """Simulate a key press event."""
        if key == 'Space':
            key = ' '  # Replace "Space" with an actual space

        focused_widget = QApplication.focusWidget()
        if focused_widget:
            # Create and post a key press event
            key_event = QKeyEvent(QEvent.KeyPress, 0, Qt.NoModifier, key)
            QApplication.postEvent(focused_widget, key_event)

            # Create and post a key release event
            release_event = QKeyEvent(QEvent.KeyRelease, 0, Qt.NoModifier, key)
            QApplication.postEvent(focused_widget, release_event)

        print(f"Simulated key press: {key}")  # Debugging



class DrawingWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Drawing Canvas")
        self.setGeometry(200, 200, 800, 600)  # Larger window size

        # Add the drawing canvas
        self.canvas = DrawingCanvas(self)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # Make the canvas fill the space

        # Create undo, redo, and clear buttons
        self.undo_button = QPushButton(self)
        undo_icon = QIcon("undo_icon.png")  # Replace with your actual icon path
        self.undo_button.setIcon(undo_icon)
        self.undo_button.setText("Undo")
        self.undo_button.setIconSize(QSize(30, 30))
        self.undo_button.clicked.connect(self.canvas.undo)

        self.redo_button = QPushButton(self)
        redo_icon = QIcon("redo_icon.png")  # Replace with your actual icon path
        self.redo_button.setIcon(redo_icon)
        self.redo_button.setText("Redo")
        self.redo_button.setIconSize(QSize(30, 30))
        self.redo_button.clicked.connect(self.canvas.redo)

        self.clear_button = QPushButton(self)
        clear_icon = QIcon("clear_icon.png")  # Replace with your actual icon path
        self.clear_button.setIcon(clear_icon)
        self.clear_button.setText("Clear")
        self.clear_button.setIconSize(QSize(30, 30))
        self.clear_button.clicked.connect(self.canvas.clear_canvas)

        # Add visual feedback for current pen color and thickness
        self.pen_color_indicator = QLabel(self)
        self.pen_color_indicator.setStyleSheet(f"background-color: {self.canvas.pen_color.name()}; border-radius: 50%;")
        self.update_pen_indicator()  # Initialize indicator size and color

        # Connect updates to the pen indicator
        self.canvas.pen_properties_updated.connect(self.update_pen_indicator)

        # Layout for the bottom controls
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)  # Spacing between buttons

        # Add buttons to the bottom layout and ensure they fill available space
        self.add_expanding_button(self.undo_button, button_layout)
        self.add_expanding_button(self.redo_button, button_layout)
        self.add_expanding_button(self.clear_button, button_layout)
        self.add_expanding_widget(self.pen_color_indicator, button_layout)

        # Main layout with canvas and buttons
        layout = QVBoxLayout(self)
        layout.addWidget(self.canvas)  # Canvas at the top
        layout.addLayout(button_layout)  # Buttons at the bottom
        self.setLayout(layout)

    def add_expanding_button(self, button, layout):
        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(button)

    def add_expanding_widget(self, widget, layout):
        widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(widget, alignment=Qt.AlignCenter)

    def update_pen_indicator(self):
        # Update the size and color of the pen color indicator
        size = self.canvas.pen_thickness * 2
        self.pen_color_indicator.setFixedSize(size, size)
        self.pen_color_indicator.setStyleSheet(
            f"background-color: {self.canvas.pen_color.name()}; border-radius: {size // 2}px;"
        )

    def keyPressEvent(self, event):
        # Map 'O' to change thickness and 'P' to change color
        if event.key() == Qt.Key_O:
            self.canvas.next_thickness()
        elif event.key() == Qt.Key_P:
            self.canvas.next_color()
        else:
            super().keyPressEvent(event)


class DrawingCanvas(QWidget):
    pen_properties_updated = pyqtSignal()  # Signal to notify updates in pen properties

    def __init__(self, parent=None):
        super().__init__(parent)
        self.image = QImage(400, 400, QImage.Format_RGB32)
        self.image.fill(Qt.white)
        self.undo_stack = []
        self.redo_stack = []
        self.drawing = False
        self.last_point = QPoint()

        # Pen attributes
        self.colors = [Qt.black, Qt.red, Qt.green, Qt.blue]  # Predefined colors
        self.thicknesses = [3, 5, 7, 9, 11]  # Larger default thicknesses
        self.current_color_index = 0
        self.current_thickness_index = 1  # Start with the second smallest thickness (5)
        self.pen_color = QColor(self.colors[self.current_color_index])
        self.pen_thickness = self.thicknesses[self.current_thickness_index]

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawImage(self.rect(), self.image, self.image.rect())

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.save_to_undo()
            self.drawing = True
            self.last_point = self.map_to_canvas(event.pos())

    def mouseMoveEvent(self, event):
        if self.drawing and (event.buttons() & Qt.LeftButton):
            current_point = self.map_to_canvas(event.pos())
            painter = QPainter(self.image)
            pen = QPen(self.pen_color, self.pen_thickness, Qt.SolidLine)
            painter.setPen(pen)
            painter.drawLine(self.last_point, current_point)
            self.last_point = current_point
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = False

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
        self.image.fill(Qt.white)
        self.update()

    def map_to_canvas(self, point):
        x_ratio = self.image.width() / self.width()
        y_ratio = self.image.height() / self.height()
        return QPoint(int(point.x() * x_ratio), int(point.y() * y_ratio))

    def next_color(self):
        # Cycle through colors
        self.current_color_index = (self.current_color_index + 1) % len(self.colors)
        self.pen_color = QColor(self.colors[self.current_color_index])
        self.pen_properties_updated.emit()  # Notify listeners

    def next_thickness(self):
        # Cycle through thickness levels
        self.current_thickness_index = (self.current_thickness_index + 1) % len(self.thicknesses)
        self.pen_thickness = self.thicknesses[self.current_thickness_index]
        self.pen_properties_updated.emit()  # Notify listeners


class SettingsWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setFixedSize(300, 200)

        layout = QVBoxLayout(self)
        label = QLabel("Settings Configuration", self)
        label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(label)
        self.setLayout(layout)


