from datetime import time
from pytz import UTC


TELEGRAM_BOT_TOKEN = ''

MAIN_MENU_STATE, IN_GAME_STATE, SETTINGS_STATE, START_GAME, SHOW_STATS,\
    SHOW_RATING, SHOW_SETTINGS, CHANGE_NOTIF_SETTING,\
    CHANGE_SHOW_IN_RATING_SETTING, GO_BACK = map(str, range(10))

MAIN_MENU_TEXT = ('Привет! Этот бот поможет тебе подготовиться к заданиям по '
                  'орфографии из ЕГЭ по русскому языку.\nОбо всех ошибках '
                  'сообщать @rov01yp.\n'
                  'Наш бот по орфоэпии: @ege_2021_stress_bot')

NOTIFICATION_TEXT =\
    'До ЕГЭ осталось всего несколько дней, самое время практиковаться!'


NOTIFICATION_TIME = time(10, 0, 0, 0, tzinfo=UTC)


GAME_CHAT_DATA_KEYS =\
    ('score', 'not_played_word_ids', 'current_word_id')

'''The symbolds used to encode special variants in database
Texts will be used to show variants to a user'''
NONE_VARIANT = '0'
NONE_VARIANT_TEXT = 'Ничего'

SPACE_VARIANT = '_'
SPACE_VARIANT_TEXT = 'Раздельно'

TOGETHER_VARIANT = '+'
TOGETHER_VARIANT_TEXT = 'Слитно'

HYPHEN_VARIANT = '-'
HYPHEN_VARIANT_TEXT = 'Через дефис'
