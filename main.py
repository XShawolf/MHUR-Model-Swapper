import sys
import os
import subprocess
from PySide6 import QtWidgets, QtGui, QtCore
from pathlib import Path
import json
import shutil

# Dependencies
uejsonPath="UEJSON/UEJSON.exe"
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
        button = QtWidgets.QPushButton("Choose mod .pak file")
        button.clicked.connect(self.open_file_dialog)
        self.layout.addWidget(button)

    def open_file_dialog(self):
        main_window = self.parent_window
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Open File",
            "",
            "PAK files (*.pak*)"
        )
        if file_name:
            subprocess.run([repakPath, "unpack", "-o", "assets/mod", file_name], creationflags=subprocess.CREATE_NO_WINDOW)
            pathList = Path("assets/mod").rglob("Mesh") # Format: assets\mod\HerovsGame\Content\Character\Ch001\Model\Default\Mesh
            meshNumber=0
            for path in pathList:
                if os.path.isdir(path):
                    if path.parent.name == "Default":
                        file = "SK_" + path.parents[2].name + "_Default_00.uasset"
                    else:
                        file = "SK_" + path.parents[3].name + "_" + path.parents[1].name + path.parent.name + ".uasset"
                    if os.path.exists(os.path.join(path, file)):
                        meshNumber+=1
                
            # TO-DO: Show error message, invalid mod
            if meshNumber != 1:
                shutil.rmtree("assets/mod")
            else:
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
            button = QtWidgets.QPushButton(character)
            button.setMinimumSize(150, 150)
            button.clicked.connect(lambda showSkins, c=character: self.show_skins(c))
            self.layout.addWidget(button, row, column)
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
        button = QtWidgets.QPushButton("Choose another mod")
        button.clicked.connect(self.go_back)
        self.layout.addWidget(button, 0, 0)

        # Add skins buttons
        column = 0
        row = 1
        for skin in skins:
            skin_id = str(skin[0]["Value"])
            skin_path = skin[1]["Value"]["AssetPath"]["AssetName"].partition("Character/")[2].partition(".")[0] #Format: ChXXX/Model/Default/Mesh/SK_ChXXX_Default_00
            skin_name = skin[1]["Value"]["AssetPath"]["AssetName"].partition("Mesh/")[2].partition(".")[0] # Format: Sk_ChXXX_Default_00
            images = os.listdir((f"assets\\HerovsGame\\Content\\Character\\{character}\\GUI\\Costume\\L"))
            for image in images:
                if image.__contains__(skin_id) and image.endswith(".png"):
                    labelImage = os.path.join(f"assets\\HerovsGame\\Content\\Character\\{character}\\GUI\\Costume\\L", image)
            pixmap=QtGui.QPixmap(labelImage).scaled(300, 300, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
            label = QtWidgets.QLabel(pixmap=pixmap)
            label.setMaximumHeight(300)
            label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

            button = QtWidgets.QPushButton(skin_name + " (" + skin_id + ")")
            button.setMaximumHeight(300)
            button.setStyleSheet("text-align: bottom")
            button.clicked.connect(lambda _, s=skin_path: self.exportMod(s))

            available_width = self.width()
            columns = max(1, available_width // 280)
            self.layout.addWidget(label, row, column)
            self.layout.addWidget(button, row, column)
            self.items.append((label, button))
            if column > columns:
                column = 0
                row+=1
            else:
                column += 1


    def go_back(self):
        if os.path.exists("assets/mod"):
            shutil.rmtree("assets/mod")
        main_window = self.parent().parent()
        main_window.central_widget.setCurrentWidget(main_window.choosemodfile)

    def exportMod(self, skin):
        # Export mesh JSON
        path = Path("assets/mod/HerovsGame/Content/Character")
        path = list(path.rglob("Mesh"))
        for file in path[0].iterdir():
            if str(file).endswith(".uasset"):
                subprocess.run([uejsonPath, "-e", file], creationflags=subprocess.CREATE_NO_WINDOW)
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
        subprocess.run([uejsonPath, "-i", final_path + skin + ".json"], creationflags=subprocess.CREATE_NO_WINDOW)
        #Save mod pak
        save_path = QtWidgets.QFileDialog.getSaveFileName(self, "Save Mod PAK", "", "PAK files (*.pak)")
        if save_path[0].partition(".")[0].endswith("_P"):
            exportPath = save_path[0].partition(".")[0] + ".pak"
            subprocess.run([repakPath, "pack", "assets/mod", exportPath], creationflags=subprocess.CREATE_NO_WINDOW)
        elif save_path[0] != "":
            exportPath = save_path[0].partition(".")[0] + "_P.pak"
            subprocess.run([repakPath, "pack", "assets/mod", exportPath], creationflags=subprocess.CREATE_NO_WINDOW)
        # Clean up and prepare for next export
        shutil.rmtree("assets/mod")
        subprocess.run([repakPath, "unpack", "-o", f"assets/mod", self.mod_file], creationflags=subprocess.CREATE_NO_WINDOW)

if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    # Extract characters PA and skins images using repak
    subprocess.run([repakPath, "--aes-key", aesKey, "unpack", "-o", "assets", "-i", "**/Ch[0-3][0-9][1-9]/PA_Ch[0-9][0-9][0-9].*", gamePath], creationflags=subprocess.CREATE_NO_WINDOW)
    subprocess.run([repakPath, "--aes-key", aesKey, "unpack", "-o", "assets", "-i", "**/Ch[0-3][0-9][1-9]/GUI/Costume/L/*0_L.*", gamePath], creationflags=subprocess.CREATE_NO_WINDOW)
    # Extract JSON files using UEJSON
    for character in os.listdir("assets/HerovsGame/Content/Character"):
            pa_path = os.path.join("assets/HerovsGame/Content/Character", character, f"PA_{character}.uasset")
            if not os.path.exists(pa_path.replace(".uasset", ".json")):
                subprocess.run([uejsonPath, "-e", pa_path], creationflags=subprocess.CREATE_NO_WINDOW)
            gui_path = os.path.join("assets\\HerovsGame\\Content\\Character", character, "GUI\\Costume\\L")
            for skinImage in os.listdir(gui_path):
                skinPath = os.path.join(gui_path, skinImage)
                if skinImage.endswith(".uasset") and not (os.path.exists(skinPath.replace(".uasset", ".png")) or os.path.exists(skinPath.replace(".uasset", ".tga"))):
                    subprocess.run(["python", ue4ddsPath, skinPath, f"--save_folder={gui_path}", "--mode=export", "--export_as=tga", "--skip_non_texture"], creationflags=subprocess.CREATE_NO_WINDOW)
                    subprocess.run([ffmpegPath, "-i", skinPath.replace(".uasset", ".tga"), skinPath.replace(".uasset", ".png")], creationflags=subprocess.CREATE_NO_WINDOW)
    if not (os.path.exists("assets/HerovsGame/Content/Character")):
        for character in os.listdir("assets/HerovsGame/Content/Character"):
            pa_path = os.path.join("assets/HerovsGame/Content/Character", character, f"PA_{character}.uasset")
            subprocess.run([uejsonPath, "-e", pa_path], creationflags=subprocess.CREATE_NO_WINDOW)
    widget = MainWindow()
    widget.show()
    
    sys.exit(app.exec())