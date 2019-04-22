from time import sleep

from argparse import ArgumentParser
from threading import Thread

from dinner_bot.bot_frontend import BotFrontend


class ScrollTxtArea:
    def __init__(self, root):
        import tkinter as tk
        frame = tk.Frame(root)
        frame.grid(row=1, column=0, columnspan=3, pady=10)
        # add a frame and put a text area into it
        padding = tk.Frame(frame)
        self.text = tk.Text(padding, height=10, width=80)

        # add a vertical scroll bar to the text area
        scroll = tk.Scrollbar(padding)
        self.text.configure(yscrollcommand=scroll.set)

        # pack everything
        self.text.pack(side=tk.LEFT)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        padding.pack(side=tk.TOP)


class TkDinnerBotWindow:
    def __init__(self, root, user_id, give_message):
        import tkinter as tk
        self.tk = tk
        self.root = root
        root.winfo_toplevel().title("Dinner Bot {}".format(user_id))
        self.user_id = user_id
        self.root = root
        l1 = tk.Label(root, text="Enter Query", width=20)
        l1.grid(row=0, column=0)
        self.entry = tk.Entry(root, bd=2, width=40)
        self.entry.grid(row=0, column=1)
        self.entry.bind('<Return>', self.submit)

        but = tk.Button(root, text="Submit", width=20, command=self.submit)
        but.grid(row=0, column=2)
        self.buffer_lines = []
        self.scroll = ScrollTxtArea(root)
        self.scroll.text.delete(1.0, tk.END)
        self.give_message = give_message

    def is_open(self):
        try:
            return self.root.state() == 'normal'
        except self.tk.TclError:
            return False

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


class TkBot(BotFrontend):
    @staticmethod
    def register_args(parser: ArgumentParser):
        parser.add_argument('--tk-windows', type=int, default=0)

    def __init__(self, args, core_bot):
        super().__init__(core_bot)
        if not args.tk_windows:
            raise NotImplementedError

        import tkinter as tk
        self.root = tk.Tk()
        self.root.withdraw()
        self.windows = []
        for i in range(1, args.tk_windows + 1):
            self.windows.append(TkDinnerBotWindow(tk.Toplevel(self.root), i, self.give_message))

    def monitor(self):
        while True:
            sleep(0.5)
            if not any(i.is_open() for i in self.windows):
                self.root.destroy()

    def run(self):
        Thread(target=self.monitor, daemon=True).start()
        self.root.mainloop()
