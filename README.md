# 🏆 Konkurs Bot

Telegram platformasida konkurs o'tkazish uchun bot.

## 📋 Xususiyatlar

### Foydalanuvchi qismi:
- Majburiy kanallarga obuna tekshiruvi
- Unikal ID va referal havola berish  
- Har bir referal uchun +1 ball
- Shaxsiy statistika va do'stlar ro'yxati

### Admin qismi:
- Kanallar qo'shish/o'chirish
- Barcha ishtirokchilarni ko'rish (reyting bo'yicha)
- ID bo'yicha qidirish va ballarni tahrirlash
- Matn/rasm/video xabar yuborish (rassilka)
- Konkursni boshlash/to'xtatish
- G'oliblarni barcha foydalanuvchilarga e'lon qilish
- Bazani nollash (yangi konkurs uchun)

## 🚀 O'rnatish

### 1. Talablarni o'rnatish
```bash
pip install -r requirements.txt
```

### 2. Konfiguratsiya
`.env.example` faylini `.env` nomi bilan ko'chiring:
```bash
cp .env.example .env
```

`.env` faylini tahrirlang:
```
BOT_TOKEN=your_bot_token
ADMIN_IDS=your_telegram_id
```

### 3. Botni ishga tushirish
```bash
python bot.py
```

## 🔑 Bot Token olish
1. [@BotFather](https://t.me/BotFather) ga boring
2. `/newbot` buyrug'ini yuboring
3. Nom va username bering
4. Token nusxalang → `.env` ga qo'ying

## 👤 Admin ID olish
[@userinfobot](https://t.me/userinfobot) ga `/start` yuboring — ID raqamingizni ko'rsatadi.

## 📁 Fayl strukturasi
```
contest_bot/
├── bot.py           # Asosiy fayl
├── config.py        # Konfiguratsiya
├── database.py      # Ma'lumotlar bazasi
├── requirements.txt
├── .env.example
└── handlers/
    ├── user.py      # Foydalanuvchi handlerlari
    └── admin.py     # Admin handlerlari
```

## 🎮 Foydalanish

### Foydalanuvchi:
1. `/start` → Kanallarga obuna → "✅ A'zo bo'ldim" → ID va referal link olish
2. Havola do'stlarga yuboring → +1 ball har yangi a'zo uchun

### Admin:
1. `/admin` → Admin panel ochiladi
2. Avval kanallar qo'shing
3. Konkursni boshlang
4. Tugaganda g'oliblarni e'lon qiling
5. Yangi konkurs uchun "Reset" qiling
