# 🔐 Admin Approval System - TaskTreasure OTP Bot

এই আপডেটে TaskTreasure OTP Bot এ একটি সম্পূর্ণ Admin Approval System যুক্ত করা হয়েছে।

## 🎯 মূল বৈশিষ্ট্য

### ✅ User Access Control
- **নতুন ইউজারদের admin approval প্রয়োজন**
- ইউজার bot start করলে admin notification পাবে
- Admin approve/reject করতে পারবে
- ইউজার notification পাবে approval/rejection এর

### ⏰ 3-Hour Cooldown System
- ইউজার একবার request পাঠানোর পর **৩ ঘন্টা** wait করতে হবে
- ৩ ঘন্টার মধ্যে আবার request পাঠাতে পারবে না
- ৩ ঘন্টা পর আবার request করতে পারবে

### 👨‍💼 Admin Commands
```bash
/approve <user_id>           # ইউজার approve করুন
/reject <user_id> [reason]   # ইউজার reject করুন (কারণ optional)
/adduser <user_id>           # সরাসরি ইউজার add করুন
/removeuser <user_id>        # ইউজার access remove করুন
/pending                     # pending requests দেখুন
/stats                       # bot statistics
/broadcast <message>         # সবাইকে message পাঠান
```

## 🔧 Setup Instructions

### 1. Database Setup
Supabase SQL Editor এ run করুন:
```sql
-- user_approval_system.sql file এর content run করুন
```

### 2. Updated Files
- `telegram_number_bot.py` - Main bot with approval system
- `user_approval_system.sql` - Database schema

### 3. Environment Variables
```bash
BOT_TOKEN=your_bot_token_here
PORT=10000
```

## 📱 User Experience

### নতুন ইউজার Flow:
1. ইউজার `/start` করে
2. Access request message দেখে
3. Admin কে notification যায়
4. Admin approve/reject করে
5. ইউজার notification পায়
6. Approved হলে normal bot access পায়

### Admin Notification:
```
🔔 New Access Request

👤 User Info:
• Name: John Doe
• Username: @johndoe
• User ID: 123456789
• Requested: 2024-01-15 14:30:25

🎯 Action Required:
[✅ Approve] [❌ Reject]
```

### User Approval Message:
```
✅ Access Approved!

🎉 Congratulations! Your access to TaskTreasure OTP Bot has been approved.

🚀 You can now:
• Get phone numbers from multiple countries
• Receive OTP codes instantly
• Manage your number assignments

💡 Get Started:
Type /start to begin using the bot!
```

### User Rejection Message:
```
❌ Access Rejected

Sorry, your access request has been rejected.
📝 Reason: Spam account

⏰ Next Steps:
• You can request access again after 3 hours
• Contact @tasktreasur_support if you have questions
```

## 🛡️ Security Features

### Access Control:
- ✅ Admin-only commands protected
- ✅ User approval required for bot access
- ✅ 3-hour cooldown prevents spam
- ✅ Detailed logging and tracking

### Database Security:
- ✅ Unique user_id constraint
- ✅ Automatic timestamp updates
- ✅ Status tracking (pending/approved/rejected)
- ✅ Admin action logging

## 📊 Admin Dashboard

### Pending Requests View:
```
📋 Pending Access Requests:

1. John Doe (@johndoe)
   ID: 123456789
   Requested: 01-15 14:30

2. Jane Smith (@janesmith)
   ID: 987654321
   Requested: 01-15 15:45

💡 Commands:
• /approve <user_id> - Approve user
• /reject <user_id> [reason] - Reject user
```

## 🔄 Migration Guide

### From Previous Version:
1. Existing approved users automatically get access
2. Admin ID remains same from database
3. All existing features work unchanged
4. New users need approval from now on

### Database Migration:
```sql
-- Run user_approval_system.sql to create new tables
-- Existing users will need to request access or admin can add them manually
```

## 🚨 Important Notes

⚠️ **Admin Setup Required:**
- Admin user ID must be set in database
- Admin gets all approval notifications
- Only admin can approve/reject users

⚠️ **Cooldown System:**
- 3-hour cooldown is strict
- Prevents spam requests
- Users notified about cooldown

⚠️ **Backward Compatibility:**
- All existing bot features work
- Only access control is added
- Approved users get normal experience

## 🔧 Troubleshooting

### Common Issues:

1. **Admin not receiving notifications:**
   - Check admin_user_id in database
   - Verify bot token permissions

2. **User can't request access:**
   - Check 3-hour cooldown
   - Verify database connection

3. **Approval buttons not working:**
   - Check admin permissions
   - Verify callback query handling

### Support:
📞 Contact: @tasktreasur_support

---
**Powered by TaskTreasure OTP System** 🚀
