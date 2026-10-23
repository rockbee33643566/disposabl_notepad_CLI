import secrets
import os
import json
from typing import Iterable, Literal

DIR_NAME = "./notepade"

# try:
#     os.mkdir(DIR_NAME)
# except FileExistsError:
#     pass

def generate_notepad(
        type: Literal["let", "num"] = "num",
        leninght: int = 360 
    ) -> Iterable[int | str]:
    alphabet = [" ", ]
    alphabet_let = list(
        chr(i) for i in range(ord("а"), ord("я") + 1)
    )
    alphabet.extend(alphabet_let)

    if type == "num":
        return [secrets.randbelow(len(alphabet)) for _ in range(leninght)]
    elif type == "let":
        return [secrets.choice(alphabet) for _ in range(leninght)]
    else:
        raise ValueError(f"type не принимает значение: {type}")

def save(
        notepad: Iterable,
        name: str | None = None,
        path: str | None = None
    ) -> None:
    if path:
        name = path[:-5] + ".json"
    elif name is None:
        name = "notepad"

    if path is None:
        path = f"./notepad.json"

    id = 0
    used = 0

    data = {
        "id": id,
        "values": notepad,
        "used": used
    }
    count = 1

    while os.path.isfile(path):
        path = f"{name}{count}.json"
        count += 1

    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    notepad = generate_notepad()
    save(notepad)