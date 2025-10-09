# Создаю полный гайд по развертыванию бота на Windows
windows_deployment_guide = '''
# 🚀 ПОЛНЫЙ ГАЙД ПО РАЗВЕРТЫВАНИЮ СПОРТИВНОГО БОТА НА WINDOWS

## 📋 СОДЕРЖАНИЕ
1. [Предварительные требования](#предварительные-требования)
2. [Установка Python](#установка-python)
3. [Установка PostgreSQL](#установка-postgresql)
4. [Создание Telegram бота](#создание-telegram-бота)
5. [Настройка проекта](#настройка-проекта)
6. [Импорт базы данных](#импорт-базы-данных)
7. [Установка зависимостей](#установка-зависимостей)
8. [Конфигурация бота](#конфигурация-бота)
9. [Запуск системы](#запуск-системы)
10. [Тестирование функций](#тестирование-функций)
11. [Решение проблем](#решение-проблем)

---

## 1. 📱 ПРЕДВАРИТЕЛЬНЫЕ ТРЕБОВАНИЯ

### Системные требования:
- **OS:** Windows 10/11 (x64)
- **RAM:** Минимум 4 ГБ (рекомендуется 8+ ГБ)
- **Место:** 2+ ГБ свободного места
- **Интернет:** Стабильное подключение

### Что вам понадобится:
- ✅ Telegram аккаунт для создания бота
- ✅ Права администратора на компьютере
- ✅ Базовые знания командной строки

---

## 2. 🐍 УСТАНОВКА PYTHON

### Шаг 1: Скачивание Python
1. Перейдите на https://www.python.org/downloads/
2. Скачайте **Python 3.11 или выше** (рекомендуется 3.11.x)
3. Выберите **Windows installer (64-bit)**

### Шаг 2: Установка Python
1. Запустите скачанный файл `python-3.11.x-amd64.exe`
2. ⚠️ **ВАЖНО:** Поставьте галочку "Add Python to PATH"
3. Выберите "Install Now"
4. Дождитесь завершения установки

### Шаг 3: Проверка установки
Откройте **Командную строку** (cmd) и выполните:
```bash
python --version
```
Должно показать версию Python (например, Python 3.11.5)

```bash
pip --version
```
Должно показать версию pip

---

## 3. 🐘 УСТАНОВКА POSTGRESQL

### Шаг 1: Скачивание PostgreSQL
1. Перейдите на https://www.postgresql.org/download/windows/
2. Скачайте **PostgreSQL 15 или 16** для Windows x86-64
3. Выберите установщик от EnterpriseDB

### Шаг 2: Установка PostgreSQL
1. Запустите скачанный файл `postgresql-16.x-windows-x64.exe`
2. Следуйте мастеру установки:
   - **Компоненты:** Оставьте все по умолчанию
   - **Каталог данных:** Оставьте по умолчанию
   - **Пароль суперпользователя:** Придумайте и **ЗАПОМНИТЕ** пароль для postgres
   - **Порт:** Оставьте 5432
   - **Локаль:** Оставьте по умолчанию

### Шаг 3: Проверка установки
1. Откройте **SQL Shell (psql)** из меню "Пуск"
2. Нажмите Enter для всех вопросов (оставьте defaults)
3. Введите пароль, который задавали при установке
4. Выполните команду:
```sql
SELECT version();
```

---

## 4. 🤖 СОЗДАНИЕ TELEGRAM БОТА

### Шаг 1: Создание бота через BotFather
1. Откройте Telegram
2. Найдите бота **@BotFather**
3. Отправьте команду `/newbot`
4. Введите название бота (например: `МойСпортБот`)
5. Введите username бота (должен заканчиваться на `bot`, например: `mysportbot_bot`)

### Шаг 2: Получение токена
1. BotFather даст вам **TOKEN** вида: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`
2. **СОХРАНИТЕ ЭТОТ ТОКЕН** - он понадобится для настройки!

### Шаг 3: Настройка бота (опционально)
```
/setdescription - установить описание бота
/setabouttext - установить текст "О боте"
/setuserpic - установить аватар бота
/setcommands - установить список команд
```

---

## 5. 📁 НАСТРОЙКА ПРОЕКТА

### Шаг 1: Создание папки проекта
1. Создайте папку на диске C: `C:\\SportBot`
2. Откройте **Командную строку** как администратор
3. Перейдите в папку проекта:
```bash
cd C:\\SportBot
```

### Шаг 2: Создание виртуального окружения
```bash
python -m venv venv
```

### Шаг 3: Активация виртуального окружения
```bash
venv\\Scripts\\activate
```
В командной строке должно появиться `(venv)` в начале строки.

### Шаг 4: Структура проекта
Создайте следующие папки и файлы:
```
C:/SportBot/
├── venv/                    # Виртуальное окружение
├── app/                     # Основной код бота
│   ├── __init__.py
│   ├── main.py             # Главный файл бота
│   ├── config.py           # Конфигурация
│   ├── database.py         # Работа с БД
│   └── modules/            # Модули бота
│       ├── __init__.py
│       ├── exercise_search.py
│       ├── one_rm.py
│       ├── workout_system.py
│       └── team_management.py
├── sql/                    # SQL скрипты
│   ├── schema.sql          # Схема БД
│   └── initial_data.sql    # Начальные данные
├── requirements.txt        # Зависимости Python
├── .env                    # Переменные окружения
└── run.bat                 # Скрипт запуска
```

---

## 6. 💾 ИМПОРТ БАЗЫ ДАННЫХ

### Шаг 1: Создание базы данных
1. Откройте **SQL Shell (psql)**
2. Подключитесь как postgres
3. Создайте базу данных:
```sql
CREATE DATABASE sportbot_db;
```
4. Создайте пользователя для бота:
```sql
CREATE USER sportbot_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE sportbot_db TO sportbot_user;
```
5. Выйдите из psql: `\\q`

### Шаг 2: Импорт схемы
Создайте файл `C:\\SportBot\\sql\\schema.sql` с полной схемой БД:

```sql
-- Скопируйте сюда содержимое всех файлов схемы:
-- 1. bot_database_schema.sql
-- 2. enhanced_workout_schema.sql  
-- 3. workout_execution_schema.sql
-- 4. team_management_schema.sql
-- 5. enhanced_team_schema.sql
```

### Шаг 3: Применение схемы
```bash
cd C:\\SportBot
psql -U sportbot_user -d sportbot_db -f sql\\schema.sql
```

---

## 7. 📦 УСТАНОВКА ЗАВИСИМОСТЕЙ

### Шаг 1: Создание requirements.txt
Создайте файл `C:\\SportBot\\requirements.txt`:

```txt
aiogram==3.10.0
asyncpg==0.29.0
python-dotenv==1.0.0
redis==5.0.0
aiofiles==23.2.1
pytz==2023.3
sqlalchemy==2.0.23
alembic==1.12.1
pydantic==2.4.2
fastapi==0.104.1
uvicorn==0.24.0
pandas==2.1.3
numpy==1.25.2
matplotlib==3.8.1
seaborn==0.13.0
plotly==5.17.0
Pillow==10.1.0
qrcode==7.4.2
openpyxl==3.1.2
python-multipart==0.0.6
```

### Шаг 2: Установка зависимостей
```bash
cd C:\\SportBot
venv\\Scripts\\activate
pip install -r requirements.txt
```

---

## 8. ⚙️ КОНФИГУРАЦИЯ БОТА

### Шаг 1: Создание файла .env
Создайте файл `C:\\SportBot\\.env`:

```env
# Telegram Bot Settings
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz  # Ваш токен от BotFather
WEBHOOK_URL=  # Оставьте пустым для polling

# Database Settings
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=sportbot_db
DATABASE_USER=sportbot_user
DATABASE_PASSWORD=your_secure_password

# Redis Settings (опционально)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Application Settings
DEBUG=True
LOG_LEVEL=INFO
MAX_CONNECTIONS=100

# Admin Settings
ADMIN_USER_IDS=123456789  # Ваш Telegram ID (можете узнать у @userinfobot)

# File Upload Settings
MAX_FILE_SIZE=50  # MB
UPLOAD_DIR=uploads/

# Security
SECRET_KEY=your_very_secret_key_here_change_in_production
```

### Шаг 2: Создание config.py
Создайте файл `C:\\SportBot\\app\\config.py`:

```python
import os
from typing import List
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

class Config:
    # Telegram Bot
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    WEBHOOK_URL: str = os.getenv("WEBHOOK_URL", "")
    
    # Database
    DATABASE_HOST: str = os.getenv("DATABASE_HOST", "localhost")
    DATABASE_PORT: int = int(os.getenv("DATABASE_PORT", "5432"))
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "sportbot_db")
    DATABASE_USER: str = os.getenv("DATABASE_USER", "sportbot_user")
    DATABASE_PASSWORD: str = os.getenv("DATABASE_PASSWORD", "")
    
    # Application
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Admin
    ADMIN_USER_IDS: List[int] = [
        int(x.strip()) for x in os.getenv("ADMIN_USER_IDS", "").split(",") if x.strip()
    ]
    
    @property
    def database_url(self) -> str:
        return f"postgresql://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"

config = Config()
```

---

## 9. 🚀 ЗАПУСК СИСТЕМЫ

### Шаг 1: Создание главного файла бота
Создайте файл `C:\\SportBot\\app\\main.py`:

```python
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import config

# Импорт всех модулей
from modules.exercise_search import exercise_search_router
from modules.one_rm import enhanced_one_rm_router
from modules.workout_system import enhanced_workout_router
from modules.team_management import enhanced_coach_router
from database import init_database

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    # Инициализация бота и диспетчера
    bot = Bot(token=config.BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Подключение роутеров
    dp.include_router(exercise_search_router)
    dp.include_router(enhanced_one_rm_router)
    dp.include_router(enhanced_workout_router)
    dp.include_router(enhanced_coach_router)
    
    # Инициализация базы данных
    await init_database()
    
    logger.info("🚀 Спортивный бот запущен!")
    
    # Запуск поллинга
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
```

### Шаг 2: Создание скрипта запуска
Создайте файл `C:\\SportBot\\run.bat`:

```batch
@echo off
cd /d C:\\SportBot
call venv\\Scripts\\activate
python app\\main.py
pause
```

### Шаг 3: Запуск бота
1. Дважды щелкните на `run.bat`
2. Или в командной строке:
```bash
cd C:\\SportBot
venv\\Scripts\\activate
python app\\main.py
```

---

## 10. 🧪 ТЕСТИРОВАНИЕ ФУНКЦИЙ

### Шаг 1: Базовые тесты
1. Найдите вашего бота в Telegram
2. Отправьте `/start`
3. Проверьте регистрацию пользователя
4. Протестируйте основное меню

### Шаг 2: Тесты модулей
- **Поиск упражнений:** Найдите "жим лежа"
- **1ПМ тест:** Протестируйте с любым упражнением
- **Создание тренировки:** Создайте простую тренировку
- **Команда:** Создайте команду и получите код

### Шаг 3: Проверка БД
В psql выполните:
```sql
\\c sportbot_db
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM exercises;
SELECT COUNT(*) FROM workouts;
```

---

## 11. 🔧 РЕШЕНИЕ ПРОБЛЕМ

### Проблема: "Модуль не найден"
**Решение:**
```bash
cd C:\\SportBot
venv\\Scripts\\activate
pip install -r requirements.txt
```

### Проблема: "Ошибка подключения к БД"
**Проверьте:**
1. Запущен ли PostgreSQL (Services → postgresql-x64-16)
2. Правильность данных в `.env`
3. Существует ли база `sportbot_db`

### Проблема: "Invalid bot token"
**Решение:**
1. Проверьте токен в `.env`
2. Создайте нового бота через @BotFather

### Проблема: "Permission denied"
**Решение:**
1. Запустите cmd как администратор
2. Проверьте права на папку проекта

### Проблема: Медленная работа
**Оптимизация:**
1. Добавьте индексы в БД
2. Увеличьте CONNECTION_POOL
3. Используйте Redis для кеширования

---

## 📞 ПОЛУЧЕНИЕ ПОДДЕРЖКИ

### Логи
Все ошибки сохраняются в консоли. Для постоянного логирования добавьте в `main.py`:

```python
import logging
logging.basicConfig(
    filename='bot.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Полезные команды
```bash
# Проверка статуса PostgreSQL
net start postgresql-x64-16

# Перезапуск PostgreSQL  
net stop postgresql-x64-16
net start postgresql-x64-16

# Просмотр процессов Python
tasklist | findstr python

# Завершение процесса
taskkill /f /pid [PID]
```

---

## 🎉 ГОТОВО!

Ваш спортивный бот теперь запущен на Windows и готов к использованию!

### Основные функции:
- ✅ Поиск упражнений и тестов
- ✅ Расчет 1ПМ для любых упражнений  
- ✅ Создание и выполнение тренировок
- ✅ Система RPE для оценки нагрузки
- ✅ Управление командами и подопечными
- ✅ Полная статистика и аналитика

### Следующие шаги:
1. Добавьте упражнения в базу данных
2. Создайте тестовые тренировки
3. Пригласите пользователей для тестирования
4. Настройте автозапуск при старте Windows
5. Рассмотрите деплой на VPS для 24/7 работы

**Удачи с вашим спортивным ботом! 🏋️‍♂️**
'''

