import os
import json
import random
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

# Загружаем список администраторов
if os.path.exists(admins_file):
    with open(admins_file, "r") as f:
        admins = json.load(f)
else:
    admins = []

def save_admins():
    with open(admins_file, "w") as f:
        json.dump(admins, f)

# Клавиатура (payload можно оставить, но в чатах работает только текст)
def get_keyboard():
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button("Вошел", color=VkKeyboardColor.POSITIVE, payload='{"action":"entered"}')
    keyboard.add_button("Вышел", color=VkKeyboardColor.NEGATIVE, payload='{"action":"exited"}')
    keyboard.add_line()
    keyboard.add_button("Админы в сети", color=VkKeyboardColor.PRIMARY, payload='{"action":"admins"}')
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
        online_admins = [
            f"{a['first_name']} {a['last_name']} (https://vk.com/id{a['id']})"
            for a in admin_info if a["online"] == 1
        ]
        if online_admins:
            response = f"🟢 Админов в сети ({len(online_admins)}):\n" + "\n".join(online_admins)
        else:
            response = "🟢 Админов в сети: 0\nНет админов в сети"
        return response
    except Exception as e:
        return f"Ошибка при получении данных: {e}"

print("Бот для админов запущен! Работает во всех чатах группы.")

# Главный цикл
for event in longpoll.listen():
    # Новое сообщение (текст команды)
    if event.type == VkBotEventType.MESSAGE_NEW:
        msg = event.message
        peer_id = msg['peer_id']
        user_id = msg['from_id']
        text = msg['text'].strip().lower()

        # Если текст начинается с упоминания сообщества, убираем его
        if text.startswith("@"):
            parts = text.split(" ", 1)
            if len(parts) > 1:
                text = parts[1]  # оставляем команду после упоминания

        # Обработка команд
        if text == "/start":
            send_message(peer_id, "Бот Логирования готов к работе")

        elif text == "вошел":
            if user_id not in admins:
                admins.append(user_id)
                save_admins()
                send_message(peer_id, "✅ Вы добавлены в список администраторов в сети.")
            else:
                send_message(peer_id, "⚠️ Вы уже в списке администраторов в сети.")

        elif text == "вышел":
            if user_id in admins:
                admins.remove(user_id)
                save_admins()
                send_message(peer_id, "❌ Вы удалены из списка администраторов из сети.")
            else:
                send_message(peer_id, "⚠️ Вас нет в списке администраторов.")

        elif text == "админы в сети":
            send_message(peer_id, get_admins_online_list())

    # Нажатие на кнопку (payload в чатах обычно не приходит)
    elif event.type == VkBotEventType.MESSAGE_EVENT:
        user_id = event.user_id
        peer_id = event.peer_id
        payload = json.loads(event.object.payload)

        # Обработка payload для ЛС (если приходит)
        if payload.get("action") == "entered":
            if user_id not in admins:
                admins.append(user_id)
                save_admins()
            send_message(peer_id, "✅ Вы вошли через кнопку")

        elif payload.get("action") == "exited":
            if user_id in admins:
                admins.remove(user_id)
                save_admins()
            send_message(peer_id, "❌ Вы вышли через кнопку")

        elif payload.get("action") == "admins":
            send_message(peer_id, get_admins_online_list())
