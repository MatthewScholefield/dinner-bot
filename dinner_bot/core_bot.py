import time

import dateutil
from durations import Duration
from os.path import join, basename, isdir

from argparse import ArgumentParser
from glob import glob
try:
    from padatious import IntentContainer
except ImportError:
    from padaos import IntentContainer
from threading import Timer
from typing import Callable, Optional
from typing import List
from typing import TYPE_CHECKING


class DinnerUser:
    def __init__(self, name, reply: Callable, ready_time: int = None, user_id='', client=None):
        from bot_frontend import DummyBot
        self.name = name
        self.user_id = user_id
        self.reply = reply
        self.has_notified = False
        self.ready_time = ready_time or time.time()
        self.client = client or DummyBot()


def format_list(parts: list) -> str:
    return {
        0: lambda x: '',
        1: lambda x: x[0],
        2: lambda x: '{} and {}'.format(*x),
        3: lambda x: '{}, and {}'.format(', '.join(x[:-1]), x[-1])
    }[min(len(parts), 3)](parts)


def plural_format(string, num, plural_string=None):
    return (string if num == 1 else plural_string or string + 's').format(num)


def format_duration(seconds: float, num_components=1) -> str:
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    hours, minutes, seconds = map(int, [hours, minutes, seconds])
    elems = (
                    [plural_format('{} hour', hours)] * bool(hours) +
                    [plural_format('{} minute', minutes)] * bool(minutes) +
                    [plural_format('{} second', seconds)] * bool(seconds)
            )[:num_components]
    return format_list(elems)


def parse_time(s) -> float:
    if 'am' not in s and 'pm' not in s:
        s = s.strip() + ' pm'
    return dateutil.parser.parse(s).timestamp()


