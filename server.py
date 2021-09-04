from Socket import Socket
from SignIn import DataBasePassword
import hashlib
import loguru
import rich


class TextColors:
    """Класс цретов для терминала"""
    OKBLUE = '\033[94m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    WARNING = '\033[93m'


class Server(Socket):
    """Класс сервера"""
    __USER = list()
    __unauthorized_users = list()
    __name_users = dict()

    def bind_connect(self, ip, host):
        """Создание и настройка сокета"""
        self.socket.bind((ip, host))
        self.socket.setblocking(False)
        self.socket.listen()
        print('Server is starting')

    async def __admin_send(self, data):
        """Отправка служебного сообщения"""
        for user in self.__USER:
            await self.main_loop.sock_sendall(
                user,
                f'\r{TextColors.ENDC}{data.decode("utf-8")}\n'
                f'{TextColors.BOLD}{TextColors.WARNING}->{TextColors.ENDC}{TextColors.BOLD} '.encode('utf-8')
            )

    async def __send_data(self, data, own_user):
        """Отправка сообщения польвователям"""
        if not data:
            return
        users_copy = self.__USER.copy()
        users_copy.remove(own_user)
        users_copy = tuple(set(users_copy) - set(self.__unauthorized_users))
        for user in users_copy:
            await self.main_loop.sock_sendall(
                user,
                f'\r{TextColors.ENDC}{TextColors.OKBLUE}{self.__name_users[own_user]}: '
                f'{TextColors.ENDC} {data.decode("utf-8")}\n'
                f'{TextColors.BOLD}{TextColors.WARNING}->{TextColors.ENDC}{TextColors.BOLD} '.encode('utf-8')
            )

    async def listen(self, username=None):
        """Прослушка клиента"""
        while True:
            data = await self.main_loop.sock_recv(username, 1024)
            print(f'{self.__name_users[username]}: {data.decode("utf-8")}')
            if not data:
                self.__USER.remove(username)
                return
            if data.decode('utf-8').startswith('/'):
                await self.__commands_handler(username, data.decode('utf-8')[1:])
            else:
                await self.__send_data(data, username)

    async def __commands_handler(self, username, command):
        pass

    async def __commands_sing_in(self, username):
        """Обработчик команд sing in"""
        command = await self.main_loop.sock_recv(username, 1024)
        command = command.decode('utf-8')[1:]
        if command.startswith('reg'):
            _, name, password = command.split(':')
            await self.main_loop.sock_sendall(username, self.__registration(name, password).encode('utf-8'))
        elif command.startswith('auth'):
            _, name, password = command.split(':')
            await self.main_loop.sock_sendall(username, self.__authorisation(name, password).encode('utf-8'))
            self.__unauthorized_users.remove(username)
            self.__name_users[username] = name
            await self.listen(username)

    @staticmethod
    def __registration(name, password):
        """Выгрузка в бд"""
        db = DataBasePassword()
        db.set_new_user(name, hashlib.sha224(password.encode('utf-8')).hexdigest())
        db.close()
        return '1'

    @staticmethod
    def __authorisation(name, password):
        """Авторизация"""
        db = DataBasePassword()
        hash_password = db.get_user_password(name)
        db.close()
        if hash_password and hash_password == hashlib.sha224(password.encode('utf-8')).hexdigest():
            return '1'  # Оба return в " для удобной последующей пересылке клиенту
        return '0'

    async def send_logs(self, username=None):
        pass

    async def __accept(self):
        """Присоединение нового пользователя"""
        while True:
            user, address = await self.main_loop.sock_accept(self.socket)
            print(f'{address[0]}:{address[1]} Join the Channel')
            self.__USER.append(user)
            self.__unauthorized_users.append(user)
            self.main_loop.create_task(self.__commands_sing_in(user))

    async def start_task(self):
        """Запуск"""
        await self.main_loop.create_task(self.__accept())


if __name__ == '__main__':
    server = Server()
    try:
        server.bind_connect('127.0.0.1', 9999)
        server.run()
    except KeyboardInterrupt:
        server.socket.close()
