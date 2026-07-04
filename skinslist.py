import os
import subprocess
import json
import shutil
import re
from PySide6 import QtWidgets, QtGui, QtCore
from pathlib import Path
from util import resource_path, uejsonPath, unrealPak, repakPath

class SkinsList(QtWidgets.QScrollArea):
    def __init__(self, character, mod_file=None, parent=None):
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

        # buttonBack = QtWidgets.QPushButton("Go back")
        # buttonBack.clicked.connect(parent.go_back)
        # self.layout.addWidget(buttonBack, 1, 0)   

        # Add skins buttons
        column = 0
        row = 1

        currentSkin = None
        if mod_file:
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
                    break
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
            button.setStyleSheet("text-align: bottom;")
            

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
        for path in meshPaths:
            for file in path.iterdir():
                if file.name.casefold().startswith('sk_ch') and file.name.casefold().endswith('_00.uasset'):
                    if file.parents[1].name == "Default":
                        meshFile = "SK_" + file.parents[3].name + "_Default_00.uasset"
                    else:
                        meshFile = "SK_" + file.parents[4].name + "_" + file.parents[2].name + file.parents[1].name + ".uasset"
                    if str(file).casefold().endswith(meshFile.casefold()):
                        subprocess.run([uejsonPath, "-e", file], creationflags=subprocess.CREATE_NO_WINDOW)
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
                                if str(name).casefold().endswith(filename.casefold().split(".")[0]):
                                    if "Model/" in name:
                                        namemap[iName] = namemap[iName].partition("Character/")[0] + namemap[iName].partition("Character/")[1] + skin
                                    else:
                                        namemap[iName] = re.sub(filename.split(".")[0], skin.partition("Mesh/")[2], namemap[iName], flags=re.IGNORECASE)
                            # Change exports
                            for export in data["Exports"]:
                                if str(export["ObjectName"].casefold()).endswith(filename.casefold().split(".")[0]): 
                                    export["ObjectName"] = re.sub(filename.split(".")[0], skin.partition("Mesh/")[2], export["ObjectName"], flags=re.IGNORECASE)

                            f.seek(0)
                            json.dump(data, f, indent=4)

                        os.makedirs(os.path.join("assets/mod/HerovsGame/Content/Character/", Path(skin).parent), exist_ok=True)
                        # Import JSON to UAsset
                        final_path = "assets/mod/HerovsGame/Content/Character/"
                        subprocess.run([uejsonPath, "-i", json_path], creationflags=subprocess.CREATE_NO_WINDOW)
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
                        subprocess.run([unrealPak, exportPath, '-create=unrealpak.txt', '-compress'], creationflags=subprocess.CREATE_NO_WINDOW)
            break
        # Clean up and prepare for next export
        if os.path.exists('dependencies/unrealpak/unrealpak.txt'): os.remove('dependencies/unrealpak/unrealpak.txt')
        shutil.rmtree("assets/mod")
        subprocess.run([repakPath, "unpack", "-o", f"assets/mod", self.mod_file], creationflags=subprocess.CREATE_NO_WINDOW)