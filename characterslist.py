import os
from PySide6 import QtWidgets, QtGui, QtCore
from skinslist import SkinsList

class CharactersList(QtWidgets.QScrollArea):
    def __init__(self):
        super().__init__()
        self.container = QtWidgets.QWidget()
        self.layout = QtWidgets.QGridLayout(self.container)
        self.setWidgetResizable(True) 
        self.setWidget(self.container)

        button = QtWidgets.QPushButton("Go back")
        button.clicked.connect(self.go_back)
        self.layout.addWidget(button, 0, 0)        
        column = 0
        row = 1
        for character in os.listdir("assets/HerovsGame/Content/Character"):
            button = QtWidgets.QPushButton(character)
            button.setMinimumSize(350, 350)
            button.setStyleSheet("text-align: bottom;")
            button.clicked.connect(lambda _, c=character: self.show_skins(c))
            
            labelImage = os.path.join(f"assets\\HerovsGame\\Content\\Character\\{character}\\GUI\\Costume\\L", os.listdir((f"assets\\HerovsGame\\Content\\Character\\{character}\\GUI\\Costume\\L"))[0])
            pixmap=QtGui.QPixmap(labelImage).scaled(300, 300, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
            label = QtWidgets.QLabel(pixmap=pixmap)
            label.setMaximumHeight(300)
            label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

            self.layout.addWidget(label, row, column)
            self.layout.addWidget(button, row, column)

            available_width = self.width()
            button_width = 350
            maxColumns = max(1, available_width // button_width)
            self.layout.addWidget(label, row, column)
            self.layout.addWidget(button, row, column)
            if column > maxColumns:
                column = 0
                row+=1
            else:
                column += 1

    def show_skins(self, character):
        skins_widget = SkinsList(character, parent=self)
        self.parent_window.central_widget.addWidget(skins_widget)
        self.parent_window.central_widget.setCurrentWidget(skins_widget)

    def go_back(self):
        main_window = self.parent().parent()
        main_window.central_widget.setCurrentWidget(main_window.choosemodfile)