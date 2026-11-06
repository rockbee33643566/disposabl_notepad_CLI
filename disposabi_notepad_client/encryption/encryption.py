import uuid
import keyring

def _alphabet() -> dict[int, str]:
    alphabet = [" ", ]
    alphabet_let = list(
        chr(i) for i in range(ord("а"), ord("я") + 1)
    )
    alphabet.extend(alphabet_let)

    return dict((ind, let) for ind, let in enumerate(alphabet))

ALPHABET = _alphabet()

def encrypt_text(notepad: list[int], text): 
    if len(notepad) < len(text):
        raise ValueError(
            f"Длина блокнота меньше длины сообщения! notepad_len={len(notepad)}, text_len={len(text)}"
        )
    
def decode(): 
    pass

def get_db_key() -> str | None:
    key = keyring.get_password("database_key", "disposabl_notepad_mess")
    return key

def generate_db_key() -> None:
    if get_db_key() is not None:
        return

    key_hex = str(uuid.uuid4())

    keyring.set_password("database_key", "disposabl_notepad_mess", key_hex)

if __name__ == "__main__": 
    generate_db_key()
    print(get_db_key())