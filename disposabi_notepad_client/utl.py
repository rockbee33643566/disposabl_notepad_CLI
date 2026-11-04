import os
import shutil
import uuid

def generate_hash() -> str:
    return str(uuid.uuid4())

def init_file_system() -> None:
    if not os.path.isdir("data"):
        os.mkdir("data")