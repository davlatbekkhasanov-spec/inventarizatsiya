# Mesta Nazorat Bot

Mesta qo'yuvchi xodimlarning ish jarayonini kuzatish va Kaizen normasi (1 pozitsiya = 3 daqiqa) bo'yicha nazorat.

## Texnologiyalar

- Python 3.12
- Aiogram 3
- PostgreSQL + SQLAlchemy (async) + Alembic
- Railway deploy
- Yordamchi hub + Kaizen integratsiyasi

## Lokal ishga tushirish

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# .env ni to'ldiring
alembic upgrade head
python -m bot.main
```

## Jarayon (tugmalar)

| Tugma | Vazifa |
|-------|--------|
| ▶️ Boshlash | Ishni boshlash, vaqt hisobi yoqiladi |
| ⏸ Pauza | Vaqt to'xtaydi |
| ▶️ Davom etish | Pauzadan keyin davom |
| 🏁 Yakunlash | Nechta pozitsiya qilganingizni so'raydi |

Yakunlashda bot normaga tushganingizni yoki bekor sarflangan vaqtni hisoblab beradi.

## Buyruqlar

| Buyruq | Kim | Vazifa |
|--------|-----|--------|
| `/start_mesta` | Xodim | Ishni boshlash |
| `/pause_mesta` | Xodim | Pauza |
| `/resume_mesta` | Xodim | Davom etish |
| `/finish_mesta` | Xodim | Yakunlash |
| `/active_mesta` | Hammaga | Aktiv xodimlar |
| `/stat_today` | Admin | Bugungi statistika |
| `/stat_week` | Admin | 7 kun |
| `/stat_month` | Admin | 30 kun |

## Norma

```
expected = floor(ish_vaqti_daqiqa / MINUTES_PER_POSITION)
bekor_vaqt = max(0, ish_vaqti - pozitsiya × MINUTES_PER_POSITION)
```

Default: `MINUTES_PER_POSITION=3`

Pauza vaqti ish vaqtiga kirmaydi.

## Railway

1. **PostgreSQL** plugin (volume bilan)
2. Bot servisida `DATABASE_URL` = `${{Postgres.DATABASE_URL}}`
3. Env:
   - `BOT_TOKEN`
   - `GROUP_CHAT_ID`
   - `ADMIN_IDS=1432810519`
   - `MINUTES_PER_POSITION=3`
   - `YORDAMCHI_HUB_URL` / `YORDAMCHI_HUB_SECRET` (yordamchi bot bilan bir xil)
4. Service type: **Worker** (polling)
5. Migration bot ishga tushganda avtomatik (`alembic upgrade head`)

Ma'lumotlar PostgreSQL da saqlanadi — deployda yo'qolmaydi.
