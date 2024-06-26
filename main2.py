from telethon.sync import TelegramClient, events

# Deine API-Daten
api_id = 25752585
api_hash = 'ebd8a0eff4d84321c9f6de9bb3e3a960'
phone_number = '+491729984906'


# Initialisiere den Telegram Client
client = TelegramClient('session_name', api_id, api_hash)

# Ereignishandler für eingehende Nachrichten
@client.on(events.NewMessage)
def handler(event):
    print(f'Nachricht von {event.sender_id}: {event.text}')

async def get_chat_id(username):
    """Ruft die Chat-ID basierend auf dem Benutzernamen ab."""
    entity = await client.get_entity(username)
    return entity.id

async def fetch_history(chat_id):
    """Funktion zum Abrufen und Ausdrucken der Chat-Historie für eine gegebene Chat-ID."""
    async for message in client.iter_messages(chat_id, limit=100):  # Limit kann angepasst werden
        print(f'Historische Nachricht von {message.sender_id}: {message.text}')

def main():
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
    client.run_until_disconnected()

if __name__ == '__main__':
    main()

