from argparse import ArgumentParser

from dinner_bot.bot_frontend import BotFrontend


class ScrollTxtArea:
    def __init__(self, root):
        import tkinter as tk
        frame = tk.Frame(root)
        frame.grid(row=1, column=0, columnspan=3, pady=10)
        # add a frame and put a text area into it
        padding = tk.Frame(frame)
        self.text = tk.Text(padding, height=5, width=40)

        # add a vertical scroll bar to the text area
        scroll = tk.Scrollbar(padding)
        self.text.configure(yscrollcommand=scroll.set)

        # pack everything
        self.text.pack(side=tk.LEFT)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        padding.pack(sidetk=tk.TOP)


class TkBot(BotFrontend):
    cur_user = 1

    @staticmethod
    def register_args(parser: ArgumentParser):
        parser.add_argument('--tk', action='store_true')

    def __init__(self, args, core_bot):
        super().__init__(core_bot)
        if not args.tk:
            raise NotImplementedError

        import tkinter as tk
        self.user_id = self.cur_user
        self.cur_user += 1
        self.rt = rt = tk.Tk()
        l1 = tk.Label(rt, text="Enter Query")
        l1.grid(row=0, column=0)
        self.entry = tk.Entry(rt, bd=5)
        self.entry.grid(row=0, column=1)
        self.entry.bind('<Return>', self.submit)

        but = tk.Button(rt, text="Submit", width=10, command=self.submit)
        but.grid(row=0, column=2)
        self.buffer_lines = []
        self.scroll = ScrollTxtArea(rt)
        self.scroll.text.delete(1.0, tk.END)

    def submit(self, event=None):
        import tkinter as tk
        def reply(x):
            self.buffer_lines.append(x)
            self.scroll.text.delete(1.0, tk.END)
            self.scroll.text.insert(tk.END, '\n'.join(self.buffer_lines))

        inp = self.entry.get()
        reply('> ' + inp)
        user_id = 'console_user_{}'.format(self.user_id)
        self.give_message(inp, user_id, user_id, reply)
        self.entry.delete(0, tk.END)

    def run(self):
        self.rt.mainloop()
