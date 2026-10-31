import secrets
import os
import json
from typing import Iterable, Literal

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
        return generate_num_notepad(
            leninght=leninght, 
            inclusive_upper_bound=len(alphabet)
        )
    elif type == "let":
        return generate_text_notepad(
            leninght=leninght, 
            alphabet=alphabet
        )
    else:
        raise ValueError(f"type не принимает значение: {type}")

def generate_num_notepad(
    leninght: int, 
    inclusive_upper_bound: int
) -> Iterable[str]:
    return [secrets.randbelow(inclusive_upper_bound + 1) for _ in range(leninght)]

def generate_text_notepad(
    leninght: int, 
    alphabet: list[str]
) -> Iterable[int]:
    return [secrets.choice(alphabet) for _ in range(leninght)]

def save(
    notepad: Iterable,
    name: str | None = None
) -> None:
    if name is None:
        name = "notepad"

    path = os.path.join("data", f"{name}.json")
    id = 0

    data = {
        "id": id,
        "values": notepad,
    }
    count = 1

    while os.path.isfile(path):
        path = os.path.join("data", f"{name}{id}.json")
        count += 1

    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    notepad = generate_notepad(type="num", leninght=12456)
    save(notepad)