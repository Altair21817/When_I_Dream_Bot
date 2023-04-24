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

TELEGRAM_BOT_TOKEN: str = os.getenv('TELEGRAM_BOT_TOKEN')
ALL_DATA: list[str] = [TELEGRAM_BOT_TOKEN]

API_TELEGRAM_UPDATE_SEC: int = 0.5

# Проверить, что все кнопки реально нужны
# Возможно добавить кнопку, чтобы завершить игру досрочно
BUTTON_ADD_CORRECT: str = '/add_correct'
BUTTON_ADD_INCORRECT: str = '/add_incorrect'
BUTTON_ADD_PENALTY: str = '/add_penalty'
BUTTON_BEGIN: str = '/begin'
BUTTON_BREAK: str = '/break'
BUTTON_CREATE: str = '/create'
BUTTON_CORRECT_ANSWER: str = '/✅'
BUTTON_EXIT: str = '/exit'
BUTTON_HELP: str = '/help'
BUTTON_INCORRECT_ANSWER: str = '/❌'
BUTTON_JOIN: str = '/join'
BUTTON_NEXT_ROUND: str = '/next_round'
BUTTON_RULES: str = '/rules'
BUTTON_START: str = '/start'

# А карты можно отправлять так:
# for i in range(0, round) and range(round, len(players))
IMAGE_CARDS: Path = Path('res/words')
IMAGE_CARDS_СOUNT: int = len(list(IMAGE_CARDS.iterdir()))
IMAGE_RULES: list[Path] = [
    Path(f'res/rules/0{i}_правила.jpg') for i in range(8)]
IMAGE_RULES_MEDIA: list[InputMediaPhoto] = []
for file_path in IMAGE_RULES:
    with open(file_path, 'rb') as file:
        IMAGE_RULES_MEDIA.append(InputMediaPhoto(
            media=file.read(), caption=Path(file_path).name))

KEYBOARD_IN_GAME: list[list[str]] = [
    [BUTTON_CORRECT_ANSWER, BUTTON_INCORRECT_ANSWER]]
KEYBOARD_IN_GAME_PAUSE: list[list[str]] = [
    [BUTTON_EXIT]]
KEYBOARD_IN_GAME_PAUSE_CAPITAN: list[list[str]] = [
    [BUTTON_NEXT_ROUND, BUTTON_EXIT, BUTTON_BREAK],
    [BUTTON_ADD_CORRECT, BUTTON_ADD_INCORRECT, BUTTON_ADD_PENALTY]]
KEYBOARD_IN_LOBBY: list[list[str]] = [
    [BUTTON_EXIT, BUTTON_RULES, BUTTON_HELP]]
KEYBOARD_IN_LOBBY_CAPITAN: list[list[str]] = [
    [BUTTON_BEGIN, BUTTON_EXIT, BUTTON_RULES, BUTTON_HELP]]
KEYBOARD_MAIN_MENU: list[list[str]] = [
    [BUTTON_CREATE, BUTTON_JOIN, BUTTON_RULES, BUTTON_HELP]]

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
    f'Для этого воспользуйся командой {BUTTON_EXIT}.')
MESSAGE_CREATE_GAME: str = (
    'Приветствую, капитан! Ты готов отправиться со своей командой в новое '
    'путешествие по миру снов? Отлично! Пожалуйста, пришли мне пять цифр, '
    'которые будут являться паролем к игре!')
MESSAGE_CREATE_GAME_FAILED: str = (
    'Какая удача, капитан! Ты угадал чей-то пароль! А ведь шанс такого '
    'события составляет менее 1%! Невероятно! Пожалуйста, пришли мне иную '
    'комбинацию цифр, попробуем еще раз!')
MESSAGE_CREATE_GAME_PASS: str = (
    'Пароль принят, капитан! Теперь в точности сообщи его своим друзьям, '
    f'чтобы они смогли подключиться через команду {BUTTON_JOIN}.''\n\n'
    f'Когда вся команда будет в сборе, используй команду {BUTTON_BEGIN} для '
    'начала игры. Желаю здорово повеселиться!\n\n'
    f'А если вдруг ты решишь проснутся - используй команду {BUTTON_EXIT}. '
    'Игра при этом не остановится!\n\n'
    f'Чтобы разбудить всех сновидцев используй команду {BUTTON_BREAK}.')
