#!/usr/bin/env python

import logging
import argparse
from bot_runner import BotRunner

from telebot import TeleBot


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="bot.py",
        description="alfredo telegram bot"
    )

    parser.add_argument(
        "-l",
        "--log-level",
        default=logging.INFO,
        type=lambda x: getattr(logging, x.upper()),
        help="Configure the logging level.",
    )

    parser.add_argument(
        "-c",
        "--config",
        default="config.json",
        help="Path to config file",
    )

    parser.add_argument(
        "-d",
        "--database",
        default="alfredo.sqlite",
        help="Path to sqlite database"
    )

    parser.add_argument(
        "-t",
        "--tmpdir",
        default="/tmp/",
        help="Temporary dir for ephemeral files"
    )

    args = parser.parse_args()

    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=args.log_level
    )
    logger = logging.getLogger(__name__)

    # disable logging for urllib3, which would spam the log when using log level DEBUG
    logging.getLogger("urllib3").propagate = False

    runner = BotRunner(args.config, TeleBot, args.database, args.tmpdir)
    runner.run()
