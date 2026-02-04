import sys
import os

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Dependencies
uejsonPath="UEJSON/UEJSON.exe"
repakPath="dependencies/repak/repak.exe"
unrealPak="dependencies/unrealpak/UnrealPak.exe"
ffmpegPath="dependencies/ffmpeg/ffmpeg.exe"
ue4ddsPath=resource_path("dependencies/ue4dds/main.py")