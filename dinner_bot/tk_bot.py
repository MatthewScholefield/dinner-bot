from argparse import ArgumentParser

from bot_frontend import BotFrontend

from tkinter import *


class ScrollTxtArea:
    def __init__(self, root):
        frame = Frame(root)
        frame.grid(row=1, column=0, columnspan=3, pady=10)
        # add a frame and put a text area into it
        textPad = Frame(frame)
        self.text = Text(textPad, height=5, width=40)

        # add a vertical scroll bar to the text area
        scroll = Scrollbar(textPad)
        self.text.configure(yscrollcommand=scroll.set)

        # pack everything
        self.text.pack(side=LEFT)
        scroll.pack(side=RIGHT, fill=Y)
        textPad.pack(side=TOP)


class TkBot(BotFrontend):
    cur_user = 1

    def register_args(parser: ArgumentParser):
        parser.add_argument('--tk', action='store_true')

    def __init__(self, args, core_bot):
        super().__init__(core_bot)
        self.user_id = self.cur_user
        self.cur_user += 1

        if not args.tk:
            raise NotImplementedError

        self.top = tk = Tk()
        l1 = Label(tk, text="Enter Query")
        l1.grid(row=0, column=0)
        self.entry = Entry(tk, bd=5)
        self.entry.grid(row=0, column=1)
        self.entry.bind('<Return>', self.submit)

        but = Button(tk, text="Submit", width=10, command=self.submit)
        but.grid(row=0, column=2)
        self.buffer_lines = []
        self.scroll = ScrollTxtArea(tk)
        self.scroll.text.delete(1.0, END)

    def submit(self, event=None):
        def reply(x):
            self.buffer_lines.append(x)
            self.scroll.text.delete(1.0, END)
            self.scroll.text.insert(END, '\n'.join(self.buffer_lines))
        inp = self.entry.get()
        reply('> ' + inp)
        user_id = 'console_user_{}'.format(self.user_id)
        self.give_message(inp, user_id, user_id, reply)
        self.entry.delete(0, END)

    def run(self):
        self.top.mainloop()
