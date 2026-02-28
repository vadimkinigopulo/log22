import os
import json
import time
from dotenv import load_dotenv
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.utils import get_random_id

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
        json.dump(admins, f, ensure_ascii=False)

# ==== Клавиатура с эмодзи ====
def get_keyboard():
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button("✅ Вошел", VkKeyboardColor.POSITIVE, payload='{"action":"entered"}')
    keyboard.add_button("❌ Вышел", VkKeyboardColor.NEGATIVE, payload='{"action":"exited"}')
    keyboard.add_line()
    keyboard.add_button("💼 Администрация в сети", VkKeyboardColor.PRIMARY, payload='{"action":"admins"}')
    return keyboard.get_keyboard()

# ==== Отправка сообщений ====
def send_message(peer_id, message):
    vk.messages.send(
        peer_id=peer_id,
        message=message,
        random_id=get_random_id(),
        keyboard=get_keyboard()
    )

# ==== Красивое время онлайн ====
def format_time(seconds):
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    if hours and minutes:
        return f"{int(hours)}ч {int(minutes)}м"
    elif hours:
        return f"{int(hours)}ч"
    elif minutes:
        return f"{int(minutes)}м"
    else:
        return "меньше минуты"

# ==== Получение имени и фамилии пользователя ====
def get_user_info(user_id):
    user = vk.users.get(user_ids=user_id)[0]
    return user["first_name"], user["last_name"]

# ==== Список админов онлайн с красотой ====
def get_admins_online_list():
    if not admins:
        return "💼 Администрация в сети:\n\nСейчас никто не авторизован."

    now = time.time()
    result = []
    for i, (uid, info) in enumerate(admins.items(), start=1):
        first_name, last_name = info["first_name"], info["last_name"]
        online_time = now - info["start_time"]
        result.append(f"{i}. [id{uid}|{first_name} {last_name}] — ⏱ {format_time(online_time)}")
    return "💼 Администрация в сети:\n\n" + "\n".join(result)

print("Бот запущен.")

# ================= ГЛАВНЫЙ ЦИКЛ =================
for event in longpoll.listen():
    if event.type == VkBotEventType.MESSAGE_NEW:
        msg = event.message
        peer_id = msg["peer_id"]
        user_id = str(msg["from_id"])

        payload = {}
        if msg.get("payload"):
            try:
                payload = json.loads(msg["payload"])
            except json.JSONDecodeError:
                send_message(peer_id, "⚠️ Ошибка обработки кнопки.")
                continue

        # ===== ВХОД =====
        if payload.get("action") == "entered":
            if user_id in admins:
                send_message(peer_id, "⚠️ Вы уже авторизованы.")
            else:
                first_name, last_name = get_user_info(user_id)
                admins[user_id] = {
                    "start_time": time.time(),
                    "first_name": first_name,
                    "last_name": last_name
                }
                save_admins()

                send_message(peer_id,
                    f"🟢 Администратор [id{user_id}|{first_name} {last_name}] успешно авторизовался.\n"
                    f"💼 Админов онлайн: {len(admins)}"
                )
            continue

        # ===== ВЫХОД =====
        elif payload.get("action") == "exited":
            if user_id not in admins:
                send_message(peer_id, "⚠️ Вы не авторизованы.")
            else:
                first_name, last_name = admins[user_id]["first_name"], admins[user_id]["last_name"]
                del admins[user_id]
                save_admins()

                send_message(peer_id,
                    f"🔴 Администратор [id{user_id}|{first_name} {last_name}] вышел из системы.\n"
                    f"💼 Админов онлайн: {len(admins)}"
                )
            continue

        # ===== СПИСОК =====
        elif payload.get("action") == "admins":
            send_message(peer_id, get_admins_online_list())
            continue
