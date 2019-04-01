from abc import ABCMeta, abstractmethod
from argparse import ArgumentParser
from typing import Callable

from core_bot import CoreBot


class BotFrontend(metaclass=ABCMeta):
    supports_indentation = True
    @staticmethod
    @abstractmethod
    def register_args(parser: ArgumentParser):
        pass

    def __init__(self, core_bot: CoreBot):
        self.core_bot = core_bot

    def give_message(self, message: str, user_id: str, name, reply: Callable):
        self.core_bot.give_message(message, '{}:{}'.format(self.__class__.__name__, user_id), name, reply, self)

    @abstractmethod
    def run(self):
        pass

    def shutdown(self):
        pass


class DummyBot(BotFrontend):
    @staticmethod
    def register_args(parser: ArgumentParser):
        pass

    def run(self):
        pass
