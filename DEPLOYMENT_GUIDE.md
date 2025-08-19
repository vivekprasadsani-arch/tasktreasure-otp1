# 🚀 OTP Telegram Bot - Deployment Guide

## 📁 GitHub এ Upload করার ফাইল:

### ✅ **আবশ্যক ফাইল (এইগুলো অবশ্যই upload করতে হবে):**
1. `otp_telegram_bot.py` - মূল বট কোড
2. `run_bot.py` - বট রানার স্ক্রিপ্ট  
3. `requirements.txt` - Python dependencies
4. `render.yaml` - Render deploy কনফিগ
5. `runtime.txt` - Python version specification
6. `Aptfile` - Chromium browser installation for Render
7. `README.md` - প্রোজেক্ট ডকুমেন্টেশন
8. `.gitignore` - Git ignore rules

### ❌ **Upload করবেন না:**
- `chromedriver.exe` (শুধু লোকাল ডেভেলপমেন্টের জন্য)
- কোন `.png` ফাইল
- `__pycache__/` ফোল্ডার
- কোন `.log` ফাইল
- টেস্ট ফাইল

## 🔧 **GitHub Setup:**

### Step 1: GitHub Repository তৈরি করুন
1. https://github.com এ যান
2. "New repository" ক্লিক করুন
3. Repository name: `otp-telegram-bot`
4. Description: `Telegram OTP Bot with global country support`
5. Public/Private যেটা চান সেট করুন
6. "Create repository" ক্লিক করুন

### Step 2: Local Git Setup
```bash
# Terminal/CMD এ প্রোজেক্ট ফোল্ডারে গিয়ে রান করুন:
git init
git add .
git commit -m "Initial commit: OTP Telegram Bot"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/otp-telegram-bot.git
git push -u origin main
```

## 🌐 **Render Deployment:**

### Step 1: Render Account
1. https://render.com এ যান
2. GitHub দিয়ে signup/login করুন

### Step 2: New Web Service
1. Dashboard এ "New +" ক্লিক করুন
2. "Web Service" সিলেক্ট করুন
3. আপনার GitHub repository connect করুন
4. Repository: `otp-telegram-bot` সিলেক্ট করুন

### Step 3: Configuration
- **Name:** `otp-telegram-bot`
- **Environment:** `Python`
- **Region:** `Oregon (US West)`
- **Branch:** `main`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `python run_bot.py`

### Step 4: Environment Variables (প্রয়োজন নেই)
বট কোডে সব credentials hardcoded আছে, তাই কোন environment variables সেট করার দরকার নেই।

### Step 5: Deploy
1. "Create Web Service" ক্লিক করুন
2. Deployment শুরু হবে (৫-১০ মিনিট সময় লাগতে পারে)
3. Build logs দেখুন

## 🔍 **Deployment যাচাই:**

### সফল Deployment এর লক্ষণ:
- ✅ Build সফল হবে
- ✅ Container চালু হবে
- ✅ Health check pass হবে
- ✅ Log এ "Login successful" দেখাবে

### সমস্যা হলে:
1. Render logs চেক করুন
2. Build errors দেখুন
3. Browser developer tools দিয়ে debug করুন

## 📱 **পোস্ট-Deployment:**

### যা হবে:
1. 🤖 বট অটো চালু হবে
2. 🔐 Website এ অটো লগইন হবে
3. 📱 নতুন OTP টেলিগ্রামে পাঠাবে
4. 🔄 24/7 চলতে থাকবে

### Monitor করুন:
- Render dashboard এ logs দেখুন
- Telegram channel এ OTP আসছে কিনা চেক করুন
- Health status monitor করুন

## 🆘 **Troubleshooting:**

### সাধারণ সমস্যা:
1. **Chrome/ChromeDriver error:** Dockerfile এ সব setup আছে
2. **Telegram API error:** Token এবং Channel ID চেক করুন  
3. **Website login error:** Website down হতে পারে
4. **Memory/CPU limit:** Free tier এর limitation

### Support:
- GitHub Issues: Repository তে issue তৈরি করুন
- Render Support: Render dashboard থেকে support ticket

## 🎉 **সফল Deployment!**

Deployment সফল হলে আপনার বট 24/7 চলবে এবং নতুন OTP সব টেলিগ্রামে পাঠাবে!
