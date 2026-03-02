import html
import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from openai import AsyncOpenAI

from config import (
    GROK_BASE_URL,
    GROK_MODEL,
    XAI_API_KEY,
    ALLOWED_USER_IDS,
    BOT_NAME,
)
from utils.memory import add_message, get_history, clear_history
from utils.prompt import get_system_prompt
from utils.web_search import tavily_search, format_results, WebSearchError

router = Router()
client = AsyncOpenAI(api_key=XAI_API_KEY, base_url=GROK_BASE_URL)

log = logging.getLogger(__name__)

WELCOME_MESSAGE = (
    "👑 Привет, Госпожа.\n\n"
    "Я — твоя ассистентка для обучения девочек онлайн-доминации.\n\n"
    "Что могу:\n"
    "— объяснять термины и правила\n"
    "— помогать с заданиями/разборами/сценариями\n"
    "— помогать писать материалы для следующего обучения\n\n"
    "Команды:\n"
    "/search <запрос> — поиск в интернете (кратко)\n"
    "/clear — очистить память\n"
)


def _access_denied_text() -> str:
    return "❌ Доступ только для участниц закрытого канала."


def _is_allowed(user_id: int) -> bool:
    return (not ALLOWED_USER_IDS) or (user_id in ALLOWED_USER_IDS)


@router.message(Command("start"))
async def cmd_start(message: Message):
    if not _is_allowed(message.from_user.id):
        await message.answer(_access_denied_text())
        return

    await message.answer(WELCOME_MESSAGE)
    await add_message(message.from_user.id, "assistant", "Приветствие отправлено.")


@router.message(Command("clear"))
async def cmd_clear(message: Message):
    if not _is_allowed(message.from_user.id):
        return

    await clear_history(message.from_user.id)
    await message.answer("🗑 Память очищена. Можем начинать заново.")


@router.message(Command("search"))
async def cmd_search(message: Message):
    if not _is_allowed(message.from_user.id):
        return

    query = (message.text or "").split(maxsplit=1)
    if len(query) < 2 or not query[1].strip():
        await message.answer("Напиши так: /search твой запрос")
        return

    q = query[1].strip()

    try:
        results = await tavily_search(q, max_results=5)
        if not results:
            await message.answer("Ничего не нашла по этому запросу.")
            return

        text = "🔎 Результаты поиска:\n\n" + "\n\n".join(
            [
                f"{i}. {r['title']}\n{r['url']}\n{r['snippet']}"
                for i, r in enumerate(results, 1)
            ]
        )
        await message.answer(text[:3800])

    except WebSearchError:
        await message.answer("Поиск не настроен: нет ключа TAVILY_API_KEY.")
    except Exception as e:
        log.exception("Search error")
        await message.answer(f"Ошибка поиска: {html.escape(str(e))}")


async def _maybe_attach_search_context(user_text: str) -> str | None:
    triggers = [
        "найди",
        "источник",
        "ссылк",
        "подтверди",
        "проверь",
        "в интернете",
        "поиск",
    ]
    lt = (user_text or "").lower()
    if not any(t in lt for t in triggers):
        return None

    results = await tavily_search(user_text, max_results=3)
    if not results:
        return None

    return (
        "\n\n"
        "[КОНТЕКСТ ИЗ ПОИСКА]\n"
        "Используй это только как справку, без фантазий и выдумок.\n"
        + format_results(results)
    )


@router.message()
async def handle_message(message: Message):
    if not _is_allowed(message.from_user.id):
        return

    user_id = message.from_user.id
    user_text = message.text or ""

    await add_message(user_id, "user", user_text)

    messages = [{"role": "system", "content": get_system_prompt(BOT_NAME)}]
    messages.extend(await get_history(user_id))

    try:
        search_ctx = await _maybe_attach_search_context(user_text)
        if search_ctx:
            messages.append({"role": "system", "content": search_ctx})
    except Exception:
        log.exception("Auto-search failed")

    try:
        response = await client.chat.completions.create(
            model=GROK_MODEL,
            messages=messages,
            temperature=0.92,
            max_tokens=2200,
            top_p=0.95,
        )

        ai_reply = (response.choices[0].message.content or "").strip()
        if not ai_reply:
            ai_reply = "Пустой ответ от модели. Попробуй переформулировать запрос."

        await add_message(user_id, "assistant", ai_reply)
        await message.answer(ai_reply[:3800])

    except Exception as e:
        log.exception("AI request error")
        err = html.escape(str(e))
        await message.answer(
            f"❌ Ошибка соединения: {err}\n"
            f"Проверь токены/доступ и соединение (VPN/прокси)."
        )