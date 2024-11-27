import sys
from PyQt5.QtCore import Qt, QPoint, QSize, QEvent, QTimer, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QMessageBox,
    QApplication, QStackedWidget, QSizePolicy, QSpacerItem, QStyleFactory, QLineEdit
)
from PyQt5.QtGui import QPainter, QColor, QIcon, QKeyEvent

from .art_program.art_canvas import ArtWidget
from .tts.virtual_keyboard import AlphaNeumericVirtualKeyboard as VKeyboard




class Overlay(QWidget):
    # Define signals
    notification_signal = pyqtSignal(str)
    change_page_signal = pyqtSignal(str)
    zoom_in_signal = pyqtSignal()
    zoom_out_signal = pyqtSignal()
    toggle_pin_signal = pyqtSignal()

    def __init__(self):
        super().__init__()

        # Define initial size dimensions
        self.default_size = (1000, 1000)
        self.is_pinned = False  # Start in expanded mode

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
        self.button_layout.addSpacerItem(QSpacerItem(10, 0, QSizePolicy.Expanding))

        # Spacer to center the buttons (removed to place notification bubble)
        # self.button_layout.addSpacerItem(QSpacerItem(10, 0, QSizePolicy.Expanding))

        # Add a notification label (notification bubble)
        self.notification_label = QLabel(self)
        self.notification_label.setStyleSheet("""
            QLabel {
                background-color: transparent;
                color: red;
                font-size: 16px;
                padding: 4px;
                border-radius: 5px;
            }
        """)
        self.notification_label.setFixedHeight(50)
        self.notification_label.setAlignment(Qt.AlignCenter)
        self.notification_label.setFixedWidth(200)  # Adjust as needed

        # Add the notification label to the button layout
        self.button_layout.addWidget(self.notification_label)

        # Spacer between notification and buttons
        self.button_layout.addSpacerItem(QSpacerItem(10, 0, QSizePolicy.Expanding))

        # Add a pin button
        self.toggle_button = QPushButton(self)
        pin_icon = QIcon("assets/pin_icon.png")
        self.setup_button(self.toggle_button, pin_icon, self.toggle_pin)

        # Add a close/power button
        self.close_button = QPushButton(self)
        power_icon = QIcon("assets/power_button.png")
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
        keyboard_icon = QIcon("assets/tts_icon.png")
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

        # Add the buttons to the layout
        self.button_layout.addWidget(self.toggle_button)
        self.button_layout.addWidget(self.close_button)
        self.button_layout.addWidget(self.settings_button)
        self.button_layout.addWidget(self.drawing_button)
        self.button_layout.addWidget(self.keyboard_button)

        # Spacer to center the buttons
        self.button_layout.addSpacerItem(QSpacerItem(10, 0, QSizePolicy.Expanding))

        # Add the horizontal button layout to the bottom of the main layout
        self.layout.addLayout(self.button_layout)

        # Create the eyeball button (icon) for minimized state
        self.eyeball_button = DraggableButton(self)
        eyeball_icon = QIcon("assets/eyecomm.png")
        self.eyeball_button.setIcon(eyeball_icon)
        self.eyeball_button.setIconSize(QSize(75, 75))  # Adjust size as needed
        self.eyeball_button.setFixedSize(85, 85)        # Adjust size as needed
        self.eyeball_button.clicked.connect(self.toggle_pin)
        self.eyeball_button.setStyleSheet("""
            QPushButton {
                background-color: #4c566a;
                border: none;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #596787;
            }
        """)        
        self.eyeball_button.hide()  # Initially hidden
        self.layout.addWidget(self.eyeball_button, alignment=Qt.AlignCenter)

        self.is_open = True
        
        # Initialize zoom variables
        self.zoom_scale = 1.0
        self.zoom_step = 0.1
        self.max_zoom = 3.0
        self.min_zoom = 0.2
        
        # Set the default widget to display
        self.stacked_widget.setCurrentWidget(self.default_label)

        # Apply styling
        self.apply_styles()

        # Connect signals to methods
        self.notification_signal.connect(self.display_notification)
        self.change_page_signal.connect(self.change_page_directional)
        self.zoom_in_signal.connect(self.zoom_in)
        self.zoom_out_signal.connect(self.zoom_out)
        self.toggle_pin_signal.connect(self.toggle_pin)

        self.dragging_window = False
        self.drag_start_position_window = QPoint()

    def setup_button(self, button, icon, callback):
        button.setIcon(icon)
        button.setIconSize(QSize(40, 40))
        button.setFixedSize(50, 50)
        button.clicked.connect(callback)
        button.setStyleSheet("""
            QPushButton {
                background-color: #596787;
                border: none;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #4c566a;
            }
        """)
        # Add the button to the layout (if not already added)
        if button not in self.button_layout.children():
            self.button_layout.addWidget(button)

    def display_notification(self, message):
        # Update the notification label with the message
        self.notification_label.setText(message)

        # Optionally, set a timer to clear the message after some time
        QTimer.singleShot(3000, self.clear_notification)

    def clear_notification(self):
        self.notification_label.setText('')

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
            # Expand the window back to default size
            self.setFixedSize(*self.default_size)
            self.is_pinned = False

            # Show main UI elements
            self.stacked_widget.show()
            for i in range(self.button_layout.count()):
                widget = self.button_layout.itemAt(i).widget()
                if widget:
                    widget.show()

            # Hide the eyeball button
            self.eyeball_button.hide()
            # Adjust margins
            self.layout.setContentsMargins(10, 10, 10, 10)
        else:
            # Collapse the window to the size of the eyeball icon
            sz = self.eyeball_button.size()
            self.setFixedSize(sz.width() * 1.2, sz.height() * 1.2)
            self.is_pinned = True

            # Hide main UI elements
            self.stacked_widget.hide()
            for i in range(self.button_layout.count()):
                widget = self.button_layout.itemAt(i).widget()
                if widget:
                    widget.hide()

            # Show the eyeball button
            self.eyeball_button.show()
            # Adjust margins
            self.layout.setContentsMargins(0, 0, 0, 0)
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

    def adjust_font_sizes(self):
        if not self.is_pinned:
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

    def apply_zoom(self):
        self.setFixedSize(
            int(self.default_size[0] * self.zoom_scale),
            int(self.default_size[1] * self.zoom_scale)
        )
        self.update()
        
    def zoom_in(self):
        if self.zoom_scale < self.max_zoom:
            self.zoom_scale += self.zoom_step
            self.update()        
            self.apply_zoom()
                        
    def zoom_out(self):
        if self.zoom_scale > self.min_zoom:
            self.zoom_scale -= self.zoom_step
            self.update()        
            self.apply_zoom()

        
    def update_button_styles(self):
        # List of buttons that correspond to widgets
        buttons = [self.settings_button, self.drawing_button, self.keyboard_button]

        # Reset styles for all buttons
        for button in buttons:
            button.setStyleSheet("""
                QPushButton {
                    background-color: #596787;
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
            
    # FOR TESTING METHODS BEFORE INTEGRATING WITH FACIAL GESTURES
    def keyPressEvent(self, event):
        """
        Overrides the keyPressEvent to handle custom key bindings.
        """
        if event.key() == Qt.Key_I:  # Zoom in
            self.zoom_in()
            print("Zoom in")
            print(self.zoom_scale)
        elif event.key() == Qt.Key_U:  # Zoom out
            self.zoom_out()
            print("Zoom out")
            print(self.zoom_scale)
            
        else:
            super().keyPressEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging_window = True
            self.drag_start_position_window = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.dragging_window and event.buttons() & Qt.LeftButton:
            self.move(event.globalPos() - self.drag_start_position_window)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.dragging_window:
            self.dragging_window = False
            event.accept()
        else:
            super().mouseReleaseEvent(event)


class KeyboardWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Main layout for the keyboard widget
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(10, 10, 10, 10)

        # Create a QLineEdit for text input
        self.text_entry = QLineEdit(self)
        self.text_entry.setPlaceholderText("Click to type...")
        self.text_entry.setStyleSheet("""
            QLineEdit {
                font-size: 18px;
                padding: 5px;
                border: 1px solid #4c566a;
                border-radius: 5px;
                color: #ECEFF4;
            }
        """)
        self.text_entry.setFixedHeight(40)
        layout.addWidget(self.text_entry)

        # Add the virtual keyboard in a horizontally centered container
        keyboard_container = QWidget(self)
        keyboard_layout = QHBoxLayout(keyboard_container)
        keyboard_layout.setContentsMargins(0, 0, 0, 0)
        keyboard_layout.setAlignment(Qt.AlignHCenter)

        # Embed the virtual keyboard
        self.virtual_keyboard = VKeyboard(self.text_entry)
        self.virtual_keyboard.setParent(keyboard_container)
        self.virtual_keyboard.setFixedSize(800, 315)  # Adjust to ensure it fits correctly
        self.virtual_keyboard.hide()
        keyboard_layout.addWidget(self.virtual_keyboard)

        layout.addWidget(keyboard_container)
        self.setLayout(layout)

        # Connect the QLineEdit mouse press event to show the keyboard
        self.text_entry.mousePressEvent = self.show_virtual_keyboard


    def show_virtual_keyboard(self, event):
        """Show the virtual keyboard directly below the text entry box."""
        if not self.virtual_keyboard.isVisible():
            # Get the text entry box's position relative to the parent
            text_entry_pos = self.text_entry.mapToParent(QPoint(0, 0))

            # Calculate the position for the keyboard relative to the container
            keyboard_x = max(0, text_entry_pos.x() + self.text_entry.width() // 2 - self.virtual_keyboard.width() // 2)
            keyboard_y = text_entry_pos.y() + self.text_entry.height() + 10

            # Display the keyboard at the calculated position
            self.virtual_keyboard.display(source=self.text_entry, x_pos=keyboard_x, y_pos=keyboard_y)

            # Show the keyboard
            self.virtual_keyboard.show()
        else:
            self.virtual_keyboard.hide()





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

class DraggableButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.dragging = False
        self.drag_start_position = QPoint()
        self.parent_widget = parent

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.drag_start_position = event.globalPos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            distance = (event.globalPos() - self.drag_start_position).manhattanLength()
            if distance > QApplication.startDragDistance():
                self.dragging = True
            if self.dragging:
                delta = event.globalPos() - self.drag_start_position
                self.parent_widget.move(self.parent_widget.pos() + delta)
                self.drag_start_position = event.globalPos()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.dragging:
            self.dragging = False
        else:
            super().mouseReleaseEvent(event)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Apply a built-in style
    app.setStyle(QStyleFactory.create('Fusion'))

    # Create and display the overlay
    overlay = Overlay()
    overlay.show()
    sys.exit(app.exec_())