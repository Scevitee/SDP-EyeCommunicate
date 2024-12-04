import pyttsx3

class TTSEngine:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 150)  # Speech rate
        self.engine.setProperty('volume', 1.0)  # Volume (0.0 to 1.0)

    def speak(self, text):
        """Speak the given text."""
        self.engine.say(text)
        self.engine.runAndWait()

    def stop(self):
        """Stop speaking."""
        self.engine.stop()
