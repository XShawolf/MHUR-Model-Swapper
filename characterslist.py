import os
from PySide6 import QtWidgets
from skinslist import SkinsList

class CharactersList(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.parent_window = parent
        self.layout = QtWidgets.QGridLayout(self)
        column = 0
        row = 0
        for character in os.listdir("assets/HerovsGame/Content/Character"):
            button = QtWidgets.QPushButton(character)
            button.setMinimumSize(150, 150)
            button.clicked.connect(lambda _, c=character: self.show_skins(c))
            self.layout.addWidget(button, row, column)
            column = column + 1
            if column > 9:
                column = 0
                row = row + 1

    def show_skins(self, character):
        skins_widget = SkinsList(character)
        self.parent_window.central_widget.addWidget(skins_widget)
        self.parent_window.central_widget.setCurrentWidget(skins_widget)