from http.server import SimpleHTTPRequestHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import User
from .settings import USERNAME, PASSWORD, DATABASENAME, DATABASEPORT
import uuid
from .models import Token
from datetime import timedelta, datetime

# Database connection
engine = create_engine(f'postgresql+psycopg2://{USERNAME}:{PASSWORD}@localhost:{DATABASEPORT}/{DATABASENAME}')
Session = sessionmaker(bind=engine)

# Web server class
class WebAppHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            with open("bot/templates/index.html", "r", encoding="utf-8") as file:
                html = file.read()
            self.wfile.write(html.encode("utf-8"))
        else:
            self.send_error(404, "Page not found.")

# Menu display function
async def show_menu(update, context):
    keyboard = [
        ['/start', '/game', '/web'],  # Main buttons of the bot
        ['/invite']#, 'Help', 'Settings']  # Add the /invite command to the menu
    ]
    
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=False, resize_keyboard=True)

    await update.message.reply_text("", reply_markup=reply_markup)

# Telegram bot functions
async def start(update, context):
    # User information
    telegram_id = update.message.from_user.id
    first_name = update.message.from_user.first_name
    last_name = update.message.from_user.last_name
    username = update.message.from_user.username

    # Database connection
    session = Session()

    # Get or create the user
    user, created = User.get_or_create(
        session=session,
        telegram_id=telegram_id,
        defaults={
            "first_name": first_name,
            "last_name": last_name,
            "username": username,
            "invite_code": str(uuid.uuid4())[:6]  # Generate a new invite code
        }
    )

    # Generate or update the token
    token, created = Token.get_or_create(
        session=session,
        user_id=user.id,
        defaults={
            "token": str(uuid.uuid4())[:10],
            "expires_at": datetime.now() + timedelta(minutes=2)
        }
    )

    # Web URL with token
    web_url = f"https://yourdjangowebsite.com/verify_token?token={token.token}"
    # web_url = f"https://dd4b-5-75-197-252.ngrok-free.app/home/?telegram_id={telegram_id}&first_name={first_name}&last_name={last_name}&username={username}"

    # "Lunch Game" button
    keyboard = [
        [InlineKeyboardButton("Lunch Game", url=f"{web_url}")]  # Game start link
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send message with the button
    await update.message.reply_text(
        "Click the button below to start the game:",
        reply_markup=reply_markup
    )

    # Commit and close the session
    session.close()


# New function to display "Lunch Game" button when the user enters /game command
async def game(update, context):
    # User information
    telegram_id = update.message.from_user.id
    # first_name = update.message.from_user.first_name
    # last_name = update.message.from_user.last_name
    # username = update.message.from_user.username

    session = Session()
    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    token, created = Token.get_or_create(
        session=session,
        user_id=user.id,
        defaults={
            "token": str(uuid.uuid4())[:10],
            "expires_at": datetime.now() + timedelta(minutes=2)
        }
    )
    session.close()
    
    # Game server URL and adding user information to the URL
    web_url = f"https://yourdjangowebsite.com/verify_token?token={token.token}"
    # web_url = f"https://dd4b-5-75-197-252.ngrok-free.app/home/?telegram_id={telegram_id}&first_name={first_name}&last_name={last_name}&username={username}"

    # "Lunch Game" button with user information
    keyboard = [
        [InlineKeyboardButton("Lunch Game", url=web_url)]  # Send information to Django site
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Click the button below to start the game:",
        reply_markup=reply_markup
    )

# New function for /invite
async def invite(update, context):
    telegram_id = update.message.from_user.id
    
    # Database connection
    session = Session()
    
    # Check if the user exists in the database
    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    
    if user:
        # If the user exists in the database, send the invite code
        invite_url = f"t.me/testpythonshahin_bot?start={user.invite_code}"
        await update.message.reply_text(
            f"Hello {user.first_name}!\nUse this link to invite your friends: {invite_url}"
        )
    else:
        # If the user is not in the database, inform them to register first
        await update.message.reply_text("You need to register first.")

    session.close()

async def handle_invite_code(update, context):
    telegram_id = update.message.from_user.id
    invite_code = update.message.text.strip()

    # Database connection
    session = Session()

    # Check the invite code
    invite = session.query(User).filter_by(invite_code=invite_code).first()
    if invite:
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        if user:
            user.inviter_id = invite.id  # Add the user to the inviter
            session.commit()

            await update.message.reply_text(f"You joined the bot through invite code from {invite.first_name}.")
        else:
            await update.message.reply_text("You need to register first.")
    else:
        await update.message.reply_text("Invalid invite code.")

    session.close()


async def show_web(update, context):
    web_url = "t.me/testpythonshahin_bot/app1"
    await update.message.reply_text(
        f"Click here to view the graphical interface:\n{web_url}"
    )

async def echo(update, context):
    user_message = update.message.text
    await update.message.reply_text(f"You said: {user_message}")

# Bot settings
def setup_bot(token):
    application = ApplicationBuilder().token(token).build()

    # Adding commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("game", game))  # Adding /game command
    application.add_handler(CommandHandler("invite", invite))  # Adding /invite command
    application.add_handler(CommandHandler("echo", echo))
    application.add_handler(CommandHandler("web", show_web))
    application.add_handler(CommandHandler("menu", show_menu))  # Adding /menu command to show menu

    return application
