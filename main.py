from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging
import os
from pathlib import Path
from random import shuffle
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
# Вообще надо нарисовать карту возможных развитий событий тыканья кнопок
BUTTON_ADD_ME_PENALTY: str = '/add_me_penalty'
BUTTON_BEGIN: str = '/begin'
BUTTON_CREATE: str = '/create'
BUTTON_CORRECT_ANSWER: str = '/YES'
BUTTON_EXIT: str = '/exit'
BUTTON_HELP: str = '/help'
BUTTON_INCORRECT_ANSWER: str = '/NO'
BUTTON_JOIN: str = '/join'
BUTTON_RULES: str = '/rules'
BUTTON_START: str = '/start'
BUTTON_START_NEXT_ROUND: str = '/next_round'

# А карты можно отправлять так:
# for i in range(0, round) and range(round, len(players))
IMAGE_CARDS_ORIGINAL_PATH: Path = Path('res/words_original')
IMAGE_CARDS_ROTATED_PATH: Path = Path('res/words_rotated')
IMAGE_CARDS: list[Path] = (
    list(IMAGE_CARDS_ORIGINAL_PATH.iterdir())
    + list(IMAGE_CARDS_ROTATED_PATH.iterdir()))
IMAGE_RULES: list[Path] = [
    Path(f'res/rules/0{i}_правила.jpg') for i in range(8)]
IMAGE_RULES_MEDIA: list[InputMediaPhoto] = []
for file_path in IMAGE_RULES:
    with open(file_path, 'rb') as file:
        IMAGE_RULES_MEDIA.append(InputMediaPhoto(
            media=file.read(), caption=Path(file_path).name))

KEYBOARD_EMPTY: list[list[str]] = [
    ['']]
KEYBOARD_IN_GAME: list[list[str]] = [
    [BUTTON_CORRECT_ANSWER, BUTTON_ADD_ME_PENALTY, BUTTON_INCORRECT_ANSWER]]
KEYBOARD_IN_LOBBY: list[list[str]] = [
    [BUTTON_RULES, BUTTON_HELP, BUTTON_EXIT]]
KEYBOARD_IN_LOBBY_HOST: list[list[str]] = [
    [BUTTON_BEGIN, BUTTON_RULES, BUTTON_HELP, BUTTON_EXIT]]
KEYBOARD_MAIN_MENU: list[list[str]] = [
    [BUTTON_CREATE, BUTTON_JOIN, BUTTON_RULES, BUTTON_HELP]]
KEYBOARD_START_NEXT_ROUND: list[list[str]] = [
    [BUTTON_START_NEXT_ROUND, BUTTON_EXIT]]

BUKA: str = 'buka'
DREAMER: str = 'dreamer'
FAIRY: str = 'fairy'
SANDMAN: str = 'sandman'
CHARACTERS_CONFIG: dict[int, dict] = {
    3:  {BUKA: 1, FAIRY: 1, SANDMAN: 1},
    4:  {BUKA: 1, FAIRY: 1, SANDMAN: 2},
    5:  {BUKA: 1, FAIRY: 2, SANDMAN: 2},
    6:  {BUKA: 2, FAIRY: 3, SANDMAN: 1},
    7:  {BUKA: 2, FAIRY: 3, SANDMAN: 2},
    8:  {BUKA: 3, FAIRY: 4, SANDMAN: 1},
    9:  {BUKA: 3, FAIRY: 4, SANDMAN: 2},
    10: {BUKA: 4, FAIRY: 5, SANDMAN: 1}}

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
    'Игра при этом не остановится!')
MESSAGE_GAME_BEGIN: str = (
    'Твое путешествие начинается через.. 3.. 2.. 1.. Сейчас!')
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
MESSAGE_LEAVE_GROUP_CHAT: str = (
    'Я могу работать только в личных переписках и вынужден покинуть этот чат!')
MESSAGE_NEXT_ROUND: str = (
    'В следующем раунде ты будешь сновидцем, остальные игроки - волшебными '
    f'созданиями. Когда все будут готовы, нажми {KEYBOARD_START_NEXT_ROUND}.')
MESSAGE_TEAMMATE: str = (
    'Проверь список сновидцев ниже: когда вся команда будет в сборе, нажми '
    f'{BUTTON_BEGIN}, чтобы отправиться в путешествие. Желаю хорошей игры!'
    '\n\n')
