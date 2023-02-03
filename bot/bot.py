#!/usr/bin/env python

import logging
import json
from os import path
from sys import exit

import telebot
from telebot import types

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

config = None
bot = None


def load_config():
    if not path.exists("config.json"):
        logger.error("config.json does not exist")
        exit(1)

    with open("config.json") as c:
        cfg = json.load(c)

    for req in ["token", "group", "admins"]:
        if req not in cfg.keys():
            logger.error(f"config key {req} not found in config.json")
            exit(1)

    if not len(cfg["admins"]) > 0:
        logger.error("need at least one admin")
        exit(1)

    return cfg


if __name__ == "__main__":
    config = load_config()
    bot = telebot.TeleBot(config["token"])

    bot.infinity_polling()
