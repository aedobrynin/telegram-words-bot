from typing import Union
from random import shuffle
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram import ParseMode
from telegram.ext import Updater, CommandHandler, CallbackContext
from telegram.ext import CallbackQueryHandler, ConversationHandler
import utils
from models import Session, Word, User
from config import TELEGRAM_BOT_TOKEN, MAIN_MENU_STATE, IN_GAME_STATE
from config import SETTINGS_STATE, START_GAME, SHOW_STATS, SHOW_RATING
from config import SHOW_SETTINGS, CHANGE_NOTIF_SETTING
from config import CHANGE_SHOW_IN_RATING_SETTING, GO_BACK, NOTIFICATION_TIME
from config import MAIN_MENU_TEXT, GAME_CHAT_DATA_KEYS
from config import TOGETHER_VARIANT, TOGETHER_VARIANT_TEXT
from config import SPACE_VARIANT, SPACE_VARIANT_TEXT


MAIN_MENU_KEYBOARD = [
    [
        InlineKeyboardButton('Начать игру 🏁', callback_data=START_GAME),
        InlineKeyboardButton('Статистика 📊', callback_data=SHOW_STATS),
    ],
    [
        InlineKeyboardButton('Рейтинг 🏆', callback_data=SHOW_RATING),
        InlineKeyboardButton('Настройки ⚙️', callback_data=SHOW_SETTINGS),
    ],
]
MAIN_MENU_KEYBOARD_MARKUP = InlineKeyboardMarkup(MAIN_MENU_KEYBOARD)


__TMP_SESS = Session()
WORDS = dict((word.id, word)
             for word in __TMP_SESS.query(Word)
             .filter(Word.variants != '').all())
__TMP_SESS.close()


def start_handler(update: Update, context: CallbackContext) -> MAIN_MENU_STATE:
    update.message.reply_text(MAIN_MENU_TEXT,
                              parse_mode=ParseMode.HTML,
                              reply_markup=MAIN_MENU_KEYBOARD_MARKUP)
    for key in GAME_CHAT_DATA_KEYS:
        context.chat_data.pop(key, None)

    return MAIN_MENU_STATE


