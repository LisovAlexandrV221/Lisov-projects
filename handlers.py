from telebot import types
from config import GIPHY_API_KEY, YOUTUBE_API_KEY
import threading
from datetime import datetime, timedelta
import time
import requests
import random
import json

def setup_handlers(bot):
    # Переменные для хранения данных 
    tables = [False] * 5
    registered_users = {}  
    orders = {}            

    # Обработчик команды start
    @bot.message_handler(commands=['start'])
    def start_handler(message):
        bot.send_message(message.from_user.id, f"Привет,{message.from_user.first_name}! Я твой персональный чайный бот поддержи! С моей помощью ты можешь заказать столик или сделать заказ, а так же многое другое! Для ознакомления со всеми моими возможностями используйте команду /help")

    # Вспомогательные функции и обработчики
    @bot.message_handler(commands=['help'])
    def help_command(message):
        help_text = """
        Бот обладает множеством функций, многие из которых требуют авторизации. Вот список доступных команд:
        /help - Получить полный список возможностей
        /registration - Регистрация аккаунта
        Команды, связанные с посещением чайной вживую:
        /check - Проверить наличие свободных столов
        /reserve - Зарезервировать столик
        Ваши заказы:
        /catalog - Открыть каталог товаров и совершить покупку 
        /order - Список текущих заказов

        Чайная традиция:
        /instruction - Инструкция по чайной церемонии
        /data - Узнать текущее время
        /morning - Пожелание доброго утра
        /stickers - Получить фирменные стикеры
        /get_videos - Получить видео про чай
        /more_tea_information - Узнайте больше всего о чае и всяком!

        Наша рассылка:
        /open_mind - Подпишитесь на нашу рассылку и не пропустите ничего важного
        /close_mind - Отписаться от рассылки

        Оцените нашу работу!
        /feedback - Отправить отзыв

        Помимо основных команд, боту можно задать вопросы "Как дела?" и "Что ты делаешь?", он ответит на них.
        """
        bot.send_message(message.chat.id, help_text)

    registered_users = {}

    @bot.message_handler(commands=['register'])
    def register_command(message):
        registered_users.add(message.from_user.id)
        bot.reply_to(message, "Теперь вы зарегистрированы и можете пользоваться всеми функциями бота!")

    def get_giphy_url(tag):
      giphy_url = f"https://api.giphy.com/v1/gifs/random?api_key={GIPHY_API_KEY}&tag={tag}"
      response = requests.get(giphy_url)
      if response.status_code == 200:
          data = response.json()
          gif_url = data['data']['images']['original']['url']
          return gif_url
      else:
          return None

    @bot.message_handler(commands=['morning'])
    def send_morning_gif(message):
        gif_url = get_giphy_url('tea')
        if gif_url:
            bot.send_message(message.chat.id, "Доброе утро!")
            bot.send_animation(message.chat.id, gif_url)
        else:
            bot.send_message(message.chat.id, "Простите, не могу найти подходящий GIF.")

    def save_data_to_file():
      with open('data.txt', 'w') as file:
          file.write("Зарегистрированные пользователи:\n")
          for chat_id, user_info in registered_users.items():
              user_data = f"ID: {chat_id}, Имя: {user_info['name']}, Возраст: {user_info.get('age', 'Не указан')}, Город: {user_info.get('city', 'Не указан')}, Email: {user_info.get('email', 'Не указан')}, Телефон: {user_info.get('phone', 'Не указан')}\n"
              file.write(user_data)
          file.write("\nЗаказы:\n")
          for chat_id, user_orders in orders.items():
              for order in user_orders:
                  order_data = f"ID: {chat_id}, Заказ: {order}\n"
                  file.write(order_data)

    def check_availability(chosen_time):
        """Проверяем количество доступных столиков на заданное время."""
        available_tables = 0  # Счетчик доступных столиков
        for table, booking_times in reservations.items():
            if is_time_available(table, chosen_time):
                available_tables += 1
        return available_tables

    @bot.message_handler(commands=['check'])
    def check_command(message):
        msg = bot.send_message(message.chat.id, "Введите время, чтобы проверить доступность столиков (например, '19:00'):")
        bot.register_next_step_handler(msg, process_time_check)

    def process_time_check(message):
        chosen_time = message.text
        # Мы предполагаем, что пользователь вводит время в правильном формате "HH:MM".
        available_tables = check_availability(chosen_time)
        if available_tables > 0:
            bot.send_message(message.chat.id, f"Количество свободных столиков на {chosen_time}: {available_tables}")
        else:
            bot.send_message(message.chat.id, f"К сожалению, нет свободных столиков на {chosen_time}. Попробуйте выбрать другое время.")



    reservations = {f"Столик {i}": [] for i in range(1, 6)}
    @bot.message_handler(commands=['reserve'])
    def reserve_command(message):
          if message.from_user.id not in registered_users:
              bot.reply_to(message, "Вы не зарегистрированы! Для использования полного функционала бота зарегистрируйтесь.")
              return  # Был исправлен return, он был вне отступа if и прерывал выполнение независимо от проверки

          markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
          table_buttons = [types.KeyboardButton(f"Столик {i}") for i in range(1, 6)]
          markup.add(*table_buttons)
          msg = bot.send_message(message.chat.id, "Выберите столик, который хотели бы забронировать:", reply_markup=markup)
          bot.register_next_step_handler(msg, process_table_selection)

    def process_table_selection(message):
          chosen_table = message.text
          bot.send_message(message.chat.id, f"Вы выбрали {chosen_table}. Теперь введите время бронирования. Например, '18:30':")
          bot.register_next_step_handler(message, process_reservation_time, chosen_table)


    def is_time_available(table, start_time):
      """Проверка доступности столика на заданное время."""
      time_format = "%H:%M"
      start = datetime.strptime(start_time, time_format)
      end = start + timedelta(hours=2)  # Длительность бронирования - 2 часа
      for interval in reservations[table]:
          booked_start, booked_end = interval
          # Проверяем пересечение временных интервалов
          if start < booked_end and end > booked_start:
              return False  # Столик занят
      return True  # Столик свободен


    def process_reservation_time(message, chosen_table):
      reservation_time = message.text
      if is_time_available(chosen_table, reservation_time):
          # Время свободно, добавляем новое бронирование
          time_format = "%H:%M"
          start = datetime.strptime(reservation_time, time_format)
          end = start + timedelta(hours=2)
          reservations[chosen_table].append((start, end))
          bot.send_message(message.chat.id, f"Столик {chosen_table} успешно забронирован на {reservation_time}!")
          with open('reservations.txt', 'a') as file:
           file.write(f"{chosen_table}, {reservation_time}, {message.from_user.username}\n")
      else:
          # Время занято, уведомляем пользователя
          bot.send_message(message.chat.id, f"К сожалению, {chosen_table} занят на выбранное время {reservation_time}. Пожалуйста, выберите другое время.")


    # Обработка каталога
    @bot.message_handler(commands=['catalog'])
    def catalog_command(message):
        if message.from_user.id not in registered_users:
          bot.reply_to(message, "Вы не зарегистрированы! Для использования полного функционала бота зарегистрируйтесь.")
          return
        markup = types.InlineKeyboardMarkup()
        tea_list = ["Пуэр", "Улун", "Габа", "Зеленый чай", "Матча"]
        for tea in tea_list:
            markup.add(types.InlineKeyboardButton(text=tea, callback_data=f'catalog_{tea}'))
        bot.send_message(message.chat.id, "Выберите чай:", reply_markup=markup)

    # Обработчик для CallbackQuery
    @bot.callback_query_handler(func=lambda call: call.data.startswith('catalog_'))
    def query_handler(call):
        bot.answer_callback_query(callback_query_id=call.id)
        tea_description = {
            "Пуэр": "Пуэр - бодрящий, плотный насыщенный чай с древесными, ореховыми и шоколадными нотками. Отличный вариант чтобы поддерживать энергию на протяжении всего дня. Заваривается быстро. Можно настаивать столько сколько душе угодно, в сильную горечь увести сложно, однако если у тебя это первый чай, то лучше заваривать до 30 секунд.",
            "Улун": "Улун - мягкий, вкусный чай на каждый день, который поможет успокоится и сфокусироваться на ежедневной работе. Богатый выбор сортов, из которых каждый найдет что-то для себя. Заваривать нужно аккуратно. Улуны легко уходят в горечь поэтому лучше выдерживать от 10 до 20 секунд, желательно чтобы вода балы нагрета до 85 градусов",
            "Габа": "Габа - если нужно расслабится то вы выбрали правильный чай. Идеальный вариант чтобы отдохнуть после тяжелого дня, восстановить нервную систему и пищеварение. Габа отличается насыщенным, пряно-фруктовым, медовым вкусом. Заваривать от 10 до 40 секунд, главное помнить что габа чай может быть как легким и мягким чаем, так и достаточно плотным настоем, который от времени заварки будет раскрываться совершенно по новому",
            "Зеленый чай": "Зелёный чай - легкий цветочный чай идеально сочетающийся с весенней и летней погодой. Прекрасный спутник в путешествии и повседневной жизни.  Отличается легким травяным вкусом. Расслабляющий и приятный. Заваривать лучше от 10 до 30 секунд, постепенно раскрывая вкус этого благородного чая.",
            "Матча": "Матча - это чай с матчей, которые помогают снимать негативные эмоции. Отличный вариант чтобы сделать себя счастливым и поддержать энергию. Становится особенно популярным среди молодежи поскольку чай с матчей помогает создать эмоциональный баланс"
        }
        tea = call.data.split('_')[1]
        bot.send_message(call.message.chat.id, tea_description[tea])
        markup = types.InlineKeyboardMarkup()
        buy_button = types.InlineKeyboardButton(text="Купить", callback_data=f'buy_{tea}')
        markup.add(buy_button)
        bot.send_message(call.message.chat.id, "Чтобы купить этот чай, нажмите 'Купить':", reply_markup=markup)

    # Обработчик кнопки "Купить"
    @bot.callback_query_handler(func=lambda call: call.data.startswith('buy_'))
    def query_buy_handler(call):
        bot.answer_callback_query(callback_query_id=call.id)
        tea = call.data.split('_')[1]
        markup = types.InlineKeyboardMarkup()
        weights = ["10 грамм", "50 грамм", "100 грамм", "250 грамм"]
        for weight in weights:
            markup.add(types.InlineKeyboardButton(text=weight, callback_data=f'order_{tea}_{weight}'))
        bot.send_message(call.message.chat.id, "Выберите количество:", reply_markup=markup)

    # Обработчик заказа
    @bot.callback_query_handler(func=lambda call: call.data.startswith('order_'))
    def query_order_handler(call):
        bot.answer_callback_query(callback_query_id=call.id)
        tea, weight = call.data.split('_')[1:3]
        chat_id = call.message.chat.id
        date_now = datetime.now().strftime('%Y-%m-%d %H:%M')
        order_info = f"{tea} {weight} - {date_now}"
        if chat_id not in orders:
            orders[chat_id] = []

        orders[chat_id].append(order_info)
        bot.send_message(call.message.chat.id, "Мы приняли ваш заказ к работе! Ожидайте звонка от нашего оператора!")
        save_data_to_file()

    # Просмотр заказов
    @bot.message_handler(commands=['order'])
    def order_command(message):
        if message.from_user.id not in registered_users:
          bot.reply_to(message, "Вы не зарегистрированы! Для использования полного функционала бота зарегистрируйтесь.")
          return
        chat_id = message.chat.id
        if chat_id not in orders or not orders[chat_id]:
            bot.send_message(chat_id, "У вас пока нет заказов.")
        else:
            order_list = "\n".join(orders[chat_id])
            bot.send_message(chat_id, f"Ваши текущие заказы:\n{order_list}")
    
  
  
  
    #Запрос с рассказом о чайной церемонии
    @bot.message_handler(commands=['instruction'])
    def send_welcome(message):
        markup = types.InlineKeyboardMarkup()
        btn_my_site= types.InlineKeyboardButton(text='Узнать больше', callback_data='more_0')
        markup.add(btn_my_site)
        bot.send_message(message.chat.id, "Чайная церемония: В Китае питьё чая - целый обряд со своими правилами и атрибутами. Чайная церемония не только помогает раскрыть вкус чая, но и эстетически дополняет этот процесс, а также знакомит участников с богатой культурой Китая.", reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: True)
    def query_handler(call):

        paragraphs = [
            "Постараемся структурировать этот процесс, чтобы было понятно, что и как нужно делать, чтобы получить максимальное удовольствие от этого процесса.",
            "1. Подготовка посуды : По китайской традиции чай пьется на специальной доске, которая называется «чабань», на ней лежит вся остальная посуда. На чабани чаще всего лежит чайная фигурка изображающая чайного духа, специальный сливник, называемый чашей справедливости или же «чахэ». Ну и про пиалы с глиняным чайничком тоже не забываем). Перед использованием посуда должна быть чистой.",
            "2. Прогрев посуды: чтобы вкус чая был насыщенным посуда прогревается. Кипяток наливается в чайник, а из него в чахэ, пиалы. Проливаем кипяток из посуды на чайного духа.",
            "3. Нулевой пролив: Одним из главных процессов чайной церемонии являются проливы. Пролив это процесс заварки чая, его сливание в чахэ и разливание напитка по пиалам. Нулевой пролив не пьется и выливается на чайного духа. Эта часть ритуала имеет и практическое значение: чай очищается от пыли и получает первый контакт с кипятком. После нулевого пролива распаренный чай по очереди нюхается каждым участником.",
            "4. Проливы: далее каждый пролив уже пьется и переодически остатки чая дарятся чайному духу. Это продолжается пока выпиваемый чай не выдохнется",
            "Также укажем на то, что лучшая чайная церемония подкрепляется добрым разговором и хорошей компанией)",
            "Если хотите узнать больше о чайной церемонии, то приходите к нам. С 9:00 до 22:00 наши чайные мастера подробно расскажут и покажут как проводить этот таинственный и занимательный обряд."
        ]

        call_data = call.data
        if "more_" in call_data:
            index = int(call_data.split("_")[1])
            if index < len(paragraphs):
                markup = types.InlineKeyboardMarkup()
                btn_my_site= types.InlineKeyboardButton(text='Узнать больше', callback_data=f'more_{index + 1}')
                markup.add(btn_my_site)
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=paragraphs[index], reply_markup=markup)
            elif index == len(paragraphs): 
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Спасибо за внимание! Для дополнительных вопросов вы всегда можете обратиться к нам.")
            else:
                bot.answer_callback_query(callback_query_id=call.id, show_alert=False, text="Вы прочли все, что мы хотели рассказать.")

    def save_user_data_to_file(chat_id):
      user_data = registered_users.get(chat_id)
      if user_data:
          with open('registrations.txt', 'a') as file:
              file.write(f"{user_data['name']}, {user_data['age']}, {user_data['city']}, {user_data['email']}, {user_data['phone']}\n")
      else:
          print("Попытка сохранить несуществующие данные пользователя.")  # или замените на более подходящее действие


    # Процесс регистрации пользователя
    @bot.message_handler(commands=['registration'])
    def registration_step_name(message):
        msg = bot.reply_to(message, "Введите ваше имя:")
        bot.register_next_step_handler(msg, registration_step_age)

    def registration_step_age(message):
        chat_id = message.chat.id
        name = message.text.strip()
        registered_users[chat_id] = {"name": name}  # Сохраняем имя
        msg = bot.send_message(chat_id, "Введите ваш возраст:")
        bot.register_next_step_handler(msg, registration_step_city)

    def registration_step_city(message):
        chat_id = message.chat.id
        age = message.text.strip()
        registered_users[chat_id]["age"] = age  # Сохраняем возраст
        msg = bot.send_message(chat_id, "Введите ваш город:")
        bot.register_next_step_handler(msg, registration_step_email)

    def registration_step_email(message):
        chat_id = message.chat.id
        city = message.text.strip()
        registered_users[chat_id]["city"] = city  # Сохраняем город
        msg = bot.send_message(chat_id, "Введите вашу электронную почту:")
        bot.register_next_step_handler(msg, registration_step_phone)

    def registration_step_phone(message):
        chat_id = message.chat.id
        email = message.text.strip()
        registered_users[chat_id]["email"] = email  # Сохраняем эл. почту
        msg = bot.send_message(chat_id, "Введите ваш телефонный номер:")
        bot.register_next_step_handler(msg, registration_finish)

    def registration_finish(message):
      registered_users[message.chat.id]['phone'] = message.text
      registered_users[message.chat.id]['user_id'] = message.chat.id  # Сохраняем идентификатор пользователя
      save_user_data_to_file(message.chat.id)
      bot.send_message(message.chat.id, "Регистрация успешно завершена!")

      # Сохраняем данные в файл после успешной регистрации
    def save_user_data_to_file(chat_id):
      user_data = registered_users.get(chat_id)
      if user_data:
          with open('registrations.txt', 'a') as file:
              file.write(json.dumps(user_data) + '\n')



    #Запрос о текущем времени
    @bot.message_handler(commands=['data'])
    def data_command(message):
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        bot.send_message(message.chat.id, f"Текущее время: {now}")

    # Следующие две функции-обработчика-простые ответы на текстовые вопросы
    @bot.message_handler(func=lambda message: message.text.lower() == "как дела?")
    def handle_message(message):
        bot.reply_to(message, "Чудесно после очередной кружки чая. Присоединяйтесь!")

    @bot.message_handler(func=lambda message: message.text.lower() == "что ты делаешь?")
    def handle_message(message):
        bot.reply_to(message, "Выполняю индивидуальное обслуживание одного клиента через телеграм! Обрадую вас – этот клиент вы!!")

    # Обработчик для принятия и возврата текста и файлов
    @bot.message_handler(content_types=['photo', 'document'])
    def echo_all(message):
        if message.content_type in ['photo', 'document']:
            bot.send_message(message.chat.id, "Ваши данные успешно сохранены.")
            if message.content_type == 'photo':
                file_info = bot.get_file(message.photo[-1].file_id)
            else:
                file_info = bot.get_file(message.document.file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            bot.send_document(message.chat.id, downloaded_file, caption="Вот ваш файл:")



    # Функция для рассылки
    def send_open_mind_message(chat_id):
        bot.send_message(chat_id, "Открой свой разум для новых вкусов настоящего китайского чая!")

    open_mind_threads = {}

    # Функция для создания задачи на отправку сообщения каждые 10 минут
    def periodic_open_mind(chat_id, stop_event):
      while not stop_event.is_set():
          send_open_mind_message(chat_id)
          time.sleep(600) # Пауза в 10 минут между сообщениями

    # Команда для начала рассылки
    @bot.message_handler(commands=['open_mind'])
    def open_mind_command(message):
      chat_id = message.chat.id
      if chat_id not in open_mind_threads:
          stop_event = threading.Event()
          thread = threading.Thread(target=periodic_open_mind, args=(chat_id, stop_event))
          thread.start()
          open_mind_threads[chat_id] = stop_event
          bot.send_message(chat_id, "Вы подписались на рассылку 'Открой свой разум'. Напоминания будут приходить каждые 10 минут.")
      else:
          bot.send_message(chat_id, "Вы уже подписаны на рассылку.")


  
    #Отказ от рассылки
    @bot.message_handler(commands=['close_mind'])
    def close_mind_command(message):
        chat_id = message.chat.id
        if chat_id in open_mind_threads:
            open_mind_threads[chat_id].set()  # Останавливаем поток
            del open_mind_threads[chat_id]  # Удаляем из словаря
            bot.send_message(chat_id, "Вы отписались от рассылки.")
        else:
            bot.send_message(chat_id, "Вы не подписаны на рассылку.")

    
    sticker_ids = ['CAACAgIAAxkBAAPMZgLQtMPyl1SuIXInzwqY3xoLxy4AApM8AAIEDqBKKJEuTAu3rkM0BA']
    #Отправка стикера в подарок за заказ 
    @bot.message_handler(commands=['stickers'])
    def stickers_command(message):
        chat_id = message.chat.id
        if chat_id in orders and orders[chat_id]:  # Проверяем наличие заказов для пользователя
            bot.send_message(chat_id, "Дарим от всей души наших дорогим клиентам!")
            for sticker_id in sticker_ids:  # Отправляем стикеры из списка
                bot.send_sticker(chat_id, sticker_id)
        else:
            bot.send_message(chat_id, "Сделайте заказ и получите в подарок набор наших стикеров")


    #Написание отзыва о работе компании
    @bot.message_handler(commands=['feedback'])
    def feedback_command(message):
        bot.send_message(message.chat.id, "Пожалуйста, введите ваш отзыв:")
        bot.register_next_step_handler(message, process_feedback)

    def process_feedback(message):
        feedback = message.text
        with open("feedback.txt", "a", encoding='utf-8') as f:
            f.write(f"Отзыв от {message.from_user.username} ({message.from_user.id}): {feedback}\n")
        bot.send_message(message.chat.id, "Спасибо за ваш отзыв!")

    @bot.message_handler(commands=['get_videos'])
    def get_random_video(message):
      """Функция, которая получает одно случайное видео про чай"""
      url = f"https://www.googleapis.com/youtube/v3/search"
      chat_id = message.chat.id
      param = {
          "key": YOUTUBE_API_KEY,
          'q': f'чай',
          'type': 'video',
          'videoDuration': 'medium',
          'maxResults': 25
      }
      randomi = random.randint(0, 24)
      result = requests.get(url, params=param).json()
      bot.send_message(chat_id, 'https://www.youtube.com/watch?v=' + result['items'][randomi]['id']['videoId'])
      bot.send_message(chat_id, 'Приятного просмотра! Остальные функции доступны по команде /help')



    #Запрос к API 
    def get_wikipedia_summary(query):
      WIKI_API_URL = "https://ru.wikipedia.org/w/api.php"
      PARAMETERS = {
          'action': 'query',
          'format': 'json',
          'titles': query,
          'prop': 'extracts',
          'exintro': True,
          'explaintext': True,
      }
      response = requests.get(WIKI_API_URL, params=PARAMETERS)
      data = response.json()

      page = next(iter(data['query']['pages'].values()))
      if 'extract' in page:
          summary = page['extract']
          return summary
      else:
          return "У нас нет информации и источников об этом("
    #Запрос к википедии для пользователя если он хочет узнать новую информацию 
    @bot.message_handler(commands=['more_tea_information'])
    def more_tea_information_command(message):
        msg = bot.reply_to(message, "О каком чае желаете узнать больше информации?")
        bot.register_next_step_handler(msg, send_tea_information)

    def send_tea_information(message):
        query = message.text
        summary = get_wikipedia_summary(query)
        bot.send_message(message.chat.id, summary)





