# PAK Parser

Unreal Engine PAK Parser written in Python 3 originally for the game Astroneer

Ability to list out files inside a PAK and get their contents.

## Usage
```
from PyPAKParser import PakParser

with open("PAKS/Astro-WindowsNoEditor.pak", "rb") as pakFile:

    PP = PakParser(pakFile)

    # Loads all headers into memory and prints out list
    print(PP.List())
    
    # Grabs the asset data and store in variable.
    assetName = "Astro/Content/Globals/PlayControllerInstance.uasset"
    assetData = PP.Unpack(assetName).Data
```