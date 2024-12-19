from threading import Thread
from http.server import HTTPServer
from bot.views import WebAppHandler, setup_bot
from bot.settings import TOKEN, HOST, PORT


def run_webserver():
    try:
        server = HTTPServer((HOST, PORT), WebAppHandler)
        print(f"Server is running on: http://{HOST}:{PORT}")
        server.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down the web server...")
        server.server_close()


def run_bot():
    try:
        application = setup_bot(TOKEN)
        application.run_polling()
    except KeyboardInterrupt:
        print("Shutting down the bot...")


if __name__ == "__main__":
    try:
        Thread(target=run_webserver, daemon=True).start()
        run_bot()
    except KeyboardInterrupt:
        print("Exiting program...")
