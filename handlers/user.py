from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from states import CourseRegistration, AdminPanel
from keyboards import get_contact_keyboard, get_yes_no_keyboard
from config import ADMIN_IDS
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


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    current = await state.get_state()
    # Admin panelda bo'lsa /start ga to'sqinlik qilmasin
    if current in (AdminPanel.in_panel, AdminPanel.waiting_for_broadcast):
        return
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
    await state.update_data(phone=message.text.strip())
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
            payment_intent="Yo'q",
            receipt_sent=False
        )
        await message.answer("Rahmat, sizga tez orada bog'lanamiz! 😊", reply_markup=ReplyKeyboardRemove())
        for admin_id in ADMIN_IDS:
            try:
                await message.bot.send_message(
                    admin_id,
                    f"🔔 Yangi ro'yxatdan o'tish (to'lov yo'q):\n"
                    f"👤 {data.get('name')}\n"
                    f"📞 {data.get('phone')}\n"
                    f"🆔 {message.from_user.id} | @{message.from_user.username or '-'}"
                )
            except Exception:
                pass
        await state.clear()

    else:
        await message.answer("Iltimos, quyidagi tugmalardan birini tanlang.", reply_markup=get_yes_no_keyboard())


@router.message(CourseRegistration.waiting_for_receipt, F.photo | F.document)
async def process_receipt(message: Message, state: FSMContext):
    file_id = message.photo[-1].file_id if message.photo else message.document.file_id
    data = await state.get_data()

    await save_registration(
        user_id=message.from_user.id,
        username=message.from_user.username,
        full_name=data.get("name", ""),
        phone=data.get("phone", ""),
        payment_intent="Ha",
        receipt_sent=True
    )
    await message.answer(
        "✅ Chekingiz qabul qilindi! Menejerimiz tez orada siz bilan bog'lanadi. Rahmat!",
        reply_markup=ReplyKeyboardRemove()
    )
    caption = (
        f"💳 YANGI TO'LOV + CHEK:\n"
        f"👤 {data.get('name')}\n"
        f"📞 {data.get('phone')}\n"
        f"🆔 {message.from_user.id} | @{message.from_user.username or '-'}"
    )
    for admin_id in ADMIN_IDS:
        try:
            if message.photo:
                await message.bot.send_photo(admin_id, file_id, caption=caption)
            else:
                await message.bot.send_document(admin_id, file_id, caption=caption)
        except Exception:
            pass
    await state.clear()


@router.message(CourseRegistration.waiting_for_receipt)
async def receipt_wrong_format(message: Message):
    await message.answer("Iltimos, chek rasmini (foto yoki fayl) yuboring:")


@router.message(F.text, ~F.text.startswith("/"))
async def unknown_message(message: Message, state: FSMContext):
    from config import ADMIN_IDS
    # Admin tugmalari admin handler da qayta ishlanadi
    if message.from_user.id in ADMIN_IDS:
        return
    current = await state.get_state()
    if current is None:
        await message.answer("Boshlash uchun /start buyrug'ini yuboring.")
