import json
import os
from pathlib import Path
from dataclasses import dataclass


@dataclass
class Config:
    first_launch: str
    host: str
    
def get_config() -> Config: 
    path = str(Path(__file__).parent.parent / "config.json")

    if os.path.isfile(path):
        create_config()

    with open(path, "r", encoding="utf-8") as file: 
        data = json.load(file)

    return Config(**data)

def edit_config() -> None: 
    pass 

def create_config() -> None:
    pass 