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


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


# --- Kirish ---
@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.set_state(AdminPanel.in_panel)
    await message.answer("🛠 Admin panelga xush kelibsiz!", reply_markup=get_admin_keyboard())


# --- Statistika ---
@router.message(AdminPanel.in_panel, F.text == "📊 Statistika")
async def show_stats(message: Message):
    rows = await get_all_registrations()
    total = len(rows)
    paid_receipt = sum(1 for r in rows if r["receipt_sent"])
    paid_no_receipt = sum(1 for r in rows if r["payment_intent"] == "Ha" and not r["receipt_sent"])
    not_paid = sum(1 for r in rows if r["payment_intent"] == "Yo'q")

    await message.answer(
        f"📊 <b>Statistika</b>\n\n"
        f"👥 Jami: <b>{total}</b>\n"
        f"✅ Chek yubordi (to'lagan): <b>{paid_receipt}</b>\n"
        f"⏳ To'layman dedi, chek yo'q: <b>{paid_no_receipt}</b>\n"
        f"❌ To'lamagan: <b>{not_paid}</b>",
        parse_mode="HTML"
    )


# --- So'nggi 10 foydalanuvchi ---
@router.message(AdminPanel.in_panel, F.text == "👥 Foydalanuvchilar")
async def show_users(message: Message):
    rows = await get_all_registrations()
    if not rows:
        await message.answer("Hali hech kim ro'yxatdan o'tmagan.")
        return
    lines = []
    for r in rows[:10]:
        if r["receipt_sent"]:
            status = "✅ chek bor"
        elif r["payment_intent"] == "Ha":
            status = "⏳ chek yo'q"
        else:
            status = "❌ to'lamagan"
        lines.append(
            f"👤 <b>{r['full_name']}</b> | 📞 {r['phone']}\n"
            f"   @{r['username'] or '-'} | {status} | {r['registered_at'].strftime('%d.%m %H:%M')}"
        )
    await message.answer("\n\n".join(lines), parse_mode="HTML")


# --- Excel ---
@router.message(AdminPanel.in_panel, F.text == "📥 Excel yuklab olish")
async def send_excel(message: Message):
    rows = await get_all_registrations()
    if not rows:
        await message.answer("Ma'lumot yo'q.")
        return

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Ro'yxat"
    ws.column_dimensions["A"].width = 5
    ws.column_dimensions["B"].width = 25
    ws.column_dimensions["C"].width = 18
    ws.column_dimensions["D"].width = 18
    ws.column_dimensions["E"].width = 22
    ws.column_dimensions["F"].width = 20

    ws.append(["#", "Ism-Familiya", "Telefon", "Username", "To'lov holati", "Sana"])
    for i, r in enumerate(rows, 1):
        if r["receipt_sent"]:
            status = "✅ Chek yubordi"
        elif r["payment_intent"] == "Ha":
            status = "⏳ To'layman dedi"
        else:
            status = "❌ To'lamagan"
        ws.append([
            i,
            r["full_name"],
            r["phone"],
            f"@{r['username']}" if r["username"] else "-",
            status,
            r["registered_at"].strftime("%d.%m.%Y %H:%M")
        ])

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    await message.answer_document(
        BufferedInputFile(buf.read(), filename="konkurs_royxat.xlsx"),
        caption=f"📊 Jami: <b>{len(rows)}</b> ta foydalanuvchi",
        parse_mode="HTML"
    )


# --- Broadcast boshlash ---
@router.message(AdminPanel.in_panel, F.text == "📢 Hammaga xabar")
async def broadcast_start(message: Message, state: FSMContext):
    await state.set_state(AdminPanel.waiting_for_broadcast)
    await message.answer(
        "Yubormoqchi bo'lgan xabarni yozing (matn, rasm, video — istalgan format).\n\n"
        "Bekor qilish uchun /cancel yuboring.",
        reply_markup=ReplyKeyboardRemove()
    )


@router.message(AdminPanel.waiting_for_broadcast, Command("cancel"))
async def broadcast_cancel(message: Message, state: FSMContext):
    await state.set_state(AdminPanel.in_panel)
    await message.answer("Bekor qilindi.", reply_markup=get_admin_keyboard())


@router.message(AdminPanel.waiting_for_broadcast)
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


# --- Chiqish ---
@router.message(AdminPanel.in_panel, F.text == "🚪 Chiqish")
async def admin_exit(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Admin paneldan chiqildi.", reply_markup=ReplyKeyboardRemove())
