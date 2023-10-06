import logging
import os
from decouple import config 
from database import get_store
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, 
    ContextTypes, 
    CommandHandler, 
    ConversationHandler, 
    MessageHandler, 
    filters
)


###LOGGER
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

###Check for running parent venv
if not os.getenv("VIRTUAL_ENV"):
    logger.error("Please activate a virtual environment before running the bot.")
    exit(1)

###Load TG api token, include check.
token = config('TG_api_token')
if not token:
     logger.info("Invalid token")
     exit(1)

###Constants for PYTB Conversation states
GET_NAME, GET_DESCRIPTION, GET_PRICE = range(3)
BUY_ITEM_NAME = 1



###BOT COMMANDS
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    available_commands = "Available commands:\n/buy - Search for item buy name to purchase \n/sell - List an item for sale \n/show_listings - Show available products for sale"
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Welcome to Flow-bot! {available_commands}")

async def sell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    await update.message.reply_text("You have initiated the item listing process. Please provide the name of the item you want to sell:")
    context.user_data['selling_item'] = {}
    logger.info(
        "%s listed an item for sale", context._user_id 
    )
    return GET_NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['selling_item']['name'] = update.message.text
    await update.message.reply_text("Please provide a description for the item:")
    return GET_DESCRIPTION

async def get_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['selling_item']['description'] = update.message.text
    await update.message.reply_text("Please provide the price of the item:")
    return GET_PRICE

async def get_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['selling_item']['price'] = update.message.text

    store = get_store()
    store.insert_one(context.user_data['selling_item'])
    await update.message.reply_text("Successfully listed item for sale.")
    
    return ConversationHandler.END

async def print_listings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    store = get_store()
    listings = store.find()

    listings_text = "Listings: \n"
    for listing in listings:
        listings_text += f"Name: {listing['name']}, Description: {listing['description']}, Price: {listing['price']}\n"
    
    await update.message.reply_text(listings_text)
    return 

async def buy(update: Update, context:ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("You have initiated the item purchase process. Please provide the name of the item you want to buy:")
    return BUY_ITEM_NAME

async def get_item_name(update: Update, context:ContextTypes.DEFAULT_TYPE):
    item_name = update.message.text
    
    store = get_store()
    myquery = { "name": item_name } 
    search_result = store.find_one(myquery)

    if search_result:
            # Item found, construct and send a response
            response = f"Item Name: {search_result['name']}\n"
            response += f"Description: {search_result['description']}\n"
            response += f"Price: {search_result['price']}\n"
            await update.message.reply_text(response)
    else:
            # Item not found
            await update.message.reply_text("Item not found.")

    return ConversationHandler.END

""" RUNNING THE BOT """
if __name__ == '__main__':
    application = ApplicationBuilder().token(token).build()

start_handler = CommandHandler(['start', 'help'], start)

sell_conversation_handler = ConversationHandler(
    entry_points=[CommandHandler('sell', sell)],
    states={
        GET_NAME: [MessageHandler(filters.TEXT & (~filters.COMMAND), get_name)],
        GET_DESCRIPTION: [MessageHandler(filters.TEXT & (~filters.COMMAND), get_description)],
        GET_PRICE: [MessageHandler(filters.TEXT & (~filters.COMMAND), get_price)],
    },
    fallbacks=[],
    )

listing_handler = CommandHandler('show_listings', print_listings)
buy_conversation_handler = ConversationHandler(
     entry_points=[CommandHandler('buy', buy)],
     states={
          BUY_ITEM_NAME: [MessageHandler(filters.TEXT & (~filters.COMMAND), get_item_name)],
     },
     fallbacks=[],
)
   
application.add_handler(start_handler)
application.add_handler(sell_conversation_handler)
application.add_handler(listing_handler)
application.add_handler(buy_conversation_handler)

application.run_polling()