import sys
import os
import subprocess
from PySide6 import QtWidgets, QtGui, QtCore
from pathlib import Path
from util import resource_path
import json
import shutil
import re

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MHUR Model Swapper")
        self.setWindowIcon(QtGui.QPixmap(resource_path('icon.ico')))
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
            subprocess.run([repakPath, "unpack", "-o", "assets/mod", file_name])
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
                print("Invalid mod file, it should contain exactly one skin mesh to swap.")
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

        # Get skins values list
        json_path = os.path.join("assets/HerovsGame/Content/Character", character, f"PA_{character}.json")
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        exports = data["Exports"][0]["Data"]
        for value in exports:
            if value["Name"] == '_costumeMeshs': skins = value["Value"]
            
        button = QtWidgets.QPushButton("Choose another mod")
        button.clicked.connect(self.go_back)
        self.layout.addWidget(button, 0, 0)

        # Add skins buttons
        column = 0
        row = 1

        path = Path("assets/mod/HerovsGame/Content/Character")
        path = next(path.rglob("Mesh"), None)
        for file in path.iterdir():
            if file.parents[1].name == "Default":
                currentSkin = "SK_" + file.parents[3].name + "_Default_00"
            else:
                currentSkin = "SK_" + file.parents[4].name + "_" + file.parents[2].name + file.parents[1].name

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

            if skin_name == currentSkin:
                button = QtWidgets.QPushButton('Base mod goes over this')
            else:
                button = QtWidgets.QPushButton(skin_name + " (" + skin_id + ")")
                button.clicked.connect(lambda _, s=skin_path: self.exportMod(s))
            button.setMaximumHeight(300)
            button.setStyleSheet("text-align: bottom")
            

            available_width = self.width()
            button_width = 280
            maxColumns = max(1, available_width // button_width)
            self.layout.addWidget(label, row, column)
            self.layout.addWidget(button, row, column)
            self.items.append((label, button))
            if column > maxColumns:
                column = 0
                row+=1
            else:
                column += 1


    def go_back(self):
        if os.path.exists("assets/mod"): shutil.rmtree("assets/mod")
        main_window = self.parent().parent()
        main_window.central_widget.setCurrentWidget(main_window.choosemodfile)

    def exportMod(self, skin):
        # Export mesh JSON
        path = Path("assets/mod/HerovsGame/Content/Character")
        meshPaths = path.rglob("Mesh")
        # Refactor this thing so I don't get sad when looking at so many indents
        for path in meshPaths:
            for file in path.iterdir():
                if file.name.casefold().startswith('sk_ch') and file.name.casefold().endswith('_00.uasset'):
                    if file.parents[1].name == "Default":
                        meshFile = "SK_" + file.parents[3].name + "_Default_00.uasset"
                    else:
                        meshFile = "SK_" + file.parents[4].name + "_" + file.parents[2].name + file.parents[1].name + ".uasset"
                    if str(file).casefold().endswith(meshFile.casefold()):
                        subprocess.run([uejsonPath, "-e", file])
                        json_path = str(file).replace(".uasset", ".json")
                        mesh_path = str(file.parent)
                        filename = file.name # Format: SK_ChXXX_Default_00.ext

                        # Edit JSON to swap mesh
                        with open(json_path, 'r+', encoding='utf-8') as f:
                            data = json.load(f)
                            # Find names that need to be replaced
                            namemap = data["NameMap"]
                            for name in namemap:
                                iName = namemap.index(name)
                                if filename.casefold().split(".")[0] in str(name).casefold() and "PhysicsAsset" not in name:
                                    if "Model/" in name:
                                        namemap[iName] = namemap[iName].partition("Character/")[0] + namemap[iName].partition("Character/")[1] + skin
                                    else:
                                        namemap[iName] = re.sub(filename.split(".")[0], skin.partition("Mesh/")[2], namemap[iName], flags=re.IGNORECASE)
                            # Change exports
                            for export in data["Exports"]:
                                if filename.casefold().split(".")[0] in export["ObjectName"].casefold(): 
                                    export["ObjectName"] = re.sub(filename.split(".")[0], skin.partition("Mesh/")[2], export["ObjectName"], flags=re.IGNORECASE)

                            f.seek(0)
                            json.dump(data, f, indent=4)

                        os.makedirs(os.path.join("assets/mod/HerovsGame/Content/Character/", Path(skin).parent))
                        # Import JSON to UAsset
                        final_path = "assets/mod/HerovsGame/Content/Character/"
                        subprocess.run([uejsonPath, "-i", json_path])
                        for file in Path(mesh_path).iterdir():
                            if (file.name.casefold().split(".")[0] == filename.casefold().split(".")[0]) and (file.name.endswith('.uasset') or file.name.endswith('.uexp')):
                                os.rename(os.path.join(mesh_path, file.name), final_path + skin + "." + file.name.split(".")[1])
                        if os.path.exists(json_path): os.remove(json_path) 
                        #Save mod pak
                        save_path = QtWidgets.QFileDialog.getSaveFileName(self, "Save Mod PAK", "", "PAK files (*.pak)")
                        if save_path[0].partition(".")[0].endswith("_P"):
                            exportPath = save_path[0].partition(".")[0] + ".pak"
                        elif save_path[0] != "":
                            exportPath = save_path[0].partition(".")[0] + "_P.pak"
                        else:
                            exportPath = save_path[0].partition(".")[0] + "SkinSwap_P.pak"
                        with open(resource_path('dependencies/unrealpak/unrealpak.txt'), 'w') as f:
                            mod_folder = os.path.abspath('assets/mod')
                            f.write(f'"{mod_folder}\\*.*" "..\\..\\..\\*.*"')
                        subprocess.run([unrealPak, exportPath, '-create=unrealpak.txt', '-compress'])
        # Clean up and prepare for next export
        if os.path.exists('dependencies/unrealpak/unrealpak.txt'): os.remove('dependencies/unrealpak/unrealpak.txt')
        shutil.rmtree("assets/mod")
        subprocess.run([repakPath, "unpack", "-o", f"assets/mod", self.mod_file])

if __name__ == "__main__":
    # Check .NET runtime installation
    netInstalled = False
    try:
        proc = subprocess.Popen(['dotnet', '--list-runtimes'], stdout=subprocess.PIPE)
        output = proc.stdout.read().split(b'\n')
        for line in output:
            if b'Microsoft.NETCore.App' in line and b'8.0.' in line:
                netInstalled = True
        if not netInstalled:
         raise Exception
    except Exception as e:
        input("This application requires .NET 8.0 runtime to be installed. Please install it from https://dotnet.microsoft.com/en-us/download/dotnet and try again.")
        raise

    
    print("Launching program, it might take a while the first time!")
    app = QtWidgets.QApplication([])

    # Dependencies
    uejsonPath="UEJSON/UEJSON.exe"
    repakPath="dependencies/repak/repak.exe"
    unrealPak="dependencies/unrealpak/UnrealPak.exe"
    ffmpegPath="dependencies/ffmpeg/ffmpeg.exe"
    ue4ddsPath=resource_path("dependencies/ue4dds/main.py")

    # Initialize config variables
    # Idea: check if aesKey is up to date?
    if os.path.exists("assets/config/config.json"):
        with open("assets/config/config.json", 'r', encoding='utf-8') as f:
            config = json.load(f)
            aesKey = config["aesKey"]
            gamePath = config["gamePakPath"]  
    else:
        if not os.path.exists("assets/config"): os.makedirs("assets/config")
        aesKey="0x332F41B1130F125444A35F420EC6D05EA3E27A972A36DAD90C83FC6958D941C7"
        gamePath="C:\\Program Files (x86)\\Steam\\steamapps\\common\\My Hero Ultra Rumble\\HerovsGame\\Content\\Paks\\HerovsGame-WindowsNoEditor.pak"
    if not os.path.exists(gamePath):
        gamePath = QtWidgets.QFileDialog.getOpenFileName(
            None,
            "Choose HerovsGame PAK file",
            "",
            "PAK files (HerovsGame-WindowsNoEditor.pak*)"
        )[0]
    with open("assets/config/config.json", 'w', encoding='utf-8') as f:
        default_config = {
            "aesKey": aesKey,
            "gamePakPath": gamePath
        }
        json.dump(default_config, f, indent=4)
        
    if not os.path.exists(gamePath): sys.exit()

    # Extract characters PA and skins images using repak
    subprocess.run([repakPath, "--aes-key", aesKey, "unpack", "-o", "assets", "-i", "**/Ch[0-3][0-9][0-9]/PA_Ch[0-9][0-9][0-9].*", gamePath])
    subprocess.run([repakPath, "--aes-key", aesKey, "unpack", "-o", "assets", "-i", "**/Ch[0-3][0-9][0-9]/GUI/Costume/L/*0_*L.*", gamePath])
    if os.path.exists('assets/HerovsGame/Content/Character/Ch000'): shutil.rmtree('assets/HerovsGame/Content/Character/Ch000')

    # Extract JSON files using UEJSON
    import time
    start_time = time.time()
    for character in os.listdir("assets/HerovsGame/Content/Character"):
            print("Checking character: ", character)
            pa_path = os.path.normpath(os.path.join("assets/HerovsGame/Content/Character", character, f"PA_{character}.uasset"))
            if not os.path.exists(pa_path.replace(".uasset", ".json")):
                subprocess.run([uejsonPath, "-e", pa_path])
            gui_path = os.path.join("assets\\HerovsGame\\Content\\Character", character, "GUI\\Costume\\L")
            for skinImage in os.listdir(gui_path):
                skinPath = os.path.join(gui_path, skinImage)
                if skinImage.endswith(".uasset") and not (os.path.exists(skinPath.replace(".uasset", ".png"))):
                    subprocess.run([resource_path('dependencies/ue4dds/python/python.exe'),ue4ddsPath, skinPath, f"--save_folder={gui_path}", "--mode=export", "--export_as=tga", "--skip_non_texture", ])
                    subprocess.run([ffmpegPath, "-i", skinPath.replace(".uasset", ".tga"), skinPath.replace(".uasset", ".png")])
    print("Time spent: ", (time.time() - start_time))

    if not (os.path.exists("assets/HerovsGame/Content/Character")):
        for character in os.listdir("assets/HerovsGame/Content/Character"):
            pa_path = os.path.join("assets/HerovsGame/Content/Character", character, f"PA_{character}.uasset")
            subprocess.run([uejsonPath, "-e", pa_path])

    widget = MainWindow()
    widget.show()
    
    sys.exit(app.exec())