MESSAGE_PLAYER_MUST_SLEEP: str = (
    'Теперь закрывай глаза, баю-бай. Игра началась!')
MESSAGE_PLAYER_ROLE: dict[str, str] = {
    BUKA: (
        'В этом раунде ты будешь грозной букой. Обманывай сновидца, сбивай '
        'его с пути, преврати его сны в кошмары! Важно, чтобы сновидец не '
        'отгадал ни единого слова!'),
    FAIRY: (
        'В этом раунде ты будешь доброй феей. Всячески помогай сновидцу '
        'пройти по его нелегкому пути. Важно, чтобы сновидец отгадал '
        'все-все-все слова!'),
    SANDMAN: (
        'В этом раунде ты будешь песочным человеком. Поддерживай хрупкий мир '
        'снов в гармонии. Помогай сновидцу отбиваться от кошмаров, если он не '
        'справляется, сбивай его с пути, если путь его слишком легок. Важно, '
        'чтобы сновидец отгадал половину слов!')}
MESSAGE_ROUND_RESULTS: str = (
    'Та-да! А вот и утро! Но перед тем как будить нашего спящего '
    'путешественника, попросите его в мельчайших подробностях рассказать свой '
    'сон. Пусть это будет абсолютный полет фантазии, полный внезапных '
    'сумасбродных сюжетных поворотов!\n\n'
    'Кстати, а вот такие получились результаты раунда:\n'
    '- слов угадано верно: {correct_answers}\n'
    '- слов угадано неверно: {incorrect_answers}')

PASSWORD_LEN: int = 5

ROUND_SEC: int = 60 * 2

SHUFFLE_IMAGE_WORDS_COUNT: int = 3

USER_STATE_WANT_JOIN: int = 0
USER_STATE_WANT_CREATE: int = 1
USER_STATE_IN_GAME: int = 2

bot: Bot = Bot(token=TELEGRAM_BOT_TOKEN)

# Может быть сделать ачивки:
#   - яркие сны: угадал больше всего слов
#   - сон на яву: угадал верно все слова
#   - сущий кошмар: не отгадал ни одного слова
#   - крестная фея: заработал больше всего очков среди фея
#   - бу-бу-бука: заработал больше всего очков как бука
#   - лицемерище: заработал больше всего очков как песочный человек
#   - кайфоломщик: получил больше всего пенальти

active_games: dict[str, dict[str, any]] = {}
# А вот непонятно - тут int или не int будет приходить, скорее всего str
users_passwords: dict[int, int] = {}
users_states: dict[int, int] = {}

# Admin может добавлять или отнимать баллы к правильным в конце тура!
# И выдать штраф!

# Если карты кончились (чего быть не может) - игра заканчивается.

# А если будет дабл-клик по кнопке?

# Сделать проверку, что игрок не в игре, чтобы ему кнопки не сбить!

# Рассмотреть 2 ситуации
#   - когда уходит игрок, который сыграл
#   - когда уходит игрок, который не сыграл


def check_env(data: list) -> None:
    """Checks env data."""
    if not all(data):
        logger.critical('Env data is empty!')
        raise SystemExit
    return


def command_add_penalty(update, context) -> None:
    """Add penalty to user if user in game."""
    global active_games
    global users_passwords
    user_id: int = update.effective_chat.id
    password: str | None = users_passwords.get(user_id, None)
    if (password is None
            or password not in active_games
            or not active_games[password]['game_started']):
        return
    active_games[password]['users'][user_id]['penalties_total'] += 1
    return


def command_begin(update, context) -> None:
    """Begin game session."""
    global active_games
    user_id: int = update.effective_chat.id
    password: str | None = users_passwords.get(user_id, None)
    if password is None:
        return
    game: dict[str, any] | None = active_games.get(password, None)
    if game is None or user_id != game['user_host'] or game['game_started']:
        return
    for user in game['users']:
        send_message(
            chat_id=user,
            message=MESSAGE_GAME_BEGIN,
            keyboard=KEYBOARD_IN_LOBBY)
    send_message(
        chat_id=game['user_host'],
        message=MESSAGE_NEXT_ROUND,
        keyboard=KEYBOARD_START_NEXT_ROUND)
    active_games[password]['game_started'] = True
    return


def command_correct_answer(update, context) -> None:
    """Send True to update_game_votes."""
    update_game_votes(update=update, vote=True)
    return


