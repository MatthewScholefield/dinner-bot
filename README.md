# Dinner Bot

*A multi-faceted dinner scheduling chat bot for groups of college students*

Organizing a time to eat every nighht normally involves either a non-trivial
amount of planning or a high chance of a suboptimal schedule where people eat
at different times. This bot aims to solve this problem. With a multi-faced
interaction model, users can chat with dinner-bot through both telegram
and groupme. By leveraging this centralized and direct communication mode,
users are faced with less unnecessary notifications and in turn a higher
engagement rate.

**Example interaction:**
```
> /help
Commands:
    Ready for dinner:
        "I'm ready for dinner"
        "I'm hungry"
    Check if anyone else is ready:
        "Who else is ready to eat"
        "Is anyone else hungry"
    Schedule when you will be ready:
        "I will be ready to eat at 8:30"
        "I will be hungry in 30 minutes"
    Inform that you are eating:
        "I'm eating right now"
        "My coordinates are (left, right, back)"
    Inform that no one is still eating:
        "We all left"
        "Dinner is done"
> Status
Dinner hasn't been scheduled yet but George is ready to eat. Sam will be ready to eat in 30 minutes.
> I'm hungry
Dinner will commence in 10 minutes with George.
```

## Setup

Run the following in a Linux or a Linux-like environment:
```
./setup.sh
```
If running on something else, you will need to [create a virtualenv](https://packaging.python.org/guides/installing-using-pip-and-virtualenv/#installing-packages-using-pip-and-virtualenv)
and install this repo inside it using `pip install -e /path/to/git/clone`.
Then, instead of `./start.sh` use `dinner-bot` inside the virtualenv.

## Usage

Run the bot with the `./start.sh` script. You can pass arguments to it as described by the help section:

```
./start.sh --help
```

For example, to start up a debug instance of dinner-bot for testing you might do:

```
./start.sh --intents-folder intents/ --tk-windows 2
```

Which will tell the bot to use the default intents folder and create two
GUI windows for interacting with the dinner bot.
