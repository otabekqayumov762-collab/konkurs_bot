"""
users_data.xlsx dagi eski userlarni PostgreSQL ga ko'chirish
"""
import asyncio
import asyncpg
import openpyxl
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

STATUS_MAP = {
    "To'lov qilinmagan": ("Yo'q", False),
    "Bekor qilingan":    ("Yo'q", False),
    "Kutilyapti":        ("Ha",   False),   # to'lagan lekin chek kutilmoqda
    "To'langan":         ("Ha",   True),
}

async def migrate():
    conn = await asyncpg.connect(DATABASE_URL)

    # Jadval borligiga ishonch
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS registrations (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            username TEXT,
            full_name TEXT,
            phone TEXT,
            payment_intent TEXT,
            receipt_sent BOOLEAN DEFAULT FALSE,
            registered_at TIMESTAMP DEFAULT NOW()
        )
    """)

    wb = openpyxl.load_workbook("users_data.xlsx")
    ws = wb.active

    inserted = 0
    skipped = 0
    for row in ws.iter_rows(min_row=2, values_only=True):
        full_name, phone, status_raw, _, user_id = row
        if not user_id:
            continue

        # Allaqachon bor ekanmi?
        exists = await conn.fetchval(
            "SELECT 1 FROM registrations WHERE user_id=$1 AND full_name=$2",
            int(user_id), str(full_name)
        )
        if exists:
            skipped += 1
            continue

        payment_intent, receipt_sent = STATUS_MAP.get(
            str(status_raw).strip(), ("Yo'q", False)
        )
        await conn.execute("""
            INSERT INTO registrations (user_id, username, full_name, phone, payment_intent, receipt_sent)
            VALUES ($1, $2, $3, $4, $5, $6)
        """, int(user_id), None, str(full_name), str(phone), payment_intent, receipt_sent)
        inserted += 1
        print(f"  ✅ {full_name} | {phone} | {payment_intent}")

    await conn.close()
    print(f"\nMigration tugadi: {inserted} ta qo'shildi, {skipped} ta o'tkazib yuborildi.")

asyncio.run(migrate())
