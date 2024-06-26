import os
import logging
from dotenv import load_dotenv
import openai
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, CallbackContext
from telethon.sync import TelegramClient, events
from telethon.tl.types import InputPeerUser
from random import choice

# Einrichten des Loggings
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Laden der Umgebungsvariablen aus der .env Datei
load_dotenv()

# Zugriff auf die API-Schlüssel und die Rolle des Bots
openai.api_key = os.getenv('OPENAI_API_KEY')
bot_token = os.getenv('TELEGRAM_BOT_TOKEN')

# Initialisiere den Telegram Client
api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
phone_number = os.getenv('PHONE_NUMBER')

client = TelegramClient('session_name', api_id, api_hash)

# Liste der zugelassenen Chat-IDs
allowed_chat_ids = [123456789, 987654321, 5186744736]  # Beispiel-IDs

# Ereignishandler für eingehende Nachrichten
@client.on(events.NewMessage)
async def handler(event):
    chat_id = event.chat_id
    if chat_id not in allowed_chat_ids:
        logger.info(f'Nachricht von {chat_id}: {event.text}')
        return

    # Verlauf abrufen und zusammenfassen
    history = await fetch_history(chat_id)
    summary = summarize_conversation(history)

    # OpenAI um Antwortmöglichkeiten bitten
    response_choices = generate_response_choices(summary)

    # Inline-Buttons erstellen
    buttons = [
        [InlineKeyboardButton(response, callback_data=f'{chat_id}:{response}') for response in response_choices]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)

    # TODO: Hier geht die query an die falsche addresse

    # An Sie eine Inline-Query senden
    await client.send_message(chat_id, "Wählen Sie eine Antwort:", buttons=reply_markup)

async def fetch_history(chat_id):
    logger.info("fetching history started")
    chat_history = ""
    async for message in client.iter_messages(chat_id, limit=10):
        chat_history += f'Nachricht von {message.sender_id}: {message.text}\n'
    logger.info(chat_history)
    logger.info("History fetched")
    return chat_history

def summarize_conversation(history):
    logger.info("Summerize...")
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Fasse diesen Chat-Verlauf zusammen:" + history}],
        max_tokens=150,
        temperature=0.7
    )
    logger.info("Summary complete")
    return response.choices[0]['message']['content']#


def generate_response_choices(summary):
    logger.info("Generating responses")
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": "Erstelle drei mögliche Antworten auf diese Konversation:"}, {"role": "user", "content": summary}],
        max_tokens=150,
        n=3
    )
    logger.info(response)
    return [choice['message']['content'].strip() for choice in response.choices]


async def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    chat_id, response = query.data.split(':')
    await client.send_message(int(chat_id), response)
    await query.edit_message_text(text="Antwort gesendet.")

def main() -> None:
    client.connect()

    if not client.is_user_authorized():
        client.send_code_request(phone_number)
        print('Code wurde gesendet. Bitte überprüfe dein Telegram.')
        code = input('Please enter the code you received: ')
        try:
            client.sign_in(phone_number, code)
        except Exception:
            password = "Mariia"
            client.sign_in(password=password)

    print("Client gestartet. Warte auf Nachrichten...")

    # Telegram Bot initialisieren
    application = Application.builder().token(bot_token).build()
    application.add_handler(CallbackQueryHandler(button))
    application.run_polling()

if __name__ == '__main__':
    main()
