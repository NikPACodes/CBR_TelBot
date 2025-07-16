import databases
from databases import PostgreSQL

#Таблица пользователей
create_Users_table = """
CREATE TABLE IF NOT EXISTS users (
  id BIGSERIAL PRIMARY KEY,
  username VARCHAR(50) NOT NULL,
  first_name VARCHAR(50),
  last_name VARCHAR(50),
  status VARCHAR(1)
);
"""

#Таблица связи бота и пользователей
create_BotUsers_table = """
CREATE TABLE IF NOT EXISTS BotUsers (
  BotID BIGSERIAL,
  UserID BIGSERIAL REFERENCES users (id), 
  DateTimeReg TIMESTAMP NOT NULL,
  DateTimeLastActive TIMESTAMP NOT NULL,
  PRIMARY KEY(BotID, UserID)
);
"""

#Таблица кодов валют
create_CurrCodesDirect_table = """
CREATE TABLE IF NOT EXISTS CurrCodesDirectCBR (
  ID_CBR VARCHAR(10) NOT NULL PRIMARY KEY,
  ISO_num VARCHAR(3) NOT NULL,
  ISO_code VARCHAR(3) NOT NULL,
  NameEng VARCHAR(50),
  NameRus VARCHAR(50)
);
"""

#Таблица курсов валют
create_ExchangeRatesCBR_table = """
CREATE TABLE IF NOT EXISTS ExchangeRatesCBR (
  ID_CBR VARCHAR(10) REFERENCES CurrCodesDirectCBR (ID_CBR),
  Date DATE,
  CurrRate DECIMAL,
  PRIMARY KEY(ID_CBR, Date)
);
"""

# Создание структуры БД
def create_structure_database(i_Name, i_User, i_Password, i_Host, i_Post):
    conectDB = None
    PostgresDB = PostgreSQL()
    try:
        conectDB = PostgresDB.connection(i_Name, i_User, i_Password, i_Host, i_Post) #Подключаемся к БД
    except databases.DBException as err:
        print(err.message)

    if conectDB is not None:
        try:
            PostgresDB.execute_query(conectDB, create_Users_table)
        except databases.DBException as err:
            print('Ошибка создания таб."users"')

        try:
            PostgresDB.execute_query(conectDB, create_BotUsers_table)
        except databases.DBException as err:
            print('Ошибка создания таб."BotUsers"')

        try:
            PostgresDB.execute_query(conectDB, create_CurrCodesDirect_table)
        except databases.DBException as err:
            print('Ошибка создания таб."CurrCodesDirect"')

        try:
            PostgresDB.execute_query(conectDB, create_ExchangeRatesCBR_table)
        except databases.DBException:
            print('Ошибка создания таб."ExchangeRatesCBR"')

        conectDB.close()