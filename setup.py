from setuptools import setup

setup(
    name='dinner-bot',
    version='0.1.0',
    description='A multi-faced dinner scheduling chat bot for groups of college students ',
    author='Matthew Scholefield',
    author_email='matthew331199@gmail.com',
    url='https://github.com/matthewscholefield/dinner-bot',
    packages=[
        'dinner_bot'
    ],
    install_requires=[
        'requests',
        'telepot',
        'GroupyAPI',
        'padatious',
        'durations',
        'python-dateutil',
        'humanhash3',
        'flask',
        'Flask-RESTPlus'
    ]
)
