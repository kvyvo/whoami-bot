import random

from aiogram.types import (
    InputRichBlockBlockQuotation,
    InputRichBlockButtons,
    InputRichBlockDetails,
    InputRichBlockDivider,
    InputRichBlockList,
    InputRichBlockListItem,
    InputRichBlockParagraph,
    InputRichBlockSectionHeading,
    InputRichBlockTable,
    InputRichMessage,
    RichBlockTableCell,
    RichMessageButton,
    RichTextBold,
    RichTextCode,
)

DICE = {
    "🎲": "кубик",
    "🎯": "дартс",
    "🏀": "баскетбол",
    "⚽": "футбол",
    "🎳": "боулинг",
    "🎰": "автомат",
}

DICE_WIN = {
    "🎲": {6: "максимум"},
    "🎯": {6: "в яблочко"},
    "🏀": {4: "попал", 5: "попал"},
    "⚽": {3: "гол", 4: "гол", 5: "гол"},
    "🎳": {6: "страйк"},
    "🎰": {64: "джекпот, три семёрки"},
}

FORTUNES = (
    "сегодня код заработает с первого раза. один раз",
    "тебя ждёт письмо, на которое можно не отвечать",
    "скоро найдётся вещь, которую ты искал позавчера",
    "лучшее решение задачи — не решать её сегодня",
    "завтра начнётся раньше, чем хотелось бы",
    "кто-то вспомнит о тебе хорошим словом и не скажет об этом",
    "не бери новых задач до среды. особенно в среду",
    "ошибка, которую ищешь третий час, — в первой строке",
)

HIDDEN = (
    "телефон — только если сам пришлёшь контакт кнопкой",
    "почту и данные для входа",
    "другие твои чаты, каналы и подписки",
    "список контактов",
    "переписку с другими людьми и ботами",
)


def _cell(text, header=False):
    return RichBlockTableCell(
        align="left", valign="middle", text=text, is_header=header
    )


def _table(rows):
    header = [
        _cell(RichTextBold(text="параметр"), header=True),
        _cell(RichTextBold(text="значение"), header=True),
    ]
    cells = [header] + [[_cell(name), _cell(value)] for name, value in rows]
    return InputRichBlockTable(cells=cells, is_bordered=True, is_striped=True)


def _item(text):
    return InputRichBlockListItem(blocks=[InputRichBlockParagraph(text=text)])


def menu():
    return InputRichBlockButtons(
        buttons=[
            RichMessageButton(text="что ты обо мне знаешь", callback_data="me"),
            RichMessageButton(text="бросить кубик", callback_data="roll"),
            RichMessageButton(text="печенье", callback_data="fortune"),
        ]
    )


def start(name):
    return InputRichMessage(
        blocks=[
            InputRichBlockSectionHeading(text=f"привет, {name}", size=2),
            InputRichBlockParagraph(
                text="показываю, что telegram сообщает обо мне боту, и развлекаю"
            ),
            InputRichBlockList(
                items=[
                    _item([RichTextCode(text="/me"), " — что бот о тебе знает"]),
                    _item([RichTextCode(text="/roll"), " — кубик, дартс, автомат"]),
                    _item([RichTextCode(text="/fortune"), " — печенье с предсказанием"]),
                ]
            ),
            InputRichBlockDivider(),
            menu(),
        ]
    )


def hint():
    return InputRichMessage(
        blocks=[
            InputRichBlockParagraph(text="я понимаю команды и кнопки ниже"),
            menu(),
        ]
    )


def user_rows(user, chat=None, photos=None):
    rows = [
        ("id", str(user.id)),
        ("имя", user.first_name or "не задано"),
    ]
    if user.last_name:
        rows.append(("фамилия", user.last_name))
    rows.append(("username", f"@{user.username}" if user.username else "не задан"))
    rows.append(("язык", user.language_code or "не сообщён"))
    rows.append(("premium", "да" if user.is_premium else "нет"))
    if chat is not None:
        rows.append(("био", getattr(chat, "bio", None) or "пустое"))
        emoji_status = getattr(chat, "emoji_status_custom_emoji_id", None)
        rows.append(("эмодзи-статус", "есть" if emoji_status else "нет"))
        usernames = getattr(chat, "active_usernames", None)
        if usernames:
            rows.append(("все username", ", ".join(f"@{n}" for n in usernames)))
    if photos is not None:
        rows.append(("фото профиля", str(photos)))
    return rows


def profile(user, chat=None, photos=None):
    return InputRichMessage(
        blocks=[
            InputRichBlockSectionHeading(text="что бот о тебе знает", size=2),
            _table(user_rows(user, chat, photos)),
            InputRichBlockDetails(
                summary="а чего не знает",
                blocks=[InputRichBlockList(items=[_item(text) for text in HIDDEN])],
            ),
            InputRichBlockParagraph(
                text="всё это приходит с сообщением и в ответе getChat"
            ),
            menu(),
        ]
    )


def dice_choice():
    return InputRichMessage(
        blocks=[
            InputRichBlockParagraph(text="что бросаем?"),
            InputRichBlockButtons(
                buttons=[
                    RichMessageButton(text=f"{emoji} {name}", callback_data=f"dice:{emoji}")
                    for emoji, name in DICE.items()
                ]
            ),
        ]
    )


def dice_result(emoji, value):
    comment = DICE_WIN.get(emoji, {}).get(value, "бывает и лучше")
    return InputRichMessage(
        blocks=[
            InputRichBlockParagraph(
                text=[f"{DICE.get(emoji, emoji)}: ", RichTextBold(text=str(value)), f" — {comment}"]
            ),
            menu(),
        ]
    )


def fortune(text=None):
    return InputRichMessage(
        blocks=[
            InputRichBlockSectionHeading(text="печенье с предсказанием", size=3),
            InputRichBlockBlockQuotation(
                blocks=[InputRichBlockParagraph(text=text or random.choice(FORTUNES))]
            ),
            menu(),
        ]
    )


def _flat(node):
    if node is None:
        return ""
    if isinstance(node, str):
        return node
    if isinstance(node, (list, tuple)):
        return "".join(_flat(part) for part in node)
    return _flat(getattr(node, "text", ""))


def as_plain_text(rich):
    lines = []
    for block in rich.blocks or []:
        kind = getattr(block, "type", "")
        if kind == "table":
            lines += [": ".join(_flat(cell.text) for cell in row) for row in block.cells]
        elif kind == "list":
            lines += [f"• {as_plain_text(InputRichMessage(blocks=item.blocks))}" for item in block.items]
        elif kind == "details":
            lines.append(_flat(block.summary))
            lines.append(as_plain_text(InputRichMessage(blocks=block.blocks)))
        elif kind == "buttons":
            continue
        elif getattr(block, "blocks", None):
            lines.append(as_plain_text(InputRichMessage(blocks=block.blocks)))
        else:
            lines.append(_flat(getattr(block, "text", "")))
    return "\n".join(line for line in lines if line)
