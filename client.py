from Socket import Socket
import sys
from aioconsole import ainput
import asyncio
import rich


class TextColors:
    """Класс цретов для терминала"""
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    WARNING = '\033[93m'


class Client(Socket):
    """Класс клиента"""

    def bind_connect(self, ip, host):
        self.socket.connect((ip, host))
        self.socket.setblocking(False)

    async def listening(self, username=None):
        """Прослушивание сервера"""
        while True:
            data = await self.main_loop.sock_recv(self.socket, 1024)
            print(data.decode('utf-8'), end='')
            if not data:
                sys.exit()

    async def send_to_server(self):
        """Отправка пакетов на сервер"""
        while True:
            data = await ainput(f'{TextColors.BOLD}{TextColors.WARNING}->{TextColors.ENDC}{TextColors.BOLD} ')
            if data:
                await self.main_loop.sock_sendall(self.socket, data.encode('utf-8'))

    async def form_sing_in(self, text_name, text_password, prefix):
        """Шаблон для авторизации и регистрации"""
        while True:
            name = await ainput(text_name)
            password = await ainput(text_password)
            if name and password:
                await self.main_loop.sock_sendall(self.socket, f'/{prefix}:{name}:{password}'.encode('utf-8'))
                request = await self.main_loop.sock_recv(self.socket, 1024)
                request = int(request.decode('utf-8'))
                if request:
                    await self.main_loop.sock_sendall(self.socket, f'1'.encode('utf-8'))
                    return
                else:
                    await self.main_loop.sock_sendall(self.socket, f'0'.encode('utf-8'))
                    print('Login or Password is invalid\n')

    async def authorisation(self):
        """Авторизация на сервере"""
        await self.form_sing_in('Name: ', 'Password: ', 'auth')
        await asyncio.gather(self.main_loop.create_task(self.send_to_server()),
                             self.main_loop.create_task(self.listening()))

    async def registration(self):
        """Регистрация на сервере"""
        await self.form_sing_in('Create name: ', 'Create password: ', 'reg')
        await self.authorisation()

    async def start_task(self):
        """Запуск"""
        data = None
        while not (data in ('1', '2')):
            print('\t[1] -- Authorisation\n\t[2] -- Registration')
            data = await ainput()
            if data == '1':
                await self.authorisation()
            elif data == '2':
                await self.registration()
            else:
                print('You can write "1" or "2"', end='\n\n')


if __name__ == '__main__':
    client = Client()
    try:
        client.bind_connect('127.0.0.1', 9999)
        client.run()
    except (Exception, KeyboardInterrupt)as ex:
        print(ex)
        print('\nBye!')
        sys.exit()
