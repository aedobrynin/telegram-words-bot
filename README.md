# Words bot

Words bot is a Telegram bot for practicticing Russian language orthography.

Tested on Python 3.8.5

## Running

1. Create new Python venv and install requirements.
```
python3 -m venv env
source env/bin/activate
pip3 install -r requirements.txt
```

2. Set your Telegram bot token in `config.py`

3. Create database
```
alembic upgrade head
```
3. Run
```
python3 main.py
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Used libraries

* [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
* [sqlalchemy](https://www.sqlalchemy.org/)
