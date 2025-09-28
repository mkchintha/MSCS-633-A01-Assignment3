from __future__ import annotations

import logging
import sys
import time
from pathlib import Path
from typing import NoReturn

from django.core.management.base import BaseCommand, CommandError

try:
    from chatterbot import ChatBot
    from chatterbot.trainers import ChatterBotCorpusTrainer, ListTrainer
except Exception as exc:
    raise CommandError(
        "ChatterBot is not available. Install it in your venv:\n"
        "  pip install chatterbot2==1.1.0a7 chatterbot-corpus==1.2.0"
    ) from exc


LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# ✅ Option A: only file logging (no StreamHandler to console)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[logging.FileHandler(LOGS_DIR / "session.log", encoding="utf-8")],
)

# Silence noisy third-party libraries so only your bot messages remain visible
for name in (
    "chatterbot",
    "chatterbot.response_selection",
    "sqlalchemy",
    "spacy",
):
    logging.getLogger(name).setLevel(logging.WARNING)
    logging.getLogger(name).propagate = False


def build_bot() -> ChatBot:
    bot = ChatBot(
        "TerminalBot",
        storage_adapter="chatterbot.storage.SQLStorageAdapter",
        database_uri="sqlite:///db.sqlite3",
        logic_adapters=[
            {
                "import_path": "chatterbot.logic.BestMatch",
                "default_response": "I’m not fully sure about that. Could you rephrase?",
                "maximum_similarity_threshold": 0.65,
            }
        ],
        read_only=False,
    )

    try:
        corpus_trainer = ChatterBotCorpusTrainer(bot)
        corpus_trainer.train(
            "chatterbot.corpus.english.greetings",
            "chatterbot.corpus.english.conversations",
        )
    except Exception as exc:
        logging.warning("Corpus training skipped due to: %s", exc)

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


BANNER = (
    "\nDjango + ChatterBot CLI\n"
    "Type your message and press Enter.\n"
    "Commands: :help  :quit\n"
)


class Command(BaseCommand):
    help = "Interactive terminal chat client backed by ChatterBot"

    def handle(self, *args, **options) -> None:
        self.stdout.write(BANNER)
        bot = build_bot()
        self._repl(bot)

    def _repl(self, bot: ChatBot) -> NoReturn:
        while True:
            try:
                user_text = input("user: ").strip()
            except KeyboardInterrupt:
                print("\nbot: Interrupted by user. Goodbye.")
                raise SystemExit(130)

            if not user_text:
                continue
            if user_text in {":quit", ":q", ":exit"}:
                print("bot: Goodbye.")
                raise SystemExit(0)
            if user_text in {":help", ":h"}:
                print("bot: Type to chat. Use :quit to exit.")
                continue

            t0 = time.perf_counter()
            try:
                response = bot.get_response(user_text)
                dt_ms = (time.perf_counter() - t0) * 1000.0
                print(f"bot: {response}  ({dt_ms:.0f} ms)")
                logging.info("user=%s | bot=%s | ms=%.0f", user_text, str(response), dt_ms)
            except Exception as exc:
                logging.exception("Error generating response: %s", exc)
                print("bot: I hit an internal error. Please try again.")
