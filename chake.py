import requests
from bs4 import BeautifulSoup
import telebot
import time

# --- Telegram Bot Token ---
BOT_TOKEN = '7889202369:AAHTJKlN-0HoIBfMeKE_K4dhwunKOJESlcs'  # Replace with your bot token
bot = telebot.TeleBot(BOT_TOKEN)

# --- User Data Temp Store (only for current session) ---
user_data = {}

# --- Login and Fetch Balance Function ---
def login_and_fetch_balance(email, password):
    base_url = 'https://playinmatch.com'
    session = requests.Session()

    # Step 1: Get CSRF Token
    try:
        resp = session.get(base_url)
        soup = BeautifulSoup(resp.text, 'html.parser')
        csrf_tag = soup.find('meta', {'name': 'csrf-token'})
        if not csrf_tag:
            return "❌ CSRF token not found."

        csrf_token = csrf_tag['content']
        csrf_cookie = session.cookies.get('XSRF-TOKEN')

        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json, text/plain, */*',
            'X-CSRF-TOKEN': csrf_token,
            'X-XSRF-TOKEN': csrf_cookie,
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': base_url,
            'Origin': base_url,
            'User-Agent': 'Mozilla/5.0'
        }
        session.headers.update(headers)

        # Step 2: Login
        login_url = f'{base_url}/api2/v2/login'
        login_payload = {'email': email, 'password': password}
        login_resp = session.post(login_url, json=login_payload)

        # Debugging log to see the response
        print(f"Login Response: {login_resp.text}")

        # Check if login was successful by checking the message in the response
        if login_resp.status_code != 200 or "Login Success" not in login_resp.text:
            return f"❌ Login failed. Response: {login_resp.text}"

        # Step 3: Fetch Balance
        time.sleep(2)
        balance_url = f'{base_url}/api/getBalance'
        balance_resp = session.post(balance_url, json={})

        # Debugging log to see balance response
        print(f"Balance Response: {balance_resp.text}")

        if balance_resp.status_code == 200:
            data = balance_resp.json()
            wallet = data.get('balance', {}).get('wallet', 'N/A')
            return f"💰 Wallet Balance: {wallet}"
        else:
            return f"❌ Failed to fetch balance. Status: {balance_resp.status_code}"

    except Exception as e:
        return f"⚠️ Error: {str(e)}"

# --- Telegram Handlers ---
@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    # Send welcome message and ask to join the channel
    bot.send_message(chat_id, "👋 Welcome! To use the bot, you must join our Telegram channel first.")
    
    # Add channel join button
    channel_button = telebot.types.InlineKeyboardButton(text="Join Our Telegram Channel", url="https://t.me/primescripter")  # Replace with your channel link
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(channel_button)
    
    bot.send_message(chat_id, "Please join the channel by clicking the button below:", reply_markup=keyboard)
    
    # Ask to confirm after joining the channel
    bot.send_message(chat_id, "Once you have joined the channel, type /joined to proceed.")

@bot.message_handler(commands=['joined'])
def join_confirmation(message):
    chat_id = message.chat.id
    try:
        # Check if user is in the channel
        member = bot.get_chat_member("@primescripter", chat_id)  # Replace @YourChannel with your actual channel's username

        if member.status in ['member', 'administrator', 'creator']:
            bot.send_message(chat_id, "🎉 Thank you for joining the channel! You can now proceed with the bot.")
            bot.send_message(chat_id, "Type /checkbalance to proceed with checking your balance.")
        else:
            bot.send_message(chat_id, "❌ You must join the channel before proceeding. Please join the channel and type /joined again.")
    except Exception as e:
        bot.send_message(chat_id, f"⚠️ Error checking your membership: {str(e)}")


@bot.message_handler(commands=['checkbalance'])
def ask_email(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "📧 Please enter your email:")
    bot.register_next_step_handler(message, get_email)

def get_email(message):
    chat_id = message.chat.id
    user_data[chat_id] = {'email': message.text}
    bot.send_message(chat_id, "🔐 Now enter your password:")
    bot.register_next_step_handler(message, get_password)

def get_password(message):
    chat_id = message.chat.id
    user_data[chat_id]['password'] = message.text
    email = user_data[chat_id]['email']
    password = user_data[chat_id]['password']
    bot.send_message(chat_id, "⏳ Logging in... Please wait...")

    result = login_and_fetch_balance(email, password)
    bot.send_message(chat_id, result)  # Send the result, which includes balance or error message

# --- Run the bot ---
bot.infinity_polling()