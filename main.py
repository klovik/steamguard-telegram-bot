import os
import json
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from dotenv import load_dotenv
import time
import hmac
import struct
import base64
import requests
from hashlib import sha1
from bs4 import BeautifulSoup

load_dotenv()

API_KEY = os.getenv("TELEGRAM_API_KEY")
bot = telebot.TeleBot(API_KEY)

script_dir = os.path.dirname(os.path.abspath(__file__))
mafiles_dir = os.path.join(script_dir, 'maFiles')

whitelist = [os.getenv("ADMIN_ID")]

def get_username(steamid64: str) -> str:
    r = requests.get(f"https://steamcommunity.com/profiles/{steamid64}")
    soup = BeautifulSoup(r.content, "html.parser")
    span = soup.find("span", class_="actual_persona_name")
    return span.text.strip() if span else steamid64

steamids = {
    get_username(path.replace(".maFile", "")): path
    for path in os.listdir(mafiles_dir)
    if os.path.isfile(os.path.join(mafiles_dir, path)) and path.endswith(".maFile")
}
def getQueryTime():
    try:
        request = requests.post('https://api.steampowered.com/ITwoFactorService/QueryTime/v0001', timeout=30)
        json_data = request.json()
        return int(json_data['response']['server_time']) - time.time()
    except:
        return 0

def getGuardCode(shared_secret):
    symbols = "23456789BCDFGHJKMNPQRTVWXY"
    code = ''
    timestamp = time.time() + getQueryTime()
    _hmac = hmac.new(base64.b64decode(shared_secret), struct.pack('>Q', int(timestamp / 30)), sha1).digest()
    _ord = _hmac[19] & 0xF
    value = struct.unpack('>I', _hmac[_ord:_ord+4])[0] & 0x7FFFFFFF
    for _ in range(5):
        code += symbols[value % len(symbols)]
        value //= len(symbols)
    return code

def mkup():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    for username in steamids.keys():
        markup.add(KeyboardButton(text=username))
    return markup

@bot.message_handler(commands=["start"])
def start(message):
    if str(message.from_user.id) in whitelist:
        bot.send_message(message.chat.id, "sup", reply_markup=mkup())

def get_guard_code(acc: int) -> str:
    with open(os.path.join(mafiles_dir, f'{acc}'), 'r') as file:
        data = json.load(file)
        return getGuardCode(data['shared_secret'])

@bot.message_handler(func=lambda message: True)
def msg(message):
    if str(message.from_user.id) in whitelist:
        if message.text in steamids:
            bot.send_message(
                message.chat.id,
                f"<code>{get_guard_code(steamids[message.text])}</code>",
                parse_mode="HTML"
            )
bot.infinity_polling()
