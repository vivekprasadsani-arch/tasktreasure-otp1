# Render Deployment Fix Guide

## 🚨 Bot Not Responding on Render - Solutions

### Issue: Bot deployed but not responding to /start command

---

## 🔧 Quick Fix Steps:

### 1️⃣ **Update Admin User ID**
Run this SQL in Supabase SQL Editor:
```sql
UPDATE admin_settings 
SET setting_value = '7325836764' 
WHERE setting_key = 'admin_user_id';
```

### 2️⃣ **Test with Simplified Bot**
Temporarily change `render.yaml` startCommand to:
```yaml
startCommand: python simple_telegram_bot.py
```

### 3️⃣ **Check Environment Variables**
In Render Dashboard > Environment, ensure these are set:
```
BOT_TOKEN=8354306480:AAGmQbuElJ3iZV4iHiMPHvLpSo7UxrStbY0
PORT=10000
SUPABASE_URL=https://wddcrtrgirhcemmobgcc.supabase.co
SUPABASE_KEY=eyJhbGci...
```

### 4️⃣ **Database Tables Check**
Ensure these SQL scripts are run in Supabase:
- `setup_database.sql` ✅
- `user_sessions_table.sql` ✅  
- `otp_history_table.sql` ⚠️ (Run this)
- `update_admin_user.sql` ⚠️ (Run this)

---

## 🔍 Debugging Steps:

### Check Render Logs:
1. Go to Render Dashboard
2. Click your service
3. Go to "Logs" tab
4. Look for these errors:
   - `BOT_TOKEN` missing
   - `Supabase` connection failed
   - `Port binding` issues
   - `Import` errors

### Common Error Messages & Solutions:

**Error:** `BOT_TOKEN not found`
**Fix:** Add `BOT_TOKEN` in Render Environment Variables

**Error:** `Port binding failed`
**Fix:** Health server should bind port immediately

**Error:** `Supabase table not found`
**Fix:** Run missing SQL scripts

**Error:** `Module import failed`
**Fix:** Check `requirements.txt` has all dependencies

---

## 🧪 Testing Strategy:

### Step 1: Test Simplified Bot
Use `simple_telegram_bot.py`:
- ✅ Minimal dependencies
- ✅ Basic /start command
- ✅ Echo functionality
- ✅ Health server

### Step 2: Test Complete Bot
Use `run_complete_bot.py`:
- ✅ Full OTP monitoring
- ✅ Number management
- ✅ Database integration
- ✅ Admin features

---

## 📋 Deployment Checklist:

### ✅ Files Ready:
- [x] GitHub repository updated
- [x] `render.yaml` configured
- [x] `simple_telegram_bot.py` (for debugging)
- [x] `requirements.txt` updated
- [x] `Aptfile` has chromium packages
- [x] `runtime.txt` specifies Python version

### ⚠️ Render Settings:
- [ ] Environment variables set
- [ ] Service type: Web
- [ ] Build command includes Playwright
- [ ] Start command correct

### ⚠️ Database Setup:
- [ ] `admin_settings` table created
- [ ] `otp_history` table created  
- [ ] Admin user ID updated to `7325836764`
- [ ] All tables have data

---

## 🎯 Recommended Action Plan:

### Phase 1: Basic Bot (Quick Test)
1. Change `render.yaml` to use `simple_telegram_bot.py`
2. Deploy and test /start command
3. If working, proceed to Phase 2

### Phase 2: Database Setup
1. Run `otp_history_table.sql` in Supabase
2. Run `update_admin_user.sql` in Supabase
3. Verify all tables exist

### Phase 3: Full Bot Deployment
1. Change back to `run_complete_bot.py`
2. Test all features
3. Verify admin commands work

---

## 🔧 Emergency Fixes:

### If Bot Still Not Responding:
1. Check Render logs for specific errors
2. Test bot token with simple curl:
   ```bash
   curl "https://api.telegram.org/bot<TOKEN>/getMe"
   ```
3. Verify webhook is not set:
   ```bash
   curl "https://api.telegram.org/bot<TOKEN>/deleteWebhook"
   ```

### If Database Errors:
1. Check Supabase URL and key
2. Verify all tables exist
3. Check table permissions

### If Import Errors:
1. Check `requirements.txt` syntax
2. Verify Python version compatibility
3. Check build logs for failed installs

---

**Next Steps:** 
1. Run `update_admin_user.sql` in Supabase
2. Test with `simple_telegram_bot.py` first
3. Check Render logs for specific errors
