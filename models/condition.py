'''Location of the class describing the user state'''

from aiogram.dispatcher.filters.state import State, StatesGroup

class Condition(StatesGroup):
    '''Describes the stage of the conversation with the bot that the user is in'''
    Request = State()
    