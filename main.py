import sys
import os
import subprocess
from PySide6 import QtWidgets, QtGui, QtCore
from pathlib import Path
import json
import shutil
# Dependencies
uejsonPath="UEJSON\\UEJSON.exe"
repakPath="dependencies/repak/repak.exe"
ue4ddsPath="dependencies/ue4dds/main.py"
ffmpegPath="dependencies/ffmpeg/ffmpeg.exe"
# Initialize config variables
if not os.path.exists("assets/config"):
    os.makedirs("assets/config")
    aesKey="0x332F41B1130F125444A35F420EC6D05EA3E27A972A36DAD90C83FC6958D941C7"
    gamePath="C:\\Program Files (x86)\\Steam\\steamapps\\common\\My Hero Ultra Rumble\\HerovsGame\\Content\\Paks\\HerovsGame-WindowsNoEditor.pak"
    if not os.path.exists(gamePath):
        gamePath = QtWidgets.QFileDialog.getOpenFileName(
            None,
            "Choose HerovsGame PAK file",
            "",
            "PAK files (*.pak*)"
        )[0]
    with open("assets/config/config.json", 'w', encoding='utf-8') as f:
        default_config = {
            "aesKey": aesKey,
            "gamePakPath": gamePath
        }
        json.dump(default_config, f, indent=4)
else:
    with open("assets/config/config.json", 'r', encoding='utf-8') as f:
        config = json.load(f)
        aesKey = config["aesKey"]
        gamePath = config["gamePakPath"]  

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
    
    def viewSkinsList(self, character, mod_file):
        self.skinsList = SkinsList(character, mod_file)
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
            subprocess.run([repakPath, "unpack", "-o", "assets/mod", file_name])
            main_window = self.parent_window
            # Temporal functionality, redirect to skins list
            selectedCharacter = os.listdir("assets/mod/HerovsGame/Content/Character")[0]
            main_window.viewSkinsList(selectedCharacter, file_name)
        
class CharactersList(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.parent_window = parent
        self.layout = QtWidgets.QGridLayout(self)
        column = 0
        row = 0
        for character in os.listdir("assets/HerovsGame/Content/Character"):
            self.button = QtWidgets.QPushButton(character)
            self.button.setMinimumSize(150, 150)
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

class SkinsList(QtWidgets.QScrollArea):
    def __init__(self, character, mod_file):
        super().__init__()  
        self.items = []
        self.mod_file = mod_file
        self.container = QtWidgets.QWidget()
        self.layout = QtWidgets.QGridLayout(self.container)
        self.container.setLayout(self.layout)
        self.setWidgetResizable(True) 
        self.setWidget(self.container)

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
            images = os.listdir((f"assets\\HerovsGame\\Content\\Character\\{character}\\GUI\\Costume\\L"))
            for image in images:
                if image.__contains__(skin_id) and image.endswith(".png"):
                    labelImage = os.path.join(f"assets\\HerovsGame\\Content\\Character\\{character}\\GUI\\Costume\\L", image)
            pixmap=QtGui.QPixmap(labelImage)
            pixmap = pixmap.scaled(300, 300, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
            self.label = QtWidgets.QLabel(pixmap=pixmap)
            self.label.setMaximumHeight(300)
            self.button = QtWidgets.QPushButton(skin_name + " (" + skin_id + ")")
            self.button.setMaximumHeight(300)
            self.button.clicked.connect(lambda _, s=skin_path: self.exportMod(s))
            available_width = self.width()
            columns = max(1, available_width // 280)
            index = len(self.items)
            row = (index // columns) + 1
            column = index % columns
            self.layout.addWidget(self.label, row, column)
            self.layout.addWidget(self.button, row, column)
            self.items.append((self.label, self.button))
            column += 1


    def go_back(self):
        shutil.rmtree("assets/mod")
        main_window = self.parent().parent()
        main_window.central_widget.setCurrentWidget(main_window.choosemodfile)

    def exportMod(self, skin):
        # Export mesh JSON
        path = Path("assets/mod/HerovsGame/Content/Character")
        path = list(path.rglob("Mesh"))
        for file in path[0].iterdir():
            if str(file).endswith(".uasset"):
                subprocess.run([uejsonPath, "-e", file])
                json_path = str(file).replace(".uasset", ".json")
                mesh_path = str(file).partition("SK_")[0]
                crumbs = str(file).split("\\")
                filename = crumbs[len(crumbs)-1].partition(".")[0] # Format: Sk_ChXXX_Default_00
        # Edit JSON to swap mesh
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
        final_path = "assets/mod/HerovsGame/Content/Character/"
        for file in os.listdir(mesh_path):
            if "PhysicsAsset" not in file:
                os.rename(mesh_path + file, final_path + skin + "." + file.split(".")[1])
        # Import JSON to UAsset
        subprocess.run([uejsonPath, "-i", final_path + skin + ".json"])
        #Save mod pak
        save_path = QtWidgets.QFileDialog.getSaveFileName(self, "Save Mod PAK", "", "PAK files (*.pak)")
        if save_path[0].partition(".")[0].endswith("_P"):
            exportPath = save_path[0].partition(".")[0] + ".pak"
            subprocess.run([repakPath, "pack", "assets/mod", exportPath])
        elif save_path[0] != "":
            exportPath = save_path[0].partition(".")[0] + "_P.pak"
            subprocess.run([repakPath, "pack", "assets/mod", exportPath])
        # Clean up and prepare for next export
        shutil.rmtree("assets/mod")
        subprocess.run([repakPath, "unpack", "-o", f"assets/mod", self.mod_file])

if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    # Extract characters PA and skins images using repak
    subprocess.run([repakPath, "--aes-key", aesKey, "unpack", "-o", "assets", "-i", "**/Ch[0-3][0-9][1-9]/PA_Ch[0-9][0-9][0-9].*", gamePath])
    subprocess.run([repakPath, "--aes-key", aesKey, "unpack", "-o", "assets", "-i", "**/Ch[0-3][0-9][1-9]/GUI/Costume/L/*0_L.*", gamePath])
    # Extract JSON files using UEJSON
    for character in os.listdir("assets/HerovsGame/Content/Character"):
            pa_path = os.path.join("assets/HerovsGame/Content/Character", character, f"PA_{character}.uasset")
            if not os.path.exists(pa_path.replace(".uasset", ".json")):
                subprocess.run([uejsonPath, "-e", pa_path])
            gui_path = os.path.join("assets\\HerovsGame\\Content\\Character", character, "GUI\\Costume\\L")
            for skinImage in os.listdir(gui_path):
                skinPath = os.path.join(gui_path, skinImage)
                if skinImage.endswith(".uasset") and not (os.path.exists(skinPath.replace(".uasset", ".png")) or os.path.exists(skinPath.replace(".uasset", ".tga"))):
                    subprocess.run(["python", ue4ddsPath, skinPath, f"--save_folder={gui_path}", "--mode=export", "--export_as=tga", "--skip_non_texture"])
                    subprocess.run([ffmpegPath, "-i", skinPath.replace(".uasset", ".tga"), skinPath.replace(".uasset", ".png")])
    if not (os.path.exists("assets/HerovsGame/Content/Character")):
        for character in os.listdir("assets/HerovsGame/Content/Character"):
            pa_path = os.path.join("assets/HerovsGame/Content/Character", character, f"PA_{character}.uasset")
            subprocess.run([uejsonPath, "-e", pa_path])
    widget = MainWindow()
    widget.show()
    
    sys.exit(app.exec())