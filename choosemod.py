import os
import subprocess
from PySide6 import QtWidgets
from pathlib import Path
from util import repakPath
import shutil


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
            meshFiles=[]
            for path in pathList:
                if os.path.isdir(path):
                    if path.parent.name == "Default":
                        file = "SK_" + path.parents[2].name + "_Default_00.uasset"
                    else:
                        file = "SK_" + path.parents[3].name + "_" + path.parents[1].name + path.parent.name + ".uasset"
                    if os.path.exists(os.path.join(path, file)):
                        meshFiles.append(Path(os.path.join(path, file)))
                
            # TO-DO: Show error message, invalid mod
            if len(meshFiles) != 1:
                print("Invalid mod file, it should contain exactly one skin mesh to swap.")
                if os.path.exists('assets/mod'): shutil.rmtree("assets/mod")
            else:
                # Temporal functionality, redirect to skins list
                selectedCharacter = meshFiles[0].parents[-7].name
                main_window.viewSkinsList(selectedCharacter, file_name)