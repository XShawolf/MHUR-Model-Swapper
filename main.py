import sys
import os
import subprocess
import json
import shutil
from PySide6 import QtWidgets, QtGui
from util import resource_path, uejsonPath, repakPath, ue4ddsPath, ffmpegPath
from skinslist import SkinsList
from choosemod import ChooseModFileWidget

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
    
    def viewSkinsList(self, character, mod_file):
        self.skinsList = SkinsList(character, mod_file)
        self.central_widget.addWidget(self.skinsList)
        self.central_widget.setCurrentWidget(self.skinsList)
    
    def closeEvent(self, event):
        # Clean up extracted mod files on exit
        if os.path.exists("assets/mod"): shutil.rmtree("assets/mod")
        event.accept()

if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    app.setStyle("windows11") # Temporal until I make my own universal style

    # Check .NET runtime installation
    # TO-DO: optimize this check, sometimes takes too long
    netInstalled = False
    try:
        proc = subprocess.Popen(['dotnet', '--list-runtimes'], stdout=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)
        output = proc.stdout.read().split(b'\n')
        for line in output:
            if b'Microsoft.NETCore.App' in line and b'8.0.' in line:
                netInstalled = True
        if not netInstalled:
         raise Exception
    except Exception as e:
        error = QtWidgets.QMessageBox()
        error.setIcon(QtWidgets.QMessageBox.Icon.Critical)
        error.setWindowTitle("Error: .NET 8.0 runtime not found")
        error.setWindowIcon(QtGui.QPixmap(resource_path('icon.ico')))
        error.setText(".NET 8.0 runtime is not installed on your system.")
        error.setInformativeText("This application requires .NET 8.0 runtime to be installed. Please install it from <a style='color: cyan' href='https://dotnet.microsoft.com/en-us/download/dotnet'>here</a> or direct download from  <a style='color: cyan' href='https://dotnet.microsoft.com/en-us/download/dotnet/thank-you/runtime-desktop-8.0.23-windows-x64-installer'>here</a> and try again.")
        sys.exit(error.exec())

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
            "MHUR PAK (HerovsGame-WindowsNoEditor.pak);;All files (*.*)"
        )[0]
    with open("assets/config/config.json", 'w', encoding='utf-8') as f:
        default_config = {
            "aesKey": aesKey,
            "gamePakPath": gamePath
        }
        json.dump(default_config, f, indent=4)
        
    if not os.path.exists(gamePath): sys.exit()

    if (os.path.exists("assets/mod")): shutil.rmtree("assets/mod")
    
    # Show loading dialog
    loading = QtWidgets.QDialog()
    loading.setWindowTitle("Loading...")
    loading.setWindowIcon(QtGui.QPixmap(resource_path('icon.ico')))
    loading.layout = QtWidgets.QVBoxLayout(loading)
    loading.layout.addWidget(QtWidgets.QLabel("Extracting game files, please wait some minutes..."))
    loading.show()
    QtWidgets.QApplication.processEvents()

    # Extract characters PA and skins images using repak
    subprocess.run([repakPath, "--aes-key", aesKey, "unpack", "-o", "assets", "-i", "**/Ch[0-3][0-9][0-9]/PA_Ch[0-9][0-9][0-9].*", gamePath], creationflags=subprocess.CREATE_NO_WINDOW)
    subprocess.run([repakPath, "--aes-key", aesKey, "unpack", "-o", "assets", "-i", "**/Ch[0-3][0-9][0-9]/GUI/Costume/L/*0_*L.*", gamePath], creationflags=subprocess.CREATE_NO_WINDOW)
    if os.path.exists('assets/HerovsGame/Content/Character/Ch000'): shutil.rmtree('assets/HerovsGame/Content/Character/Ch000')

    # Extract JSON files using UEJSON
    for character in os.listdir("assets/HerovsGame/Content/Character"):
            print("Checking character: ", character)
            pa_path = os.path.normpath(os.path.join("assets/HerovsGame/Content/Character", character, f"PA_{character}.uasset"))
            subprocess.run([uejsonPath, "-e", pa_path], creationflags=subprocess.CREATE_NO_WINDOW)

            # Extract skin thumbnails if missing
            gui_path = os.path.join("assets\\HerovsGame\\Content\\Character", character, "GUI\\Costume\\L")
            for skinImage in os.listdir(gui_path):
                skinPath = os.path.join(gui_path, skinImage)
                if skinImage.endswith(".uasset") and not (os.path.exists(skinPath.replace(".uasset", ".png"))):
                    subprocess.run([resource_path('dependencies/ue4dds/python/python.exe'),ue4ddsPath, skinPath, f"--save_folder={gui_path}", "--mode=export", "--export_as=tga", "--skip_non_texture", ], creationflags=subprocess.CREATE_NO_WINDOW)
                    subprocess.run([ffmpegPath, "-i", skinPath.replace(".uasset", ".tga"), skinPath.replace(".uasset", ".png")], creationflags=subprocess.CREATE_NO_WINDOW)

    if not (os.path.exists("assets/HerovsGame/Content/Character")):
        for character in os.listdir("assets/HerovsGame/Content/Character"):
            pa_path = os.path.join("assets/HerovsGame/Content/Character", character, f"PA_{character}.uasset")
            subprocess.run([uejsonPath, "-e", pa_path], creationflags=subprocess.CREATE_NO_WINDOW)

    loading.close()
    widget = MainWindow()
    widget.show()
    
    sys.exit(app.exec())
