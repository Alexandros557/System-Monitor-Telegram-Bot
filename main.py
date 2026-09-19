import telebot
import psutil
import time
from telebot import types
from config import TOKEN


bot = telebot.TeleBot(TOKEN)

# ВСТАВЬ СЮДА СВОЙ TELEGRAM ID
MY_ID = 1855921762


# =========================
# ПРОВЕРКА ДОСТУПА
# =========================

def check_access(message):
    return message.from_user.id == MY_ID


# =========================
# СКЛОНЕНИЕ СЛОВА "ДЕНЬ"
# =========================

def days_word(days):
    if 11 <= days % 100 <= 14:
        return "дней"
    elif days % 10 == 1:
        return "день"
    elif 2 <= days % 10 <= 4:
        return "дня"
    else:
        return "дней"


# =========================
# ВРЕМЯ РАБОТЫ СИСТЕМЫ
# =========================

def get_uptime():
    uptime = time.time() - psutil.boot_time()

    days = int(uptime // 86400)
    hours = int((uptime % 86400) // 3600)
    minutes = int((uptime % 3600) // 60)

    return f"{days} {days_word(days)} {hours} часов {minutes} минут"


# =========================
# ГЛАВНОЕ МЕНЮ
# =========================

def main_keyboard():
    keyboard = types.InlineKeyboardMarkup()

    keyboard.add(
        types.InlineKeyboardButton(
            "🖥 Система",
            callback_data="system"
        ),
        types.InlineKeyboardButton(
            "💾 RAM",
            callback_data="ram"
        )
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "⚡ Перегрузка",
            callback_data="load"
        ),
        types.InlineKeyboardButton(
            "⏱ Аптайм",
            callback_data="uptime"
        )
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "🔥 TOP-5 CPU",
            callback_data="top"
        )
    )

    return keyboard


# =========================
# /START
# =========================

@bot.message_handler(commands=["start"])
def start(message):

    if not check_access(message):
        bot.send_message(
            message.chat.id,
            "❌ У вас нет доступа."
        )
        return

    bot.send_message(
        message.chat.id,
        "Привет! Выбери нужную информацию:",
        reply_markup=main_keyboard()
    )


# =========================
# ИНФОРМАЦИЯ О СИСТЕМЕ
# =========================

def get_system_info():

    cpu = psutil.cpu_percent(interval=1)

    ram = psutil.virtual_memory()

    # Для Windows лучше использовать системный диск
    disk = psutil.disk_usage("C:\\")

    battery = psutil.sensors_battery()

    if battery:
        battery_percent = battery.percent
    else:
        battery_percent = "Нет данных"

    return cpu, ram, disk, battery_percent


# =========================
# /RAM
# =========================

@bot.message_handler(commands=["ram"])
def ram_command(message):

    if not check_access(message):
        return

    ram = psutil.virtual_memory()

    total = ram.total / (1024 ** 3)
    used = ram.used / (1024 ** 3)
    available = ram.available / (1024 ** 3)

    text = (
        "💾 Оперативная память:\n\n"
        f"Всего: {total:.2f} GB\n"
        f"Используется: {used:.2f} GB\n"
        f"Свободно: {available:.2f} GB\n"
        f"Загрузка: {ram.percent}%"
    )

    bot.send_message(
        message.chat.id,
        text
    )


# =========================
# ПРОВЕРКА ПЕРЕГРУЗКИ
# =========================

def check_load():

    cpu = psutil.cpu_percent(interval=1)

    ram = psutil.virtual_memory().percent

    if cpu >= 80 or ram >= 80:

        return (
            "⚠️ ВНИМАНИЕ!\n"
            f"CPU: {cpu}%\n"
            f"RAM: {ram}%\n"
            "Система перегружена!"
        )

    return (
        "✅ Перегрузки нет.\n"
        f"CPU: {cpu}%\n"
        f"RAM: {ram}%"
    )


# =========================
# /UPTIME
# =========================

@bot.message_handler(commands=["uptime"])
def uptime_command(message):

    if not check_access(message):
        return

    bot.send_message(
        message.chat.id,
        f"⏱ Система работает {get_uptime()}"
    )


# =========================
# TOP-5 ПРОЦЕССОВ ПО CPU
# =========================

def get_top_processes():

    processes = []

    # Сначала запускаем измерение CPU
    for process in psutil.process_iter(["pid", "name"]):

        try:
            process.cpu_percent(None)

        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied
        ):
            pass

    # Небольшая пауза для измерения
    time.sleep(0.5)

    # Получаем результаты
    for process in psutil.process_iter(["pid", "name"]):

        try:

            cpu = process.cpu_percent(None)

            processes.append(
                (
                    process.info["pid"],
                    process.info["name"] or "Unknown",
                    cpu
                )
            )

        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied
        ):
            pass

    # Сортируем от большего CPU к меньшему
    processes.sort(
        key=lambda x: x[2],
        reverse=True
    )

    return processes[:5]


