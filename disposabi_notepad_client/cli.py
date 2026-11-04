from .client import Client
from .config import Config

class CLI:
    def __init__(self, client: Client, config: Config):
        self.client = client
        self.config = config

        self.running = True

    def main(self) -> None: 
        if self.config.first_launch:
            self.first_launch()

        self.switch_user()
        while self.running:
            self.menu()

    def switch_user(self) -> None:
        accounts = self.client.get_accounts()

        if accounts is None:
            self.create_user()
            return self.switch_user()
            
        if len(accounts.accounts) == 1:
            user_local_id = accounts.accounts[0].id
        else:
            print("Выберите аккаунт")

            for i, acc in enumerate(accounts.accounts):
                print(f"{i}) {acc.user_name}: {acc.user_id}")

            acc_index = int(input("Ваш выбор: "))

            user_local_id = accounts.accounts[acc_index].id

        self.client.open_session(user_local_id)

    def first_launch(self):
        self.create_user()
        

    def create_user(self): 
        print("Создения пользавателя")
        name = input("Введите имя: ")

        self.client.create_user(name=name)

    def display_menu(self) -> None:
        print("Меню:")
        print("1) Написать сообщения")
        print("2) Проверить сообщения")
        print("3) Сменить пользавателя")
        print("4) Создать пользавателя")
        print("0) Выход")

    def menu(self) -> None:
        menu_actions = {
            "1": self.send_message, 
            "2": self.check_messages,
            "3": self.switch_user,
            "4": self.create_user,
            "0": lambda: setattr(self, "running", False)
        }
        self.display_menu()

        action = input("Выбор: ")

        menu_actions[action]()

    def send_message(self):
        recipient_id = input("id получателя: ")
        text = input("текст: ")

        self.client.send_message(
            text=text, 
            recipient_id=recipient_id
        )

    def check_messages(self): 
        messages = self.client.check_messages()
        if messages is None:
            print("Вам не приходило сообщений")
            return

        print("Сообщения: ")
        for msg in messages.messages:
            print(f"=== от: {msg.sender_id}\n{msg.text}\n")