class CoreBot:
    HELP_LINES = [
        'Commands:',
        '    Ready for dinner:',
        '        "I\'m ready for dinner"',
        '        "I\'m hungry"',
        '    Check if anyone else is ready:',
        '        "Who else is ready to eat"',
        '        "Is anyone else hungry"',
        '    Schedule when you will be ready:',
        '        "I will be ready to eat at 8:30"',
        '        "I will be hungry in 30 minutes"',
        '    Inform that you are eating:',
        '        "I\'m eating right now"',
        '        "My coordinates are (left, right, back)"',
        '    Inform that no one is still eating:',
        '        "We all left"',
        '        "Dinner is done"'
    ]

    UNKNOWN_STR = '\n'.join([
        'Not sure how to help with that. Ask me /help for a list of commands.'
    ])

    default_location = "(left, right, back)"

    @staticmethod
    def register_args(parser: ArgumentParser):
        parser.add_argument('--intents-folder', help='Location of installed intents', required=True)

    def __init__(self, args):
        self.dinner_start_time = None
        self.dinner_location = None
        self.eating_users = []  # type: List[DinnerUser]
        self.scheduled_users = []  # type: List[DinnerUser]
        self.dinner_notify_timers = []
        self.scheduled_timers = []

        self.container = IntentContainer('.intent-cache')
        self.load_intents(args.intents_folder)

    def load_intents(self, folder):
        if not isdir(folder):
            raise OSError('No such folder: {}'.format(folder))
        intent_files = glob(join(folder, '*.intent'))
        entity_files = glob(join(folder, '*.entity'))
        for intent_file in intent_files:
            name = basename(intent_file).replace('.intent', '')
            self.container.load_intent(name, intent_file)
        for entity_file in entity_files:
            name = basename(entity_file).replace('.entity', '')
            self.container.load_entity(name, entity_file)
        self.container.train(debug=True)

    def give_message(self, message, user_id, name, reply: Callable, client):
        print('Received message:', message)
        intent = self.container.calc_intent(message)
        print('Calculated intent:', intent)
        if intent.conf < 0.5:
            reply(self.UNKNOWN_STR)
        else:
            user = DinnerUser(name, reply, user_id=user_id, client=client)
            {
                'help': lambda *_: reply('\n'.join(i if client.supports_indentation else i.strip() for i in self.HELP_LINES)),
                'eating.now': self.inform_eating,
                'dinner.inform.ready': self.inform_ready,
                'dinner.inform.schedule': self.inform_schedule,
                'dinner.ask.ready': self.ask_ready,
                'dinner.done': self.dinner_done,
            }[intent.name](intent.matches, user)

    def min_till_dinner(self) -> Optional[int]:
        if self.dinner_start_time is None:
            return None
        dinner_delta = self.dinner_start_time - time.time()
        dinner_delta_min = int(dinner_delta / 60 + 0.5)
        return dinner_delta_min

    def name_list(self, exclude_user: DinnerUser = None, users=None) -> str:
        return format_list(
            [i.name for i in users or self.eating_users if not exclude_user or i.name != exclude_user.name])

    def get_scheduled_info(self, exclude_user: DinnerUser = None):
        info = format_list(['{} will be ready to eat in {}'.format(
            i.name, format_duration(i.ready_time - time.time(), 1)
        ) for i in self.scheduled_users if not exclude_user or i.user_id != exclude_user.user_id])
        return (info + '.') * bool(info)

    def remove_user(self, user):
        self.scheduled_users = [i for i in self.scheduled_users if i.user_id != user.user_id]
        self.eating_users = [i for i in self.eating_users if i.user_id != user.user_id]

    def raw_dinner_status(self, user: DinnerUser) -> str:
        if self.dinner_start_time is None:
            s = "Dinner hasn't been scheduled yet"
            if len(self.eating_users) == 1:
                if self.eating_users[0].user_id == user.user_id:
                    name = 'you are'
                else:
                    name = self.eating_users[0].name + ' is'
                s += ' but {} ready to eat'.format(name)
            s += '.'
            return s
        if time.time() < self.dinner_start_time:
            return 'Dinner is starting in {} with {}.'.format(
                format_duration(self.dinner_start_time - time.time()), self.name_list(user)
            )
        return "{} started eating dinner {} ago.".format(
            self.name_list(user), format_duration(time.time() - self.dinner_start_time)
        )

    def notify_when_time(self, user: DinnerUser):
        timer = Timer(self.dinner_start_time - time.time(), lambda: user.reply('Dinner has commenced {}.'.format(
            self.location_str()
        )))
        timer.start()
        self.dinner_notify_timers.append(timer)

    def location_str(self):
        return (
            "at the assumed location of {}".format(self.default_location)
            if not self.dinner_location else
            "at the location of {}".format(self.dinner_location)
        )

    def fix_location(self, matches: dict):
        if 'location' in matches:
            matches['location'] = '({})'.format(matches['location'])

    def inform_eating(self, matches: dict, user: DinnerUser):
        self.fix_location(matches)
        self.remove_user(user)
        self.eating_users.append(user)
        if not self.dinner_start_time:
            user.reply("You are the only one. I'll let you know if anyone joins you.")
            self.dinner_start_time = time.time()
            self.dinner_location = matches.get('location')
        elif time.time() < self.dinner_start_time:  # Before dinner
            self.dinner_start_time = time.time()
            self.dinner_location = matches.get('location')
            for i in self.dinner_notify_timers:
                i.cancel()
            for i in self.eating_users:
                if i.user_id != user.user_id:
                    i.reply('{} just mentioned they are already eating {}. Dinner has commenced.'.format(
                        user.name, self.location_str()
                    ))
            user.reply("OK, I've started dinner {}. {} will be joining.".format(
                self.location_str(), self.name_list(user)
            ))
        else:  # After dinner
            custom_others = self.dinner_location is not None
            custom_self = 'location' in matches
            if custom_others:
                custom_self = False
            for i in self.eating_users:
                if i.user_id != user.user_id:
                    s = '{} is also already eating.'.format(self.name_list(i))
                    if custom_self:
                        s += ' They are at {}.'.format(matches['location'])
                    if custom_others:
                        s += 'I\'ve told them where you are.'
                    i.reply(s)

            if not custom_self and not custom_others and time.time() - self.dinner_start_time < 10 * 60:
                loc_str = ' ' + self.location_str()
            else:
                loc_str = (' ' + self.dinner_location) if self.dinner_location else ''
            s = "OK, {} began eating dinner {} ago{}.".format(
                self.name_list(user), format_duration(time.time() - self.dinner_start_time),
                loc_str
            )
            if custom_self:
                s += " I've let them know where you are."
            user.reply(s)

    def inform_ready(self, _: dict, user: DinnerUser):
        self.remove_user(user)
        if self.dinner_start_time is None:
            if len(self.eating_users) == 0:
                if len(self.scheduled_users) > 0:
                    user.reply(
                        self.get_scheduled_info() + " I'll let you know if anyone else gets hungry before then.")
                else:
                    user.reply("You are the only one ready so far. I'll let you know when anyone else gets hungry")
                self.eating_users.append(user)
            else:
                self.eating_users.append(user)
                self.dinner_start_time = time.time() + 10 * 60
                for i in self.eating_users:
                    i.reply('Dinner will commence in {} with {}'.format(
                        format_duration(self.dinner_start_time - time.time()), self.name_list(i)
                    ))
                    self.notify_when_time(i)
        elif time.time() < self.dinner_start_time:  # Before dinner
            user.reply(self.raw_dinner_status(user) + ' ' + self.get_scheduled_info())
            for i in self.eating_users:
                i.reply('{} will be joining you.'.format(user.name))
            self.eating_users.append(user)
        else:  # After dinner began
            user.reply(
                self.raw_dinner_status(user) +
                " I've notified them that you'll be joining. " +
                self.get_scheduled_info()
            )
            for i in self.eating_users:
                i.reply('{} will be joining you.'.format(user.name))
            self.eating_users.append(user)

    def inform_schedule(self, matches: dict, user: DinnerUser):
        self.remove_user(user)
        if 'duration' in matches:
            user.ready_time = time.time() + Duration(matches['duration']).to_seconds()
        else:
            user.ready_time = parse_time(matches['time'])
        self.scheduled_users.append(user)
        def on_schedule():
            self.scheduled_users.remove(user)
            self.remove_user(user)
            self.inform_ready({}, user)

        t = Timer(user.ready_time - time.time(), on_schedule)
        t.daemon = True
        t.start()
        self.scheduled_timers.append(t)
        user.reply("I've marked that you won't be ready for another {}. {}".format(
            format_duration(user.ready_time - time.time() + 1, 1),
            self.get_scheduled_info(user) + ' ' + self.raw_dinner_status(user)
        ))

    def ask_ready(self, _: dict, user):
        user.reply(self.raw_dinner_status(user) + ' ' + self.get_scheduled_info())

    def dinner_done(self, _, user):
        self.dinner_start_time = None
        self.dinner_location = None
        for i in self.dinner_notify_timers:
            i.cancel()
        self.dinner_notify_timers = []
        self.eating_users = []
        for i in self.scheduled_timers:
            i.cancel()
        self.scheduled_users = []
        user.reply('Okay, I\'ve marked dinner as completed')
