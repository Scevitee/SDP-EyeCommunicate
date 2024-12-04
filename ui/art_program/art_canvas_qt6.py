
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget,
    QHBoxLayout, QLabel, QFileDialog, QLineEdit
)
from PyQt6.QtGui import QPainter, QImage, QPen, QColor, QBrush
from PyQt6.QtCore import Qt, QPoint, QThread, pyqtSignal, QEvent
import subprocess

class GenerateImageThread(QThread):
    finished = pyqtSignal(str)

    def __init__(self, temp_path, output_path, prompt):
        super().__init__()
        self.temp_path = temp_path
        self.output_path = output_path
        self.prompt = prompt

    def run(self):
        subprocess.run([
            "python3", "generate_image.py",
            self.temp_path, self.output_path, self.prompt
        ])
        self.finished.emit(self.output_path)


class PenIndicator(QWidget):
    def __init__(self, max_thickness, parent=None):
        super().__init__(parent)
        self.pen_color = QColor(Qt.GlobalColor.black)
        self.pen_thickness = 1
        self.max_thickness = max_thickness
        self.fixed_size = 50  # Fixed size for the grey circle
        self.setFixedSize(self.fixed_size, self.fixed_size)

    def set_pen_color(self, color):
        self.pen_color = color
        self.update()

    def set_pen_thickness(self, thickness):
        self.pen_thickness = thickness
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw fixed grey circle
        grey_color = QColor(Qt.GlobalColor.lightGray)
        painter.setBrush(QBrush(grey_color))
        painter.setPen(Qt.PenStyle.NoPen)
        radius = self.fixed_size / 2
        center = QPoint(self.width() // 2, self.height() // 2)
        painter.drawEllipse(center, int(radius), int(radius))

        # Calculate size of inner colored circle based on pen thickness
        max_thickness = self.max_thickness
        thickness_ratio = self.pen_thickness / max_thickness
        inner_radius = radius * thickness_ratio

        # Draw inner colored circle
        painter.setBrush(QBrush(self.pen_color))
        painter.drawEllipse(center, int(inner_radius), int(inner_radius))


class DrawingCanvas(QWidget):
    def __init__(self, color_indicator):
        super().__init__()
        self.image = QImage(400, 400, QImage.Format.Format_RGB32)
        self.image.fill(Qt.GlobalColor.white)
        self.undo_stack = []
        self.redo_stack = []
        self.drawing = False
        self.last_point = QPoint()

        # Define colors, thicknesses, and set initial color and thickness
        self.colors = [
            QColor(Qt.GlobalColor.black), QColor(Qt.GlobalColor.white), QColor(Qt.GlobalColor.red),
            QColor(Qt.GlobalColor.green), QColor(Qt.GlobalColor.blue),
            QColor(Qt.GlobalColor.yellow), QColor(Qt.GlobalColor.magenta), QColor(Qt.GlobalColor.cyan)
        ]
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
        if event.button() == Qt.MouseButton.LeftButton:
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                # Perform flood fill
                self.save_to_undo()
                point = self.map_to_image(event.position().toPoint())
                self.flood_fill(point.x(), point.y(), self.pen_color)
                self.update()
            else:
                # Start drawing
                self.save_to_undo()
                self.drawing = True
                self.last_point = self.map_to_image(event.position().toPoint())

    def mouseMoveEvent(self, event):
        if (event.buttons() & Qt.MouseButton.LeftButton) and self.drawing:
            painter = QPainter(self.image)
            pen = QPen(
                self.pen_color, self.pen_thickness,
                Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin
            )
            painter.setPen(pen)
            current_point = self.map_to_image(event.position().toPoint())
            painter.drawLine(self.last_point, current_point)
            self.last_point = current_point
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
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
        self.image.fill(Qt.GlobalColor.white)
        self.update()  # Refresh the display

    def save_canvas(self, file_path="temp_sketch.png"):
        # Save the canvas to a specified file path
        self.image.save(file_path)

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
        self.current_thickness_index = (
            self.current_thickness_index + 1
        ) % len(self.thicknesses)
        self.change_thickness()

    def update_color_indicator(self):
        self.color_indicator.set_pen_color(self.pen_color)
        self.color_indicator.set_pen_thickness(self.pen_thickness)

    def load_image(self, file_path):
        # Load an image from file and set it as the current canvas image
        self.image.load(file_path)
        self.update()  # Refresh the display

    def flood_fill(self, x, y, new_color):
        width = self.image.width()
        height = self.image.height()
        target_color = self.image.pixel(x, y)
        new_color_rgb = new_color.rgb()

        if target_color == new_color_rgb:
            return

        pixel_stack = [(x, y)]

        while pixel_stack:
            x, y = pixel_stack.pop()

            if x < 0 or x >= width or y < 0 or y >= height:
                continue

            current_color = self.image.pixel(x, y)
            if current_color != target_color:
                continue

            self.image.setPixel(x, y, new_color_rgb)

            pixel_stack.append((x + 1, y))
            pixel_stack.append((x - 1, y))
            pixel_stack.append((x, y + 1))
            pixel_stack.append((x, y - 1))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Create pen indicator widget
        max_thickness = max([1, 2, 3, 4, 5])  # Should match the max pen thickness
        self.color_indicator = PenIndicator(max_thickness)

        # Initialize canvas with color indicator
        self.canvas = DrawingCanvas(self.color_indicator)

        # Create undo/redo/clear/save/load/generate buttons
        undo_button = QPushButton("Undo")
        undo_button.clicked.connect(self.canvas.undo)
        
        redo_button = QPushButton("Redo")
        redo_button.clicked.connect(self.canvas.redo)

        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(self.canvas.clear_canvas)

        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_sketch)

        load_button = QPushButton("Load")
        load_button.clicked.connect(self.load_image)

        self.generate_button = QPushButton("Generate")
        self.generate_button.clicked.connect(self.generate_image)

        # Create the loading message label
        self.loading_label = QLabel("Please wait while we generate your image")
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_label.hide()  # Initially hidden

        # Create prompt input field and submit button
        self.prompt_input = QLineEdit()
        self.prompt_input.setPlaceholderText("Enter an image generation prompt")
        self.prompt_submit_button = QPushButton("Generate Image")
        self.prompt_submit_button.clicked.connect(self.start_image_generation)

        # Create a widget to hold the prompt input and button
        self.prompt_widget = QWidget()
        prompt_layout = QVBoxLayout(self.prompt_widget)
        prompt_layout.addWidget(self.prompt_input)
        prompt_layout.addWidget(self.prompt_submit_button)
        self.prompt_widget.hide()  # Initially hidden

        # Button and color indicator layout
        button_layout = QHBoxLayout()
        button_layout.addWidget(undo_button)
        button_layout.addWidget(redo_button)
        button_layout.addWidget(clear_button)
        button_layout.addWidget(save_button)
        button_layout.addWidget(load_button)
        button_layout.addWidget(self.generate_button)
        button_layout.addWidget(self.color_indicator)

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.canvas)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.prompt_widget)    # Add prompt widget to layout
        main_layout.addWidget(self.loading_label)    # Add loading label to layout

        # Set main layout
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # Set initial window size
        self.resize(750, 750)

        # Install event filter to capture key events
        self.installEventFilter(self)

    def save_sketch(self):
        # Since we're not specifying any special options, we can omit the 'options' parameter
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Image", "",
            "PNG Files (*.png);;JPEG Files (*.jpg);;All Files (*)"
        )
        if file_path:
            self.canvas.save_canvas(file_path)

    def load_image(self):
        # Similarly, omit the 'options' parameter
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load Image", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif);;All Files (*)"
        )
        if file_path:
            self.canvas.load_image(file_path)

    def generate_image(self):
        # Toggle the visibility of the prompt widget
        if self.prompt_widget.isVisible():
            self.prompt_widget.hide()
        else:
            self.prompt_widget.show()
            self.loading_label.hide()  # Hide the loading label if it's visible

    def start_image_generation(self):
        # Hide prompt widget
        self.prompt_widget.hide()
        # Show loading message
        self.loading_label.show()

        # Save the current canvas as a temporary image
        temp_path = "images/temp_sketch.png"
        output_path = "images/generated_image.png"
        self.canvas.save_canvas(temp_path)

        # Get the prompt from the input field
        prompt = self.prompt_input.text()
        if not prompt:
            prompt = "A man holding a spoon"

        # Clear the prompt input for next time
        self.prompt_input.clear()

        # Create and start the generation thread
        self.thread = GenerateImageThread(temp_path, output_path, prompt)
        self.thread.finished.connect(self.load_generated_image)
        self.thread.start()

    def load_generated_image(self, output_path):
        # Hide the loading message
        self.loading_label.hide()

        # Load the generated image into the canvas
        self.canvas.load_image(output_path)

    def eventFilter(self, source, event):
        if event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_P:
                self.canvas.next_color()
                return True
            elif event.key() == Qt.Key.Key_O:
                self.canvas.next_thickness()
                return True
        return super().eventFilter(source, event)


app = QApplication([])
window = MainWindow()
window.show()
app.exec()
