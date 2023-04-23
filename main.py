from pprint import pprint

from dotenv import load_dotenv
import logging
import os
from pathlib import Path
from random import choice, shuffle
from re import match
from telegram import Bot, InputMediaPhoto, ReplyKeyboardMarkup, TelegramError
from telegram.ext import (
    CommandHandler, Dispatcher, Filters, MessageHandler, Updater)

import app_logger

load_dotenv()
logger: logging.Logger = app_logger.get_logger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ALL_DATA = [TELEGRAM_BOT_TOKEN]

API_TELEGRAM_UPDATE_SEC = 0.5

# А карты можно отправлять так: for i in range(0, round) and range(round, len(players))
IMAGE_CARDS: Path = Path('res/words')
IMAGE_CARDS_СOUNT: int = len(list(IMAGE_CARDS.iterdir()))
IMAGE_RULES = [Path(f'res/rules/0{i}_правила.jpg') for i in range(8)]
IMAGE_RULES_MEDIA = []
for file_path in IMAGE_RULES:
    with open(file_path, 'rb') as file:
        IMAGE_RULES_MEDIA.append(InputMediaPhoto(
            media=file.read(), caption=Path(file_path).name))

KEYBOARD_MAIN_MENU: list[list[str]] = [['/create', '/join', '/rules', '/help']]
KEYBOARD_IN_GAME: list[list[str]] = [['/✅', '/❌']]

CHARACTERS_CONFIG: dict[int, dict] = {
    4: {
        'fairy': 1,
        'buka': 1,
        'sandman': 2},
    5: {
        'fairy': 2,
        'buka': 1,
        'sandman': 2},
    6: {
        'fairy': 3,
        'buka': 2,
        'sandman': 1},
    7: {
        'fairy': 3,
        'buka': 2,
        'sandman': 2},
    8: {
        'fairy': 4,
        'buka': 3,
        'sandman': 1},
    9: {
        'fairy': 4,
        'buka': 3,
        'sandman': 2},
    10: {
        'fairy': 5,
        'buka': 4,
        'sandman': 1}}

MESSAGE_CANT_CREATE_OR_JOIN: str = (
    'Сновидец, я вижу, что ты уже участвуешь в одной из игр. Чтобы создать '
    'новую или подключиться к другой, тебе сначала нужно выйти из текущей! '
    'Для этого воспользуйся командой /exit.')
MESSAGE_CREATE_GAME: str = (
    'Приветствую, капитан! Ты готов отправиться со своей командой в новое '
    'путешествие по миру снов? Отлично! Пожалуйста, пришли мне пять цифр ,'
    'которые будут являться паролем к игре!')
MESSAGE_CREATE_GAME_FAILED: str = (
    'Какая удача, капитан! Ты угадал чей-то пароль! А ведь шанс такого '
    'события составляет менее 1%! Невероятно! Пожалуйста, пришли мне иную '
    'комбинацию цифр, попробуем еще раз!')
MESSAGE_CREATE_GAME_PASS: str = (
    'Пароль принят, капитан! Теперь в точности сообщи его своим друзьям, '
    'чтобы они смогли подключиться через команду /join. Когда вся команда '
    'будет в сборе, используй команду /begin для начала игры. Желаю здорово '
    'повеселиться!')
MESSAGE_GREET_1: str = (
    'Добро пожаловать, о чудесный сновидец!\n\n'
    'Сегодня ты отправляешься в невероятное путешествие по миру снов. Миру, '
    'где обитают сказочные создания, вершится магия и процветает фантазия. '
    'Там ты встретишь друзей и врагов, правдолюбов и лжецов, людей искренних '
    'и лицемерных.\n\n'
    'Чтобы успешно пройти через любые испытания тебе нужно проявить смелость, '
    'умение думать на ходу и, конечно же, чувство юмора. Чтобы помочь тебе на '
    'этом пути я высылаю тебе правила игры. Приятных снов!')
