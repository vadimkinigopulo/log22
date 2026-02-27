# ==== НАЧАЛО: Загрузка токена из .env ====
from dotenv import load_dotenv
import os
load_dotenv()  # загружает переменные из .env
TOKEN = os.environ['VK_TOKEN']  # токен VK

# ==== Импорты и настройки бота ====
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import json
import random

vk_session = vk_api.VkApi(token=TOKEN)
vk = vk_session.get_api()
longpoll = VkLongPoll(vk_session)

admins_file = "admins.json"

# Загружаем список администраторов
if os.path.exists(admins_file):
    with open(admins_file, "r") as f:
        admins = json.load(f)
else:
    admins = []

def save_admins():
    with open(admins_file, "w") as f:
        json.dump(admins, f)

# Создание клавиатуры
def get_keyboard():
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button("Вошел", VkKeyboardColor.POSITIVE)
    keyboard.add_button("Вышел", VkKeyboardColor.NEGATIVE)
    keyboard.add_line()
    keyboard.add_button("Админы в сети", VkKeyboardColor.PRIMARY)
    return keyboard.get_keyboard()

# Отправка сообщений
def send_message(peer_id, message):
    vk.messages.send(
        peer_id=peer_id,
        message=message,
        random_id=random.randint(1, 10**6),
        keyboard=get_keyboard()
    )

# Список онлайн админов (только онлайн)
def get_admins_online_list():
    if not admins:
        return "Список администраторов пуст."
    try:
        admin_info = vk.users.get(user_ids=",".join(map(str, admins)), fields="online")
        online_admins = [f"{a['first_name']} {a['last_name']} (https://vk.com/id{a['id']})" 
                         for a in admin_info if a["online"] == 1]
        if online_admins:
            response = f"🟢 Админов в сети ({len(online_admins)}):\n" + "\n".join(online_admins)
        else:
            response = "🟢 Админов в сети: 0\nНет админов в сети"
        return response
    except Exception as e:
        return f"Ошибка при получении данных: {e}"

print("Бот для администрации запущен...")

# Основной цикл обработки сообщений
for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW:
        peer_id = event.peer_id
        text = event.text.strip()

        # Команда /start
        if text.lower() == "/start":
            send_message(peer_id, "Бот Логирования готов к работе")

        # Вход в список админов
        elif text == "Вошел":
            if event.from_user:  # проверяем, что это пользователь
                user_id = event.user_id
                if user_id not in admins:
                    admins.append(user_id)
                    save_admins()
                    send_message(peer_id, "✅ Вы добавлены в список администраторов в сети.")
                else:
                    send_message(peer_id, "⚠️ Вы уже в списке администраторов в сети.")

        # Выход из списка админов
        elif text == "Вышел":
            if event.from_user:
                user_id = event.user_id
                if user_id in admins:
                    admins.remove(user_id)
                    save_admins()
                    send_message(peer_id, "❌ Вы удалены из списка администраторов из сети.")
                else:
                    send_message(peer_id, "⚠️ Вас нет в списке администраторов.")

        # Список онлайн админов
        elif text == "Админы в сети":
            send_message(peer_id, get_admins_online_list())
