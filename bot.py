from dotenv import load_dotenv
import os
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import json
import random

# ==== Загрузка токена и GROUP_ID из .env ====
load_dotenv()
TOKEN = os.getenv("VK_TOKEN")  # токен сообщества
GROUP_ID = int(os.getenv("GROUP_ID"))  # числовой ID сообщества

vk_session = vk_api.VkApi(token=TOKEN)
vk = vk_session.get_api()
longpoll = VkBotLongPoll(vk_session, GROUP_ID)

admins_file = "admins.json"

# Загружаем список админов
if os.path.exists(admins_file):
    with open(admins_file, "r") as f:
        admins = json.load(f)
else:
    admins = []

def save_admins():
    with open(admins_file, "w") as f:
        json.dump(admins, f)

# Клавиатура
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

# Список онлайн админов
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

print("Бот для админов запущен! Работает во всех чатах, куда добавлено сообщество.")

# Главный цикл
for event in longpoll.listen():
    if event.type == VkBotEventType.MESSAGE_NEW:
        msg = event.message
        peer_id = msg['peer_id']
        user_id = msg['from_id']
        text = msg['text'].strip()

        if text.lower() == "/start":
            send_message(peer_id, "Бот Логирования готов к работе")

        elif text == "Вошел":
            if user_id not in admins:
                admins.append(user_id)
                save_admins()
                send_message(peer_id, "✅ Вы добавлены в список администраторов в сети.")
            else:
                send_message(peer_id, "⚠️ Вы уже в списке администраторов в сети.")

        elif text == "Вышел":
            if user_id in admins:
                admins.remove(user_id)
                save_admins()
                send_message(peer_id, "❌ Вы удалены из списка администраторов из сети.")
            else:
                send_message(peer_id, "⚠️ Вас нет в списке администраторов.")

        elif text == "Админы в сети":
            send_message(peer_id, get_admins_online_list())
