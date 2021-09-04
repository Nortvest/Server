import sqlite3


class DataBasePassword:
    def __init__(self):
        self.__connect = sqlite3.connect('user_data.db')
        self.__cursor = self.__connect.cursor()

    def get_user_password(self, name):
        self.__cursor.execute(f'SELECT password FROM user_passwords WHERE name = "{name}"')
        data = self.__cursor.fetchone()
        return data and data[0] or False

    def set_new_user(self, name, password):
        self.__cursor.execute('INSERT INTO user_passwords(name, password) VALUES (?, ?)', (name, password))
        self.__connect.commit()

    def close(self):
        self.__connect.close()
