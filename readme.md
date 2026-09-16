# whoami-bot

бот показывает, что телеграм рассказывает о тебе боту. плюс кубики и печенье с предсказанием.

- `/me` — таблица: id, имя, username, язык, premium, био, фото профиля. ниже — чего бот не видит
- `/roll` — кубик, дартс, мяч, боулинг, автомат
- `/fortune` — предсказание

aiogram 3.31, сообщения собраны блоками rich messages (`sendRichMessage`), поэтому карточка рисуется таблицей. если чат не примет rich — уйдёт тем же текстом.

## запуск

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
.venv/bin/python bot.py
```

токен от @botfather кладётся в `.env`, он в гитигноре. тесты без сети и токена:

```bash
.venv/bin/python -m unittest
```

команды для `/setcommands`:

```
me - что бот обо мне знает
roll - бросить кубик
fortune - печенье с предсказанием
```
