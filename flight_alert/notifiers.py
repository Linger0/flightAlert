from collections.abc import Iterable
from typing import Protocol

import requests


class Notifier(Protocol):
    def send(self, title: str, content: str) -> None:
        ...


class ConsoleNotifier:
    def send(self, title: str, content: str) -> None:
        print(title)
        print(content)


class ServerChanNotifier:
    def __init__(self, tokens: Iterable[str], timeout: int = 20) -> None:
        self.tokens = [token for token in tokens if token]
        self.timeout = timeout

    def send(self, title: str, content: str) -> None:
        send_data = {"title": title, "content": content}
        for token in self.tokens:
            response = requests.post(
                f"https://sctapi.ftqq.com/{token}.send",
                data=send_data,
                timeout=self.timeout,
            )
            response.raise_for_status()
