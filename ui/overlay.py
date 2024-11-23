# enhanced_ui.py
import sys
from PyQt5.QtCore import Qt, QPoint, QSize, pyqtSignal, QEvent
from PyQt5.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QMessageBox,
    QApplication, QStackedWidget, QSizePolicy, QSpacerItem, QStyleFactory
)
from PyQt5.QtGui import QPainter, QColor, QImage, QPen, QIcon, QKeyEvent, QFont

from .art_program.art_canvas import ArtWidget

class Overlay(QWidget):
    def __init__(self):
        super().__init__()

        # Define initial and compact size dimensions
        self.default_size = (1000, 1000)
        self.button_size = 50  # Increased button size for better visibility
        self.compact_height = self.button_size - 25
        self.compact_width = (self.button_size + 5) * 5  # Adjusted for spacing

        # Start in expanded mode
        self.is_pinned = False

        # Set up the window properties
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(100, 100, *self.default_size)
        self.setMinimumSize(300, 300)

        # Set up main vertical layout with margins
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(5)

        # Create a stacked widget to switch between different UI elements
        self.stacked_widget = QStackedWidget(self)
        self.layout.addWidget(self.stacked_widget)

        # Create instances of the different UI elements
        self.default_label = QLabel('Welcome to EyeCommunicate', self)
        self.default_label.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
        self.default_label.setAlignment(Qt.AlignCenter)
        self.stacked_widget.addWidget(self.default_label)

        self.settings_widget = SettingsWidget(self)
        self.stacked_widget.addWidget(self.settings_widget)

        self.drawing_widget = ArtWidget()
        self.stacked_widget.addWidget(self.drawing_widget)

        self.keyboard_widget = KeyboardWidget(self)
        self.stacked_widget.addWidget(self.keyboard_widget)

 
        # Add a horizontal layout for the buttons (tabs) at the bottom
        self.button_layout = QHBoxLayout()
        self.button_layout.setContentsMargins(0, 0, 0, 0)
        self.button_layout.setSpacing(10)

        # Spacer to center the buttons
        self.button_layout.addSpacerItem(QSpacerItem(10, 0, QSizePolicy.Expanding))

        # Add a pin button
        self.toggle_button = QPushButton(self)
        pin_icon = QIcon("assets/pin_icon.png")
        self.setup_button(self.toggle_button, pin_icon, self.toggle_pin)

        # Add a close/power button
        self.close_button = QPushButton(self)
        power_icon = QIcon("assets/power_icon.png")
        self.setup_button(self.close_button, power_icon, self.show_confirmation_dialog)

        # Add a settings button
        self.settings_button = QPushButton(self)
        settings_icon = QIcon("assets/settings_icon.png")
        self.setup_button(self.settings_button, settings_icon, self.show_settings)

        # Add a drawing button
        self.drawing_button = QPushButton(self)
        draw_icon = QIcon("assets/draw_icon.png")
        self.setup_button(self.drawing_button, draw_icon, self.show_drawing_canvas)

        # Add a keyboard button
        self.keyboard_button = QPushButton(self)
        keyboard_icon = QIcon("assets/keyboard_icon.png")
        self.setup_button(self.keyboard_button, keyboard_icon, self.show_keyboard)


        self.widget_button_mapping = {
            self.default_label: None,  # No button corresponds to the default label
            self.settings_widget: self.settings_button,
            self.drawing_widget: self.drawing_button,
            self.keyboard_widget: self.keyboard_button
        }
        # List of widgets to cycle through
        self.widget_list = [
            self.default_label,
            self.settings_widget,
            self.drawing_widget,
            self.keyboard_widget
        ]
        self.current_widget_index = 0  # Starting index

        # Spacer to center the buttons
        self.button_layout.addSpacerItem(QSpacerItem(10, 0, QSizePolicy.Expanding))

        # Add the horizontal button layout to the bottom of the main layout
        self.layout.addLayout(self.button_layout)

        # Variables for dragging
        self.is_dragging = False
        self.drag_start_position = QPoint(0, 0)
        
        self.is_open = True

        # Set the default widget to display
        self.stacked_widget.setCurrentWidget(self.default_label)

        # Apply styling
        self.apply_styles()

    def setup_button(self, button, icon, callback):
        button.setIcon(icon)
        button.setIconSize(QSize(self.button_size - 10, self.button_size - 10))
        button.setFixedSize(self.button_size, self.button_size)
        button.clicked.connect(callback)
        button.setStyleSheet("""
            QPushButton {
                background-color: #2e3440;
                border: none;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #4c566a;
            }
        """)
        self.button_layout.addWidget(button)

    def toggleMinimize(self):
        if self.is_open:
            self.showMinimized()
            print("Should be minimized")
        else:
            self.showNormal()
            print("Should be normal")
        self.is_open = not self.is_open

    def paintEvent(self, event):
        # Semi-transparent background with rounded corners
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()
        rect = rect.adjusted(1, 1, -1, -1)
        painter.setBrush(QColor(46, 52, 64, 220))  # Slightly transparent background
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(rect, 15, 15)

    def toggle_pin(self):
        if self.is_pinned:
            self.resize(*self.default_size)
            self.is_pinned = False
        else:
            # Ensure the buttons remain visible and appropriately sized
            self.resize(self.compact_width, self.compact_height + 50)
            self.is_pinned = True
        # Adjust font sizes when resizing
        self.adjust_font_sizes()

    def show_confirmation_dialog(self):
        confirmation_dialog = QMessageBox(self)
        confirmation_dialog.setWindowTitle("Confirm Exit")
        confirmation_dialog.setText("Are you sure you want to close the application?")
        confirmation_dialog.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        result = confirmation_dialog.exec_()
        if result == QMessageBox.Yes:
            sys.exit(0)

    def show_settings(self):
        self.stacked_widget.setCurrentWidget(self.settings_widget)
        self.update_button_styles()

    def show_drawing_canvas(self):
        self.stacked_widget.setCurrentWidget(self.drawing_widget)
        self.update_button_styles()

    def show_keyboard(self):
        self.stacked_widget.setCurrentWidget(self.keyboard_widget)
        self.update_button_styles()

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

    def adjust_font_sizes(self):
        # Adjust font sizes based on the current size of the window
        scale_factor = self.width() / self.default_size[0]
        font_size = max(12, int(24 * scale_factor))
        style = f"color: white; font-size: {font_size}px; font-weight: bold;"
        self.default_label.setStyleSheet(style)

    def apply_styles(self):
        # Apply overall style to the application
        style_sheet = """
            QWidget {
                background-color: transparent;
                color: #ECEFF4;
            }
            QLabel {
                color: #ECEFF4;
            }
        """
        self.setStyleSheet(style_sheet)

    def change_page_directional(self, direction):
        if direction.lower() == 'right':
            self.current_widget_index = (self.current_widget_index + 1) % len(self.widget_list)
        elif direction.lower() == 'left':
            self.current_widget_index = (self.current_widget_index - 1) % len(self.widget_list)
        else:
            return  # Invalid direction; do nothing

        # Set the current widget based on the updated index
        self.stacked_widget.setCurrentWidget(self.widget_list[self.current_widget_index])
        self.update_button_styles()
        
    def update_button_styles(self):
        # List of buttons that correspond to widgets
        buttons = [self.settings_button, self.drawing_button, self.keyboard_button]

        # Reset styles for all buttons
        for button in buttons:
            button.setStyleSheet("""
                QPushButton {
                    background-color: #2e3440;
                    border: none;
                    border-radius: 10px;
                }
                QPushButton:hover {
                    background-color: #4c566a;
                }
            """)

        # Highlight the active button
        current_widget = self.stacked_widget.currentWidget()
        active_button = self.widget_button_mapping.get(current_widget)

        if active_button:
            active_button.setStyleSheet("""
                QPushButton {
                    background-color: #81a1c1;
                    border: none;
                    border-radius: 10px;
                }
                QPushButton:hover {
                    background-color: #88c0d0;
                }
            """)


class KeyboardWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Main layout for the keyboard
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(10, 10, 10, 10)

        key_rows = [
            ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P'],
            ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L'],
            ['Z', 'X', 'C', 'V', 'B', 'N', 'M', 'Space']
        ]

        for row in key_rows:
            row_layout = QHBoxLayout()
            row_layout.setSpacing(5)
            for key in row:
                button = QPushButton(key)
                button.setFixedSize(60, 60)
                button.clicked.connect(lambda _, k=key: self.key_pressed(k))
                button.setStyleSheet("""
                    QPushButton {
                        background-color: #3b4252;
                        color: #ECEFF4;
                        border: none;
                        border-radius: 5px;
                        font-size: 18px;
                    }
                    QPushButton:hover {
                        background-color: #4c566a;
                    }
                """)
                row_layout.addWidget(button)
            layout.addLayout(row_layout)

        self.setLayout(layout)

    def key_pressed(self, key):
        if key == 'Space':
            key = ' '

        focused_widget = QApplication.focusWidget()
        if focused_widget:
            key_event = QKeyEvent(QEvent.KeyPress, 0, Qt.NoModifier, key)
            QApplication.postEvent(focused_widget, key_event)
            release_event = QKeyEvent(QEvent.KeyRelease, 0, Qt.NoModifier, key)
            QApplication.postEvent(focused_widget, release_event)

        print(f"Simulated key press: {key}")


class SettingsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        label = QLabel("Settings", self)
        label.setStyleSheet("font-size: 24px; font-weight: bold; color: #ECEFF4;")
        layout.addWidget(label)

        # Placeholder for settings options
        settings_label = QLabel("Settings options will go here.", self)
        settings_label.setStyleSheet("font-size: 16px; color: #ECEFF4;")
        layout.addWidget(settings_label)

        layout.addStretch()
        self.setLayout(layout)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Apply a built-in style
    app.setStyle(QStyleFactory.create('Fusion'))

    # Create and display the overlay
    overlay = Overlay()
    overlay.show()
    sys.exit(app.exec_())
