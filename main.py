import subprocess
import requests
from bs4 import BeautifulSoup
import telebot
from pytube import YouTube
import os

# Ваш токен Telegram бота
TOKEN = '5643712939:AAGQgl4N6CkSuQfHUH1ZwdxDNRgX_cvk1Go'

# Создание объекта бота
bot = telebot.TeleBot(TOKEN)


# Функция для отправки видео пользователю фрагментами по 2 минуты
def send_video_by_segments(chat_id, video_file):
    duration = 120  # duration in seconds (2 minutes)
    segment_number = 1

    # Run ffmpeg command to split the video
    subprocess.call(
        ['ffmpeg', '-i', video_file, '-c', 'copy', '-map', '0', '-segment_time', str(duration), '-f', 'segment',
         '-reset_timestamps', '1', 'output%03d.mp4'])

    # Send video segments to user
    for segment_file in os.listdir():
        if "output" in segment_file:
            with open(segment_file, 'rb') as f:
                bot.send_video(chat_id, f, caption=segment_file)
            os.remove(segment_file)
            segment_number += 1

        # Обработчик команды /start


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, 'Привет! Отправьте мне ссылку на видео на YouTube.')


# Обработчик всех сообщений
@bot.message_handler(func=lambda message: True)
def send_video(message):
    try:
        # Получение ссылки на видео из сообщения
        link = message.text
        if 'youtube.com/' not in link:
            raise ValueError('Ссылка не является ссылкой на YouTube.')

            # Парсинг информации о видео
        bot.reply_to(message, 'Парсю видео.....')
        html = requests.get(link, timeout=10).content
        soup = BeautifulSoup(html, 'html.parser')
        title = soup.find('title').text.replace(' - YouTube', '')
        video_url = 'https://www.youtube.com' + soup.find('meta', {'property': 'og:video:url'})['content']

        bot.reply_to(message, 'Видео спарсено')
        bot.reply_to(message, 'Видео начало скачиваться')
        # Загрузка видео
        video = YouTube(video_url)
        video_file = video.streams.get_highest_resolution().download()
        bot.reply_to(message, 'Видео скачано')

        # Отправка видео пользователю фрагментами по 2 минуты
        bot.reply_to(message, 'Отправляю видео')
        send_video_by_segments(message.chat.id, video_file)
        bot.reply_to(message, 'Все видео отправлены')

        # Удаление видео с сервера
        os.remove(video_file)

    except requests.exceptions.Timeout as e:
        bot.reply_to(message, 'Произошла ошибка Timeout: {}'.format(str(e)))
    except Exception as e:
        bot.reply_to(message, 'Произошла ошибка: {}'.format(str(e)))

    # Запуск бота


bot.polling()