MESSAGE_LEAVE_GROUP_CHAT: str = (
    'Я могу работать только в личных переписках и вынужден покинуть этот чат!')
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
    f'Нажми {BUTTON_CREATE}, чтобы создать новую игру.''\n'
    f'Нажми {BUTTON_JOIN}, чтобы присоединиться к игре.''\n'
    f'Нажми {BUTTON_RULES}, чтобы посмотреть правила игры.''\n'
    f'Нажми {BUTTON_HELP}, чтобы получить справку по использованию бота.')
MESSAGE_HELP: str = (  # НЕ НАПИСАЛ ДО КОНЦА!!!!!!
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
    'Желаю здорово повеселиться! А если вдруг ты решишь проснутся - используй '
    f'команду {BUTTON_EXIT}.')
MESSAGE_TEAMMATE: str = (
    'Проверь список сновидцев ниже: когда вся команда будет в сборе, нажми '
    f'{BUTTON_BEGIN}, чтобы отправиться в путешествие. Желаю хорошей игры!'
    '\n\n')

PASSWORD_LEN: int = 5

ROUND_SEC: int = 60 * 2

USER_STATE_JOIN: int = 0
USER_STATE_CREATE: int = 1
USER_STATE_IN_GAME: int = 2

bot: Bot = Bot(token=TELEGRAM_BOT_TOKEN)

cards_seq: list[int] = list(range(5))
rotate_or_not: bool = choice([True, False])

