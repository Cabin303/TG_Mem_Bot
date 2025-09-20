# TG Meme Bot 🎭

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://www.python.org/)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-blue?logo=telegram)](https://core.telegram.org/bots)
[![Deploy](https://img.shields.io/badge/Deploy-Railway-purple?logo=railway)](https://railway.app/)

Телеграм-бот-мемогенератор на базе **aiogram v3** и **g4f**.  
Умеет:
- 📸 Генерировать мемы по заданной теме  
- 🧩 Вести общение с памятью по темам  
- 📝 Поддерживать разные роли (стили ответов)  

---

## 🚀 Установка и запуск

1. Клонируем репозиторий:
   ```bash
   git clone https://github.com/yourname/tg-mem-bot.git
   cd tg-mem-bot
   ```

2. Создаём виртуальное окружение и ставим зависимости:
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Linux/Mac
   .venv\Scripts\activate      # Windows

   pip install -r requirements.txt
   ```

3. Создаём `.env` файл:
   ```env
   TOKEN_TG=your_telegram_bot_token
   ```

4. Запуск:
   ```bash
   python TG_mem_bot.py
   ```

---

## ⚙️ Переменные окружения

- `TOKEN_TG` — токен бота от BotFather  
- `G4F_TEXT_TIMEOUT` — таймаут генерации текста (сек), по умолчанию `15`  
- `G4F_IMAGE_TIMEOUT` — таймаут генерации картинки (сек), по умолчанию `20`  

---

## 📖 Команды

- `/start` — запуск бота  
- `/help` — справка по командам  
- `/clear` — очистка памяти  

Текстовые команды:
- `Общение: <тема>` — задать тему разговора  
- `Роль: <роль>` — установить system-роль (стиль ответов)  
- `Мем: <тема>` — создать мем по теме  

---

## 🛠 Деплой на Railway

1. Подключи репозиторий к [Railway](https://railway.app/).  
2. В **Variables** добавь:
   ```
   TOKEN_TG=your_telegram_bot_token
   ```
3. Задеплой — и бот работает в Телеге 🚀

---

## 📜 Лицензия
MIT
