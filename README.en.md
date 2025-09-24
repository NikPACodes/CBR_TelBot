# CBR Telegram Bot

[![RUS](https://img.shields.io/badge/README-Russian-blue.svg)](README.md)
[![ENG](https://img.shields.io/badge/README-English-red.svg)](README.en.md)

A Telegram bot for retrieving data from the official website of the Central Bank of the Russian Federation. The Telegram bot supports currency conversion, exchange rate information, the key rate, and operational information.


## Table of contents
- [CBR Telegram Bot](#cbr-telegram-bot)
  - [Table of contents](#table-of-contents)
  - [Peculiarities](#peculiarities)
  - [Project structure](#project-structure)
  - [DB structure](#db-structure)
    - [Table _Users_](#table-users)
    - [Table _BotUsers_](#table-botusers)
    - [Table _CurrCodesDirectCBR_](#table-currcodesdirectcbr)
    - [Table _ExchangeRatesCBR_](#table-exchangeratescbr)
  - [Installing and running](#installing-and-running)
    - [1. Cloning the repository and installing dependencies](#1-cloning-the-repository-and-installing-dependencies)
    - [2. Setting up configurations _(config.py)_](#2-setting-up-configurations-configpy)
    - [3. Launching the bot](#3-launching-the-bot)
  - [List of commands](#list-of-commands)
    - [Examples of use](#examples-of-use)
  - [Note](#note)
  - [License](#license)
  - [Contributing](#contributing)


## Peculiarities
:exclamation: This bot requires a PostgreSQL database connection to work.
- When the project is launched, the PostgreSQL database structure required for the bot to operate is created  
  ***(if the structure already exists, this step is skipped)***
- The bot works primarily with PostgreSQL data.  
  If information is missing from the database, the bot requests data from the Central Bank of the Russian Federation website and completes the missing information.
- Exchange rate data is filled into the database exclusively upon request (rate, conversion) on the specified date.
- Data on operational information is taken exclusively from the Central Bank website, without being stored in the database, and is a link to the corresponding source.


## Project structure
| File                  | Description                                                 |
|-----------------------|-------------------------------------------------------------|
| config.py             | Configuration: bot token and database connection parameters |
| databases.py          | Connecting and working with a PostgreSQL database           |
| CBR_Exceptions.py     | Class for exception handling                                |
| extensions.py         | Basic functionality, parsing, and working with the API      |
| requirements.txt      | List of dependencies                                        |
| structure_database.py | Creating a DB structure                                     |
| run.py                | Launching the bot, command handlers, keyboards              |
| README.md             | Documentation in Russian                                    |
| README.en.md          | Documentation in English                                    |
| .gitignore            | Ignoring temporary files                                    |
| LICENSE               | License                                                     |


## DB structure
|Table                | Name                                |
|---------------------|-------------------------------------|
| Users               | Users                               |
| BotUsers            | Connection between a bot and a user |
| CurrCodesDirectCBR  | Currency codes                      |
| ExchangeRatesCBR    | Exchange rates                      |

<p align="left">
 <img src="pictures/DB.png" alt="DB" width="450px"/>
</p>


### <u>Table _Users_</u>
  |Field        | Name                  |
  |-------------|-----------------------|
  | ID          | User ID               |
  | UserName    | Telegram user         |
  | First_Name  | First name            |
  | Last_Name   | Last name             |
  | Status      | Status (for blocking) |

### <u>Table _BotUsers_</u>
  |Field                | Name                   |
  |---------------------|------------------------|
  | BotID               | Bot ID                 |
  | UserID              | User ID                |
  | DateTimeReg         | User registration date |
  | DateTimeLastActive  | Last user activity     |

### <u>Table _CurrCodesDirectCBR_</u>
  |Field      | Name                    |
  |-----------|-------------------------|
  | ID_CBR    | CB Currency ID          |
  | ISO_num   | ISO Currency ID         |
  | ISO_code  | ISO currency codes      |
  | NameEng   | Currency name (English) | 
  | NameRus   | Currency name (Russian) | 

### <u>Table _ExchangeRatesCBR_</u>
  |Field       | Name                      |
  |-----------|----------------------------|
  | ID_CBR    | CB Currency ID             |
  | Date      | Exchange rate date         |
  | CurrRate  | Exchange rate to the ruble |


## Installing and running

### 1. Cloning the repository and installing dependencies:
    git clone https://github.com/NikPACodes/CBR_TelBot.git
    cd CBR_TelBot
    pip install -r requirements.txt

or for further development in your own repository, create [Fork](https://github.com/NikPACodes/CBR_TelBot/fork)

    git clone https://github.com/yourusername/CBR_TelBot.git
    cd CBR_TelBot
    pip install -r requirements.txt

### 2. Setting up configurations _(config.py)_
- You need to fill the `config.py` file with your own data:
  ```
  # Личный токен телеграмм
  TOKEN = '*****'

  # Параметры для подключения БД
  DB_NAME     = '*****'
  DB_USER     = '*****'
  DB_PASSWORD = '*****'
  DB_HOST     = '*****'
  DB_PORT     = '*****'
  ```

  |Parameter      | Description                 |
  |---------------|-----------------------------|
  | _TOKEN_       | Telegram bot personal token |
  | _DB_NAME_     | Database name               |
  | _DB_USER_     | Database user               |
  | _DB_PASSWORD_ | Password                    |
  | _DB_HOST_     | Host                        |
  | _DB_PORT_     | Port                        |


### 3. Launching the bot
    python run.py


## List of commands
1) ***/help*** - List of available commands 
2) ***/current_codes*** - Directory of available currency codes
3) ***/find_name_code*** - Search for currency code by name
4) ***/oper_info*** - Operational information  
  (by category: "Monetary Policy", "Bank of Russia Decisions", "Statistics", "Analytics", "Database", "Research")
1) ***/convert*** - Currency converter
2) ***/current_rate*** - CB exchange rate
3) ***/key_rate*** - Key rate of the CB

### Examples of use
- **/find_name_code**  
  ```Примеры: RUB, rub, рубл```

- **/convert**  
  ```
  Примеры (по умолчанию USD/RUB):
  1) 100 - конвертация USD в RUB
  2) 100 EUR - конвертация EUR в RUB
  3) 1000 USD/EUR - конвертация USD в EUR
  4) 01.01.2001 1000 EUR - конвертация EUR в RUB по курсу 01.01.2001
  5) 01.01.2001 1000 USD/EUR - конвертация USD в EUR по курсу 01.01.2001
  ```

- **/current_rate**
  ```
  Пример (по умолчанию на последнюю доступную дату):
  1) USD - курс USD к RUB
  2) USD/EUR - курс USD к EUR
  3) 01.01.2001 USD - курс USD к RUB на указанную дату
  4) Все или ALL - вывести курсы всех валют к RUB
  ```


## Note
The main goal of this bot is to create a template for the further implementation of more complex projects with more interesting functionality.  
In the future, the functionality of this template will be expanded in terms of:
- Adding support for other databases (MySQL, Redis)
- Adding notifications
- Checking statuses and automatically blocking users
- Logging software operation
- Improvements to database update automation
- Addition Mini Apps


## License
MIT License - feel free to use, modify, and distribute this work as long as you give credit to the author.


## Contributing
1. Any improvements are welcome, from bug fixes to new features!
2. Before pushing, make sure your changes don't break core functionality.
3. Create a pull request or [issues](https://github.com/NikPACodes/CBR_TelBot/issues) for discussion.
4. To develop your own project or use it as a template, create a [Fork](https://github.com/NikPACodes/CBR_TelBot/fork) to your repository.
