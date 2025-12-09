import sys
import os
import subprocess
from PySide6 import QtCore, QtWidgets, QtGui
import variables
class CharactersList(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QtWidgets.QGridLayout(self)
        for character in os.listdir("assets/HerovsGame/Content/Character"):
            self.button = QtWidgets.QPushButton(character)
            self.layout.addWidget(self.button)

if __name__ == "__main__":
    # Extract characters PA using repak
    subprocess.run(["repak/repak.exe", "--aes-key", variables.aesKey, "unpack", "-o", "assets", "-i", "**/Ch[0-3][0-9][1-9]/PA_Ch[0-9][0-9][0-9].*", variables.path])
    app = QtWidgets.QApplication([])
    widget = CharactersList()
    widget.resize(800, 600)
    widget.show()

    sys.exit(app.exec())