from aiogram import Router, F, Bot
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from states import CourseRegistration
from keyboards import get_contact_keyboard, get_yes_no_keyboard
from config import ADMIN_ID

router = Router()

@router.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext):
    await message.answer(
        "Assalomu alaykum! 'Kontent Formula' kursiga ro'yxatdan o'tish uchun ism va familiyangizni kiriting:",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(CourseRegistration.waiting_for_name)

@router.message(CourseRegistration.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer(
        "Rahmat! Endi telefon raqamingizni yozib qoldiring yoki pastdagi tugma orqali kontaktingizni ulashing:",
        reply_markup=get_contact_keyboard()
    )
    await state.set_state(CourseRegistration.waiting_for_phone)

@router.message(CourseRegistration.waiting_for_phone, F.contact)
async def process_phone_contact(message: Message, state: FSMContext):
    await state.update_data(phone=message.contact.phone_number)
    await ask_payment_intent(message, state)

@router.message(CourseRegistration.waiting_for_phone, F.text)
async def process_phone_text(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await ask_payment_intent(message, state)

async def ask_payment_intent(message: Message, state: FSMContext):
    await message.answer(
        "Kursni 10 baravar arzonga xarid qilish uchun to'lov qiling!",
        reply_markup=get_yes_no_keyboard()
    )
    await state.set_state(CourseRegistration.waiting_for_payment_intent)

@router.message(CourseRegistration.waiting_for_payment_intent)
async def process_payment_intent(message: Message, state: FSMContext):
    if message.text == "To'lov qilaman":
        await state.update_data(payment_intent="Ha")
        
        card_info = (
            "To'lov qiladigan karta raqami:\n\n"
            "💳 <code>5614 6835 1146 7011</code>\n"
            "👤 Xamrayev Dilshodjon\n\n"
            "🔸 Minimal summa: 100.000 so'm\n"
            "🔹 Maksimal summa: 490.000 so'm\n\n"
            "To'lov qilgandan keyin chekni (rasm yoki skrinshot) tasdiqlash uchun menejerimizga ( <b>@mobilograf_menejer</b> ) yuboring. \n\nRahmat sizga tez orada bog'lanamiz."
        )
        await message.answer(card_info, reply_markup=ReplyKeyboardRemove(), parse_mode="HTML")
        
        # User details can be logged here if needed later (e.g. to a DB)
        await state.clear()
    elif message.text == "To'lov qilmayman":
        # User hasn't paid
        await message.answer("Rahmat, sizga tez orada bog'lanamiz", reply_markup=ReplyKeyboardRemove())
        await state.clear()
    else:
        # Invalid input
        await message.answer("Iltimos, quyidagi tugmalardan birini tanlang.", reply_markup=get_yes_no_keyboard())

@router.message()
async def unknown_message(message: Message):
    await message.answer("Kechirasiz, men sizni tushunmadim. Yangidan boshlash uchun /start buyrug'ini yuboring.")
