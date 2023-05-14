from datetime import datetime, timedelta
import logging
import os
from pathlib import Path
from random import shuffle
from re import match
from telegram import Bot, InputMediaPhoto, ReplyKeyboardMarkup, TelegramError
from telegram.ext import (
    CommandHandler, Dispatcher, Filters, MessageHandler, Updater)
import sys

import app_logger

from app_data import (
    ALL_DATA, TELEGRAM_BOT_TOKEN,
    ACHIEVEMENTS, ACHIEVEMENTS_KEYS_GUESS, ACHIEVEMENTS_KEYS_OTHER,

    BUTTON_ADD_ME_PENALTY, BUTTON_BEGIN, BUTTON_CREATE, BUTTON_CORRECT_ANSWER,
    BUTTON_EXIT, BUTTON_HELP, BUTTON_INCORRECT_ANSWER, BUTTON_JOIN,
    BUTTON_RULES, BUTTON_START, BUTTON_START_NEXT_ROUND,

    IMAGE_CARDS, IMAGE_CHARACTERS, IMAGE_RULES_MEDIA,

    KEYBOARD_EMPTY, KEYBOARD_IN_GAME, KEYBOARD_IN_LOBBY,
    KEYBOARD_IN_LOBBY_HOST, KEYBOARD_MAIN_MENU, KEYBOARD_START_NEXT_ROUND,

    BUKA, DREAMER, FAIRY, CHARACTERS_CONFIG, USERS_MAX, USERS_MIN,

    MESSAGE_CANT_BEGIN, MESSAGE_CANT_CREATE_OR_JOIN, MESSAGE_CREATE_GAME,
    MESSAGE_CREATE_GAME_FAILED, MESSAGE_CREATE_GAME_PASS, MESSAGE_GAME_BEGIN,
    MESSAGE_GREET_1, MESSAGE_GREET_2, MESSAGE_HELP, MESSAGE_JOIN_GAME,
    MESSAGE_JOIN_GAME_FAILED, MESSAGE_JOIN_GAME_FAILED_TO_MUCH_USERS, 
    MESSAGE_JOIN_GAME_PASS, MESSAGE_IN_GAME_BUTTONS_INSTRUCTIONS,
    MESSAGE_LEAVE_GROUP_CHAT, MESSAGE_NEXT_ROUND, MESSAGE_TEAMMATE,
    MESSAGE_PLAYER_MUST_SLEEP, MESSAGE_PLAYER_ROLE, MESSAGE_ROUND_RESULTS,

    USER_STATE_WANT_JOIN, USER_STATE_WANT_CREATE, USER_STATE_IN_GAME)

from app_settings import (
    API_TELEGRAM_UPDATE_SEC, PASSWORD_LEN, ROUND_SEC,
    SHUFFLE_IMAGE_WORDS_COUNT)

logger: logging.Logger = app_logger.get_logger(__name__)

bot: Bot = Bot(token=TELEGRAM_BOT_TOKEN)

active_games: dict[str, dict[str, any]] = {}
users_passwords: dict[int, int] = {}
users_states: dict[int, int] = {}

# А если будет дабл-клик по кнопке?
# Сделать проверку, что игрок не в игре, чтобы ему кнопки не сбить!

# Рассмотреть 2 ситуации
#   - когда уходит игрок, который сыграл
#   - когда уходит игрок, который не сыграл


