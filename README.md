# TG Mem Bot 🎭

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://www.python.org/)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-blue?logo=telegram)](https://core.telegram.org/bots)
[![Deploy](https://img.shields.io/badge/Deploy-Railway-purple?logo=railway)](https://railway.app/)

Telegram meme-generator bot built with **aiogram v3** and **g4f**.

Features:
- 📸 Generate memes based on a given topic
- 🧩 Maintain conversational context with memory
- 📝 Support different roles (response styles)

---

## 🚀 Installation & Run

1. Clone the repository:
   ```bash
   git clone https://github.com/yourname/tg-mem-bot.git
   cd tg-mem-bot
   ```

2. Create virtual environment & install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Linux/Mac
   .venv\Scripts\activate      # Windows

   pip install -r requirements.txt
   ```

3. Create `.env` file:
   ```env
   TOKEN_TG=your_telegram_bot_token
   ```

4. Run:
   ```bash
   python TG_mem_bot.py
   ```

---

## ⚙️ Environment Variables

- `TOKEN_TG` — Telegram bot token from BotFather
- `G4F_TEXT_TIMEOUT` — text generation timeout (sec), default `15`
- `G4F_IMAGE_TIMEOUT` — image generation timeout (sec), default `20`

---

## 📖 Commands

- `/start` — start bot
- `/help` — show help
- `/clear` — clear memory

Text commands:
- `Общение: <topic>` — set topic for dialog (with memory)
- `Роль: <role>` — set system role (response style)
- `Мем: <topic>` — generate meme with caption & image

---

## 🛠 Deploy on Railway

1. Connect repository to [Railway](https://railway.app/).
2. Add **Variables**:
   ```
   TOKEN_TG=your_telegram_bot_token
   ```
3. Deploy → Bot is live in Telegram 🚀

---

## 📜 License
MIT
