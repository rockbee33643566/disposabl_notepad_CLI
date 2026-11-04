import json
import os
import shutil
from pathlib import Path
from dataclasses import dataclass, asdict


@dataclass
class Config:
    first_launch: str
    host: str

def _get_path(): 
    return str(Path(__file__).parent.parent / "config.json")
    
def get_config() -> Config: 
    path = _get_path()

    if not os.path.isfile(path):
        create_config()

    with open(path, "r", encoding="utf-8") as file: 
        data = json.load(file)

    return Config(**data)

def edit_config(conf: Config) -> None: 
    path = _get_path()

    if not os.path.isfile(path): 
        create_config()

    data = asdict(conf)

    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

def create_config() -> None:
    if not os.path.isfile("config.json"):
        shutil.copy("config.example.json", "config.json")