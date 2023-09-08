from flask import render_template, redirect, url_for, request, session
from flask_babel import refresh
from time import time
from os import urandom
from server.babel import get_locale, get_languages
import functools
import logging
from gapp import app


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            return redirect("/login")
            # url = url_for('login')
            # print(url)
            # return redirect(url)
        return view(*args, **kwargs)

    return wrapped_view


def load_login_details():
    login_details = {}
    try:
        with open("login_details.txt", "r") as file:
            for line in file:
                username, password = line.strip().split(":")
                login_details[username] = password
    except FileNotFoundError:
        print("Login details file not found.")
    return login_details


def authenticate(username, password):
    login_details = load_login_details()
    return username in login_details and login_details[username] == password


class Website:
    def __init__(self, bp, url_prefix) -> None:
        self.bp = bp
        self.url_prefix = url_prefix
        self.routes = {
            '/': {
                'function': lambda: redirect(url_for('._index')),
                'methods': ['GET', 'POST']
            },
            "/login": {"function": self._login, "methods": ["GET", "POST"]},
            '/chat/': {
                'function': self._index,
                'methods': ['GET', 'POST']
            },
            '/chat/<conversation_id>': {
                'function': self._chat,
                'methods': ['GET', 'POST']
            },
            '/change-language': {
                'function': self.change_language,
                'methods': ['POST']
            },
            '/get-locale': {
                'function': self.get_locale,
                'methods': ['GET']
            },
            '/get-languages': {
                'function': self.get_languages,
                'methods': ['GET']
            },
            "/logout": {"function": self._logout, "methods": ["GET", "POST"]},
        }

    def _logout():
        session.pop("user_id", None)
        return redirect("/login")

    def _login(self):
        if request.method == "POST":
            user_id = request.form["user_id"]
            password = request.form.get("password")

            if not user_id or not password:
                error_message = "Please fill in all the required fields."
                return render_template("login.html", error=error_message)

            if not authenticate(user_id, password):
                error_message = "Invalid login details. Please try again."
                return render_template("login.html", error=error_message)
            session["user_id"] = user_id
            # conversations[user_id] = initialize_conversation()
            log_file = f"log/{user_id}.log"
            handler = logging.FileHandler(log_file, encoding="utf-8")
            handler.setLevel(logging.INFO)
            formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            handler.setFormatter(formatter)
            message = "登陆"
            logmes = f"{user_id}: {message}"

            app.logger.addHandler(handler)
            app.logger.info(logmes)
            app.logger.removeHandler(handler)

            # lock = threading.Lock()

            # def write_log(message):
            #     with lock:
            #         logger = logging.getLogger()
            #         logger.addHandler(handler)
            #         logger.info(message)
            #         logger.removeHandler(handler)

            # write_log(logmes)

            return redirect("/")
        return render_template("login.html")

    @login_required
    def _chat(self, conversation_id):
        if '-' not in conversation_id:
            return redirect(url_for('._index'))

        return render_template('index.html', chat_id=conversation_id, url_prefix=self.url_prefix)

    @login_required
    def _index(self):
        return render_template('index.html', chat_id=f'{urandom(4).hex()}-{urandom(2).hex()}-{urandom(2).hex()}-{urandom(2).hex()}-{hex(int(time() * 1000))[2:]}', url_prefix=self.url_prefix)

    def change_language(self):
        data = request.get_json()
        session['language'] = data.get('language')
        refresh()
        return '', 204

    def get_locale(self):
        return get_locale()
    
    def get_languages(self):  
        return get_languages()
