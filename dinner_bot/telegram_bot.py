import time

from flask import Flask
from hashlib import md5
from time import sleep

import humanhash
from os.path import isfile

import telepot
from argparse import ArgumentParser

from bot_frontend import BotFrontend
from core_bot import CoreBot


class TelegramDinnerBot(BotFrontend):
    @staticmethod
    def register_args(parser: ArgumentParser):
        parser.add_argument('--telegram-token-file')
        parser.add_argument('--telegram-cache')

    def __init__(self, args, core_bot: CoreBot):
        super().__init__(core_bot)
        if not args.telegram_token_file:
            raise NotImplementedError
        with open(args.telegram_token_file) as f:
            token = f.read().strip()
        self.cache_file = args.telegram_cache or ('.lastmsg.' + args.telegram_token_file)
        self.last_msg = 0
        if isfile(self.cache_file):
            with open(self.cache_file) as f:
                self.last_msg = int(f.read())
        self.bot = telepot.Bot(token)

    def save_last_msg(self, last_msg: int):
        self.last_msg = last_msg
        with open(self.cache_file, 'w') as f:
            f.write(str(self.last_msg))

    def run(self):
        while True:
            for data in self.bot.getUpdates(offset=self.last_msg + 1):
                msg = data['message']
                chat_id = msg['chat']['id']
                seconds_delta = time.time() - msg['date']
                user_id = str(msg['from']['id'])
                gen_name = ' '.join(humanhash.humanize(md5(user_id.encode()).hexdigest(), words=2, separator=' '))
                from_name = msg['from'].get('first_name', msg['from'].get('username', gen_name))

                def send_reply(msg, chat_id=chat_id, from_name=from_name):
                    self.bot.sendMessage(chat_id, '@{} {}'.format(from_name, msg))

                if seconds_delta > 60:
                    self.save_last_msg(data['update_id'])
                    print('Skipping old message:', msg['text'])
                    continue

                self.give_message(msg['text'], user_id, from_name, send_reply)

                self.save_last_msg(data['update_id'])
            sleep(1)