def command_create_game(update, context) -> None:
    """Set user state as USER_STATE_CREATE and ask to come up with password
    for creating new game session."""
    global users_states
    user_id: int = update.effective_chat.id
    user_state: int | None = users_states.get(user_id, None)
    if user_state is None or user_state == USER_STATE_IN_GAME:
        message: str = MESSAGE_CANT_CREATE_OR_JOIN
    else:
        users_states[user_id] = USER_STATE_WANT_CREATE
        message: str = MESSAGE_CREATE_GAME
    send_message(chat_id=user_id, message=message)
    return


def command_exit(update, context) -> None:
    """Delete user game state and exclude user from game."""
    # Вот тут надо передать права хоста следующему по списку
    global users_passwords
    user_id: int = update.effective_chat.id
    password: str | None = users_passwords.get(user_id, None)
    if password is None:
        return
    global active_games
    global users_states
    game: dict[str, any] = active_games.get(password, None)
    if game is None:
        return
    username: str = game['users'][user_id]['name']
    active_games[password]['users'].pop(user_id, None)
    users_states.pop(user_id, None)
    if len(active_games[password]['users']) == 0:
        active_games.pop(password, None)
    elif not active_games[password]['game_started']:
        update_teammate_message(active_games=active_games, password=password)
    else:
        send_message(
            chat_id=active_games[password]['user_host'],
            message=f'Сновидец {username} проснулся!')
    return


def command_help(update, context) -> None:
    """Send bot manual to user and pin message."""
    chat_id: int = update.effective_chat.id
    # Вот тут - уедут ли кнопки..
    message: any = send_message(chat_id=chat_id, message=MESSAGE_HELP)
    bot.pinChatMessage(chat_id=chat_id, message_id=message.message_id)
    return


def command_incorrect_answer(update, context) -> None:
    """Send False to update_game_votes."""
    update_game_votes(update=update, vote=False)
    return


def command_join_game(update, context) -> None:
    """Set user state as USER_STATE_JOIN and ask for a password to connect
    the user to an existing game."""
    global users_states
    user_id: int = update.effective_chat.id
    user_state: int | None = users_states.get(user_id, None)
    if user_state is None or user_state == USER_STATE_IN_GAME:
        message: str = MESSAGE_CANT_CREATE_OR_JOIN
    else:
        users_states[user_id] = USER_STATE_WANT_JOIN
        message: str = MESSAGE_JOIN_GAME
    send_message(chat_id=user_id, message=message)
    return


def command_next_round(update, context) -> None:
    """Shuffle roles and start new game round."""
    # Предусмотреть, чтобы не было двойного нажатия
    global active_games
    global users_passwords
    user_id: int = update.effective_chat.id
    password: str | None = users_passwords.get(user_id, None)
    if (password is None
            or password not in active_games
            or not active_games[password]['game_started']):
        return
    round_number: int = active_games[password]['round_number']
    users_list: list[int] = list(active_games[password]['users'].keys())
    if user_id != users_list[round_number]:
        return
    send_message(
        chat_id=user_id,
        message=MESSAGE_PLAYER_MUST_SLEEP,
        keyboard=KEYBOARD_EMPTY)
    users_list.pop(user_id)
    characters_config: dict[str, int] = CHARACTERS_CONFIG[len(users_list)]
    available_characters: list[str] = []
    for character, count in characters_config.items():
        available_characters.extend([character] * count)
    shuffle(available_characters)
    for user in users_list:
        current_role: str = available_characters.pop()
        active_games[password]['users'][
            user]['current_role'] = current_role
        send_message(
            chat_id=user,
            message=MESSAGE_PLAYER_ROLE[current_role],
            keyboard=KEYBOARD_IN_GAME)
    active_games[password]['users'][user_id]['current_role'] = DREAMER
    active_games[password]['users'][user_id][
        'round_end_time'] = datetime.now() + timedelta(seconds=ROUND_SEC)
    send_next_word_image(active_games=active_games, password=password)
    return


def command_rules(update, context) -> None:
    """Send game rules to user and pin message."""
    chat_id: int = update.effective_chat.id
    # Вот тут - уедут ли кнопки..
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


def finish_game(
        active_games: dict[str, dict[str, any]],
        password: int) -> None:
    """"""
    active_games.pop(password)
    pass


