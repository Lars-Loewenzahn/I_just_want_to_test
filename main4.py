import os
import logging
from dotenv import load_dotenv
import openai
from telegram import Update, Message
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from random import random, randint, choice
from telethon.sync import TelegramClient, events
from time import sleep


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

# Verarbeiten der mehrzeiligen Rolle
bot_role_raw = os.getenv('BOT_ROLE', 'You are a helpful assistant.')
bot_role = bot_role_raw.replace('|', '\n')

# Liste von möglichen zusätzlichen Nachrichten
additional_prompts = [
    "Verscuhe in deiner Antwort witzig zu sein.",
    "Versuche in deiner Antwort einen Reim zu verwenden.",
    "Bau ein Zitat von einer berühmten Person ein.",
    "Verwende in deiner Antwort ein paar Smileys wie :), :D etc.",
    "Versuche, dass die antwort leicht geflirtet oder doppeldeutig ist."
]

# Initialisiere den Telegram Client
api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
phone_number = os.getenv('PHONE_NUMBER')

client = TelegramClient('session_name', api_id, api_hash)

# Dictionary zur Speicherung des Chatverlaufs
chat_history = ""

# Ereignishandler für eingehende Nachrichten
@client.on(events.NewMessage)

def handler(event):
    print(f'Nachricht von {event.sender_id}: {event.text}')

async def get_chat_id(username):
    """Ruft die Chat-ID basierend auf dem Benutzernamen ab."""
    entity = await client.get_entity(username)
    return entity.id

async def fetch_history(chat_id):
    global chat_history
    """Funktion zum Abrufen und Ausdrucken der Chat-Historie für eine gegebene Chat-ID."""
    async for message in client.iter_messages(chat_id, limit=100):  # Limit kann angepasst werden
        chat_history += "/n" + f'Nachricht von {message.sender_id}: {message.text}'
        if "/restart" in message.text:
            break
    print(chat_history)

def engage_openai(user_id: int, prompt: str) -> str:
    """
    Holt eine Antwort von OpenAI basierend auf dem bereitgestellten Prompt.
    """
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=50 + int(random() * 250),
        temperature=random()
    )
    bot_response = response.choices[0].message['content'].strip()
    if bot_response.find("Nachricht von 7419959268:") != -1:
        bot_response = bot_response[len("Nachricht von 7419959268:"):]
    logger.info(f"Generated response for user {user_id}: {bot_response}")
    # sleep(len(bot_response))
    return bot_response

async def start_command(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    logger.info(f"Started conversation with user {user_id}")
    await update.message.reply_text('Hey, hier ist Lisa! <3')

def prepare_prompt():
    additional_prompt = choice(additional_prompts)
    logger.info(f"Added additional prompt for variety: {additional_prompt}")
    prompt = "Hier ist der Chatverlauf vom bisherigen Gespräch. Finde eine Fortsetzung die Sinn macht. Antworte nur mit dem Text der Antwort. Der Text'nNachricht von ....:' soll nicht tiel deiner Antwort sein. "
    prompt += additional_prompt
    prompt += chat_history
    return prompt

async def handle_message(update: Update, context: CallbackContext) -> None:
    global chat_history
    user_id = update.message.from_user.id
    user_message = update.message.text
    timestamp = update.message.date.strftime("%Y-%m-%d %H:%M:%S")

    logger.info(f"Received message from user {user_id}: {user_message}")

    # Store the user's message in the conversation history
    # TODO
    chat_history += f'Nachricht von {user_id}: {user_message}'
    # chat_histories[user_id].append({"role": "user", "content": user_message, "timestamp": timestamp})
    # log_conversation_history(user_id)

    try:
        prompt = prepare_prompt()
        bot_response = engage_openai(user_id, prompt)
        await update.message.reply_text(bot_response)

        # Update the messages with the new conversation history
        chat_history += f'Nachricht von 7419959268: {user_message}'

    except Exception as e:
        logger.error(f"Error generating response for user {user_id}: {e}")
        await update.message.reply_text("Sorry, I couldn't process your request.")

async def error_handler(update: Update, context: CallbackContext) -> None:
    logger.error(msg="Exception while handling an update:", exc_info=context.error)

def main() -> None:
    # Verbinde dich mit dem Telegram Client
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

    # Benutzername des Chats, dessen ID abgerufen werden soll
    username = '@Lisa_the_robot'

    with client:
        chat_id = client.loop.run_until_complete(get_chat_id(username))
        print(f'Die Chat-ID von {username} ist: {chat_id}')
        client.loop.run_until_complete(fetch_history(chat_id))

    # Halte den Client am Laufen, um auf Ereignisse zu warten
    #client.run_until_disconnected()

    logger.info("Starting bot")

    application = Application.builder().token(bot_token).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)

    application.run_polling()
    logger.info("Bot is polling")

if __name__ == '__main__':
    main()
