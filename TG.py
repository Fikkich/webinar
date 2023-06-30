import telebot
import sqlite3

TOKEN = ""  # Замените на ваш токен
bot = telebot.TeleBot(TOKEN)

# Создание базы данных
def create_database():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY,
                        telegram_id TEXT,
                        username TEXT,
                        full_name TEXT,
                        email TEXT)
                    """)
    cursor.execute("""CREATE TABLE IF NOT EXISTS webinars (
                        id INTEGER PRIMARY KEY,
                        title TEXT,
                        date TEXT,
                        recording_link TEXT)
                    """)
    cursor.execute("""CREATE TABLE IF NOT EXISTS registrations (
                        id INTEGER PRIMARY KEY,
                        user_id TEXT,
                        webinar_id INTEGER,
                        FOREIGN KEY (user_id) REFERENCES users (telegram_id),
                        FOREIGN KEY (webinar_id) REFERENCES webinars (id))
                    """)
    conn.commit()
    conn.close()

# Добавление пользователя в БД
def add_user(user_id, username, full_name, email):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (telegram_id, username, full_name, email) VALUES (?, ?, ?, ?)",
                   (user_id, username, full_name, email))
    conn.commit()
    conn.close()

# Добавление вебинара в БД
def add_webinar(title, date, recording_link):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO webinars (title, date, recording_link) VALUES (?, ?, ?)",
                   (title, date, recording_link))
    conn.commit()
    conn.close()

# Удаление вебинара из БД
def delete_webinar(webinar_id):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM webinars WHERE id = ?", (webinar_id,))
    cursor.execute("DELETE FROM registrations WHERE webinar_id = ?", (webinar_id,))
    conn.commit()
    conn.close()

# Стартовое сообщение
@bot.message_handler(commands=['start'])
def start_message(message):
    if message.chat.id == 000000000:  # Замените 000000000 на ваш Telegram ID администратора
        bot.send_message(message.chat.id, "Добро пожаловать в SaleBot!\n\n"
                                          "Доступные команды:\n"
                                          "/webinars - просмотреть список вебинаров\n"
                                          "/add_webinar - добавить новый вебинар\n"
                                          "/delete_webinar - удалить вебинар\n"
                                          "/add_recording - отправить запись вебинара\n"
                                          "/profile - зарегистрировать профиль\n"
                                          "/help - получить справку по командам")
    else:
        bot.send_message(message.chat.id, "Добро пожаловать в SaleBot!\n\n"
                                          "Доступные команды:\n"
                                          "/webinars - просмотреть список вебинаров\n"
                                          "/register - зарегистрироваться на вебинар\n"
                                          "/profile - зарегистрировать профиль\n"
                                          "/help - получить справку по командам")

# Регистрация профиля
@bot.message_handler(commands=['profile'])
def profile_message(message):
    user_id = message.chat.id
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (user_id,))
    user = cursor.fetchone()
    if user:
        bot.send_message(message.chat.id, "Профиль уже зарегистрирован.")
    else:
        msg = bot.send_message(message.chat.id, "Введите свое имя и фамилию:")
        bot.register_next_step_handler(msg, process_name_step)

def process_name_step(message):
    full_name = message.text
    user_id = message.chat.id
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (user_id,))
    user = cursor.fetchone()
    if user:
        bot.send_message(message.chat.id, "Профиль уже зарегистрирован.")
    else:
        msg = bot.send_message(message.chat.id, "Введите свой email:")
        bot.register_next_step_handler(msg, process_email_step, full_name)

def process_email_step(message, full_name):
    email = message.text
    user_id = message.chat.id
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (user_id,))
    user = cursor.fetchone()
    if user:
        bot.send_message(message.chat.id, "Профиль уже зарегистрирован.")
    else:
        add_user(user_id, message.from_user.username, full_name, email)
        bot.send_message(message.chat.id, f"Профиль успешно зарегистрирован, {full_name}!")

    conn.close()
# Получение ссылки на запись администратором
@bot.message_handler(commands=['add_recording'])
def add_recording(message):
    if message.chat.id == 000000000:  # Замените YOUR_ADMIN_ID на ваш Telegram ID администратора
        msg = bot.send_message(message.chat.id, "Введите номер вебинара:")
        bot.register_next_step_handler(msg, process_webinar_recording)
    else:
        bot.send_message(message.chat.id, "У вас нет прав доступа к этой команде.")

def process_webinar_recording(message):
    webinar_id = message.text
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM webinars WHERE id = ?", (webinar_id,))
    webinar = cursor.fetchone()
    if webinar:
        msg = bot.send_message(message.chat.id, "Введите ссылку на запись вебинара:")
        bot.register_next_step_handler(msg, process_recording_step, webinar_id)
    else:
        bot.send_message(message.chat.id, "Неверный номер вебинара.")
    conn.close()

def process_recording_step(message, webinar_id):
    recording_link = message.text
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT users.telegram_id FROM registrations "
                   "JOIN users ON registrations.user_id = users.telegram_id "
                   "WHERE registrations.webinar_id = ?", (webinar_id,))
    registered_users = cursor.fetchall()
    conn.close()

    if registered_users:
        for user in registered_users:
            bot.send_message(user[0], f"Ссылка на запись вебинара:\n{recording_link}")
        bot.send_message(message.chat.id, "Ссылка на запись вебинара успешно отправлена зарегистрированным пользователям.")
    else:
        bot.send_message(message.chat.id, "На данный момент нет зарегистрированных пользователей на этом вебинаре.")

# Регистрация на вебинар
@bot.message_handler(commands=['register'])
def register_message(message):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM webinars")
    webinars = cursor.fetchall()
    conn.close()

    if len(webinars) > 0:
        response = "Выберите вебинар для регистрации:\n\n"
        for webinar in webinars:
            response += f"Номер: {webinar[0]}\nНазвание: {webinar[1]}\nДата: {webinar[2]}\n\n"
        msg = bot.send_message(message.chat.id, response)
        bot.register_next_step_handler(msg, process_webinar_registration)
    else:
        bot.send_message(message.chat.id, "На данный момент нет доступных вебинаров.")

def process_webinar_registration(message):
    webinar_id = message.text
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM webinars WHERE id = ?", (webinar_id,))
    webinar = cursor.fetchone()
    conn.close()

    if webinar:
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO registrations (user_id, webinar_id) VALUES (?, ?)",
                       (message.chat.id, webinar_id))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, f"Вы успешно зарегистрированы на вебинар '{webinar[1]}'!")
    else:
        bot.send_message(message.chat.id, "Неверный номер вебинара.")

# Добавление вебинара администратором
@bot.message_handler(commands=['add_webinar'])
def add_webinar_message(message):
    if message.chat.id == 000000000:  # Замените 000000000 на ваш Telegram ID администратора
        msg = bot.send_message(message.chat.id, "Введите название вебинара:")
        bot.register_next_step_handler(msg, process_webinar_title_step)
    else:
        bot.send_message(message.chat.id, "У вас нет прав доступа к этой команде.")

def process_webinar_title_step(message):
    webinar_title = message.text
    msg = bot.send_message(message.chat.id, "Введите дату вебинара (в формате ДД.ММ.ГГГГ):")
    bot.register_next_step_handler(msg, process_webinar_date_step, webinar_title)

def process_webinar_date_step(message, webinar_title):
    webinar_date = message.text
    msg = bot.send_message(message.chat.id, "Введите ссылку на запись вебинара:")
    bot.register_next_step_handler(msg, process_webinar_recording_step, webinar_title, webinar_date)

def process_webinar_recording_step(message, webinar_title, webinar_date):
    webinar_recording = message.text
    add_webinar(webinar_title, webinar_date, webinar_recording)
    bot.send_message(message.chat.id, "Вебинар успешно добавлен!")

# Удаление вебинара администратором
@bot.message_handler(commands=['delete_webinar'])
def delete_webinar_message(message):
    if message.chat.id == 000000000:  # Замените 000000000 на ваш Telegram ID администратора
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM webinars")
        webinars = cursor.fetchall()
        conn.close()

        if len(webinars) > 0:
            response = "Выберите вебинар для удаления:\n\n"
            for webinar in webinars:
                response += f"Номер: {webinar[0]}\nНазвание: {webinar[1]}\nДата: {webinar[2]}\n\n"
            msg = bot.send_message(message.chat.id, response)
            bot.register_next_step_handler(msg, process_webinar_deletion)
        else:
            bot.send_message(message.chat.id, "На данный момент нет доступных вебинаров для удаления.")
    else:
        bot.send_message(message.chat.id, "У вас нет прав доступа к этой команде.")

def process_webinar_deletion(message):
    webinar_id = message.text
    delete_webinar(webinar_id)
    bot.send_message(message.chat.id, "Вебинар успешно удален!")
# Команда для администратора: просмотр зарегистрированных пользователей на вебинаре
@bot.message_handler(commands=['registered_users'])
def registered_users_message(message):
    if message.chat.id == 000000000:  # Замените YOUR_ADMIN_ID на ваш Telegram ID администратора
        msg = bot.send_message(message.chat.id, "Введите номер вебинара:")
        bot.register_next_step_handler(msg, process_registered_users)
    else:
        bot.send_message(message.chat.id, "У вас нет прав доступа к этой команде.")

def process_registered_users(message):
    webinar_id = message.text
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM webinars WHERE id = ?", (webinar_id,))
    webinar = cursor.fetchone()
    if webinar:
        cursor.execute("SELECT users.full_name, users.email, users.telegram_id "
                       "FROM registrations "
                       "JOIN users ON registrations.user_id = users.telegram_id "
                       "WHERE registrations.webinar_id = ?", (webinar_id,))
        registered_users = cursor.fetchall()
        if registered_users:
            response = f"Зарегистрированные пользователи на вебинаре '{webinar[1]}':\n\n"
            for user in registered_users:
                response += f"Имя: {user[0]}\nПочта: {user[1]}\nТелеграм ID: {user[2]}\n\n"
        else:
            response = f"На данный момент нет зарегистрированных пользователей на вебинаре '{webinar[1]}'."
        bot.send_message(message.chat.id, response)
    else:
        bot.send_message(message.chat.id, "Неверный номер вебинара.")

    conn.close()

# Просмотр списка вебинаров
@bot.message_handler(commands=['webinars'])
def webinars_message(message):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM webinars")
    webinars = cursor.fetchall()
    if webinars:
        response = "Список доступных вебинаров:\n\n"
        for webinar in webinars:
            response += f"Название: {webinar[1]}\nДата: {webinar[2]}\nСсылка на вебинар: {webinar[3]}\n\n"
        bot.send_message(message.chat.id, response)
    else:
        bot.send_message(message.chat.id, "На данный момент нет доступных вебинаров.")
    conn.close()
# Справка по командам
@bot.message_handler(commands=['help'])
def help_message(message):
    if message.chat.id == 000000000:  # Замените 000000000 на ваш Telegram ID администратора
        bot.send_message(message.chat.id, "Список доступных команд:\n"
                                          "/webinars - просмотреть список вебинаров\n"
                                          "/add_webinar - добавить новый вебинар\n"
                                          "/delete_webinar - удалить вебинар\n"
                                          "/add_recording - отправить запись вебинара \n"
                                          "/profile - зарегистрировать профиль\n"
                                          "/help - получить справку по командам")
    else:
        bot.send_message(message.chat.id, "Список доступных команд:\n"
                                          "/webinars - просмотреть список вебинаров\n"
                                          "/register - зарегистрироваться на вебинар\n"
                                          "/profile - зарегистрировать профиль\n"
                                          "/help - получить справку по командам")

if __name__ == "__main__":
    create_database()
    bot.polling(none_stop=True)
