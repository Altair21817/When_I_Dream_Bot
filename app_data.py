from dotenv import load_dotenv
from pathlib import Path
from telegram import InputMediaPhoto
import os

load_dotenv()

TELEGRAM_BOT_TOKEN: str = os.getenv('TELEGRAM_BOT_TOKEN')
ALL_DATA: list[str] = [TELEGRAM_BOT_TOKEN]

ACHIEVEMENTS: dict[str, str] = {
    'points_total': (
        '\n\nВсем угощение за мой счет: заработал(а) больше '
        'всего очков!\n{}'),
    'guess_all_words': (
        '\n\nCон на яву: отгадал(а) все слова!\n{}'),
    'points_dreamer': (
        '\n\nЯркие сны: угадал(а) больше всего слов!\n{}'),
    'points_fairy': (
        '\n\nКрестная фея: заработал(а) больше всего очков как фея!\n{}'),
    'points_buka':  (
        '\n\nБу-бу-бука: заработал(а) больше всего очков как бука!\n{}'),
    'points_sandman': (
        '\n\nЛицемерище: заработал(а) больше всего очков как '
        'песочный человек!\n{}'),
    'points_penalty': (
        '\n\nКайфоломщик: получил(а) больше всего пенальти!\n{}'),
    'guess_none_words': (
        '\n\nCущий кошмар: не отгадал(а) ни одного слова!\n{}')}
ACHIEVEMENTS_KEYS_GUESS: list[str] = ['guess_all_words', 'guess_none_words']
ACHIEVEMENTS_KEYS_OTHER: list[str] = [
    key for key in ACHIEVEMENTS.keys() if key not in ACHIEVEMENTS_KEYS_GUESS]

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

USER_STATE_WANT_JOIN: int = 0
USER_STATE_WANT_CREATE: int = 1
USER_STATE_IN_GAME: int = 2
