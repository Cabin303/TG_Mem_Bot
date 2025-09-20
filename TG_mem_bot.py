# TG_mem_bot.py
# Telegram Бот-Мемогенератор (aiogram v3 + g4f) с кнопками

import os
import asyncio
import tempfile
from typing import Dict, Any, List, Optional

import aiohttp
from dotenv import load_dotenv
from g4f.client import Client

import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    FSInputFile,
)
from aiogram.enums import ParseMode

# ------------------------ Настройка ------------------------
load_dotenv()
TOKEN_TG: str = os.getenv("TOKEN_TG", "").strip()
if not TOKEN_TG:
    raise RuntimeError("Укажи TOKEN_TG в .env")

TEXT_TIMEOUT = int(os.getenv("G4F_TEXT_TIMEOUT", "15"))      # сек на одну текстовую модель
IMAGE_TIMEOUT = int(os.getenv("G4F_IMAGE_TIMEOUT", "20"))    # сек на генерацию картинки
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')
MAX_HISTORY = 16  # хранить не более 16 пар (user/assistant) на тему

# ------------------------ Инициализация --------------------
bot_tg = Bot(token=TOKEN_TG, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
dp = Dispatcher()
gpt = Client()

# ------------------------ Память диалогов ------------------
# BOT_HISTORY[user_id][theme] -> {"role": {"role": "system", "content": ...}, "messages": [...]}
BOT_HISTORY: Dict[int, Dict[str, Dict[str, Any]]] = {}
# Текущая тема для каждого пользователя
TG_CHATS: Dict[int, str] = {}

# ------------------------ Клавиатура -----------------------
def main_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[
            KeyboardButton(text="📸 Мем"),
            KeyboardButton(text="🧩 Тема для общения"),
            KeyboardButton(text="📝 Новая роль"),
        ]],
        resize_keyboard=True
    )

# ======================== УТИЛИТЫ ПАМЯТИ ===================
def add_new_role(user_id: int, theme: str, role: str) -> None:
    if user_id not in BOT_HISTORY:
        BOT_HISTORY[user_id] = {}
    if theme not in BOT_HISTORY[user_id]:
        BOT_HISTORY[user_id][theme] = {}
    BOT_HISTORY[user_id][theme]['role'] = {"role": "system", "content": role}


def add_messages(user_id: int, theme: str, prompt: str, answer_ai: str) -> None:
    if user_id not in BOT_HISTORY:
        BOT_HISTORY[user_id] = {}
    if theme not in BOT_HISTORY[user_id]:
        BOT_HISTORY[user_id][theme] = {}
    if 'messages' not in BOT_HISTORY[user_id][theme]:
        BOT_HISTORY[user_id][theme]['messages'] = []
    BOT_HISTORY[user_id][theme]['messages'].append({"role": "user", "content": prompt})
    BOT_HISTORY[user_id][theme]['messages'].append({"role": "assistant", "content": answer_ai})
    # Обрезаем историю, чтобы не раздувалась
    msgs = BOT_HISTORY[user_id][theme]['messages']
    limit = MAX_HISTORY * 2  # каждая пара = 2 сообщения
    if len(msgs) > limit:
        del msgs[: len(msgs) - limit]


def get_role(user_id: int, theme: str) -> Optional[str]:
    if user_id not in BOT_HISTORY:
        return False
    if theme not in BOT_HISTORY[user_id]:
        return False
    if 'role' not in BOT_HISTORY[user_id][theme]:
        return False
    return BOT_HISTORY[user_id][theme]['role']["content"]


def get_messages(user_id: int, theme: str) -> Optional[List[Dict[str, str]]]:
    if user_id not in BOT_HISTORY:
        return False
    if theme not in BOT_HISTORY[user_id]:
        return False
    if 'messages' not in BOT_HISTORY[user_id][theme]:
        return False
    return BOT_HISTORY[user_id][theme]['messages']

# ======================== G4F (текст) ======================
TEXT_MODELS: List[str] = ["gpt-4.1-mini", "mistral", "gpt-4o-mini"]


