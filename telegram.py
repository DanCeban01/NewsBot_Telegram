import requests
import os
import sqlite3 
import threading 
from flask import Flask, request 
from asyncore import dispatcher_with_send
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

app = Flask(__name__)
bot_token = '6095098964:AAFw2xhbDAQF3Ma5rIUP9-T966xTxPEvdXY'  # Replace with your Telegram bot token
bot = Bot(token=bot_token)
dispatcher = dispatcher_with_send(bot, None)

# Create a thread-local SQLite connection and cursor
local = threading.local()

def get_connection():
    if not hasattr(local, "conn"):
        local.conn = sqlite3.connect('news.db')
    return local.conn

def get_cursor():
    if not hasattr(local, "cursor"):
        local.cursor = get_connection().cursor()
    return local.cursor

# Create the 'news' table if it doesn't exist
cursor = get_cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS news
                  (user_id INTEGER, url TEXT)''')
get_connection().commit()

# Handler for the /start command
def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Hello! Welcome to the bot.")

# Handler for the /latest_news command
def latest_news(update, context):
    topic = context.args[0] if len(context.args) > 0 else None

    # Make a request to the NYT API
    nyt_api_key = 'Bhza85VHX50Hg2hrRzfiRxTG0esz61OJ'  # Replace with your NYT API key
    url = f"https://api.nytimes.com/svc/search/v2/articlesearch.json?q={topic}&api-key={nyt_api_key}"
    response = requests.get(url)
    articles = response.json().get('response', {}).get('docs', [])[:5]  # Fetch up to 5 articles

    # Extract relevant information from the articles
    news_links = []
    for article in articles:
        headline = article.get('headline', {}).get('main', '')
        web_url = article.get('web_url', '')
        news_links.append(f"{headline}\n{web_url}")

    # Send the news links as a response
    if news_links:
        context.bot.send_message(chat_id=update.effective_chat.id, text='\n'.join(news_links))
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="No news articles found.")

# Handler for the /save_news command
def save_news(update, context):
    # Get the user ID and the news URL to save
    user_id = update.effective_chat.id
    url = ' '.join(context.args)

    # Save the news URL in the database
    cursor = get_cursor()
    cursor.execute("INSERT INTO news (user_id, url) VALUES (?, ?)", (user_id, url))
    get_connection().commit()

    context.bot.send_message(chat_id=update.effective_chat.id, text="News saved successfully.")

# Handler for the /saved_news command
def saved_news(update, context):
    # Get the user ID
    user_id = update.effective_chat.id

    # Retrieve the saved news URLs for the user from the database
    cursor = get_cursor()
    cursor.execute("SELECT url FROM news WHERE user_id = ?", (user_id,))
    saved_urls = cursor.fetchall()

    # Send the saved news URLs as a response
    if saved_urls:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Your saved news:")
        for url in saved_urls:
            context.bot.send_message(chat_id=update.effective_chat.id, text=url[0])
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="No saved news found.")


# Handler for the /spider_menance command
def spider_menance(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Fetching Spider-Man photos...")

    # Make a request to fetch Spider-Man photos from Unsplash API
    unsplash_access_key = 'SeA564rjGuafduq9BxleS_pREX1UPmx1cXgdIM1bK9g'  # Replace with your Unsplash Access Key
    query = "Spider-Man"
    url = f"https://api.unsplash.com/search/photos"
    headers = {"Authorization": f"Client-ID {unsplash_access_key}"}
    params = {"query": query, "per_page": 5}
    response = requests.get(url, headers=headers, params=params)
    photos = response.json().get('results', [])

    # Send the photos as a response
    for photo in photos:
        photo_url = photo.get("urls", {}).get("regular", "")
        context.bot.send_photo(chat_id=update.effective_chat.id, photo=photo_url)

# Handler for contacting me
def contact(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Here is my contact to thank me: ceband2001@gmail.com") 

# Handler for other non-command messages
def echo(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="I'm sorry, I don't understand that command.")

def main():
    updater = Updater(token=bot_token, use_context=True)
    dispatcher = updater.dispatcher

    # Set up command handlers
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('latest_news', latest_news))
    dispatcher.add_handler(CommandHandler('save_news', save_news))
    dispatcher.add_handler(CommandHandler('saved_news', saved_news))
    dispatcher.add_handler(CommandHandler('spider_menance', spider_menance))
    dispatcher.add_handler(CommandHandler('contact', contact))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

   # Webhook route
@app.route('/webhooks/telegram', methods=['POST'])

def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = Update.de_json(json_string)
        dispatcher.process_update(update)
    return 'OK'

if __name__ == '__main__':
    # Set up webhook
    webhook_url = 'https://e175-31-148-133-1.ngrok-free.app/webhooks/telegram'  # Replace with your Ngrok URL and webhook path
    bot.setWebhook(webhook_url)

    # Start the Flask server
    app.run(port=5000)