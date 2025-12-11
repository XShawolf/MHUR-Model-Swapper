import sys
import os
import subprocess
from PySide6 import QtCore, QtWidgets, QtGui
from pathlib import Path
import variables
import json
import shutil

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MHUR Model Swapper")
        self.resize(1024, 768)
        self.central_widget = QtWidgets.QStackedWidget()
        self.setCentralWidget(self.central_widget)
        self.choosemodfile = ChooseModFileWidget(parent=self)
        self.central_widget.addWidget(self.choosemodfile)
        self.characters_list = CharactersList(parent=self)
    
    def viewSkinsList(self, character):
        self.skinsList = SkinsList(character)
        self.central_widget.addWidget(self.skinsList)
        self.central_widget.setCurrentWidget(self.skinsList)
    
    def closeEvent( self, event):
        # Clean up extracted mod files on exit
        if os.path.exists("assets/mod"):
            shutil.rmtree("assets/mod")
        event.accept()

class ChooseModFileWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.parent_window = parent
        self.layout = QtWidgets.QVBoxLayout(self)
        # TO-DO: Implement logic to check if mod is valid
        self.button = QtWidgets.QPushButton("Choose mod .pak file")
        self.button.clicked.connect(self.open_file_dialog)
        self.layout.addWidget(self.button)

    def open_file_dialog(self):
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Open File",
            "",
            "PAK files (*.pak*)"
        )
        if file_name:
            subprocess.run(["repak/repak.exe", "unpack", "-o", f"assets/mod", file_name])
            main_window = self.parent_window
            # Temporal functionality, redirect to skins list
            selectedCharacter = os.listdir("assets/mod/HerovsGame/Content/Character")[0]
            main_window.viewSkinsList(selectedCharacter)
            #main_window.central_widget.addWidget(main_window.characters_list)
            #main_window.central_widget.setCurrentWidget(main_window.characters_list)
        
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
        self.button = QtWidgets.QPushButton("Choose another mod")
        self.button.clicked.connect(self.go_back)
        self.layout.addWidget(self.button, 0, 0)
        for skin in skins:
            skin_id = str(skin[0]["Value"])
            # Extract skin filename from asset path
            skin_path = skin[1]["Value"]["AssetPath"]["AssetName"].partition("Character/")[2].partition(".")[0] #Format: ChXXX/Model/Default/Mesh/SK_ChXXX_Default_00
            skin_name = skin[1]["Value"]["AssetPath"]["AssetName"].partition("Mesh/")[2].partition(".")[0] # Format: Sk_ChXXX_Default_00
            self.button = QtWidgets.QPushButton(skin_name + " (" + skin_id + ")")
            self.button.setMinimumSize(150, 150)  # Square size (150x150)
            self.button.clicked.connect(lambda exportMod, s=skin_path: self.exportMod(s))
            self.layout.addWidget(self.button, row, column)
            column = column + 1
            if column > 4:
                column = 0
                row = row + 1

    def go_back(self):
        main_window = self.parent().parent()
        main_window.central_widget.setCurrentWidget(main_window.choosemodfile)

    def exportMod(self, skin):
        # Export mesh JSON
        print("Exporting skin: " + skin)
        path = Path("assets/mod/HerovsGame/Content/Character")
        path = list(path.rglob("Mesh"))
        for file in path[0].iterdir():
            if str(file).endswith(".uasset"):
                subprocess.run([variables.uejsonPath, "-e", file])
                json_path = str(file).replace(".uasset", ".json")
                mesh_path = str(file).partition("SK_")[0]
                crumbs = str(file).split("\\")
                filename = crumbs[len(crumbs)-1].partition(".")[0] # Format: Sk_ChXXX_Default_00
        # Edit JSON to swap mesh
        # TO-DO: Add option to select more than one replace, have in mind that JSON being moved breaks it
        with open(json_path, 'r+', encoding='utf-8') as f:
            data = json.load(f)
            # Find names that need to be replaced
            namemap = data["NameMap"]
            for name in namemap:
                if filename in name and "PhysicsAsset" not in name:
                    if "Model/" in name:
                        namemap[namemap.index(name)] = namemap[namemap.index(name)].partition("Character/")[0] + namemap[namemap.index(name)].partition("Character/")[1] + skin
                    else:
                        namemap[namemap.index(name)] = skin.partition("Mesh/")[2]
            # Change export
            data["Exports"][0]["ObjectName"] = skin.partition("Mesh/")[2]


            f.seek(0)
            json.dump(data, f, indent=4)
        # Make correct file structure for repak
        newPath = "assets/mod/HerovsGame/Content/Character/"
        for folder in skin.split("/")[:-1]:
                if not os.path.exists(newPath + folder):
                    os.mkdir(newPath + folder)
                newPath = newPath + folder + "/"

        for file in os.listdir(mesh_path):
            final_path = "assets/mod/HerovsGame/Content/Character/"
            os.rename(mesh_path + file, final_path + skin + "." + file.split(".")[1])
        # Import JSON to UAsset
        subprocess.run([variables.uejsonPath, "-i", final_path + skin + ".json"])
        #Save mod pak
        save_path = QtWidgets.QFileDialog.getSaveFileName(self, "Save Mod PAK", "", "PAK files (*.pak)")
        subprocess.run(["repak/repak.exe", "pack", "assets/mod", save_path[0]])

if __name__ == "__main__":
    # Extract characters PA using repak
    subprocess.run(["repak/repak.exe", "--aes-key", variables.aesKey, "unpack", "-o", "assets", "-i", "**/Ch[0-3][0-9][1-9]/PA_Ch[0-9][0-9][0-9].*", variables.path])
    # Extract JSON files using UEJSON
    for character in os.listdir("assets/HerovsGame/Content/Character"):
            pa_path = os.path.join("assets/HerovsGame/Content/Character", character, f"PA_{character}.uasset")
            subprocess.run([variables.uejsonPath, "-e", pa_path])
    if not (os.path.exists("assets/HerovsGame/Content/Character")):
        for character in os.listdir("assets/HerovsGame/Content/Character"):
            pa_path = os.path.join("assets/HerovsGame/Content/Character", character, f"PA_{character}.uasset")
            subprocess.run([variables.uejsonPath, "-e", pa_path])
    app = QtWidgets.QApplication([])
    widget = MainWindow()
    widget.show()
    
    sys.exit(app.exec())