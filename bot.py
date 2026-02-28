import os
import json
import random
import time
from datetime import datetime
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

# Загружаем список
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
    keyboard.add_button("Админы в сети", VkKeyboardColor.PRIMARY, payload='{"action":"admins"}')
    return keyboard.get_keyboard()

# Отправка
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

# Список онлайн админов
def get_admins_online_list():
    if not admins:
        return "Список администраторов пуст."

    user_ids = list(admins.keys())
    user_info = vk.users.get(user_ids=",".join(user_ids))

    now = time.time()
    result = []

    for user in user_info:
        uid = str(user["id"])
        start_time = admins.get(uid)

        if start_time:
            online_time = now - start_time
            result.append(
                f"{user['first_name']} {user['last_name']} — ⏳ {format_time(online_time)}"
            )

    if result:
        return f"🟢 Админов в сети ({len(result)}):\n" + "\n".join(result)
    else:
        return "🟢 Сейчас никто не в сети."

print("Бот запущен!")

# ================= ГЛАВНЫЙ ЦИКЛ =================

for event in longpoll.listen():

    if event.type == VkBotEventType.MESSAGE_NEW:

        msg = event.message
        peer_id = msg["peer_id"]
        user_id = str(msg["from_id"])
        text = msg["text"].strip().lower()

        # ===== КНОПКИ =====
        if msg.get("payload"):
            payload = json.loads(msg["payload"])

            if payload.get("action") == "entered":

                if user_id in admins:
                    send_message(peer_id, "⚠️ Ты уже в сети.")
                else:
                    admins[user_id] = time.time()
                    save_admins()
                    send_message(peer_id, "✅ Ты вошел в онлайн.")

                continue

            elif payload.get("action") == "exited":

                if user_id not in admins:
                    send_message(peer_id, "⚠️ Ты не находишься в сети.")
                else:
                    start_time = admins[user_id]
                    total_time = time.time() - start_time
                    del admins[user_id]
                    save_admins()
                    send_message(peer_id, f"❌ Ты вышел. Был в сети: {format_time(total_time)}")

                continue

            elif payload.get("action") == "admins":
                send_message(peer_id, get_admins_online_list())
                continue

        # ===== ТЕКСТ =====

        if text == "/start":
            send_message(peer_id, "Бот логирования готов к работе.")
