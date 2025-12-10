import sys
import os
import subprocess
from PySide6 import QtCore, QtWidgets, QtGui
import variables
import json

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MHUR Model Swapper")
        self.resize(1024, 768)
        self.central_widget = QtWidgets.QStackedWidget()
        self.setCentralWidget(self.central_widget)
        self.characters_list = CharactersList(parent=self)
        self.central_widget.addWidget(self.characters_list)

class CharactersList(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.parent_window = parent
        self.layout = QtWidgets.QGridLayout(self)
        column = 0
        row = 0
        for character in os.listdir("assets/HerovsGame/Content/Character"):
            self.button = QtWidgets.QPushButton(character)
            self.button.setMinimumSize(150, 150)  # Square size (150x150)
            self.button.clicked.connect(lambda showSkins, c=character: self.show_skins(c))
            self.layout.addWidget(self.button, row, column)
            column = column + 1
            if column > 9:
                column = 0
                row = row + 1

    def show_skins(self, character):
        skins_widget = SkinsList(character)
        self.parent_window.central_widget.addWidget(skins_widget)
        self.parent_window.central_widget.setCurrentWidget(skins_widget)
        
class SkinsList(QtWidgets.QWidget):
    def __init__(self, character):
        super().__init__()
        self.layout = QtWidgets.QGridLayout(self)
        json_path = os.path.join("assets/HerovsGame/Content/Character", character, f"PA_{character}.json")
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        skins = data["Exports"][0]["Data"][0]["Value"]
        column = 0
        row = 1
        self.button = QtWidgets.QPushButton("Back")
        self.button.clicked.connect(self.go_back)
        self.layout.addWidget(self.button, 0, 0)
        for skin in skins:
            print(skin)
            skin_id = str(skin[0]["Value"])
            # Extract skin filename from asset path
            skin_path = skin[1]["Value"]["AssetPath"]["AssetName"].partition("Mesh/")[2]
            skin_name = skin_path.partition(".")[0]
            print("skin path: " + skin_path)
            print("skin name: " + skin_name)
            self.button = QtWidgets.QPushButton(skin_name + " (" + skin_id + ")")
            self.button.setMinimumSize(150, 150)  # Square size (150x150)
            self.layout.addWidget(self.button, row, column)
            column = column + 1
            if column > 4:
                column = 0
                row = row + 1

    def go_back(self):
        main_window = self.parent().parent()
        main_window.central_widget.setCurrentWidget(main_window.characters_list)
if __name__ == "__main__":
    # Extract characters PA using repak
    subprocess.run(["repak/repak.exe", "--aes-key", variables.aesKey, "unpack", "-o", "assets", "-i", "**/Ch[0-3][0-9][1-9]/PA_Ch[0-9][0-9][0-9].*", variables.path])
    # Extract JSON files using UEJSON
    for character in os.listdir("assets/HerovsGame/Content/Character"):
        pa_path = os.path.join("assets/HerovsGame/Content/Character", character, f"PA_{character}.uasset")
        subprocess.run([variables.uejsonPath, "-e", pa_path])
    app = QtWidgets.QApplication([])
    widget = MainWindow()
    widget.show()
    
    sys.exit(app.exec())