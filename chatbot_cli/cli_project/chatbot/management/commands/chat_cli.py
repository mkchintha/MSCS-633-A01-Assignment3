from __future__ import annotations

import logging
import sys
import time
from pathlib import Path
from typing import NoReturn

from django.core.management.base import BaseCommand, CommandError

# Attempt to import ChatterBot and trainers. If unavailable, raise an error
try:
    from chatterbot import ChatBot
    from chatterbot.trainers import ChatterBotCorpusTrainer, ListTrainer
except Exception as exc:
    # Raise a Django CommandError with clear installation instructions
    raise CommandError(
        "ChatterBot is not available. Install it in your venv:\n"
        "  pip install chatterbot2==1.1.0a7 chatterbot-corpus==1.2.0"
    ) from exc


# Create a logs directory (if not already present) to store session logs
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Configure logging: only file logging, no console output
logging.basicConfig(
    level=logging.INFO,  # Capture INFO level and above
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[logging.FileHandler(LOGS_DIR / "session.log", encoding="utf-8")],
)

# Silence noisy third-party libraries to keep logs clean and focused on chatbot
for name in (
    "chatterbot",
    "chatterbot.response_selection",
    "sqlalchemy",
    "spacy",
):
    logging.getLogger(name).setLevel(logging.WARNING)
    logging.getLogger(name).propagate = False


def build_bot() -> ChatBot:
    """
    Build and configure the chatbot instance.

    - Uses SQLite database for persistence.
    - Trains using both corpus data and a custom list of Q&A pairs.
    - Adds logic adapter with fallback response.
    """
    bot = ChatBot(
        "TerminalBot",
        storage_adapter="chatterbot.storage.SQLStorageAdapter",  # Store conversations in SQLite
        database_uri="sqlite:///db.sqlite3",
        logic_adapters=[
            {
                "import_path": "chatterbot.logic.BestMatch",  # Match best possible response
                "default_response": "I’m not fully sure about that. Could you rephrase?",
                "maximum_similarity_threshold": 0.65,  # Avoid very loose matches
            }
        ],
        read_only=False,  # Allow learning (database persistence)
    )

    # Train chatbot with predefined corpus datasets
    try:
        corpus_trainer = ChatterBotCorpusTrainer(bot)
        corpus_trainer.train(
            "chatterbot.corpus.english.greetings",
            "chatterbot.corpus.english.conversations",
        )
    except Exception as exc:
        # Skip training gracefully if corpus training fails
        logging.warning("Corpus training skipped due to: %s", exc)

    # Train chatbot with a few custom conversational pairs
    ListTrainer(bot).train(
        [
            "Hello",
            "Hello. How can I help you today?",
            "What are you?",
            "I am a simple terminal chatbot built with Django and ChatterBot.",
            "bye",
            "Goodbye. Talk to you later.",
        ]
    )
    return bot


# Welcome banner for the CLI
BANNER = (
    "\nDjango + ChatterBot CLI\n"
    "Type your message and press Enter.\n"
    "Commands: :help  :quit\n"
)


class Command(BaseCommand):
    """
    Django custom management command that launches an interactive chatbot CLI.

    Usage:
        python manage.py <command_name>

    It provides a REPL loop where the user can chat with the bot.
    """

    help = "Interactive terminal chat client backed by ChatterBot"

    def handle(self, *args, **options) -> None:
        """
        Entry point when the command is executed.
        - Prints banner.
        - Builds chatbot.
        - Starts REPL loop.
        """
        self.stdout.write(BANNER)
        bot = build_bot()
        self._repl(bot)

    def _repl(self, bot: ChatBot) -> NoReturn:
        """
        Run an infinite Read-Eval-Print-Loop (REPL) for user interaction.

        - Reads input from user.
        - Handles special commands (:quit, :help).
        - Passes other inputs to the bot.
        - Logs interactions with timestamps and latency.
        """
        while True:
            try:
                user_text = input("user: ").strip()
            except KeyboardInterrupt:
                # Graceful exit on Ctrl+C
                print("\nbot: Interrupted by user. Goodbye.")
                raise SystemExit(130)

            if not user_text:
                continue  # Ignore empty input

            # Handle exit commands
            if user_text in {":quit", ":q", ":exit"}:
                print("bot: Goodbye.")
                raise SystemExit(0)

            # Handle help command
            if user_text in {":help", ":h"}:
                print("bot: Type to chat. Use :quit to exit.")
                continue

            # Process input with chatbot
            t0 = time.perf_counter()  # Start timer for performance measurement
            try:
                response = bot.get_response(user_text)
                dt_ms = (time.perf_counter() - t0) * 1000.0  # Response time in ms
                print(f"bot: {response}  ({dt_ms:.0f} ms)")
                # Log conversation
                logging.info("user=%s | bot=%s | ms=%.0f", user_text, str(response), dt_ms)
            except Exception as exc:
                # Catch unexpected chatbot errors
                logging.exception("Error generating response: %s", exc)
                print("bot: I hit an internal error. Please try again.")
