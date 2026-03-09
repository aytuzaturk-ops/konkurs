# Railway PostgreSQL Setup Instructions

## 1. PostgreSQL Database yaratish

1. Railway dashboard ga kiring
2. **New** → **Database** → **PostgreSQL** tanlang
3. Database yaratiladi va sizga connection ma'lumotlari beriladi

## 2. Bot Service uchun Environment Variables

Bot servisingizda quyidagi environment variables ni sozlang:

```env
BOT_TOKEN=your_telegram_bot_token_here
ADMIN_IDS=123456789,987654321
DATABASE_URL=${{Postgres.DATABASE_URL}}
```

**Muhim:**
- `DATABASE_URL` ni Railway PostgreSQL servisidan reference qiling
- Railway da bu `${{Postgres.DATABASE_URL}}` ko'rinishida bo'ladi
- Postgres service nomi sizda boshqacha bo'lishi mumkin (masalan: `PostgreSQL`, `Database`, va hokazo)

## 3. Web Ilova Service uchun Environment Variables

Web ilova servisingizda ham xuddi shunday qilib qo'shing:

```env
DATABASE_URL=${{Postgres.DATABASE_URL}}
```

Ikkala servis ham bir xil PostgreSQL database ga ulanadi.

## 4. Connection String formati

Railway avtomatik connection string beradi, lekin qo'lda yozish kerak bo'lsa:

```
postgresql://username:password@hostname:port/database_name
```

Misol:
```
postgresql://postgres:mypassword@containers-us-west-123.railway.app:5432/railway
```

## 5. Deploy qilish

1. Yangilangan kodlarni GitHub repository ga push qiling
2. Railway avtomatik rebuild va deploy qiladi
3. Bot va Web ilova ishga tushadi

## 6. Database Migration

Birinchi marta ishga tushganda, bot avtomatik ravishda barcha table larni yaratadi (`init_db()` funksiyasi orqali).

Agar eski SQLite ma'lumotlaringiz bor bo'lsa va ularni ko'chirish kerak bo'lsa, alohida migration script yozish kerak.

## 7. Tekshirish

Bot ishga tushgandan keyin:
1. Railway Logs ni tekshiring (xatolar yo'qligiga ishonch hosil qiling)
2. Telegram bot ga `/start` yuboring
3. Database ga ma'lumot yozilishini tekshiring

## Muammolar va Yechimlar

### Connection Error
Agar `connection refused` xatosi chiqsa:
- DATABASE_URL to'g'ri reference qilinganligini tekshiring
- PostgreSQL service ishga tushganligini tekshiring

### Module Not Found
Agar `ModuleNotFoundError: No module named 'asyncpg'` chiqsa:
- `requirements.txt` fayli to'g'ri yuklanganligini tekshiring
- Railway rebuild qiling

### Table Not Found
Agar table topilmasa:
- Bot birinchi ishga tushganda `init_db()` chaqirilganligini tekshiring
- Logs da initialization xatolarini qidiring