# =========================
# /TOP
# =========================

@bot.message_handler(commands=["top"])
def top_command(message):

    if not check_access(message):
        return

    processes = get_top_processes()

    text = "🔥 TOP-5 процессов по CPU:\n\n"

    for i, (pid, name, cpu) in enumerate(
        processes,
        1
    ):

        text += (
            f"{i}. {name} | "
            f"PID: {pid} | "
            f"CPU: {cpu:.1f}%\n"
        )

    bot.send_message(
        message.chat.id,
        text
    )


# =========================
# INLINE-КНОПКИ
# =========================

@bot.callback_query_handler(
    func=lambda call: True
)
def callback_handler(call):

    # Проверяем пользователя
    if call.from_user.id != MY_ID:

        bot.answer_callback_query(
            call.id,
            "❌ У вас нет доступа!"
        )

        return

    # ==================================
    # ВАЖНО:
    # СРАЗУ ОТВЕЧАЕМ TELEGRAM
    # ==================================

    bot.answer_callback_query(call.id)

    # =========================
    # СИСТЕМА
    # =========================

    if call.data == "system":

        cpu, ram, disk, battery = get_system_info()

        text = (
            "🖥 Параметры системы:\n\n"
            f"CPU: {cpu}%\n"
            f"RAM: {ram.percent}%\n"
            f"Disk: {disk.percent}%\n"
            f"Battery: {battery}%"
        )

    # =========================
    # RAM
    # =========================

    elif call.data == "ram":

        ram = psutil.virtual_memory()

        text = (
            "💾 RAM:\n\n"
            f"Всего: "
            f"{ram.total / (1024 ** 3):.2f} GB\n"
            f"Используется: "
            f"{ram.used / (1024 ** 3):.2f} GB\n"
            f"Свободно: "
            f"{ram.available / (1024 ** 3):.2f} GB\n"
            f"Загрузка: {ram.percent}%"
        )

    # =========================
    # ПЕРЕГРУЗКА
    # =========================

    elif call.data == "load":

        text = check_load()

    # =========================
    # UPTIME
    # =========================

    elif call.data == "uptime":

        text = (
            f"⏱ Система работает "
            f"{get_uptime()}"
        )

    # =========================
    # TOP-5 CPU
    # =========================

    elif call.data == "top":

        processes = get_top_processes()

        text = "🔥 TOP-5 процессов по CPU:\n\n"

        for i, (pid, name, cpu) in enumerate(
            processes,
            1
        ):

            text += (
                f"{i}. {name} | "
                f"PID: {pid} | "
                f"CPU: {cpu:.1f}%\n"
            )

    # =========================
    # НЕИЗВЕСТНАЯ КНОПКА
    # =========================

    else:

        text = "Неизвестная команда."

    # =========================
    # ОТПРАВЛЯЕМ РЕЗУЛЬТАТ
    # =========================

    bot.send_message(
        call.message.chat.id,
        text,
        reply_markup=main_keyboard()
    )


# =========================
# ЗАПУСК БОТА
# =========================

print("🤖 Бот запущен...")

bot.infinity_polling(
    skip_pending=True
)
