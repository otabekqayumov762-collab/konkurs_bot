from aiogram import Router, F, Bot
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from states import CourseRegistration
from keyboards import get_contact_keyboard, get_yes_no_keyboard
from config import ADMIN_ID
from utils.database import save_registration

router = Router()

CARD_INFO = (
    "To'lov qiladigan karta raqami:\n\n"
    "💳 <code>5614 6835 1146 7011</code>\n"
    "👤 Xamrayev Dilshodjon\n\n"
    "🔸 Minimal summa: 100.000 so'm\n"
    "🔹 Maksimal summa: 490.000 so'm\n\n"
    "To'lov qilgandan keyin <b>chek rasmini shu yerga yuboring</b>."
)


@router.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Assalomu alaykum! 'Kontent Formula' kursiga ro'yxatdan o'tish uchun ism va familiyangizni kiriting:",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(CourseRegistration.waiting_for_name)


@router.message(CourseRegistration.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    if not message.text or len(message.text.strip()) < 2:
        await message.answer("Iltimos, to'liq ism-familiyangizni kiriting:")
        return
    await state.update_data(name=message.text.strip())
    await message.answer(
        "Rahmat! Endi telefon raqamingizni yozib qoldiring yoki pastdagi tugma orqali kontaktingizni ulashing:",
        reply_markup=get_contact_keyboard()
    )
    await state.set_state(CourseRegistration.waiting_for_phone)


@router.message(CourseRegistration.waiting_for_phone, F.contact)
async def process_phone_contact(message: Message, state: FSMContext):
    phone = message.contact.phone_number
    if not phone.startswith("+"):
        phone = "+" + phone
    await state.update_data(phone=phone)
    await ask_payment_intent(message, state)


@router.message(CourseRegistration.waiting_for_phone, F.text)
async def process_phone_text(message: Message, state: FSMContext):
    phone = message.text.strip()
    await state.update_data(phone=phone)
    await ask_payment_intent(message, state)


async def ask_payment_intent(message: Message, state: FSMContext):
    await message.answer(
        "Kursni 10 baravar arzonga xarid qilish uchun to'lov qilasizmi?",
        reply_markup=get_yes_no_keyboard()
    )
    await state.set_state(CourseRegistration.waiting_for_payment_intent)


@router.message(CourseRegistration.waiting_for_payment_intent)
async def process_payment_intent(message: Message, state: FSMContext):
    if message.text == "To'lov qilaman":
        await state.update_data(payment_intent="Ha")
        await message.answer(CARD_INFO, reply_markup=ReplyKeyboardRemove(), parse_mode="HTML")
        await state.set_state(CourseRegistration.waiting_for_receipt)

    elif message.text == "To'lov qilmayman":
        data = await state.get_data()
        await save_registration(
            user_id=message.from_user.id,
            username=message.from_user.username,
            full_name=data.get("name", ""),
            phone=data.get("phone", ""),
            payment_intent="Yo'q"
        )
        await message.answer(
            "Rahmat, sizga tez orada bog'lanamiz! 😊",
            reply_markup=ReplyKeyboardRemove()
        )
        if ADMIN_ID:
            await message.bot.send_message(
                ADMIN_ID,
                f"🔔 Yangi ro'yxatdan o'tish:\n"
                f"👤 Ism: {data.get('name')}\n"
                f"📞 Tel: {data.get('phone')}\n"
                f"💰 To'lov: Yo'q\n"
                f"🆔 User ID: {message.from_user.id}\n"
                f"📱 Username: @{message.from_user.username or 'yo\'q'}"
            )
        await state.clear()

    else:
        await message.answer("Iltimos, quyidagi tugmalardan birini tanlang.", reply_markup=get_yes_no_keyboard())


@router.message(CourseRegistration.waiting_for_receipt, F.photo | F.document)
async def process_receipt(message: Message, state: FSMContext):
    if message.photo:
        file_id = message.photo[-1].file_id
    else:
        file_id = message.document.file_id

    data = await state.get_data()
    await save_registration(
        user_id=message.from_user.id,
        username=message.from_user.username,
        full_name=data.get("name", ""),
        phone=data.get("phone", ""),
        payment_intent="Ha",
        receipt_file_id=file_id
    )

    await message.answer(
        "✅ Chekingiz qabul qilindi! Menejerimiz tez orada siz bilan bog'lanadi. Rahmat!",
        reply_markup=ReplyKeyboardRemove()
    )

    if ADMIN_ID:
        caption = (
            f"💳 Yangi TO'LOV:\n"
            f"👤 Ism: {data.get('name')}\n"
            f"📞 Tel: {data.get('phone')}\n"
            f"🆔 User ID: {message.from_user.id}\n"
            f"📱 Username: @{message.from_user.username or 'yo\'q'}"
        )
        if message.photo:
            await message.bot.send_photo(ADMIN_ID, file_id, caption=caption)
        else:
            await message.bot.send_document(ADMIN_ID, file_id, caption=caption)

    await state.clear()


@router.message(CourseRegistration.waiting_for_receipt)
async def receipt_wrong_format(message: Message, state: FSMContext):
    await message.answer("Iltimos, chek rasmini (foto yoki fayl) yuboring:")


@router.message()
async def unknown_message(message: Message):
    await message.answer("Kechirasiz, men sizni tushunmadim. Yangidan boshlash uchun /start buyrug'ini yuboring.")