def finish_round(
        active_games: dict[str, dict[str, any]],
        password: int) -> None:
    """Add personal points to each user for ended round.
    Finish game and form achievements and results if all rounds are passed."""
    correct_answers: int = active_games[password]['round_answers_correct']
    incorrect_answers: int = active_games[password]['round_answers_incorrect']
    message = MESSAGE_ROUND_RESULTS.format(
        correct_answers=correct_answers, incorrect_answers=incorrect_answers)
    for user, user_data in active_games[password]['users'].items():
        user_role: str = user_data['current_role']
        if user_role == BUKA:
            active_games[password]['users'][user][
                'points_as_buka'] += incorrect_answers
        elif user_role == DREAMER:
            active_games[password]['users'][user][
                    'points_as_dreamer'] += correct_answers
            if incorrect_answers == 0:
                active_games[password]['users'][user][
                    'guess_all_words'] = True
            elif correct_answers == 0:
                active_games[password]['users'][user][
                    'guess_none_words'] = True
        elif user_role == FAIRY:
            active_games[password]['users'][user][
                'points_as_fairy'] += correct_answers
        else:
            if correct_answers == incorrect_answers:
                sandman_points: int = correct_answers + 2
            elif abs(correct_answers - incorrect_answers) == 1:
                sandman_points: int = max(correct_answers, incorrect_answers)
            else:
                sandman_points: int = min(correct_answers, incorrect_answers)
            active_games[password]['users'][user][
                'points_as_sandman'] += sandman_points
        send_message(
            chat_id=user,
            message=message,
            keyboard=KEYBOARD_IN_LOBBY)
    active_games[password]['round_answers_correct'] = 0
    active_games[password]['round_answers_incorrect'] = 0
    active_games[password]['round_number'] += 1
    round_number: int = active_games[password]['round_number']
    if round_number < (len(active_games[password]['users']) - 1):
        send_message(
            chat_id=list(active_games[password]['users'].keys())[round_number],
            message=MESSAGE_NEXT_ROUND,
            keyboard=KEYBOARD_START_NEXT_ROUND)
    else:
        finish_game()
    return


# Если отредактировать сообщение: пропадут ли кнопки?
def edit_message(chat_id: int, message_id: int, text: str) -> None:
    """Edit message with given message_id in target telegram chat."""
    bot.edit_message_text(
            chat_id=chat_id, message_id=message_id, text=text)
    return


def message_processing(update, context) -> None:
    """Check user message. Update active_games if message match password and
    user can host or join the game. Also bound user_id with the game throw
    users_states."""
    global active_games
    global users_passwords
    global users_states
    update_teammates: bool = False
    user_id: int = update.effective_chat.id
    user_state: int | None = users_states.get(user_id, None)
    if user_state not in (USER_STATE_WANT_JOIN, USER_STATE_WANT_CREATE):
        return
    password: str = update.message.text
    if match(rf'\d{PASSWORD_LEN}', password):
        update_teammates: bool = True
        user_name: str = represent_user(update)
        users_states[user_id] = USER_STATE_IN_GAME
        users_passwords[user_id] = password
        if user_state == USER_STATE_WANT_CREATE:
            for _ in range(SHUFFLE_IMAGE_WORDS_COUNT):
                shuffle(IMAGE_CARDS)
            # А может user_host не хранить, а брать первый элемент users?
            active_games[password] = {
                'user_host': user_id,
                'teammates_message_id': None,
                'game_started': False,
                'cards_seq': IMAGE_CARDS,
                'users': {user_id: represent_user_data(user_name)},
                'votes': [],
                'voted_users': [],
                'round_answers_correct': 0,
                'round_answers_incorrect': 0,
                'next_word_image': 0,
                'round_number': 0,
                'round_end_time': None}
            message: str = MESSAGE_CREATE_GAME_PASS
        else:
            active_games[password]['users'][
                user_id] = represent_user_data(user_name)
            message: str = MESSAGE_JOIN_GAME_PASS
    else:
        if user_state == USER_STATE_WANT_CREATE:
            message: str = MESSAGE_CREATE_GAME_FAILED
        else:
            message: str = MESSAGE_JOIN_GAME_FAILED
    send_message(
        chat_id=user_id,
        message=message,
        ReplyKeyboardMarkup=KEYBOARD_IN_LOBBY)
    if update_teammates:
        update_teammate_message(active_games=active_games, password=password)
    return


def represent_user(update) -> str:
    """Get user data and return his name."""
    user: any = update.callback_query.from_user
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
    return {
        'current_role': None,
        'guess_all_words': False,
        'guess_none_words': False,
        'user_name': username,
        'penalties_total': 0,
        'points_as_buka': 0,
        'points_as_dreamer': 0,
        'points_as_fairy': 0,
        'points_as_sandman': 0,
        'points_total': 0}


