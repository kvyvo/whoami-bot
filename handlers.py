import asyncio
import logging

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message

import cards

router = Router()

DICE_ANIMATION = 4


async def send(bot, chat_id, rich):
    try:
        await bot.send_rich_message(chat_id=chat_id, rich_message=rich)
    except TelegramBadRequest as error:
        logging.warning("rich-сообщение не прошло: %s", error.message)
        await bot.send_message(chat_id=chat_id, text=cards.as_plain_text(rich))


async def profile(bot, user):
    chat = photos = None
    try:
        chat = await bot.get_chat(user.id)
        photos = (await bot.get_user_profile_photos(user_id=user.id, limit=1)).total_count
    except TelegramBadRequest as error:
        logging.warning("профиль дополнить не вышло: %s", error.message)
    return cards.profile(user, chat, photos)


@router.message(CommandStart())
async def start(message: Message, bot: Bot):
    await send(bot, message.chat.id, cards.start(message.from_user.first_name))


@router.message(Command("me"))
async def me(message: Message, bot: Bot):
    await send(bot, message.chat.id, await profile(bot, message.from_user))


@router.message(Command("roll"))
async def roll(message: Message, bot: Bot):
    await send(bot, message.chat.id, cards.dice_choice())


@router.message(Command("fortune"))
async def fortune(message: Message, bot: Bot):
    await send(bot, message.chat.id, cards.fortune())


@router.callback_query(F.data.startswith("dice:"))
async def throw(callback: CallbackQuery, bot: Bot):
    emoji = callback.data.removeprefix("dice:")
    thrown = await bot.send_dice(chat_id=callback.message.chat.id, emoji=emoji)
    await callback.answer()
    await asyncio.sleep(DICE_ANIMATION)
    await send(bot, callback.message.chat.id, cards.dice_result(emoji, thrown.dice.value))


@router.callback_query(F.data.in_({"me", "roll", "fortune"}))
async def buttons(callback: CallbackQuery, bot: Bot):
    if callback.data == "me":
        rich = await profile(bot, callback.from_user)
    elif callback.data == "roll":
        rich = cards.dice_choice()
    else:
        rich = cards.fortune()
    await send(bot, callback.message.chat.id, rich)
    await callback.answer()


@router.message(F.text)
async def anything(message: Message, bot: Bot):
    await send(bot, message.chat.id, cards.hint())