MESSAGE_GREET_2: str = (
    'Чтобы создать игровую сессию нажми /create\n'
    'Чтобы присоединиться к игровой сессии нажми /join\n'
    'Чтобы посмотреть правила настольной игры нажми /rules\n'
    'Чтобы получить справку по использованию бота нажми /help')
MESSAGE_INSTRUCTIONS: str = (  # НЕ НАПИСАЛ ДО КОНЦА!!!!!!
    'Как играть через бота:\n\n'

    '0. Сбор команды\n\n'
    'Дорогие друзья! Целью создания данного бота было не сделать игру "Пока '
    'я сплю" доступной в онлайн, а лишь освободить игроков от необходимости '
    'иметь при себе ее физический экземпляр. Я всей душой рекомендую играть '
    'в настолку, только собравшись всем вместе. Лишь в этом случае вы сможете '
    'по-настоящему ощутить атмосферу этой потрясающей игры!\n\n'

    '1. Создание новой игровой сессии\n\n'

    'Для того, чтобы создать игровую сессию, одному из членов команды '
    'необходимо использовать команду /create. В ответном сообщении бот '
    'попросит придумать пароль для игровой сессии из четырех цифр. Его нужно '
    'отправить как обычное сообщение.\n\n'

    '2. Присоединение к существующей игровой сессии\n\n'

    'Чтобы присоединиться к созданной игровой сессии, остальным членам '
    'команды необходимо использовать команду /join. В ответном сообщении бот '
    'попросит ввести пароль. Его нужно отправить как обычное сообщение.'
    'Пароль должен полностью совпадать с придуманным в пункте 1.\n\n'

    '3. Начало игры..... to be continue..'
    
    # добавить пункт, если сервер вылетел!
)

MESSAGE_JOIN_GAME: str = (
    'Приветствую, сновидец! Ты готов отправиться с друзьями в новое '
    'путешествие по миру снов? Отлично! Пожалуйста, пришли мне пароль от '
    'игры, который придумал капитан команды!')
MESSAGE_JOIN_GAME_FAILED: str = (
    'О нет! Приключился неверный пароль! Пожалуйста, уточни у капитана его '
    'еще раз и пришли мне новую комбинацию цифр!')
MESSAGE_JOIN_GAME_PASS: str = (
    'Пароль принят, сновидец! Когда вся команда будет в сборе, капитан '
    'начнет новую игру, а я тебе сразу же пришлю об этом уведомление! '
    'Желаю здорово повеселиться!')

PASSWORD_LEN: int = 5

ROUND_SEC: int = 60 * 2

USER_STATE_JOIN: int = 0
USER_STATE_CREATE: int = 1
USER_STATE_IN_GAME: int = 2

bot: Bot = Bot(token=TELEGRAM_BOT_TOKEN)

cards_seq: list[int] = list(range(5))
shuffle(cards_seq)
rotate_or_not: bool = choice([True, False])

active_games_test: dict[str, dict] = {
    '/game_password': {
        'user_host': '/host_user_chat_id',
        'can_join': '/bool',
        'users': {
            '/user_1_chat_id': {
                'points': '/total_points',
                'name': '/username_full_name)'}},
        'verdicts': ['/user_1_True', '/user_2_True',],
        'correct_answers': '/correct_answers_count',
        'incorrect_answers': '/incorrect_answers_count',
        'penalties': ['/user_1', '/user_3', '/user_3'],
        'cards_seq': cards_seq,
        'last_card': '/last_card_num',
        'round_number': 'round_number'}}
active_games: dict[str, dict] = {}

users_passwords_test: dict[int, int] = {
    '/user_1': '/password_1',
    '/user_2': '/password_5',
    '/user_3': '/password_1'}
users_passwords_test: dict[int, int] = {}

users_states: dict[int, int] = {}

# Admin может добавлять или отнимать баллы к правильным в конце тура!
# И выдать штраф!

# Если карты кончились (чего быть не может) - игра заканчивается.

