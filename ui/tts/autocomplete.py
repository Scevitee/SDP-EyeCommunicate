import nltk
from nltk.corpus import brown
from collections import Counter
from PyQt5.QtWidgets import QApplication, QLineEdit, QVBoxLayout, QWidget, QPushButton, QLabel
from PyQt5.QtGui import QColor, QPainter, QFontMetrics
from PyQt5.QtCore import Qt

# Ensure required datasets are downloaded
# nltk.download('brown')

# Generate the 1500 most common words with initial frequencies
def get_common_words_with_frequencies():
    # Get all words from the Brown Corpus
    words = brown.words()

    # Count word frequencies
    word_frequencies = Counter(words)

    # Get the 1500 most common words
    common_words = word_frequencies.most_common(1500)

    # Return as a dictionary: {'word': frequency}
    return {word.lower(): freq for word, freq in common_words}

class ShadowAutoCompleteLineEdit(QLineEdit):
    def __init__(self, word_frequencies, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.word_frequencies = word_frequencies  # A dictionary of words with their frequencies
        self.suggestion = ""

    def updateSuggestion(self):
        """
        Update the shadow suggestion based on the last word being typed.
        """
        text = self.text()
        if text:
            # Split text into words and get the last word
            words = text.split()
            last_word = words[-1] if words else ""

            # Find the most likely completion for the last word, sorted by frequency
            matches = sorted(
                (word for word in self.word_frequencies if word.startswith(last_word.lower())),
                key=lambda word: -self.word_frequencies[word],
            )
            self.suggestion = matches[0][len(last_word):] if matches else ""
        else:
            self.suggestion = ""
        self.update()

    def paintEvent(self, event):
        """
        Paint the shadow suggestion on the QLineEdit, aligning it with the main text and avoiding overlap.
        """
        super().paintEvent(event)

        if self.suggestion:
            painter = QPainter(self)

            # Use the same font as the QLineEdit for consistency
            painter.setFont(self.font())

            # Light gray color for shadow text
            painter.setPen(QColor(150, 150, 150))

            # Measure the width of the existing text to position the shadow suggestion
            font_metrics = QFontMetrics(self.font())
            text = self.text()
            words = text.split()
            last_word = words[-1] if words else ""

            # Correctly calculate the position of the suggestion
            base_text = text[:text.rfind(last_word)] + last_word
            base_text_width = font_metrics.horizontalAdvance(base_text)  # Width of the current text

            x = base_text_width + 8  # Small padding to avoid overlap
            y = (self.height() + font_metrics.ascent() - font_metrics.descent()) // 2

            # Draw only the portion of the suggestion that hasn't been typed yet
            painter.drawText(x, y, self.suggestion)
            painter.end()


    def keyPressEvent(self, event):
        """
        Handle key presses to accept the suggestion for the last word.
        """
        if event.key() == Qt.Key_Tab and self.suggestion:
            # Append the suggestion to the last word
            text = self.text()
            words = text.split()
            if words:
                words[-1] += self.suggestion  # Complete the last word
                self.setText(" ".join(words))
                self.suggestion = ""
            event.accept()  # Prevent focus change
        else:
            super().keyPressEvent(event)
            self.updateSuggestion()

class AutoCompleteApp(QWidget):
    def __init__(self):
        super().__init__()
        self.word_frequencies = get_common_words_with_frequencies()
        self.initUI()

    def initUI(self):
        # Widgets
        self.line_edit = ShadowAutoCompleteLineEdit(self.word_frequencies)
        self.line_edit.setPlaceholderText("Type something...")
        self.submit_button = QPushButton("Submit")
        self.submit_button.clicked.connect(self.handleSubmit)
        # self.status_label = QLabel("Enter text and click submit.")

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.line_edit)
        layout.addWidget(self.submit_button)
        # layout.addWidget(self.status_label)
        self.setLayout(layout)

        self.setWindowTitle("AutoComplete")
        self.resize(600, 150)

    def handleSubmit(self):
        """
        Handle the submission of the text.
        - Clears the input field.
        - Updates the word frequencies based on the entered text.
        """
        text = self.line_edit.text().strip()
        if text:
            words = text.split()
            for word in words:
                # Increment frequency if the word exists, otherwise add it
                word_lower = word.lower()
                if word_lower in self.word_frequencies:
                    self.word_frequencies[word_lower] += 1
                else:
                    self.word_frequencies[word_lower] = 1

            # Clear the input field
            self.line_edit.clear()
            self.line_edit.updateSuggestion()

            # Update the status label
        #     # self.status_label.setText(f"Submitted: '{text}'")
        # else:
        #     self.status_label.setText("Nothing to submit!")

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = AutoCompleteApp()
    window.show()
    sys.exit(app.exec_())
