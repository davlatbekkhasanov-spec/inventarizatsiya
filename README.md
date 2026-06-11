# Mesta Nazorat Bot

Mesta qo'yuvchi xodimlarning ish jarayonini real vaqtda kuzatish va Kaizen normasi (1 pozitsiya = 4 daqiqa) bo'yicha nazorat qilish.

## Texnologiyalar

- Python 3.12
- Aiogram 3
- PostgreSQL + SQLAlchemy (async) + Alembic
- Railway deploy

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

## Buyruqlar

| Buyruq | Kim | Vazifa |
|--------|-----|--------|
| `/start_mesta` | Xodim | Ishni boshlash |
| `/add 10` | Xodim | Pozitsiya qo'shish |
| `+10 pozitsiya` | Xodim | Tugma / inline |
| `/finish_mesta` | Xodim | Yakunlash + hisobot |
| `/active_mesta` | Hammaga | Aktiv xodimlar |
| `/stat_today` | Admin | Bugungi statistika |
| `/stat_week` | Admin | 7 kun |
| `/stat_month` | Admin | 30 kun |

## Norma

```
expected = floor(o'tgan_daqiqa / MINUTES_PER_POSITION)
```

Default: `MINUTES_PER_POSITION=4`

Har 15 daqiqada fon nazorati — normadan ortda qolgan aktiv xodimlar uchun guruhga ogohlantirish.

## Railway

1. **PostgreSQL** plugin qo'shing
2. Bot servisida **Reference variable**:
   - `DATABASE_URL` = `${{Postgres.DATABASE_URL}}`
3. Env:
   - `BOT_TOKEN`
   - `GROUP_CHAT_ID` — monitoring guruhi
   - `ADMIN_IDS=1432810519`
   - `MINUTES_PER_POSITION=4`
4. Service type: **Worker** (polling)
5. Migration bot ishga tushganda avtomatik (`alembic upgrade head`)

## Struktura

```
bot/
  handlers/      — Telegram buyruqlar
  services/      — biznes logika, monitor, statistika
  database/      — modellar, session, migration
  middlewares/   — DB session
  keyboards/     — tugmalar
  utils/         — vaqt, norma
```

## Repo

https://github.com/davlatbekkhasanov-spec/mesta-nazorat-bot
