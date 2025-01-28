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

    await update.message.reply_text("Welcome! Please choose an option from the menu below:", reply_markup=reply_markup)

# Telegram bot functions
async def start(update, context):
    # User information
    telegram_id = update.message.from_user.id
    first_name = update.message.from_user.first_name
    last_name = update.message.from_user.last_name
    username = update.message.from_user.username

    # Get invite code from the start parameters (if provided)
    args = context.args  # Input arguments from the start link
    invite_code = args[0] if args else None

    # Database connection
    session = Session()
    # Create or retrieve the user
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
            "expires_at": datetime.now() + timedelta(minutes=2),
            'is_used': False, 
        }
    )
    
    # If invite code exists and user does not already have an inviter
    if invite_code and user.inviter_id is None:
        inviter = session.query(User).filter_by(invite_code=invite_code).first()
        if inviter:
            user.inviter_id = inviter.id  # Set the inviter
            session.commit()

            await update.message.reply_text(
                f"Welcome {user.first_name}! You joined through {inviter.first_name}'s invite link."
            )
        else:
            await update.message.reply_text("Invalid invite code.")
    elif created:
        await update.message.reply_text(
            f"Welcome {user.first_name}! Your invite code is t.me/testpythonshahin_bot?start={user.invite_code}."
        )
    else:
        await update.message.reply_text("Welcome back!")
    # Web URL with token
    # web_url = f"https://yourdjangowebsite.com/verify_token?token={token.token}&invite_code={user.invite_code}"
    web_url = f"46.249.99.31:8000/verify_token?token={token.token}"
    # web_url = f"https://dd4b-5-75-197-252.ngrok-free.app/home/?telegram_id={telegram_id}&first_name={first_name}&last_name={last_name}&username={username}"
    session.close()
    # "Lunch Game" button
    keyboard = [
        [InlineKeyboardButton("Lunch Game", url=f"{web_url}")]  # Game start link
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send message with the button
    await update.message.reply_text(
        "This button is valid for 2 minutes. After 2 minutes,"
        "you need to press /start again to receive a new button."
        "Please do not forward this message.", reply_markup=reply_markup
    )


        # Send the main menu
        # await show_menu(update, context)



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
    web_url = f"46.249.99.31:8000/verify_token?token={token.token}"
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
    with Session() as session:
        # Find the user
        user = session.query(User).filter_by(telegram_id=telegram_id).first()

        if user:
            # Generate invite link
            invite_url = f"t.me/testpythonshahin_bot?start={user.invite_code}"
            await update.message.reply_text(
                f"Hello {user.first_name}!\nShare this link to invite your friends:\n{invite_url}"
            )
        else:
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
