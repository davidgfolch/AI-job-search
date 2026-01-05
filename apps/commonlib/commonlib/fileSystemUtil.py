from pathlib import Path
from os.path import isfile, join
import os

def createFolder(filename: str) -> Path:
    path = Path(filename)
    path.parent.mkdir(exist_ok=True, parents=True)
    return path

def listFiles(folder: Path) -> list[str]:
    return [f for f in os.listdir(folder.absolute()) if isfile(join(folder, f))]

def getSrcPath() -> str:
    return str(Path(os.getcwd()))