print("✅ Создан полный гайд по развертыванию бота на Windows!")
print()
print("📋 ВКЛЮЧАЕТ:")
print("1. 🐍 Установка Python и настройка окружения")
print("2. 🐘 Установка и настройка PostgreSQL") 
print("3. 🤖 Создание Telegram бота через BotFather")
print("4. 📁 Структура проекта и файлы")
print("5. 💾 Импорт схемы базы данных")
print("6. 📦 Установка всех зависимостей")
print("7. ⚙️ Конфигурация и переменные окружения")
print("8. 🚀 Запуск системы")
print("9. 🧪 Тестирование всех модулей")
print("10. 🔧 Решение типичных проблем")

# Сохраняем гайд
with open('WINDOWS_DEPLOYMENT_GUIDE.md', 'w', encoding='utf-8') as f:
    f.write(windows_deployment_guide)

print()
print("📄 Сохранен файл: WINDOWS_DEPLOYMENT_GUIDE.md")
print()
print("🎯 ГОТОВЫЙ ПОШАГОВЫЙ ГАЙД!")
print("Следуйте инструкциям и ваш спортивный бот будет работать на Windows!")
print()
print("💡 ОСНОВНЫЕ ЭТАПЫ:")
print("1. Установить Python 3.11+ с PATH")
print("2. Установить PostgreSQL и создать БД") 
print("3. Создать Telegram бота и получить токен")
print("4. Настроить структуру проекта")
print("5. Импортировать схемы БД")
print("6. Установить зависимости Python")
print("7. Настроить .env файл с токеном и БД")
print("8. Запустить через run.bat")
print()
print("🚀 СИСТЕМА ГОТОВА К ДЕПЛОЮ!")