import json
import os
import shutil
from pathlib import Path
from dataclasses import dataclass, asdict


@dataclass
class Config:
    first_launch: bool
    host: str

def _get_path() -> str:
    return str(Path(__file__).parent.parent / "config.json")

def _example_path() -> str:
    return str(Path(__file__).parent.parent / "config.example.json")

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
    path = _get_path()
    example = _example_path()

    if not os.path.isfile(path) and os.path.isfile(example):
        shutil.copy(example, path)