def restart_callback_handler(update: Update, _: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    query.edit_message_text('Кажется, что произошёл перезапуск бота.\n'
                            'Данные о текущей игре могли быть утрачены.\n'
                            'Для продолжения работы введите команду /start')


def main_menu_callback_handler(update: Update, context: CallbackContext)\
        -> Union[MAIN_MENU_STATE, IN_GAME_STATE, SETTINGS_STATE]:
    query = update.callback_query
    query.answer()

    if query.data == START_GAME:
        return in_game_callback_handler(update, context)

    if query.data == SHOW_STATS:
        session = Session()
        user = session.query(User).get(query.from_user.id)

        message: str
        if user is None:
            message = 'Вы не сыграли ни одной игры'
        else:
            message = (f'<b>Рекорд:</b> {user.best_score}🏅\n'
                       f'<b>Всего игр:</b> {user.total_games}\n\n')

            top_mistakes =\
                utils.get_top_five_locally_mistaken(user.get_stats())
            if top_mistakes:
                message += '<b>Ваши самые частые ошибки:</b>\n'
                for (i, (word, success_cnt, total_cnt))\
                        in enumerate(top_mistakes):
                    message += (f'{i + 1}) Слово "{word}" — '
                                f'угадано {success_cnt} из {total_cnt}.\n')

        session.close()
        query.edit_message_text(message,
                                parse_mode=ParseMode.HTML,
                                reply_markup=MAIN_MENU_KEYBOARD_MARKUP)
        return MAIN_MENU_STATE

    if query.data == SHOW_RATING:
        top_mistakes = utils.get_top_five_globally_mistaken()
        best_players = utils.get_best_players()

        message = ""
        if top_mistakes:
            message += '<b>Самые популярные ошибки</b>\n'
            for (i, (word, success_cnt, total_cnt)) in enumerate(top_mistakes):
                message += (f'{i + 1}) Слово "{word}" — угадано {success_cnt} '
                            f'из {total_cnt}.\n')
            message += '\n'

        message += f'<b>Всего игроков:</b> {utils.get_total_players_cnt()}\n\n'

        if best_players:
            message += '⭐ <b>Топ игроков</b> ⭐\n'
            for (emoji, (name, score)) in zip('🥇🥈🥉', best_players):
                message += f'{emoji} {name} — {score}🏅\n'

        query.edit_message_text(message,
                                parse_mode=ParseMode.HTML,
                                reply_markup=MAIN_MENU_KEYBOARD_MARKUP)
        return MAIN_MENU_STATE

    if query.data == SHOW_SETTINGS:
        session = Session()
        user = session.query(User).get(query.from_user.id)
        if user is None:
            user = User(query.from_user.id, query.from_user.first_name)
            session.add(user)

        message = utils.get_settings_message(user)
        keyboard_markup = utils.get_settings_keyboard_markup(user)

        query.edit_message_text(message,
                                parse_mode=ParseMode.HTML,
                                reply_markup=keyboard_markup)

        session.commit()
        session.close()
        return SETTINGS_STATE

    return MAIN_MENU_STATE


def settings_callback_handler(update: Update, _: CallbackContext)\
        -> Union[MAIN_MENU_STATE, SETTINGS_STATE]:
    query = update.callback_query
    query.answer()

    if query.data == GO_BACK:
        query.edit_message_text(MAIN_MENU_TEXT,
                                parse_mode=ParseMode.HTML,
                                reply_markup=MAIN_MENU_KEYBOARD_MARKUP)
        return MAIN_MENU_STATE

    if query.data in (CHANGE_NOTIF_SETTING, CHANGE_SHOW_IN_RATING_SETTING):
        session = Session()

        # User is present in database at this moment
        user = session.query(User).get(query.from_user.id)

        if query.data == CHANGE_NOTIF_SETTING:
            user.daily_notification = not user.daily_notification
        else:
            user.show_in_rating = not user.show_in_rating

        message = utils.get_settings_message(user)
        keyboard_markup = utils.get_settings_keyboard_markup(user)

        session.commit()
        session.close()

        query.edit_message_text(message,
                                parse_mode=ParseMode.HTML,
                                reply_markup=keyboard_markup)

    return SETTINGS_STATE


def in_game_callback_handler(update: Update, context: CallbackContext)\
        -> Union[MAIN_MENU_STATE, IN_GAME_STATE]:
    query = update.callback_query
    query.answer()

    if 'current_word_id' in context.chat_data:
        session = Session()
        user = session.query(User).get(query.from_user.id)
        word_id = context.chat_data['current_word_id']
        word = session.query(Word).get(word_id)

        if query.data == WORDS[word_id].get_correct_variant():
            context.chat_data['score'] += 1
            user.update_stats(word_id, True)
            word.update_stats(True)
            session.commit()
            session.close()
        else:
            score = context.chat_data['score']

            correct = WORDS[word_id].get_correct_word()
            query.edit_message_text(
                (f'Неверно! Правильный вариант: <b>"{correct}"</b>.\n'
                 f'<b>Ваш итоговый счёт:</b> {score}🏅'),
                parse_mode=ParseMode.HTML,
                reply_markup=MAIN_MENU_KEYBOARD_MARKUP,
            )

            user.update_best_score(score)
            user.update_stats(word_id, False)
            word.update_stats(False)
            session.commit()
            session.close()

            for key in GAME_CHAT_DATA_KEYS:
                context.chat_data.pop(key, None)

            return MAIN_MENU_STATE
    else:
        #  Straight from the main menu
        session = Session()

        user = session.query(User).get(query.from_user.id)
        if user is None:
            user = User(query.from_user.id, query.from_user.first_name)
            session.add(user)
        user.total_games += 1

        session.commit()
        session.close()

        context.chat_data['not_played_word_ids'] = set(WORDS.keys())
        context.chat_data['score'] = 0

    if not context.chat_data['not_played_word_ids']:
        score = context.chat_data['score']
        query.edit_message_text(
            '✨Поздравляем! Вы ответили на все вопросы правильно!✨\n'
            f'<b>Ваш итоговый счёт:</b> {score}🏅',
            parse_mode=ParseMode.HTML,
            reply_markup=MAIN_MENU_KEYBOARD_MARKUP,
        )

        session = Session()
        user = session.query(User).get(query.from_user.id)
        user.update_best_score(score)
        session.commit()
        session.close()

        for key in GAME_CHAT_DATA_KEYS:
            context.chat_data.pop(key, None)

        return MAIN_MENU_STATE

    current_word_id =\
        utils.get_word_id(context.chat_data['not_played_word_ids'])
    context.chat_data['current_word_id'] = current_word_id

    variants = WORDS[current_word_id].get_variants()
    shuffle(variants)
    keyboard = [[]]
    for variant in variants:
        keyboard[0]\
            .append(InlineKeyboardButton(variant[0], callback_data=variant[1]))
    markup = InlineKeyboardMarkup(keyboard)

    message = f'<b>Счёт:</b> {context.chat_data["score"]} 🏅\n'
    if (TOGETHER_VARIANT_TEXT, TOGETHER_VARIANT) in variants or\
            (SPACE_VARIANT_TEXT, SPACE_VARIANT) in variants:
        message += 'Как должно писаться слово: '
    else:
        message += 'Что должно быть на месте многоточия: '
    message += f'<b>"{WORDS[current_word_id].word}"</b>?'

    query.edit_message_text(
        message,
        parse_mode=ParseMode.HTML,
        reply_markup=markup,
    )
    return IN_GAME_STATE


def main() -> None:
    updater = Updater(TELEGRAM_BOT_TOKEN)
    dispatcher = updater.dispatcher

    restart_handler = CallbackQueryHandler(restart_callback_handler)

    main_conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start_handler)],
        states={
            MAIN_MENU_STATE:
                [CallbackQueryHandler(main_menu_callback_handler)],
            IN_GAME_STATE:
                [CallbackQueryHandler(in_game_callback_handler)],
            SETTINGS_STATE:
                [CallbackQueryHandler(settings_callback_handler)],
        },
        fallbacks=[],
        allow_reentry=True,
    )

    dispatcher.add_handler(main_conversation_handler)
    dispatcher.add_handler(restart_handler)

    updater.job_queue.run_daily(utils.send_notification, NOTIFICATION_TIME)

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
