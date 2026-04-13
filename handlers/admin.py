import io
import openpyxl
from aiogram import Router, F
from aiogram.types import Message, BufferedInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from states import Broadcast
from config import ADMIN_IDS
from utils.database import get_all_registrations, get_all_user_ids

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


@router.message(Command("admin"))
async def admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        return
    rows = await get_all_registrations()
    total = len(rows)
    paid_with_receipt = sum(1 for r in rows if r["receipt_sent"])
    paid_no_receipt = sum(1 for r in rows if r["payment_intent"] == "Ha" and not r["receipt_sent"])
    not_paid = sum(1 for r in rows if r["payment_intent"] == "Yo'q")

    text = (
        f"🛠 <b>Admin panel</b>\n\n"
        f"👥 Jami ro'yxatdan o'tganlar: <b>{total}</b>\n"
        f"✅ Chek yuborgan (to'lagan): <b>{paid_with_receipt}</b>\n"
        f"⏳ To'layman dedi, chek yo'q: <b>{paid_no_receipt}</b>\n"
        f"❌ To'lamagan: <b>{not_paid}</b>\n\n"
        f"Buyruqlar:\n"
        f"/excel — Excel fayl yuklash\n"
        f"/broadcast — Hammaga xabar yuborish\n"
        f"/users — So'nggi 10 ta foydalanuvchi"
    )
    await message.answer(text, parse_mode="HTML")


@router.message(Command("users"))
async def show_users(message: Message):
    if not is_admin(message.from_user.id):
        return
    rows = await get_all_registrations()
    if not rows:
        await message.answer("Hali hech kim ro'yxatdan o'tmagan.")
        return
    lines = []
    for r in rows[:10]:
        chek = "✅ chek bor" if r["receipt_sent"] else ("⏳ chek yo'q" if r["payment_intent"] == "Ha" else "❌ to'lamagan")
        lines.append(
            f"👤 {r['full_name']} | 📞 {r['phone']} | {chek}\n"
            f"   @{r['username'] or '-'} | {r['registered_at'].strftime('%d.%m.%Y %H:%M')}"
        )
    await message.answer("\n\n".join(lines))


@router.message(Command("excel"))
async def send_excel(message: Message):
    if not is_admin(message.from_user.id):
        return
    rows = await get_all_registrations()
    if not rows:
        await message.answer("Ma'lumot yo'q.")
        return

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Ro'yxat"
    ws.append(["#", "Ism-Familiya", "Telefon", "Username", "To'lov", "Chek", "Sana"])
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
            r["payment_intent"],
            status,
            r["registered_at"].strftime("%d.%m.%Y %H:%M")
        ])

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    await message.answer_document(
        BufferedInputFile(buf.read(), filename="konkurs_royxat.xlsx"),
        caption=f"📊 Jami: {len(rows)} ta foydalanuvchi"
    )


@router.message(Command("broadcast"))
async def broadcast_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await message.answer("Hammaga yuboriladigan xabarni yozing (matn, rasm, video bo'lishi mumkin):")
    await state.set_state(Broadcast.waiting_for_message)


@router.message(Broadcast.waiting_for_message)
async def broadcast_send(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    user_ids = await get_all_user_ids()
    sent, failed = 0, 0
    for uid in user_ids:
        try:
            await message.copy_to(uid)
            sent += 1
        except Exception:
            failed += 1
    await message.answer(f"✅ Yuborildi: {sent}\n❌ Xato: {failed}")
    await state.clear()