async def chat_once(messages: List[Dict[str, str]]) -> str:
    """
    Универсальный вызов g4f с принудительным приведением контента к строке.
    Это снимает проблему: `messagesX.content did not match any variant of MessageContent`.
    """
    loop = asyncio.get_running_loop()
    last_error = None

    # ► Жёстко приводим контент к строке и чистим None/пустоты
    safe_messages: List[Dict[str, str]] = []
    for m in messages:
        role = str(m.get("role", "user"))
        content = m.get("content", "")
        if content is None:
            content = ""
        content = str(content).strip()
        if content == "":
            content = " "
        safe_messages.append({"role": role, "content": content})

    def _call(model: str) -> str:
        resp = gpt.chat.completions.create(model=model, messages=safe_messages)
        return resp.choices[0].message.content.strip()

    for model in TEXT_MODELS:
        try:
            logging.info(f"g4f.chat via model={model}")
            fut = loop.run_in_executor(None, _call, model)
            return await asyncio.wait_for(fut, timeout=TEXT_TIMEOUT)
        except asyncio.TimeoutError as e:
            last_error = e
            logging.warning(f"g4f timeout on model={model} after {TEXT_TIMEOUT}s")
            continue
        except Exception as e:
            last_error = e
            logging.warning(f"g4f error on model={model}: {e}")
            await asyncio.sleep(0.2)

    raise RuntimeError(f"Все текстовые модели отвалились: {last_error}")


async def just_get_answer(prompt: str) -> str:
    return await chat_once([{"role": "user", "content": prompt}])


async def just_answer_with_role(role: str, prompt: str) -> str:
    return await chat_once([{"role": "system", "content": role}, {"role": "user", "content": prompt}])


async def answer_with_history(history: List[Dict[str, str]], prompt: str) -> str:
    return await chat_once(history + [{"role": "user", "content": prompt}])


async def answer_with_history_and_role(role: str, history: List[Dict[str, str]], prompt: str) -> str:
    return await chat_once([{"role": "system", "content": role}] + history + [{"role": "user", "content": prompt}])

# ======================== G4F (картинка) ===================
async def make_meme_caption(topic: str) -> str:
    prompt = f"Придумай короткую смешную подпись для мема на тему: {topic}. 1 фраза, без эмодзи."
    return await just_get_answer(prompt)


async def make_meme_image_url(topic_or_caption: str) -> Optional[str]:
    loop = asyncio.get_running_loop()

    def _gen() -> Optional[str]:
        try:
            resp = gpt.images.generate(
                model="flux",
                prompt=f"Создай забавную мем-картинку в стиле Reaction memes — лицо или сцена, выражающие эмоцию. под подпись: {topic_or_caption}",
                response_format="url",
            )
            return resp.data[0].url
        except Exception:
            return None

    fut = loop.run_in_executor(None, _gen)
    try:
        return await asyncio.wait_for(fut, timeout=IMAGE_TIMEOUT)
    except asyncio.TimeoutError:
        logging.warning(f"g4f image timeout after {IMAGE_TIMEOUT}s")
        return None


async def download_to_temp(url: str) -> Optional[str]:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=30) as r:
                r.raise_for_status()
                fd, path = tempfile.mkstemp(suffix=".jpg")
                with os.fdopen(fd, "wb") as f:
                    f.write(await r.read())
                return path
    except Exception:
        return None

# ======================== TG‑хендлеры ======================
async def add_theme_tg(user_id: int, theme: str, message: Message):
    TG_CHATS[user_id] = theme.strip()
    await message.reply("✅ Тема разговора сохранена!")


async def change_role_tg(user_id: int, role: str, message: Message):
    if user_id not in TG_CHATS:
        await message.reply("Сначала задай тему: *Общение: <тема>*")
        return
    add_new_role(user_id, TG_CHATS[user_id], role.strip())
    await message.reply("🧠 Роль обновлена!")