# Может быть сделать ачивки:
#   - яркие сны: угадал больше всего слов
#   - сон на яву: угадал верно все слова
#   - сущий кошмар: не отгадал ни одного слова
#   - крестная фея: заработал больше всего очков среди фея
#   - бу-бу-бука: заработал больше всего очков как бука
#   - лицемерище: заработал больше всего очков как песочный человек
#   - кайфоломщик: получил больше всего пенальти
_active_games_test: dict[str, dict] = {
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

_users_passwords_test: dict[int, int] = {
    '/user_1': '/password_1',
    '/user_2': '/password_5',
    '/user_3': '/password_1'}
users_passwords: dict[int, int] = {}

users_states: dict[int, int] = {}

# Admin может добавлять или отнимать баллы к правильным в конце тура!
# И выдать штраф!

# Если карты кончились (чего быть не может) - игра заканчивается.

# А если будет дабл-клик по кнопке?

# Сделать проверку, что игрок не в игре, чтобы ему кнопки не сбить!

"""✅✅✅ ГОТОВЫЕ КОМАНДЫ ✅✅✅"""


def command_begin(update, context) -> None:
    return


def command_create_game(update, context) -> None:
    """Set user state as USER_STATE_CREATE and ask to come up with password
    for creating new game session."""
    global users_states
    user_id: int = update.effective_chat.id
    if users_states.get(user_id, None) == USER_STATE_IN_GAME:
        message: str = MESSAGE_CANT_CREATE_OR_JOIN
    else:
        users_states[user_id] = USER_STATE_CREATE
        message: str = MESSAGE_CREATE_GAME
    send_message(chat_id=user_id, message=message)
    return


def command_exit(update, context) -> None:
    # Надо отработать вариант, когда уходит капитан и надо передать управление
    # А еще лучше - сделать управление по кругу
    global users_passwords
    user_id: int = update.effective_chat.id
    if user_id not in users_passwords:
        return
    global active_games
    global users_states
    password = users_passwords[user_id]
    username = active_games[password]['users'][user_id]['name']
    active_games[password]['users'].pop(user_id, None)
    users_states.pop(user_id, None)
    if active_games[password]['users_can_join']:
        update_teammate_message(active_games=active_games, password=password)
    else:
        send_message(
            chat_id=active_games[password]['user_host'],
            message=f'Сновидец {username} проснулся!',
            ReplyKeyboardMarkup=KEYBOARD_IN_GAME_PAUSE_CAPITAN) # Проверить!
    return


def command_help(update, context) -> None:
    """Send bot manual to user and pin message."""
    chat_id: int = update.effective_chat.id
    message: any = send_message(chat_id=chat_id, message=MESSAGE_HELP)
    bot.pinChatMessage(chat_id=chat_id, message_id=message.message_id)
    return


def command_join_game(update, context) -> None:
    """Set user state as USER_STATE_JOIN and ask for a password to connect
    the user to an existing game."""
    global users_states
    user_id: int = update.effective_chat.id
    if users_states.get(user_id, None) == USER_STATE_IN_GAME:
        message: str = MESSAGE_CANT_CREATE_OR_JOIN
    else:
        users_states[user_id] = USER_STATE_JOIN
        message: str = MESSAGE_JOIN_GAME
    send_message(chat_id=user_id, message=message)
    return


def command_rules(update, context) -> None:
    """Send game rules to user and pin message."""
    chat_id: int = update.effective_chat.id
    message: any = send_media_group(chat_id=chat_id, media=IMAGE_RULES_MEDIA)
    bot.pinChatMessage(chat_id=chat_id, message_id=message.message_id)
    return


def command_start(update, context) -> None:
    """Answer for the first time user runs bot.
    Greet user and sent game rules."""
    global users_states
    chat_id: int = update.effective_chat.id
    if update.effective_chat.type != 'private':
        send_message(chat_id=chat_id, message=MESSAGE_LEAVE_GROUP_CHAT)
        bot.leave_chat(chat_id)
    if chat_id in users_states:
        return
    send_message(chat_id=chat_id, message=MESSAGE_GREET_1)
    command_rules(update, context)
    send_message(
        chat_id=chat_id, keyboard=KEYBOARD_MAIN_MENU, message=MESSAGE_GREET_2)
    return


def message_processing(update, context) -> None:
    """Check user message. Update active_games if message match password and
    user can host or join the game. Also bound user_id with the game throw
    users_states."""
    global active_games
    global users_passwords
    global users_states
    update_teammate: bool = False
    user_id: int = update.effective_chat.id
    user_state: int | None = users_states.get(user_id, None)
    if not user_state or user_state == USER_STATE_IN_GAME:
        return
    password: str = update.message.text
    if match(rf'\d{PASSWORD_LEN}', password):
        update_teammate: bool = True
        user_name: str = represent_user(update)
        users_states[user_id] = USER_STATE_IN_GAME
        users_passwords[user_id] = password
        if user_state == USER_STATE_CREATE:
            active_games[password] = {
                'user_host': user_id,
                'teammate_message_id': None,
                'users': {user_id: represent_user_data(user_name)},
                'users_can_join': True,
                'game_verdicts': [None],
                'game_answers_correct': 0,
                'game_answers_incorrect': 0,
                'users_penalties': [None],
                'cards_seq': shuffle(cards_seq),
                'last_card': -1,
                'round_number': 0}
            message: str = MESSAGE_CREATE_GAME_PASS
        elif user_state == USER_STATE_JOIN:
            active_games[password]['users'][
                user_id] = represent_user_data(user_name)
            message: str = MESSAGE_JOIN_GAME_PASS
    else:
        if user_state == USER_STATE_CREATE:
            message: str = MESSAGE_CREATE_GAME_FAILED
        elif user_state == USER_STATE_JOIN:
            message: str = MESSAGE_JOIN_GAME_FAILED
    send_message(
        chat_id=user_id,
        message=message,
        ReplyKeyboardMarkup=KEYBOARD_IN_LOBBY)
    if update_teammate:
        update_teammate_message(active_games=active_games, password=password)
    return


def represent_user(update) -> str:
    """Get user data and return his name."""
    user = update.callback_query.from_user
    user_first_name: str = user.first_name
    user_second_name: str = user.second_name
    user_username: str = user.username
    if not user_first_name:
        user_first_name: str = ''
    if not user_second_name:
        user_second_name: str = ''
    if not user_username:
        return f'{user_first_name} {user_second_name}'
    return f'{user_first_name} {user_second_name} @{user_username}'


def represent_user_data(username: str) -> dict[str, any]:
    """Create user data to include in active_game['users']."""
    return {'name': username,
            'points': 0,
            'points_as_fairy': 0,
            'points_as_buka': 0,
            'points_as_sandman': 0,
            'perfect_round': 0,
            'guess_all_times': 0,
            'guess_none_times': 0}


def update_teammate_message(
        active_games: dict[str, dict],
        password: int) -> None:
    """Send (or edit) message to user_host with joined teammates."""
    chat_id: int = active_games[password]['user_host']
    message_id: int = active_games[password]['teammate_message_id']
    text: str = (
        MESSAGE_TEAMMATE + '\n'.join(
            user['name'] for user in active_games[password]['users'].values()))
    if message_id:
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=text,
            ReplyKeyboardMarkup=KEYBOARD_IN_LOBBY_CAPITAN)
    else:
        message = send_message(
            chat_id=chat_id,
            message=text,
            ReplyKeyboardMarkup=KEYBOARD_IN_LOBBY_CAPITAN)
        active_games[password]['teammate_message_id'] = message.message_id
    return


