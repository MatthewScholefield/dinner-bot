import requests
from signal import SIGINT
from time import sleep

from argparse import ArgumentParser
from flask import Flask, request
from subprocess import Popen, PIPE
from threading import Thread

from dinner_bot.bot_frontend import BotFrontend


class GroupmeBot(BotFrontend):
    POST_URL = 'https://api.groupme.com/v3/bots/post'
    supports_indentation = False

    @staticmethod
    def register_args(parser: ArgumentParser):
        parser.add_argument('--groupme-bot-id-file')

    def __init__(self, args, core_bot):
        super().__init__(core_bot)
        if not args.groupme_bot_id_file:
            raise NotImplementedError
        with open(args.groupme_bot_id_file) as f:
            self.bot_id = f.read().strip()
        self.app = Flask(__name__)
        self.app.add_url_rule('/groupmeMessage', 'get_message', self.get_message, methods=['POST'])
        self.lt_process = None  # type: Popen
        self.port = 18712
        self.subdomain = 'mds-groupme-dinner-bot-1'
        self.callback_url = 'https://{}.localtunnel.me/groupmeMessage'.format(self.subdomain)

    def get_message(self):
        data = request.json
        if data['sender_type'] == 'bot':
            return '{}'

        def reply(msg, data=data):
            tag = '@{}'.format(data['name'])
            text = '{}  {}'.format(tag, msg)
            data = {
                'attachments': [{
                    'loci': [[0, len(tag)]],
                    'type': 'mentions',
                    'user_ids': [int(data['user_id'])]
                }],
                'text': text,
                'bot_id': self.bot_id
            }
            r = requests.post(self.POST_URL, data=data)
            if not r.ok:
                print('Request failed with code {}: {}'.format(r.status_code, r.text))

        self.give_message(data['text'], data['sender_id'], data['name'], reply)
        return '{}'

    def create_local_tunnel(self):
        sleep(2)
        self.lt_process = Popen(['lt', '--port', str(self.port), '--subdomain', self.subdomain], stdout=PIPE)
        print('Callback is live at:', self.callback_url)

    def run(self):
        Thread(target=self.create_local_tunnel, daemon=True).start()
        try:
            self.app.run('localhost', self.port, debug=False)
        finally:
            self.shutdown()

    def shutdown(self):
        if self.lt_process:
            self.lt_process.send_signal(SIGINT)
            self.lt_process = None
