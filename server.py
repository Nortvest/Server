from Socket import Socket
from SignIn import DataBasePassword
import hashlib
from loguru import logger


class TextColors:
    """Класс цретов для терминала"""
    OKBLUE = '\033[94m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    WARNING = '\033[93m'


class Server(Socket):
    """Класс сервера"""
    __unauthorized_users = list()
    __name_users = dict()

    def bind_connect(self, ip, host):
        """Создание и настройка сокета"""
        self.socket.bind((ip, host))
        self.socket.setblocking(False)
        self.socket.listen()
        logger.success('Server is starting')

    async def __admin_send(self, data):
        """Отправка служебного сообщения"""
        for user in self.__name_users.keys():
            await self.main_loop.sock_sendall(
                user,
                f'\r{TextColors.ENDC}{data.decode("utf-8")}\n'
                f'{TextColors.BOLD}{TextColors.WARNING}->{TextColors.ENDC}{TextColors.BOLD} '.encode('utf-8')
            )

    async def __send_data(self, data, own_user):
        """Отправка сообщения польвователям"""
        if not data:
            return
        users_copy = list(self.__name_users.keys())
        users_copy.remove(own_user)
        users_copy = tuple(set(users_copy) - set(self.__unauthorized_users))
        for user in users_copy:
            await self.main_loop.sock_sendall(
                user,
                f'\r{TextColors.ENDC}{TextColors.OKBLUE}{self.__name_users[own_user]}: '
                f'{TextColors.ENDC} {data.decode("utf-8")}\n'
                f'{TextColors.BOLD}{TextColors.WARNING}->{TextColors.ENDC}{TextColors.BOLD} '.encode('utf-8')
            )

    async def listening(self, username=None):
        """Прослушка клиента"""
        logger.success(f'"{self.__name_users[username]}" Join the Channel')
        while True:
            data = await self.main_loop.sock_recv(username, 1024)
            if not data:
                logger.success(f'"{self.__name_users[username]}" Left the Channel')
                self.__name_users.pop(username, None)
                return
            logger.info(f'{self.__name_users[username]}: {data.decode("utf-8")}')
            if data.decode('utf-8').startswith('/'):
                await self.__commands_handler(username, data.decode('utf-8')[1:])
            else:
                await self.__send_data(data, username)

    async def __commands_handler(self, username, command):
        pass

    async def __form_sing_in(self, username):
        command = await self.main_loop.sock_recv(username, 1024)
        command = command.decode('utf-8')[1:]
        if not command:
            return None
        prefix, name, password = command.split(':')
        return prefix, name, password

    @logger.catch()
    async def __commands_sing_in(self, username):
        """Обработчик команд sing in"""
        command = await self.__form_sing_in(username)
        if command is None:
            return None
        prefix, name, password = command
        if prefix == 'reg':
            await self.__command_reg(username, name, password)
        elif prefix == 'auth':
            await self.__command_auth(username, name, password)

    async def __command_reg(self, username, name, password):
        await self.main_loop.sock_sendall(username, self.__registration(name, password).encode('utf-8'))
        answer = await self.main_loop.sock_recv(username, 1024)
        if int(answer.decode('utf-8')):
            await self.__commands_sing_in(username)

    async def __command_auth(self, username, name, password):
        answer = await self.__form_auth(username, name, password)
        if not answer:
            name = await self.__repeat_auth(username)
        self.__unauthorized_users.remove(username)
        self.__name_users[username] = name
        await self.listening(username)

    async def __form_auth(self, username, name, password):
        await self.main_loop.sock_sendall(username, self.__authorisation(name, password).encode('utf-8'))
        answer = await self.main_loop.sock_recv(username, 1024)
        answer = int(answer.decode('utf-8'))
        return answer

    async def __repeat_auth(self, username):
        pnp = await self.__form_sing_in(username)
        if pnp is None:
            return None
        _, name, password = pnp
        answer = await self.__form_auth(username, name, password)
        if not answer:
            name = await self.__repeat_auth(username)
        return name

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

    async def __accept(self):
        """Присоединение нового пользователя"""
        while True:
            user, address = await self.main_loop.sock_accept(self.socket)
            logger.success(f'{address[0]}:{address[1]} Enters the System')
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
