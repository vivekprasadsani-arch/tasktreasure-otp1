# Admin Approval System - TaskTreasure OTP Bot

## Overview
The TaskTreasure OTP Bot now includes a comprehensive admin approval system that requires users to get approval before accessing bot features.

## Features

### 🔐 Access Control
- **Admin Approval Required**: Users must be approved by admin to use the bot
- **3-Hour Cooldown**: Users can only request access once every 3 hours
- **Automatic Notifications**: Admin gets notified of new requests, users get notified of approval/rejection

### 🎛️ Admin Commands

#### User Management
- `/approve <user_id> [notes]` - Approve a pending access request
- `/reject <user_id> [reason]` - Reject a pending access request
- `/pending` - View all pending access requests
- `/adduser <user_id> [username] [first_name]` - Manually add approved user
- `/removeuser <user_id>` - Remove user access and revoke permissions

#### Statistics & Monitoring
- `/stats` - View bot statistics including approval metrics
- `/broadcast <message>` - Broadcast message to all approved users

### 📊 Database Schema

#### New Tables Added:
1. **`user_access_requests`** - Stores access requests with status tracking
2. **`approved_users`** - Manages approved users list
3. **`access_request_cooldown`** - Enforces 3-hour request cooldown

## User Flow

### 1. Initial Access Request
```
User sends /start → Request created → Admin notified → User waits for response
```

### 2. Admin Response
```
Admin approves/rejects → User notified → Access granted/denied
```

### 3. Cooldown System
```
Request sent → 3-hour cooldown activated → Auto-expires → Can request again
```

## Admin Setup

### 1. Database Setup
Run the SQL script in `admin_approval_schema.sql` in your Supabase dashboard:

```sql
-- Creates all necessary tables for admin approval system
-- Run this in Supabase SQL Editor
```

### 2. Admin Configuration
The admin user ID is set in the `admin_settings` table:
```sql
INSERT INTO admin_settings (setting_key, setting_value) 
VALUES ('admin_user_id', 'YOUR_ADMIN_USER_ID');
```

## Security Features

- **Duplicate Prevention**: Users cannot submit multiple pending requests
- **Cooldown Enforcement**: 3-hour minimum between requests
- **Session Management**: Approved status is checked for all bot interactions
- **Automatic Cleanup**: Expired sessions and old requests are managed
- **Admin-only Commands**: All management commands require admin privileges

## Example Usage

### Admin Workflow:
1. Receive notification: "🔔 New Access Request from User: John (ID: 123456789)"
2. Review request: `/pending` to see all pending requests
3. Make decision: `/approve 123456789 Welcome to the bot!` or `/reject 123456789 Invalid request`
4. User gets automatic notification of approval/rejection

### User Experience:
1. User starts bot: `/start`
2. If not approved: Gets access request form
3. Submits request: Auto-notification sent to admin
4. Waits for approval: Cannot use bot features until approved
5. Gets notified: Receives approval/rejection message
6. Access granted: Can use all bot features if approved

## Monitoring & Analytics

The admin stats command now shows:
- ✅ Total approved users
- ⏳ Pending requests count  
- ❌ Rejected requests count
- 📊 Historical approval metrics

This ensures complete visibility into the user approval process and system usage.
