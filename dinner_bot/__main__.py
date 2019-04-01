from builtins import NotImplementedError

from argparse import ArgumentParser
from threading import Thread, Event

from dinner_bot.core_bot import CoreBot
from dinner_bot.telegram_bot import TelegramDinnerBot
from dinner_bot.groupme_bot import GroupmeBot
from dinner_bot.tk_bot import TkBot

bot_classes = [
    TelegramDinnerBot,
    GroupmeBot,
    TkBot
]

bot_instances = []


def run_bot(cls, args, core_bot):
    try:
        instance = cls(args, core_bot)
        bot_instances.append(instance)
        instance.run()
    except NotImplementedError:
        pass


def main():
    parser = ArgumentParser()
    CoreBot.register_args(parser)
    for i in bot_classes:
        i.register_args(parser)
    args = parser.parse_args()

    core_bot = CoreBot(args)
    for bot_cls in bot_classes:
        Thread(target=run_bot, args=[bot_cls, args, core_bot], daemon=True).start()
    Event().wait()
    for i in bot_instances:
        i.shutdown()


if __name__ == '__main__':
    main()
