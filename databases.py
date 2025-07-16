import psycopg2


# Исключения возникающие при работе с БД
class DBException(Exception):
    pass

# Ошибка подключения к БД
class ConnectionError(DBException):
    def __init__(self, i_name):
        self.message = f"DB '{i_name}' connection error"

# Ошибка при запросе к БД
class QueryError(DBException):
    def __init__(self):
        self.message = f"DB query error"

# Ошибка создания БД
class DBCreateError(DBException):
    def __init__(self):
        self.message = f"DB create error"


class PostgreSQL:
    def __init__(self):
        pass

    #Подключение к серверу PostgreSQL
    def connection(self, i_name, i_user, i_password, i_host, i_port):
        connection = None
        try:
            connection = psycopg2.connect(
                database=i_name,
                user=i_user,
                password=i_password,
                host=i_host,
                port=i_port,
            )
            print("Connection to PostgreSQL DB successful")
            return connection
        except Exception:
            raise ConnectionError(i_name)

    # Создание базы данных
    def create_db(self, connection, query):
        cursor = connection.cursor()
        try:
            cursor.execute(query)
            print("Query executed successfully")
            connection.commit()
            cursor.close()
        except Exception:
            cursor.close()
            raise DBCreateError()

    # Запрос к базе данных (для создания/изменения/удаления)
    def execute_query(self, connection, query, vars=()):
        cursor = connection.cursor()
        try:
            cursor.execute(query, vars) #Параметр передается строго кортежем, либо списком кортежей
            connection.commit()
            cursor.close()
            print("Query executed successfully")
        except Exception:
            cursor.close()
            raise QueryError()

    # Запрос к базе данных (для чтения)
    def execute_read_query(self, connection, query, vars=()):
        cursor = connection.cursor()
        try:
            cursor.execute(query, vars) #Параметр передается строго кортежем, либо списком кортежей
            result = cursor.fetchall()
            cursor.close()
            return result
        except Exception:
            cursor.close()
            raise QueryError()