def send_media_group(chat_id: int, media: list[InputMediaPhoto]) -> None:
    """Send several photo to target telegram chat."""
    try:
        bot.send_media_group(chat_id=chat_id, media=media)
        return
    except TelegramError as err:
        raise Exception(f'Bot failed to send media! Error: {err}')


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
    # Сделать отдельную функцию, которая бы отправляла бы ошибки мне
    except TelegramError:
        raise Exception("Bot can't send the message!")


def send_next_word_image(
        active_games: dict[str, dict[str, any]],
        password: int) -> None:
    """Send game word (image) to players except the dreamer."""
    round_number: int = active_games[password]['round_number']
    users_list: list[int] = list(active_games[password]['users'].keys())
    users_list.pop(users_list[round_number])
    next_photo_number: int = active_games[password]['next_word_image']
    next_photo: Path = active_games[password]['cards_seq'][next_photo_number]
    for user in users_list:
        send_photo(chat_id=user, photo=next_photo)
    active_games[password]['next_word_image'] += 1
    return


def send_photo(chat_id: int, photo: str, message: str = None) -> None:
    """Send photo with optional message to target telegram chat."""
    try:
        bot.send_photo(caption=message, chat_id=chat_id, photo=photo)
    except TelegramError as err:
        raise Exception(f'Bot failed to send photo-message! Error: {err}')
    return


def update_game_votes(update, vote: int):
    """Update active_game votes.
    If all users voted update round_answers.
    If round time's up - finish round."""
    # Везде ли писать user_id?
    global active_games
    global users_passwords
    user_id: int = update.effective_chat.id
    password: str | None = users_passwords.get(user_id, None)
    if (password is None
            or password not in active_games
            or not active_games[password]['game_started']
            or user_id in active_games[password]['voted_users']):
        return
    active_games[password]['votes'].append(vote)
    active_games[password]['voted_users'].append(user_id)
    """Voted users are always 1 less than total because dreamer can't vote."""
    if len(active_games[password]['voted_users']) != (
            len(active_games[password]['users'] - 1)):
        return
    count_true: int = active_games[password]['votes'].count(True)
    count_false: int = active_games[password]['votes'].count(False)
    if count_true >= count_false:
        active_games[password]['round_answers_correct'] += 1
    else:
        active_games[password]['round_answers_incorrect'] += 1
    active_games[password]['votes'] = []
    active_games[password]['voted_users'] = []
    if datetime.now() < active_games[password]['round_end_time']:
        send_next_word_image(active_games=active_games, password=password)
    else:
        finish_round(active_games=active_games, password=password)
    return


def update_teammate_message(
        active_games: dict[str, dict],
        password: int) -> None:
    """Send (or edit) message to user_host with joined teammates."""
    chat_id: int = active_games[password]['user_host']
    message_id: int | None = active_games[password]['teammate_message_id']
    text: str = (
        MESSAGE_TEAMMATE + '\n'.join(
            user['name'] for user in active_games[password]['users'].values()))
    if message_id:
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=text,
            ReplyKeyboardMarkup=KEYBOARD_IN_LOBBY_HOST)
    else:
        message = send_message(
            chat_id=chat_id,
            message=text,
            ReplyKeyboardMarkup=KEYBOARD_IN_LOBBY_HOST)
        active_games[password]['teammate_message_id'] = message.message_id
    return


if __name__ == '__main__1':
    # from pprint import pprint
    pass


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
            (BUTTON_ADD_ME_PENALTY, command_add_penalty),
            (BUTTON_BEGIN, command_begin),
            (BUTTON_CREATE, command_create_game),
            (BUTTON_CORRECT_ANSWER, command_correct_answer),
            (BUTTON_EXIT, command_exit),
            (BUTTON_HELP, command_help),
            (BUTTON_INCORRECT_ANSWER, command_incorrect_answer),
            (BUTTON_JOIN, command_join_game),
            (BUTTON_RULES, command_rules),
            (BUTTON_START, command_start),
            (BUTTON_START_NEXT_ROUND, command_next_round)]:
        dispatcher.add_handler(CommandHandler(command[0], command[1]))
    dispatcher.add_handler(MessageHandler(Filters.text, message_processing))
    updater.start_polling(poll_interval=API_TELEGRAM_UPDATE_SEC)
