import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# Logging konfigurieren
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

# Start Befehl
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Hallo! Ich bin dein Bot. Wie kann ich dir helfen?')

# Echo Funktion für Nachrichten
async def echo(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(update.message.text)

# Fehlerbehandlung
def error(update: Update, context: CallbackContext) -> None:
    logger.warning('Update "%s" hat einen Fehler verursacht: %s', update, context.error)

def main() -> None:
    # Setzen Sie Ihren Token hier ein
    token = '7419959268:AAH9q2F8AE9Gpc_ula0n8td5sAMi9LRqECY'

    # Application initialisieren
    application = Application.builder().token(token).build()

    # Handler für /start Befehl
    application.add_handler(CommandHandler("start", start))

    # Handler für alle Nachrichten
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Fehler-Handler
    application.add_error_handler(error)

    # Bot starten
    application.run_polling()

if __name__ == '__main__':
    main()
