from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, filters
import sqlite3
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Bot token
TOKEN = '8409651760:AAEWG6upbiuiGS68f3Ib1uWCS8-21WZwhmE'

# Admin username (without @)
ADMIN_USERNAME = 'ITZ_RG9988'

# Database setup
DB_NAME = 'steam_accounts.db'

# Conversation states for adding accounts
USERNAME, PASSWORD, GAME_NAME = range(3)

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_name TEXT NOT NULL,
            account_details TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Function to add account
def add_account(game_name, account_details):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO accounts (game_name, account_details) VALUES (?, ?)', (game_name, account_details))
    conn.commit()
    conn.close()

# Function to search games (case-insensitive)
def search_games(query):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT game_name FROM accounts')
    all_games = [row[0] for row in cursor.fetchall()]
    conn.close()
    query = query.lower()
    return [game for game in all_games if query in game.lower()]

# Function to get account details
def get_account(game_name):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT account_details FROM accounts WHERE game_name = ?', (game_name,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

# Start command: Main menu with emojis
async def start(update: Update, context):
    keyboard = [
        [InlineKeyboardButton("🔗 JOIN MAIN CHANNEL!", url='https://t.me/FREE_STEAM_ACCOUNTS_OFFICIAL')],
        [InlineKeyboardButton("🔍 SEARCH", callback_data='search')],
        [InlineKeyboardButton("📞 CONTACT ADMIN", url='https://t.me/CONTACT_RG_bot')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    welcome_message = "🎮 Welcome to Free Steam Accounts Bot!\nChoose an option:"
    if update.message:
        await update.message.reply_text(welcome_message, reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.edit_message_text(welcome_message, reply_markup=reply_markup)
    return None

# Handle button clicks
async def button(update: Update, context):
    query = update.callback_query
    await query.answer()
    if query.data == 'search':
        keyboard = [[InlineKeyboardButton("⬅ Go Back to Main Menu", callback_data='back_to_main')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text="🔍 Enter a game name to search (e.g., 'CYBER'):", reply_markup=reply_markup)
    elif query.data == 'back_to_main':
        return await start(update, context)

# Handle text messages (search)
async def handle_message(update: Update, context):
    text = update.message.text.strip()
    matches = search_games(text)
    if matches:
        keyboard = [[InlineKeyboardButton(match, callback_data=f'game_{match}')] for match in matches]
        keyboard.append([InlineKeyboardButton("⬅ Go Back to Main Menu", callback_data='back_to_main')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text('Select a game:', reply_markup=reply_markup)
    else:
        keyboard = [[InlineKeyboardButton("⬅ Go Back to Main Menu", callback_data='back_to_main')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text('No matches found. Try again!', reply_markup=reply_markup)

# Handle game selection
async def select_game(update: Update, context):
    query = update.callback_query
    await query.answer()
    game_name = query.data.replace('game_', '')
    account = get_account(game_name)
    keyboard = [[InlineKeyboardButton("⬅ Go Back to Main Menu", callback_data='back_to_main')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if account:
        await query.edit_message_text(text=f'🎮 Game: {game_name}\nAccount: {account}', reply_markup=reply_markup)
    else:
        await query.edit_message_text(text='Account not found.', reply_markup=reply_markup)

# Admin: Start adding account
async def add_account_start(update: Update, context):
    if update.message.from_user.username != ADMIN_USERNAME:
        await update.message.reply_text("🚫 Only the admin (@ITZ_RG9988) can add accounts.")
        return ConversationHandler.END
    await update.message.reply_text("👋 Hello Admin! Want to add a new account? Let's begin.\nEnter the username:")
    return USERNAME

# Admin: Receive username
async def add_account_username(update: Update, context):
    context.user_data['username'] = update.message.text.strip()
    await update.message.reply_text("🔑 Enter the password:")
    return PASSWORD

# Admin: Receive password
async def add_account_password(update: Update, context):
    context.user_data['password'] = update.message.text.strip()
    await update.message.reply_text("🎮 Enter the game name(s) this account has:")
    return GAME_NAME

# Admin: Receive game name and save
async def add_account_game_name(update: Update, context):
    game_name = update.message.text.strip()
    username = context.user_data['username']
    password = context.user_data['password']
    account_details = f"{username}:{password}"
    add_account(game_name, account_details)
    await update.message.reply_text(f"✅ Added: {game_name} with account {account_details}")
    context.user_data.clear()  # Clear stored data
    return await start(update, context)  # Return to main menu

# Admin: Cancel adding account
async def cancel(update: Update, context):
    await update.message.reply_text("❌ Account addition cancelled.")
    context.user_data.clear()
    return await start(update, context)

def main():
    init_db()
    application = Application.builder().token(TOKEN).build()

    # Conversation handler for adding accounts
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('add', add_account_start)],
        states={
            USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_account_username)],
            PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_account_password)],
            GAME_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_account_game_name)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    # Add handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(button, pattern='^(search|back_to_main)$'))
    application.add_handler(CallbackQueryHandler(select_game, pattern='^game_'))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(conv_handler)

    application.run_polling()

if __name__ == '__main__':
	main()