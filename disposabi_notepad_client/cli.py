from __future__ import annotations

import time
from typing import Optional

from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import (
    Button, Footer, Header, Input, Label, ListItem, ListView, Static,
)

from .schemas import user, message


def _fmt_time(ts: int | None) -> str:
    if not ts:
        return "--:--:--"
    return time.strftime("%H:%M:%S", time.localtime(ts))


def _format_exception(e: BaseException) -> str:
    status = (
        getattr(e, "status_code", None)
        or getattr(getattr(e, "response", None), "status_code", None)
    )
    return f"HTTP {status}: {e}" if status is not None else f"{type(e).__name__}: {e}"


class AccountItem(ListItem):
    def __init__(self, account: user.Account) -> None:
        super().__init__()
        self.account = account

    def compose(self) -> ComposeResult:
        yield Label(f"#{self.account.id}  {self.account.user_name}")


class ChatItem(ListItem):
    def __init__(self, chat: dict) -> None:
        super().__init__()
        self.peer_id = chat["peer_id"]
        self.preview = chat.get("last_text", "")

    def compose(self) -> ComposeResult:
        yield Label(f"#{self.peer_id}  {self.preview[:30]}")


class AccountSelectScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="login-wrapper"):
            with Vertical(id="login-container"):
                yield Label("Выберите аккаунт", id="login-title")
                yield ListView(id="accounts")
                yield Label("— или создайте новый —", classes="hint")
                yield Input(placeholder="Имя нового аккаунта", id="new-name")
                yield Button("Создать аккаунт", id="create-btn", variant="primary")
        yield Footer()

    def on_mount(self) -> None:
        self.app.title = "Мессенджер"
        self.refresh_accounts()

    @work(exclusive=True, group="accounts")
    async def refresh_accounts(self) -> None:
        lv = self.query_one("#accounts", ListView)
        lv.clear()
        try:
            accounts: Optional[user.Accounts] = await self.app.client.get_accounts()
        except Exception as e:
            self.app.notify(_format_exception(e), severity="error", title="Ошибка аккаунтов")
            return

        if not accounts or not accounts.accounts:
            lv.append(ListItem(Label("Нет аккаунтов")))
            return

        for acc in accounts.accounts:
            lv.append(AccountItem(acc))

    @on(Button.Pressed, "#create-btn")
    @on(Input.Submitted, "#new-name")
    def create_account(self) -> None:
        inp = self.query_one("#new-name", Input)
        name = inp.value.strip()
        if not name:
            return
        self._create_account(name)

    @work(exclusive=True, group="create-account")
    async def _create_account(self, name: str) -> None:
        try:
            await self.app.client.create_user(name)
        except Exception as e:
            self.app.notify(_format_exception(e), severity="error", title="Ошибка создания")
            return
        self.query_one("#new-name", Input).value = ""
        self.refresh_accounts()

    @on(ListView.Selected, "#accounts")
    def choose_account(self, event: ListView.Selected) -> None:
        if isinstance(event.item, AccountItem):
            acc = event.item.account
            self.app.enter_account(acc.id, acc.user_name)


