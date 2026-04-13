import io
import openpyxl
from aiogram import Router, F
from aiogram.types import Message, BufferedInputFile, ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from states import AdminPanel
from keyboards import get_admin_keyboard
from config import ADMIN_IDS
from utils.database import get_all_registrations, get_all_user_ids

router = Router()

ADMIN_BUTTONS = {
    "📊 Statistika",
    "👥 Foydalanuvchilar",
    "📥 Excel yuklab olish",
    "📢 Hammaga xabar",
    "🚪 Chiqish",
}


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


# --- Kirish ---
@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.set_state(AdminPanel.in_panel)
    await message.answer("🛠 Admin panelga xush kelibsiz!", reply_markup=get_admin_keyboard())


# --- Admin tugmalari: state yo'q bo'lsa ham ishlaydi ---
@router.message(F.text.in_(ADMIN_BUTTONS))
async def admin_buttons_handler(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    current = await state.get_state()
    # Broadcast kutayotgan bo'lsa tugmalarni ignore qilmasin
    if current == AdminPanel.waiting_for_broadcast:
        await broadcast_send(message, state)
        return

    # State yo'q bo'lsa ham (restart dan keyin) ishlaydi
    if current not in (AdminPanel.in_panel, None):
        return

    await state.set_state(AdminPanel.in_panel)
    text = message.text

    if text == "📊 Statistika":
        await show_stats(message)
    elif text == "👥 Foydalanuvchilar":
        await show_users(message)
    elif text == "📥 Excel yuklab olish":
        await send_excel(message)
    elif text == "📢 Hammaga xabar":
        await state.set_state(AdminPanel.waiting_for_broadcast)
        await message.answer(
            "Yubormoqchi bo'lgan xabarni yozing.\n/cancel — bekor qilish.",
            reply_markup=ReplyKeyboardRemove()
        )
    elif text == "🚪 Chiqish":
        await state.clear()
        await message.answer("Chiqildi.", reply_markup=ReplyKeyboardRemove())


# --- Statistika ---
async def show_stats(message: Message):
    rows = await get_all_registrations()
    total = len(rows)
    paid_receipt = sum(1 for r in rows if r["receipt_sent"])
    paid_no_receipt = sum(1 for r in rows if r["payment_intent"] == "Ha" and not r["receipt_sent"])
    not_paid = sum(1 for r in rows if r["payment_intent"] == "Yo'q")
    await message.answer(
        f"📊 <b>Statistika</b>\n\n"
        f"👥 Jami: <b>{total}</b>\n"
        f"✅ Chek yubordi: <b>{paid_receipt}</b>\n"
        f"⏳ To'layman dedi, chek yo'q: <b>{paid_no_receipt}</b>\n"
        f"❌ To'lamagan: <b>{not_paid}</b>",
        parse_mode="HTML",
        reply_markup=get_admin_keyboard()
    )


# --- Foydalanuvchilar ---
async def show_users(message: Message):
    rows = await get_all_registrations()
    if not rows:
        await message.answer("Hali hech kim ro'yxatdan o'tmagan.", reply_markup=get_admin_keyboard())
        return
    lines = []
    for r in rows[:10]:
        if r["receipt_sent"]:
            status = "✅"
        elif r["payment_intent"] == "Ha":
            status = "⏳"
        else:
            status = "❌"
        lines.append(
            f"{status} <b>{r['full_name']}</b> | {r['phone']}\n"
            f"   @{r['username'] or '-'} | {r['registered_at'].strftime('%d.%m %H:%M')}"
        )
    await message.answer("\n\n".join(lines), parse_mode="HTML", reply_markup=get_admin_keyboard())


# --- Excel ---
async def send_excel(message: Message):
    rows = await get_all_registrations()
    if not rows:
        await message.answer("Ma'lumot yo'q.", reply_markup=get_admin_keyboard())
        return

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Ro'yxat"
    for col, width in zip("ABCDEF", [5, 25, 18, 18, 22, 20]):
        ws.column_dimensions[col].width = width
    ws.append(["#", "Ism-Familiya", "Telefon", "Username", "To'lov holati", "Sana"])

    for i, r in enumerate(rows, 1):
        if r["receipt_sent"]:
            status = "Chek yubordi"
        elif r["payment_intent"] == "Ha":
            status = "Tolayman dedi"
        else:
            status = "Tolamagan"
        ws.append([
            i, r["full_name"], r["phone"],
            f"@{r['username']}" if r["username"] else "-",
            status,
            r["registered_at"].strftime("%d.%m.%Y %H:%M")
        ])

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    await message.answer_document(
        BufferedInputFile(buf.read(), filename="konkurs_royxat.xlsx"),
        caption=f"📊 Jami: <b>{len(rows)}</b> ta",
        parse_mode="HTML",
        reply_markup=get_admin_keyboard()
    )


# --- Broadcast ---
@router.message(AdminPanel.waiting_for_broadcast, Command("cancel"))
async def broadcast_cancel(message: Message, state: FSMContext):
    await state.set_state(AdminPanel.in_panel)
    await message.answer("Bekor qilindi.", reply_markup=get_admin_keyboard())


async def broadcast_send(message: Message, state: FSMContext):
    user_ids = await get_all_user_ids()
    sent, failed = 0, 0
    for uid in user_ids:
        try:
            await message.copy_to(uid)
            sent += 1
        except Exception:
            failed += 1
    await state.set_state(AdminPanel.in_panel)
    await message.answer(
        f"✅ Yuborildi: {sent}\n❌ Xato: {failed}",
        reply_markup=get_admin_keyboard()
    )