"""❌❌❌ В стадии разработки ❌❌❌"""


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


# Если отредактировать сообщение: пропадут ли кнопки?
def edit_message(chat_id: int, message_id: int, text: str) -> None:
    """Edit message with given message_id in target telegram chat."""
    bot.edit_message_text(
            chat_id=chat_id, message_id=message_id, text=text)
    return


def send_message(
        chat_id: int,
        message: str,
        keyboard: list[list[str]] = None) -> None:
    """Send message to target telegram chat."""
    try:
        if keyboard:
            bot.send_message(
                chat_id=chat_id,
                reply_markup=ReplyKeyboardMarkup(
                    keyboard, resize_keyboard=True),
                text=message)
        else:
            bot.send_message(chat_id=chat_id, text=message)
        return
    # Вот эти ошибки не перехватываются, надо их писать в логи и пропускать
    # В целом логов не так много
    except TelegramError:
        raise Exception("Bot can't send the message!")


def send_photo(chat_id: int, photo: str, message: str = None) -> None:
    """Send photo with optional message to target telegram chat."""
    try:
        bot.send_photo(caption=message, chat_id=chat_id, photo=photo)
        return
    except TelegramError as err:
        raise Exception(f'Bot failed to send photo-message! Error: {err}')


def send_media_group(chat_id: int, media: list[InputMediaPhoto]) -> None:
    """Send several photo to target telegram chat."""
    try:
        bot.send_media_group(chat_id=chat_id, media=media)
        return
    except TelegramError as err:
        raise Exception(f'Bot failed to send media! Error: {err}')


if __name__ == '__main__1':
    from pprint import pprint
    


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
            (BUTTON_ADD_CORRECT, command_add_correct),
            (BUTTON_ADD_INCORRECT, command_add_incorrect),
            (BUTTON_ADD_PENALTY, command_add_penalty),
            (BUTTON_BEGIN, command_begin),
            (BUTTON_CREATE, command_create_game),                 # Done!
            (BUTTON_CORRECT_ANSWER, command_correct_answer),
            (BUTTON_EXIT, command_exit),
            (BUTTON_HELP, command_help),                          # Done!
            (BUTTON_INCORRECT_ANSWER, command_incorrect_answer),
            (BUTTON_JOIN, command_join_game),                     # Done!
            (BUTTON_NEXT_ROUND, command_next_round),
            (BUTTON_RULES, command_rules),                        # Done!
            (BUTTON_START, command_start)]:                       # Done!
        dispatcher.add_handler(CommandHandler(command[0], command[1]))
    dispatcher.add_handler(MessageHandler(Filters.text, message_processing))
    updater.start_polling(poll_interval=API_TELEGRAM_UPDATE_SEC)
