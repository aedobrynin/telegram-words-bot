from random import sample
from typing import Set, Tuple, List, Iterable, Any
from itertools import islice
from time import sleep
from sqlalchemy import desc
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import CallbackContext
from models import Session, Word, User
from config import CHANGE_NOTIF_SETTING, CHANGE_SHOW_IN_RATING_SETTING, GO_BACK
from config import NOTIFICATION_TEXT


def get_word_id(ids: Set[int]) -> int:
    """Picks random word id from the set. The Id is removed from the set."""
    picked_id = sample(ids, 1)[0]
    ids.remove(picked_id)
    return picked_id


def get_top_five_globally_mistaken() -> List[Tuple[str, int, int]]:
    session = Session()
    query =\
        session.query(Word).filter(
            (Word.total_count >= 1) &
            (Word.success_count != Word.total_count)
        ).order_by(desc(Word.total_count - Word.success_count))\
        .order_by(desc(Word.total_count))\
        .limit(5)\
        .all()
    session.close()

    ret_val = list()
    for word in query:
        ret_val.append((
            word.get_correct_word(),
            word.success_count,
            word.total_count
        ))
    return ret_val


def get_top_five_locally_mistaken(word_stats: dict)\
        -> List[Tuple[str, int, int]]:
    items =\
        list(item for item in word_stats.items() if item[1][0] != item[1][1])
    items.sort(key=lambda x: (x[1][1] - x[1][0], x[1][1]), reverse=True)
    session = Session()

    ret_val = list()
    for i in range(min(len(items), 5)):
        word = session.query(Word).get(items[i][0])
        ret_val.append((word.get_correct_word(), *items[i][1]))

    session.close()

    return ret_val


def get_best_players() -> List[Tuple[str, int]]:
    session = Session()
    players =\
        session.query(User.name, User.best_score)\
               .filter(User.show_in_rating == 1)\
               .order_by(desc(User.best_score)).limit(3).all()
    session.close()
    return players


def get_total_players_cnt() -> int:
    session = Session()
    total_players = session.query(User).count()
    session.close()
    return total_players


def get_settings_message(user: User) -> str:
    message = (f'Сейчас вы {"" if user.show_in_rating else "не "}'
               'отображаетесь в рейтинге.\nУ вас '
               f'{"включено" if user.daily_notification else "выключено"} '
               'ежедневное уведомление.')
    return message


def get_settings_keyboard_markup(user: User) -> InlineKeyboardMarkup:
    change_show_in_rating_message: str
    if user.show_in_rating:
        change_show_in_rating_message = 'Не отображать меня в рейтинге ⛔'
    else:
        change_show_in_rating_message = 'Отображать меня в рейтинге 👁️'

    change_notification_message: str
    if user.daily_notification:
        change_notification_message = 'Не присылать ежедневное уведомление 🔕'
    else:
        change_notification_message = 'Присылать ежедневное уведомление 🔔'

    keyboard = [
        [
            InlineKeyboardButton(
                change_show_in_rating_message,
                callback_data=CHANGE_SHOW_IN_RATING_SETTING
            ),
        ],
        [
            InlineKeyboardButton(
                change_notification_message,
                callback_data=CHANGE_NOTIF_SETTING
            )
        ],
        [
            InlineKeyboardButton(
                'Назад 🔙',
                callback_data=GO_BACK
            ),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


def send_notification(context: CallbackContext) -> None:
    """Sends notification message to users with User.daily_notification == True
        It makes 5 messages per second in order to not exceed the rate limit"""

    def make_chunks(iterable: Iterable[Any], size: int) ->\
            Iterable[Tuple[Any, ...]]:
        """Splits iterable into chuncks of provided size.
            make_chunks([1, 2, 3, 4, 5, 6], 2) -> [(1, 2), (3, 4), (5, 6)].
            make_chunks([1, 2], 3) -> [(1, 2)]
        """
        iterator = iter(iterable)
        return iter(lambda: tuple(islice(iterator, size)), ())

    session = Session()
    send_to_ids = [data[0] for data in
                   session.query(User.id).filter(User.daily_notification == 1)
                   .all()]
    session.close()
    if not send_to_ids:
        return

    for chunk in make_chunks(send_to_ids, 5):
        for chat_id in chunk:
            context.bot.send_message(
                chat_id,
                NOTIFICATION_TEXT,
                parse_mode=ParseMode.HTML
            )
        sleep(1)
