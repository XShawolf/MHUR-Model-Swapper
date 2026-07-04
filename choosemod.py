import os
import subprocess
import shutil
from PySide6 import QtWidgets, QtGui
from pathlib import Path
from util import repakPath, resource_path
from characterslist import CharactersList
class NoMesh(Exception):
    pass  

class MultipleMesh(Exception):
    pass      

class ChooseModFileWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.parent_window = parent
        self.layout = QtWidgets.QVBoxLayout(self)

        button = QtWidgets.QPushButton("Choose mod .pak file")
        button.clicked.connect(self.openModfile)
        self.layout.addWidget(button)

        buttonDefault = QtWidgets.QPushButton("Change default game costume")
        buttonDefault.clicked.connect(self.show_characters)
        self.layout.addWidget(buttonDefault)

    def show_characters(self):
        characters_widget = CharactersList(parent=self)
        self.parent_window.central_widget.addWidget(characters_widget)
        self.parent_window.central_widget.setCurrentWidget(characters_widget)     

    def openModfile(self):
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
            try:
                # Check if mod file is valid
                for path in pathList:
                    if os.path.isdir(path):
                        if path.parent.name == "Default":
                            file = "SK_" + path.parents[2].name + "_Default_00.uasset"
                        else:
                            file = "SK_" + path.parents[3].name + "_" + path.parents[1].name + path.parent.name + ".uasset"
                        if os.path.exists(os.path.join(path, file)):
                            meshFiles.append(Path(os.path.join(path, file)))
                if len(meshFiles) == 0:
                    raise NoMesh
                if len(meshFiles) > 1:
                    raise MultipleMesh  
                
                # If valid, show skins list
                selectedCharacter = meshFiles[0].parents[-7].name
                main_window.viewSkinsList(selectedCharacter, file_name)
            except NoMesh:
                error = QtWidgets.QMessageBox()
                error.setIcon(QtWidgets.QMessageBox.Icon.Critical)
                error.setWindowTitle("Error: No skin model found")
                error.setWindowIcon(QtGui.QPixmap(resource_path('icon.ico')))
                error.setText("No skin model found in the selected mod file.")
                error.setInformativeText("Please make sure your mod file contains a valid skin model and try again.")
                error.exec()
                if os.path.exists('assets/mod'): shutil.rmtree("assets/mod")
            except MultipleMesh:
                error = QtWidgets.QMessageBox()
                error.setIcon(QtWidgets.QMessageBox.Icon.Critical)
                error.setWindowTitle("Error: Multiple skin models")
                error.setWindowIcon(QtGui.QPixmap(resource_path('icon.ico')))
                error.setText("This mod contains multiple skin models, which is not supported yet.")
                error.setInformativeText("This program currently only supports mods that contain one skin model to swap. Please modify your mod to contain only one skin model or wait for future updates that support multiple skin models.")
                error.exec()
                if os.path.exists('assets/mod'): shutil.rmtree("assets/mod")