async def send_answer_tg(message: Message):
    if message.from_user.id not in TG_CHATS:
        await message.answer("Сначала задай тему: *Общение: <тема>*")
        return

    user_text = (message.text or "").strip()
    if not user_text:
        await message.answer("Пришли текстовое сообщение 🙂")
        return

    role = get_role(message.from_user.id, TG_CHATS[message.from_user.id])
    history = get_messages(message.from_user.id, TG_CHATS[message.from_user.id])
    theme = TG_CHATS[message.from_user.id]
    effective_role = role or (
        f"Ты дружелюбный и остроумный помощник. Тема диалога: {theme}. "
        f"Отвечай по теме, кратко и полезно. Учитывай предыдущие сообщения, если они есть."
    )
    if not history:
        answer = await just_answer_with_role(effective_role, user_text)
    else:
        answer = await answer_with_history_and_role(effective_role, history, user_text)

    add_messages(message.from_user.id, TG_CHATS[message.from_user.id], user_text, answer)

    answer = (answer or "").strip()
    if not answer:
        answer = "Не удалось сгенерировать ответ, попробуй переформулировать запрос."

    await message.answer(answer)


async def handle_meme_tg(message: Message, topic: str):
    await message.answer("Генерирую мем… ⏳")
    caption = await make_meme_caption(topic)
    caption = (caption or "").strip() or "Вот твой мемас!"
    url = await make_meme_image_url(caption) or await make_meme_image_url(topic)
    if url:
        img_path = await download_to_temp(url)
        if img_path:
            try:
                await message.answer_photo(FSInputFile(img_path), caption=caption)
                os.remove(img_path)
                return
            except Exception:
                pass
    await message.answer(f"{caption}\n\n_(Картинку не удалось получить от бесплатного провайдера)_")

# ======================== Регистрация ======================
@dp.message(Command("start"))
async def start_command(message: Message):
    await message.answer(
        "Привет! Я ==Member== *Мемогенератор*.\n"
        "— Нажми кнопки ниже или используй текстовые команды:\n"
        "• `Общение: <тема>`\n"
        "• `Роль: <роль>`\n"
        "• `Мем: <тема>`",
        reply_markup=main_kb()
    )


@dp.message(Command("help"))
async def help_command(message: Message):
    await message.answer(
        "*Справка по командам*\n"
        "• `Общение: <тема>` — задать тему (включает память для этой темы)\n"
        "• `Роль: <роль>` — задать system‑роль (стиль ответов)\n"
        "• `Мем: <тема>` — сгенерировать подпись и картинку\n"
        "• `/clear` — очистить всю память и сбросить тему",
        reply_markup=main_kb()
    )


@dp.message(Command("clear"))
async def clear_command(message: Message):
    # Удаляем все темы/историю для пользователя и сбрасываем текущую тему
    BOT_HISTORY.pop(message.from_user.id, None)
    TG_CHATS.pop(message.from_user.id, None)
    await message.reply("🧹 Память очищена, тема сброшена.")


@dp.message()
async def router(message: Message):
    text = (message.text or "").strip()
    low = text.lower()

    if low.startswith("общение:"):
        await add_theme_tg(message.from_user.id, text.split(":", 1)[1], message)
    elif low.startswith("роль:"):
        await change_role_tg(message.from_user.id, text.split(":", 1)[1], message)
    elif low.startswith("мем:"):
        topic = text.split(":", 1)[1].strip()
        if topic:
            await handle_meme_tg(message, topic)
        else:
            await message.answer("Формат: `Мем: <тема>`")
    elif text in ("📸 Мем", "🧩 Общение", "📝 Новая роль"):
        if text == "📸 Мем":
            await message.answer("Напиши: `Мем: <тема>` — и я всё сделаю.")
        elif text == "🧩 Общение":
            await message.answer("Напиши: `Общениe: <тема>`")
        else:
            await message.answer("Напиши: `Роль: <роль>`")
    else:
        await send_answer_tg(message)

# ======================== Запуск ===========================
async def main():
    try:
        await dp.start_polling(bot_tg)
    finally:
        # Корректно закрываем HTTP‑сессию бота (graceful shutdown)
        await bot_tg.session.close()

if __name__ == "__main__":
    asyncio.run(main())