class MainScreen(Screen):
    BINDINGS = [
        ("ctrl+r", "refresh", "Обновить"),
        ("ctrl+m", "check_msgs", "Проверить"),
        ("ctrl+l", "logout", "Сменить аккаунт"),
    ]

    def __init__(self, account_id: int, account_name: str) -> None:
        super().__init__()
        self.user_id = account_id
        self.user_name = account_name
        self.peer_id: Optional[int] = None

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            with Vertical(id="left-panel"):
                yield Label("Чаты", classes="panel-title")
                with Horizontal(id="top-buttons"):
                    yield Button("Обновить", id="refresh-btn")
                    yield Button("Проверить", id="check-msgs-btn", variant="warning")
                yield ListView(id="chat-list")
                yield Label("Новый чат по ID:", classes="hint")
                yield Input(placeholder="ID + Enter", id="new-chat-input")
            with Vertical(id="right-panel"):
                yield Label("Чат не выбран", id="chat-header")
                yield VerticalScroll(id="messages")
                with Horizontal(id="input-row"):
                    yield Input(placeholder="Сообщение...", id="message-input", disabled=True)
                    yield Button("Отправить", id="send-btn", variant="primary", disabled=True)
        yield Footer()

    def on_mount(self) -> None:
        self.app.title = f"Мессенджер — {self.user_name}"
        self.refresh_chats()

    @on(Button.Pressed, "#refresh-btn")
    def _refresh_btn(self) -> None:
        self.refresh_chats()

    @work(exclusive=True, group="chats")
    async def refresh_chats(self) -> None:
        try:
            chats = await self.app.client.get_chats()
        except Exception as e:
            self.app.notify(_format_exception(e), severity="error")
            return
        self._apply_chats(chats)

    def _apply_chats(self, chats: list[dict]) -> None:
        lv = self.query_one("#chat-list", ListView)
        lv.clear()
        for c in chats:
            lv.append(ChatItem(c))

    @on(ListView.Selected, "#chat-list")
    def _choose_chat(self, event: ListView.Selected) -> None:
        if isinstance(event.item, ChatItem):
            self.open_chat(event.item.peer_id)

    def open_chat(self, peer_id: int) -> None:
        self.peer_id = peer_id
        self.query_one("#chat-header", Label).update(f"Чат с #{peer_id}")
        self.query_one("#message-input", Input).disabled = False
        self.query_one("#send-btn", Button).disabled = False
        self.query_one("#message-input", Input).focus()
        self.load_history()

    @work(exclusive=True, group="history")
    async def load_history(self) -> None:
        if self.peer_id is None:
            return
        peer_id = self.peer_id
        try:
            history = await self.app.client.get_chat_history(peer_id)
        except Exception as e:
            self.app.notify(_format_exception(e), severity="error")
            return
        self._apply_history(peer_id, history)

    def _apply_history(self, peer_id: int, history: list[message.HistoryMessage]) -> None:
        if peer_id != self.peer_id:
            return
        container = self.query_one("#messages", VerticalScroll)
        container.remove_children()
        for m in history:
            ts = _fmt_time(m.time)
            if m.sender_id == self.user_id:
                container.mount(self._bubble(f"[green]→[/] {m.text}", ts, True))
            else:
                container.mount(self._bubble(f"[blue]←[/] {m.text}", ts, False))
        container.scroll_end(animate=False)

    def _bubble(self, text: str, ts: str, outgoing: bool) -> Static:
        align = "right" if outgoing else "left"
        return Static(f"[dim]{ts}[/] {text}", classes=f"msg {align}")

    @on(Input.Submitted, "#new-chat-input")
    def _new_chat(self) -> None:
        inp = self.query_one("#new-chat-input", Input)
        try:
            peer_id = int(inp.value.strip())
        except ValueError:
            return
        inp.value = ""
        self._check_user(peer_id)

    @work(group="check-user")
    async def _check_user(self, peer_id: int) -> None:
        try:
            exists = await self.app.client.is_user_exists(peer_id)
        except Exception as e:
            self.app.notify(_format_exception(e), severity="error")
            return
        if not exists:
            self.app.notify(f"#{peer_id} не найден", severity="warning")
            return
        self.open_chat(peer_id)

    @on(Button.Pressed, "#send-btn")
    @on(Input.Submitted, "#message-input")
    def send_current(self) -> None:
        if self.peer_id is None:
            return
        inp = self.query_one("#message-input", Input)
        text = inp.value.strip()
        if not text:
            return
        inp.value = ""
        self._send_worker(text, self.peer_id)

    @work(group="send")
    async def _send_worker(self, text: str, recipient_id: int) -> None:
        try:
            await self.app.client.send_message(text, recipient_id)
        except Exception as e:
            self.app.notify(_format_exception(e), severity="error")
            return
        self._on_send_ok(text, recipient_id)

    def _on_send_ok(self, text: str, recipient_id: int) -> None:
        if recipient_id == self.peer_id:
            self._append_bubble(text, int(time.time()), True)
        self.query_one("#message-input", Input).focus()
        self.refresh_chats()

    def _append_bubble(self, text: str, ts: int, outgoing: bool) -> None:
        container = self.query_one("#messages", VerticalScroll)
        container.mount(self._bubble(f"[green]→[/] {text}" if outgoing else f"[blue]←[/] {text}", _fmt_time(ts), outgoing))
        container.scroll_end(animate=False)

    def action_check_msgs(self) -> None:
        self._check_msgs_worker()

    @on(Button.Pressed, "#check-msgs-btn")
    def _check_btn(self) -> None:
        self._check_msgs_worker()

    @work(exclusive=True, group="check-msgs")
    async def _check_msgs_worker(self) -> None:
        try:
            msgs: list[message.Message] = await self.app.client.check_messages()
        except Exception as e:
            self.app.notify(_format_exception(e), severity="error")
            return
        self._on_msgs(msgs)

    def _on_msgs(self, msgs: list[message.Message]) -> None:
        if not msgs:
            self.app.notify("Новых сообщений нет")
            return
        self.app.notify(f"Получено: {len(msgs)}")
        if self.peer_id is not None:
            self.load_history()
        self.refresh_chats()

    def action_refresh(self) -> None:
        self.refresh_chats()
        if self.peer_id is not None:
            self.load_history()

    def action_logout(self) -> None:
        self.app.switch_screen(AccountSelectScreen())


class MessengerApp(App):
    CSS = """
    Screen { background: $surface; }
    #login-wrapper { width: 1fr; height: 1fr; align: center middle; }
    #login-container { width: 60; height: auto; padding: 2 3; border: thick $primary; background: $panel; }
    #login-title { text-style: bold; text-align: center; width: 100%; margin-bottom: 1; }
    #accounts { height: 12; margin-bottom: 1; }
    .hint { color: $text-muted; margin: 1 0; }
    .panel-title { text-style: bold; padding: 1 0; }
    #left-panel { width: 38; border-right: solid $primary; padding: 0 1; }
    #right-panel { width: 1fr; padding: 0 1; }
    #top-buttons { height: auto; }
    #top-buttons Button { width: 1fr; margin: 0 1 0 0; }
    #chat-list { height: 1fr; border: solid $primary; }
    #chat-header { text-style: bold; padding: 1 0; }
    #messages { height: 1fr; border: solid $accent; padding: 0 1; }
    .msg { width: auto; margin: 0 0 1 0; }
    .msg.right { text-align: right; }
    .msg.left { text-align: left; }
    #input-row { height: 3; margin-top: 1; }
    #message-input { width: 1fr; }
    """

    def __init__(self, client) -> None:
        super().__init__()
        self.client = client

    def on_mount(self) -> None:
        self.push_screen(AccountSelectScreen())

    @work(exclusive=True, group="enter")
    async def enter_account(self, account_id: int, account_name: str) -> None:
        try:
            await self.client.open_session(account_id)
        except Exception as e:
            self.notify(_format_exception(e), severity="error", title="Ошибка входа")
            return
        self.switch_screen(MainScreen(account_id, account_name))


async def run(client) -> None:
    await MessengerApp(client).run_async()