# А если будет дабл-клик по кнопке?

"""✅✅✅ ГОТОВЫЕ КОМАНДЫ ✅✅✅"""


# Тут бы сделать проверку, что игрок не в игре, чтобы ему кнопки не сбить!
def command_bot_help(update, context) -> None:
    """Send bot manual to user."""
    send_message(
        chat_id=update.effective_chat.id,
        keyboard=KEYBOARD_MAIN_MENU,
        message=MESSAGE_INSTRUCTIONS)
    return


def command_create_game(update, context) -> None:
    """Set user state as USER_STATE_CREATE and ask to come up with password
    for creating new game session."""
    global users_states
    user_id: int = update.effective_chat.id
    users_states[user_id: USER_STATE_CREATE]
    if users_states.get(user_id, None) == USER_STATE_IN_GAME:
        keyboard: list[list[str]] = KEYBOARD_IN_GAME
        message: str = MESSAGE_CANT_CREATE_OR_JOIN
    else:
        users_states[user_id: USER_STATE_JOIN]
        keyboard: list[list[str]] = KEYBOARD_MAIN_MENU
        message: str = MESSAGE_CREATE_GAME
    send_message(
        chat_id=user_id,
        keyboard=keyboard,
        message=message)
    return


# Тут бы сделать проверку, что игрок не в игре, чтобы ему кнопки не сбить!
def command_game_rules(update, context) -> None:
    """Send game rules to user."""
    send_media_group(chat_id=update.effective_chat.id, media=IMAGE_RULES_MEDIA)
    return


def command_join_game(update, context) -> None:
    """Set user state as USER_STATE_JOIN and ask for a password to connect
    the user to an existing game."""
    global users_states
    user_id: int = update.effective_chat.id
    if users_states.get(user_id, None) == USER_STATE_IN_GAME:
        keyboard: list[list[str]] = KEYBOARD_IN_GAME
        message: str = MESSAGE_CANT_CREATE_OR_JOIN
    else:
        users_states[user_id: USER_STATE_JOIN]
        keyboard: list[list[str]] = KEYBOARD_MAIN_MENU
        message: str = MESSAGE_JOIN_GAME
    send_message(
        chat_id=user_id,
        keyboard=keyboard,
        message=message)
    return


def command_start(update, context) -> None:
    """Answer for the first time user runs bot.
    Greet user and sent game rules."""
    chat_id: int = update.effective_chat.id
    if update.effective_chat.type != 'private':
        # Надо бы отправить сообщение, чтобы в л.с. к боту переходили
        # Да и в целом протестировать, что update.effective_chat.type пишет
        bot.leave_chat(chat_id)
    send_message(
        chat_id=chat_id,
        keyboard=KEYBOARD_MAIN_MENU,
        message=MESSAGE_GREET_1)
    send_media_group(
        chat_id=chat_id,
        media=IMAGE_RULES_MEDIA)
    send_message(
        chat_id=chat_id,
        keyboard=KEYBOARD_MAIN_MENU,
        message=MESSAGE_GREET_2)
    return


def message_processing(update, context) -> None:
    global active_games
    global users_states
    user_id: int = update.effective_chat.id
    user_state: int | None = users_states.get(user_id, None)
    if not user_state or user_state == USER_STATE_IN_GAME:
        return
    password: str = update.message.text
    if user_state == USER_STATE_CREATE:
        if match(rf'\d{PASSWORD_LEN}', password):
            user_name: str = None
            users_states[user_id] = USER_STATE_IN_GAME
            active_games[password] = {
                'user_host': user_id,
                'users': {
                    user_id: {
                        'points': 0,
                        'name': user_name}},
                'users_can_join': True,
                'game_verdicts': [None],
                'game_answers_correct': 0,
                'game_answers_incorrect': 0,
                'users_penalties': [None],
                'cards_seq': cards_seq,
                'last_card': -1,
                'round_number': 0}
            message: str = MESSAGE_CREATE_GAME_PASS
            # Вот тут еще надо отправить сообщение капитану со списком команд
        else:
            message: str = MESSAGE_CREATE_GAME_FAILED
    elif user_state == USER_STATE_JOIN:
        if password in active_games:
            user_name: str = None
            users_states[user_id] = USER_STATE_IN_GAME
            active_games[password]['users'][user_id]= {
                user_id: {
                    'points': 0,
                    'name': user_name}}
            message: str = MESSAGE_JOIN_GAME_PASS
            # Вот тут еще надо изменить сообщение капитану со списком команд
        else:
            message: str = MESSAGE_JOIN_GAME_FAILED
    send_message(chat_id=user_id, message=message)
    return
    


