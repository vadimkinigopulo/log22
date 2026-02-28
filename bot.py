import os
import json
import random
import time
from dotenv import load_dotenv
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

# ==== Загрузка токена и GROUP_ID ====
load_dotenv()
TOKEN = os.getenv("VK_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))

vk_session = vk_api.VkApi(token=TOKEN)
vk = vk_session.get_api()
longpoll = VkBotLongPoll(vk_session, GROUP_ID)

admins_file = "admins.json"

# Загружаем администраторов
if os.path.exists(admins_file):
    with open(admins_file, "r") as f:
        admins = json.load(f)
else:
    admins = {}

def save_admins():
    with open(admins_file, "w") as f:
        json.dump(admins, f)

# Клавиатура
def get_keyboard():
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button("Вошел", VkKeyboardColor.POSITIVE, payload='{"action":"entered"}')
    keyboard.add_button("Вышел", VkKeyboardColor.NEGATIVE, payload='{"action":"exited"}')
    keyboard.add_line()
    keyboard.add_button("Администрация в сети", VkKeyboardColor.PRIMARY, payload='{"action":"admins"}')
    return keyboard.get_keyboard()

# Отправка сообщений
def send_message(peer_id, message):
    vk.messages.send(
        peer_id=peer_id,
        message=message,
        random_id=random.randint(1, 10**6),
        keyboard=get_keyboard()
    )

# Формат времени
def format_time(seconds):
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return f"{int(hours)}ч {int(minutes)}м"

# Получение имени и фамилии
def get_user_info(user_id):
    user = vk.users.get(user_ids=user_id)[0]
    return user["first_name"], user["last_name"]

# Список администрации онлайн
def get_admins_online_list():
    if not admins:
        return "Администрация в сети:\n\nСейчас никто не авторизован."

    now = time.time()
    result = []

    for uid, start_time in admins.items():
        first_name, last_name = get_user_info(uid)
        online_time = now - start_time

        result.append(
            f"• [id{uid}|{first_name} {last_name}] — {format_time(online_time)}"
        )

    return "Администрация в сети:\n\n" + "\n".join(result)

print("Бот запущен.")

# ================= ГЛАВНЫЙ ЦИКЛ =================

for event in longpoll.listen():

    if event.type == VkBotEventType.MESSAGE_NEW:

        msg = event.message
        peer_id = msg["peer_id"]
        user_id = str(msg["from_id"])

        if msg.get("payload"):
            payload = json.loads(msg["payload"])

            # ===== ВХОД =====
            if payload.get("action") == "entered":

                if user_id in admins:
                    send_message(peer_id, "Вы уже авторизованы.")
                else:
                    admins[user_id] = time.time()
                    save_admins()

                    first_name, last_name = get_user_info(user_id)

                    send_message(
                        peer_id,
                        f"Администратор [id{user_id}|{first_name} {last_name}] успешно авторизовался."
                    )
                continue

            # ===== ВЫХОД =====
            elif payload.get("action") == "exited":

                if user_id not in admins:
                    send_message(peer_id, "Вы не авторизованы.")
                else:
                    first_name, last_name = get_user_info(user_id)
                    del admins[user_id]
                    save_admins()

                    send_message(
                        peer_id,
                        f"Администратор [id{user_id}|{first_name} {last_name}] вышел из системы."
                    )
                continue

            # ===== СПИСОК =====
            elif payload.get("action") == "admins":
                send_message(peer_id, get_admins_online_list())
                continue
