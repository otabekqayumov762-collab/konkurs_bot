from aiogram.fsm.state import State, StatesGroup

class CourseRegistration(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_payment_intent = State()
    waiting_for_receipt = State()

class Broadcast(StatesGroup):
    waiting_for_message = State()
