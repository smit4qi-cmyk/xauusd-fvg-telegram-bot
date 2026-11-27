# XAUUSD (Gold) SMC Killzone FVG Telegram Bot 🚀

This is a production-ready, zero-external-dependency automated trading bot for **XAUUSD (Gold)** based on the high win-rate **SMC Killzone Fair Value Gap (FVG)** strategy.

When a setup is detected in real time during London or New York Killzones, it generates a custom candlestick chart with Entry, Stop Loss, and Take Profit levels, and sends instant alert signals directly to your Telegram chat/channel.

---

## 🌟 Key Features

- **Automated Market Surveillance:** Monitors live XAUUSD (Gold) candles continuously.
- **SMC / Killzone Alignment:**
  - London Killzone (12:30 PM – 4:30 PM IST / 07:00 – 11:00 UTC)
  - New York Killzone (06:30 PM – 10:30 PM IST / 13:00 – 17:00 UTC)
- **High-Probability FVG Detection:** Identifies 3-bar displacement imbalances ($8+ point move) and catches the optimal entry on zone retest.
- **Built-in Pure-Python Chart Generator:** Generates high-definition candlestick charts with Entry, Stop Loss, and Take Profit levels without needing external dependencies like matplotlib or PIL!
- **Telegram Integration:** Delivers instant messages with full signal parameters (Entry, SL, TP1, TP2, Risk-Reward) and visual chart images.
- **Duplicate Prevention:** Tracks signal states so you never get spammed for the same setup.

---

## 📋 Signal Message Example

```text
🚨 XAUUSD (GOLD) SMC SIGNAL DETECTED! 🚨

📊 Setup: Bullish FVG Displacement & Retest
⏰ Session: London / New York Killzone

🟢 Direction: BUY / LONG
🎯 Entry Price: $2650.50
🛑 Stop Loss: $2643.00 (Risk: $7.50)
🎯 Take Profit 1 (1:1 RR): $2658.00 (Close 70% & Move SL to BE)
🚀 Take Profit 2 (1:2.5 RR): $2669.25 (Runner 30%)

⚠️ Risk Management:
• Risk only 1.5% - 2% of capital per trade.
• Move Stop Loss to Break-Even once TP1 is hit.
```

---

## 🛠️ Quick Setup Guide

### 1. Clone the Repository
```bash
git clone https://github.com/smit4qi-cmyk/xauusd-fvg-telegram-bot.git
cd xauusd-fvg-telegram-bot
```

### 2. Configure Telegram Credentials
Get your Telegram Bot Token from [@BotFather](https://t.me/botfather) and your Chat ID from [@userinfobot](https://t.me/userinfobot).

Open `.env` (or set environment variables):
```env
TELEGRAM_BOT_TOKEN="your_bot_token_here"
TELEGRAM_CHAT_ID="your_chat_id_here"
CHECK_INTERVAL_SECONDS=60
```

### 3. Run the Bot
```bash
python3 bot.py
```

To run a one-time test simulation and verify Telegram alerts:
```bash
python3 bot.py --test
```
