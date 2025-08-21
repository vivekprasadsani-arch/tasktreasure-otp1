# OTP Telegram Bot

A Python bot that monitors a website for incoming OTP/SMS messages and forwards them to a Telegram channel.

## Features

- 🔐 Automatic website login with captcha solving
- 📱 Monitors SMS/OTP messages every 3 seconds
- 🚫 Prevents duplicate message sending
- 📨 Formats messages according to specified template
- 🤖 Sends messages to Telegram channel

## Setup

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Make sure you have Chrome browser installed (for Selenium)

3. Configure the bot settings in `otp_telegram_bot.py` if needed:
   - Telegram bot token: `8354306480:AAFPh2CTRZpjOdntLM8zqdM5kNkE6fthqPw`
   - Telegram channel: `-1002724043027`
   - Website credentials: `Roni_dada` / `Roni_dada`

## Running the Bot

```bash
python run_bot.py
```

Or run directly:
```bash
python otp_telegram_bot.py
```

## How it Works

1. **Login**: Bot logs into `http://94.23.120.156/ints/login` with provided credentials
2. **Captcha**: Automatically solves simple math captcha (e.g., "What is 7 + 4 = ?")
3. **Monitor**: Checks `http://94.23.120.156/ints/client/SMSCDRStats` every 3 seconds
4. **Format**: Formats found SMS messages using the specified template
5. **Send**: Sends formatted messages to Telegram channel (no duplicates)

## Message Format

```
🔔Guinea 🇬🇳 Whatsapp Otp Code Received Successfully.

⏰Time: 2025-08-13 12:42:09
📱Number: 224610945741
🌍Country: Guinea 🇬🇳
💬Service: Whatsapp
🔐Otp Code: 3526
📝Message:
```
3526 est votre code de vérification 3ggNv9RHae
```
```

## Configuration

The bot automatically:
- Runs Chrome in headless mode
- Logs activities to `otp_bot.log`
- Prevents sending duplicate messages
- Handles login session management

## Stopping the Bot

Press `Ctrl+C` to stop the bot gracefully.

## Troubleshooting

- Check `otp_bot.log` for detailed logs
- Ensure Telegram bot has admin permissions in the channel
- Verify website credentials are correct
- Make sure Chrome browser is installed
