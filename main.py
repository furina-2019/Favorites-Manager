import sys
import os
from PyQt6.QtWidgets import QApplication
from main_window import MainWindow

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

if __name__ == "__main__":
    browsers_path = resource_path("browsers")
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = browsers_path
    print(f"[DEBUG] PLAYWRIGHT_BROWSERS_PATH set to: {browsers_path}")
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