"""❌❌❌ В стадии разработки ❌❌❌"""


def command_begin_game(update, context) -> None:
    return


def command_start_game(update, context) -> None:
    return


def command_exit_game(update, context) -> None:
    return


def command_correct_answer(update, context) -> None:
    return


def command_incorrect_answer(update, context) -> None:
    return


def command_next_round(update, context) -> None:
    return


def command_add_penalty(update, context) -> None:
    return


def command_add_correct(update, context) -> None:
    return


def command_add_incorrect(update, context) -> None:
    return


"""⚠️⚠️⚠️ Основные функции ⚠️⚠️⚠️"""


def change_answers_points(password: int, answer: str, points: int) -> None:
    global active_games
    active_games[password][answer] += points
    return


def check_env(data: list) -> None:
    """Checks env data."""
    if not all(data):
        logger.critical('Env data is empty!')
        raise SystemExit
    return


def send_message(
        chat_id: int,
        keyboard: list[list[str]],
        message: str) -> None:
    """Send message to target telegram chat."""
    try:
        bot.send_message(
            chat_id=chat_id,
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
            text=message)
        return
    except TelegramError:
        raise Exception("Bot can't send the message!")


def send_photo(chat_id: int, photo: str, message: str = None) -> None:
    """Send photo with optional message to target telegram chat."""
    try:
        bot.send_photo(caption=message, chat_id=chat_id, photo=photo)
        return
    except TelegramError as err:
        raise Exception(f'Bot failed to send photo-message! Error: {err}')


def send_media_group(
        chat_id: int,
        media: list[InputMediaPhoto]) -> None:
    """Send several photo to target telegram chat."""
    try:
        bot.send_media_group(chat_id=chat_id, media=media)
        return
    except TelegramError as err:
        raise Exception(f'Bot failed to send media! Error: {err}')



if __name__ == '__main__1':
    from pprint import pprint
    pprint(active_games_test)


if __name__ == '__main__':

    try:
        logger.info('Program is running.')
        check_env(data=ALL_DATA)
    except SystemExit as err:
        """Error in code. Program execution is not possible."""
        logger.critical(err)
        raise

    updater: Updater = Updater(token=TELEGRAM_BOT_TOKEN)
    dispatcher: Dispatcher = updater.dispatcher

    # Можно попробовать:
    # dispatcher.chat_data['my_dict'] = my_dict
    # Тогда в функции будет:
    # my_dict = context.chat_data['my_dict']
    for command in [
            ('add_penalty', command_add_penalty),
            ('add_correct', command_add_correct),
            ('add_incorrect', command_add_incorrect),
            ('begin', command_begin_game),
            ('create', command_create_game),            # Done!
            ('exit', command_exit_game),
            ('help', command_bot_help),                 # Done!
            ('join', command_join_game),                # Done!
            ('next_round', command_next_round),
            ('rules', command_game_rules),              # Done!
            ('start', command_start),                   # Done!
            ('correct', command_correct_answer),
            ('incorrect', command_incorrect_answer)]:
        dispatcher.add_handler(CommandHandler(command[0], command[1]))
    dispatcher.add_handler(MessageHandler(Filters.text, message_processing))
    updater.start_polling(poll_interval=API_TELEGRAM_UPDATE_SEC)
