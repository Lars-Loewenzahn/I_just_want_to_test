import os
import logging
from dotenv import load_dotenv
import openai
from telegram import Update, Message
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from random import random, randint, choice

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
    "Erzähle immer einen Witz.",
    "Versuche in deiner Antwort immer einen Reim zu verwenden.",
    "Bau ein Zitat von einer berühmten Person ein.",
    "Verwende immer ein paar Smileys wie :), :D etc.",
    "Jede deiner Antworten sollte geflirtet sein."
]

# Dictionary zur Speicherung des Chatverlaufs
chat_histories = {}

def log_conversation_history(user_id: int):
    if user_id in chat_histories:
        logger.info(f"Current conversation history for user {user_id}:")
        for message in chat_histories[user_id]:
            logger.info(f"{message['timestamp']} - {message['role']}: {message['content']}")

def format_prompt(user_id: int) -> str:
    """
    Formatiert den Chatverlauf für den OpenAI-Prompt.
    """
    prompt = "Bisheriger Chatverlauf:\n"
    for msg in chat_histories.get(user_id, []):
        prompt += f"{msg['timestamp']} - {msg['role']}: {msg['content']}\n"
    logger.info(f"Formatted prompt for user {user_id}: {prompt}")
    return prompt

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
    logger.info(f"Generated response for user {user_id}: {bot_response}")
    return bot_response

async def start_command(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    chat_histories[user_id] = []
    logger.info(f"Started conversation with user {user_id}")
    await update.message.reply_text('Hello! I am a bot powered by ChatGPT. How can I help you today?')

async def handle_message(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    user_message = update.message.text
    timestamp = update.message.date.strftime("%Y-%m-%d %H:%M:%S")

    logger.info(f"Received message from user {user_id}: {user_message}")

    # Initialize conversation history for the user if not already present
    if user_id not in chat_histories:
        chat_histories[user_id] = []
        logger.info(f"Initialized conversation history for user {user_id}")

    # Store the user's message in the conversation history
    chat_histories[user_id].append({"role": "user", "content": user_message, "timestamp": timestamp})
    log_conversation_history(user_id)

    # Prepare the prompt
    prepared_prompt = format_prompt(user_id)

    try:
        additional_prompt = choice(additional_prompts)
        prepared_prompt += f"\n{additional_prompt}"
        logger.info(f"Added additional prompt for variety: {additional_prompt}")

        bot_response = engage_openai(user_id, prepared_prompt)
        await update.message.reply_text(bot_response)

        # Update the messages with the new conversation history
        chat_histories[user_id].append({"role": "assistant", "content": bot_response, "timestamp": timestamp})
        log_conversation_history(user_id)

    except Exception as e:
        logger.error(f"Error generating response for user {user_id}: {e}")
        await update.message.reply_text("Sorry, I couldn't process your request.")

async def error_handler(update: Update, context: CallbackContext) -> None:
    logger.error(msg="Exception while handling an update:", exc_info=context.error)

def main() -> None:
    logger.info("Starting bot")
    application = Application.builder().token(bot_token).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)

    application.run_polling()
    logger.info("Bot is polling")

if __name__ == '__main__':
    main()
