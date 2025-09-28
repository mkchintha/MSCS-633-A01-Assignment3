# Django Terminal Chatbot with ChatterBot

A Django project that exposes a text-based chatbot client in the terminal using ChatterBot. This setup is designed with good software engineering practices to align with secure software development coursework.

## Features

- Run via Django management command: `python manage.py chat_cli`
- Uses ChatterBot with a BestMatch logic adapter
- Small corpus training plus deterministic custom pairs
- Logs are saved to `logs/session.log` but terminal output remains clean
- Works on Python 3.11 using the `chatterbot2` fork

## Folder structure

```
chatterbot_cli/
  manage.py                # Django entrypoint
  README.md                # Project documentation
  requirements.txt         # Dependency pins
  project/                 # Django project core
    settings.py            # Global settings (includes chatbot app)
    urls.py, asgi.py, wsgi.py
  chatbot/                 # Our chatbot app
    apps.py                # Registers app with Django
    management/
      commands/
        chat_cli.py        # Main terminal chatbot command
  logs/
    session.log            # Conversation logs
```

### Why these files exist

- **manage.py** – launches Django commands, including our `chat_cli`.
- **project/** – standard Django project config (settings, URL routing, etc.).
- **chatbot/** – app holding our chatbot logic.
  - **apps.py** – tells Django this is a valid app.
  - **management/commands/chat\_cli.py** – where the CLI chatbot lives. Django auto-discovers management commands in this folder.
- **logs/** – persistent log file of all conversations.

## How to run

1. Create and activate a virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
   ```
3. Run database migrations:
   ```bash
   python manage.py migrate
   ```
4. Launch the chatbot:
   ```bash
   python manage.py chat_cli
   ```

Example session:

```
user: Hello
bot: Hello. How can I help you today? (78 ms)
user: What are you?
bot: I am a simple terminal chatbot built with Django and ChatterBot. (65 ms)
user: bye
bot: Goodbye. Talk to you later. (40 ms)
```

Commands:

- `:help` – show help
- `:quit` – exit the chatbot

## Requirements

```
Django==4.2.14
chatterbot2==1.1.0a7
chatterbot-corpus==1.2.0
SQLAlchemy>=1.3,<1.4
python-dateutil==2.8.2
mathparse==0.1.2
pint==0.17
nltk==3.8.1
spacy<3.8
```

If you get NLTK lookup errors, run:

```bash
python -c "import nltk; nltk.download('punkt'); nltk.download('wordnet')"
```

## Explanation of main code (chat\_cli.py)

- **Logging setup**: logs go to `logs/session.log`; third-party libraries (chatterbot, spacy, sqlalchemy) are silenced to keep the terminal clean.

- ``\*\* function\*\*:

  - Creates a ChatterBot instance backed by SQLite.
  - Configures a BestMatch adapter with a default response.
  - Attempts to train on a small English corpus.
  - Adds a few deterministic pairs like "Hello" and "bye" for predictable output.

- **REPL loop (**``**)**:

  - Reads user input, exits gracefully on `:quit` or Ctrl+C.
  - Measures response time in milliseconds.
  - Calls `bot.get_response(user_text)` to generate a reply.
  - Prints a clean `bot:` line to the terminal.
  - Logs user and bot messages to `session.log`.

## Why this design

- **Django management command**: integrates with the framework and can later be extended into a web UI.
- **Logging separation**: clean console for user, detailed logs for debugging.
- **Small deterministic training set**: ensures predictable grading output.
- **Pinned dependencies**: avoids common breakages with ChatterBot on Python 3.11.

## Troubleshooting

- `No module named 'django'` → install Django inside the venv.
- `No module named 'spacy'` → install spaCy and the `en_core_web_sm` model.
- SQLAlchemy version errors → reinstall with `pip install "SQLAlchemy>=1.3,<1.4"`.
- NLTK errors → run the two `nltk.download` commands above.