# Только один параметр!
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
    if len(game['users']) not in range(USERS_MIN, USERS_MAX + 1):
        send_message(
            chat_id=game['user_host'],
            message=MESSAGE_CANT_BEGIN.format(users_count=len(game['users'])))
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
    active_games[password]['users'][user_id]['current_role'] = DREAMER
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
        send_photo(
            chat_id=user,
            photo=IMAGE_CHARACTERS[current_role],
            message=MESSAGE_PLAYER_ROLE[current_role])
        send_message(
            chat_id=user,
            message=MESSAGE_IN_GAME_BUTTONS_INSTRUCTIONS,
            keyboard=KEYBOARD_IN_GAME)
    active_games[password]['round_end_time'] = (
        datetime.now() + timedelta(seconds=ROUND_SEC))
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
    """Send game results to each user.
    Delete users from users_passwords, users_states.
    Delete game from active_games."""
    global users_passwords
    global users_states
    achievements = {
        'guess_all_words': [],
        'guess_none_words': [],
        'points_total': [0, None],
        'points_dreamer': [0, None],
        'points_fairy': [0, None],
        'points_buka': [0, None],
        'points_sandman': [0, None],
        'points_penalty': [0, None]}
    results: list[tuple[int, str]] = []
    for user_data in active_games[password]['users'].values():
        username = user_data['user_name']
        user_data['points_total'] = (
            user_data['points_buka']
            + user_data['points_dreamer']
            + user_data['points_fairy']
            + user_data['points_sandman']
            - user_data['points_penalty'])
        results.append((
            user_data['points_total'] - user_data['points_penalty'],
            username))
        for key in ACHIEVEMENTS_KEYS_GUESS:
            if user_data[key]:
                achievements[key].append(username)
        for key in ACHIEVEMENTS_KEYS_OTHER:
            if user_data[key] == achievements[key][0]:
                achievements[key].append(username)
            elif user_data[key] > achievements[key][0]:
                achievements[key] = [user_data[key], username]
    results.sort(reverse=True)
    results_list: list[str] = ['🏆 Результаты путешествия 🏆\n']
    for result in results:
        results_list.append(f'· {result[0]} {result[1]}')
    achievements_result: list[str] = ['🎯 Ачивки 🎯']
    for key in ACHIEVEMENTS_KEYS_GUESS:
        if achievements[key]:
            achievements_result.append(ACHIEVEMENTS[key].format(
                '\n· '.join(achievements[key])))
    for key in ACHIEVEMENTS_KEYS_OTHER:
        if None not in achievements[key]:
            achievements_result.append(ACHIEVEMENTS[key].format(
                points=achievements[key][0],
                players='\n· '.join(achievements[key][1:])))
    message_achievements: str = ''.join(achievements_result)
    message_results: str = '\n'.join(results_list)
    for user in active_games[password]['users']:
        send_message(
            chat_id=user,
            message=message_results,
            keyboard=KEYBOARD_MAIN_MENU)
        send_message(
            chat_id=user,
            message=message_achievements,
            keyboard=KEYBOARD_MAIN_MENU)
        for data in (users_passwords, users_states):
            data.pop(user, None)
    active_games.pop(password, None)
    return


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
                'points_buka'] += incorrect_answers
        elif user_role == DREAMER:
            active_games[password]['users'][user][
                    'points_dreamer'] += correct_answers
            if incorrect_answers == 0:
                active_games[password]['users'][user][
                    'guess_all_words'] = True
            elif correct_answers == 0:
                active_games[password]['users'][user][
                    'guess_none_words'] = True
        elif user_role == FAIRY:
            active_games[password]['users'][user][
                'points_fairy'] += correct_answers
        else:
            if correct_answers == incorrect_answers:
                sandman_points: int = correct_answers + 2
            elif abs(correct_answers - incorrect_answers) == 1:
                sandman_points: int = max(correct_answers, incorrect_answers)
            else:
                sandman_points: int = min(correct_answers, incorrect_answers)
            active_games[password]['users'][user][
                'points_sandman'] += sandman_points
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
            keyboard: list[list[str]] = KEYBOARD_IN_LOBBY_HOST
            update_teammates: bool = True
        elif len(active_games[password]['users']) >= USERS_MAX:
            message: str = MESSAGE_JOIN_GAME_FAILED_TO_MUCH_USERS
            keyboard: list[list[str]] = KEYBOARD_MAIN_MENU
            update_teammates: bool = False
        else:
            active_games[password]['users'][
                user_id] = represent_user_data(user_name)
            message: str = MESSAGE_JOIN_GAME_PASS
            keyboard: list[list[str]] = KEYBOARD_IN_LOBBY
            update_teammates: bool = True
    else:
        if user_state == USER_STATE_WANT_CREATE:
            message: str = MESSAGE_CREATE_GAME_FAILED
        else:
            message: str = MESSAGE_JOIN_GAME_FAILED
        keyboard: list[list[str]] = KEYBOARD_MAIN_MENU
    send_message(
        chat_id=user_id,
        message=message,
        ReplyKeyboardMarkup=keyboard)
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
        'points_buka': 0,
        'points_dreamer': 0,
        'points_fairy': 0,
        'points_penalty': 0,
        'points_sandman': 0,
        'points_total': 0,
        'user_name': username}


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
        sys.exit()

    def __restart_program():
        python = sys.executable
        os.execl(python, python, *sys.argv)

    try:
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
    except Exception as err:
        logger.critical(err)
        __restart_program()
