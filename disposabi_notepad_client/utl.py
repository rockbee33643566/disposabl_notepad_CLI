import uuid
from pathlib import Path

def generate_hash() -> str:
    return str(uuid.uuid4())

def init_file_system() -> None:
    path = Path(__file__).parent.parent / "data"
    path.mkdir(parents=True, exist_ok=True)