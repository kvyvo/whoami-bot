import asyncio
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from aiogram.exceptions import TelegramBadRequest

import cards
import handlers
from config import Settings


def user(**kwargs):
    fields = {
        "id": 777000, "first_name": "Ростислав", "last_name": None, "username": None,
        "language_code": None, "is_premium": None,
    }
    return mock.Mock(**(fields | kwargs))


class CardsTest(unittest.TestCase):
    def test_every_card_builds(self):
        cards.start("Ростислав")
        cards.hint()
        cards.dice_choice()
        cards.dice_result("🎲", 6)
        cards.fortune()
        cards.profile(user())

    def test_rows_without_optional_fields(self):
        rows = dict(cards.user_rows(user()))
        self.assertEqual(rows["id"], "777000")
        self.assertEqual(rows["username"], "не задан")
        self.assertEqual(rows["premium"], "нет")
        self.assertNotIn("фамилия", rows)
        self.assertNotIn("био", rows)

    def test_rows_with_chat_and_photos(self):
        chat = mock.Mock(bio="про меня", emoji_status_custom_emoji_id="1", active_usernames=["a", "b"])
        rows = dict(cards.user_rows(user(username="kvyvo", is_premium=True), chat, photos=3))
        self.assertEqual(rows["username"], "@kvyvo")
        self.assertEqual(rows["premium"], "да")
        self.assertEqual(rows["био"], "про меня")
        self.assertEqual(rows["эмодзи-статус"], "есть")
        self.assertEqual(rows["все username"], "@a, @b")
        self.assertEqual(rows["фото профиля"], "3")

    def test_profile_has_table_and_details(self):
        blocks = {block.type for block in cards.profile(user()).blocks}
        self.assertIn("table", blocks)
        self.assertIn("details", blocks)
        self.assertIn("buttons", blocks)

    def test_dice_result_marks_win(self):
        self.assertIn("страйк", cards.as_plain_text(cards.dice_result("🎳", 6)))
        self.assertIn("бывает", cards.as_plain_text(cards.dice_result("🎳", 3)))

    def test_plain_text_keeps_table_and_list(self):
        text = cards.as_plain_text(cards.profile(user(username="kvyvo")))
        self.assertIn("id: 777000", text)
        self.assertIn("username: @kvyvo", text)
        self.assertIn("• телефон", text)
        self.assertNotIn("бросить кубик", text)


class HandlersTest(unittest.TestCase):
    def test_falls_back_to_plain_message(self):
        bot = mock.AsyncMock()
        bot.send_rich_message.side_effect = TelegramBadRequest(
            method=mock.Mock(), message="Bad Request: rich messages are not supported"
        )
        asyncio.run(handlers.send(bot, 1, cards.fortune("предсказание")))
        bot.send_message.assert_awaited_once()
        self.assertIn("предсказание", bot.send_message.await_args.kwargs["text"])

    def test_profile_survives_failed_get_chat(self):
        bot = mock.AsyncMock()
        bot.get_chat.side_effect = TelegramBadRequest(
            method=mock.Mock(), message="Bad Request: chat not found"
        )
        rich = asyncio.run(handlers.profile(bot, user()))
        self.assertIn("id: 777000", cards.as_plain_text(rich))

    def test_dice_throw_waits_for_animation(self):
        bot = mock.AsyncMock()
        bot.send_dice.return_value = mock.Mock(dice=mock.Mock(value=6))
        callback = mock.AsyncMock()
        callback.data = "dice:🎳"
        callback.message.chat.id = 1
        with mock.patch.object(handlers.asyncio, "sleep", mock.AsyncMock()) as sleep:
            asyncio.run(handlers.throw(callback, bot))
        sleep.assert_awaited_once_with(handlers.DICE_ANIMATION)
        bot.send_dice.assert_awaited_once()
        self.assertEqual(bot.send_dice.await_args.kwargs["emoji"], "🎳")
        sent = bot.send_rich_message.await_args.kwargs["rich_message"]
        self.assertIn("страйк", cards.as_plain_text(sent))


class ConfigTest(unittest.TestCase):
    def test_token_from_environment(self):
        with mock.patch.dict(os.environ, {"BOT_TOKEN": "123456:AAE"}):
            self.assertEqual(Settings(_env_file=None).bot_token, "123456:AAE")

    def test_without_token_bot_says_what_to_do(self):
        env = {k: v for k, v in os.environ.items() if k != "BOT_TOKEN"}
        bot_py = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot.py")
        with tempfile.TemporaryDirectory() as empty:
            result = subprocess.run(
                [sys.executable, bot_py], capture_output=True, text=True,
                env=env, cwd=empty, timeout=60,
            )
        self.assertEqual(result.returncode, 1)
        self.assertIn("нет токена", result.stderr)


if __name__ == "__main__":
    unittest.main()
