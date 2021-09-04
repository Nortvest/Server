import socket
from socket import SOL_SOCKET, SO_REUSEADDR
import asyncio


class Socket:
    """Класс-шаблон для сервера и клтента"""
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.main_loop = asyncio.get_event_loop()

    def bind_connect(self, ip, host):
        raise NotImplementedError

    async def listen_(self, username=None):
        raise NotImplementedError

    async def start_task(self):
        raise NotImplementedError

    def run(self):
        self.main_loop.run_until_complete(self.start_task())
