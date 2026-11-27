import os
import json
import time
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from chart_engine import generate_candlestick_chart

# Load configuration from environment or config file
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

def fetch_gold_candles(interval="1h", range_period="5d"):
    """Fetch live XAUUSD (Gold) candles from Yahoo Finance."""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/GC=F?interval={interval}&range={range_period}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode())
        res = data['chart']['result'][0]
        ts = res['timestamp']
        q = res['indicators']['quote'][0]
        
    bars = []
    for i in range(len(ts)):
        if q['open'][i] and q['high'][i] and q['low'][i] and q['close'][i]:
            dt = datetime.fromtimestamp(ts[i], timezone.utc)
            bars.append({
                'dt': dt,
                'hour': dt.hour,
                'o': round(q['open'][i], 2),
                'h': round(q['high'][i], 2),
                'l': round(q['low'][i], 2),
                'c': round(q['close'][i], 2)
            })
    return bars

def send_telegram_message(bot_token, chat_id, text):
    """Send text alert to Telegram."""
    if not bot_token or not chat_id:
        print(f"[DRY-RUN MESSAGE]\n{text}")
        return False
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = json.dumps({"chat_id": chat_id, "text": text, "parse_mode": "HTML"}).encode('utf-8')
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception as e:
        print("Telegram Send Error:", e)
        return False

def send_telegram_photo(bot_token, chat_id, photo_path, caption=""):
    """Send chart image to Telegram using multipart/form-data without external libraries."""
    if not bot_token or not chat_id:
        print(f"[DRY-RUN PHOTO] {photo_path} (Caption: {caption})")
        return False
        
    url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    
    with open(photo_path, "rb") as f:
        file_bytes = f.read()

    body = bytearray()
    # chat_id field
    body.extend(f"--{boundary}\r\n".encode('utf-8'))
    body.extend(f'Content-Disposition: form-data; name="chat_id"\r\n\r\n{chat_id}\r\n'.encode('utf-8'))
    # caption field
    body.extend(f"--{boundary}\r\n".encode('utf-8'))
    body.extend(f'Content-Disposition: form-data; name="caption"\r\n\r\n{caption}\r\n'.encode('utf-8'))
    body.extend(f"--{boundary}\r\n".encode('utf-8'))
    body.extend(f'Content-Disposition: form-data; name="parse_mode"\r\n\r\nHTML\r\n'.encode('utf-8'))
    # photo file field
    body.extend(f"--{boundary}\r\n".encode('utf-8'))
    body.extend(f'Content-Disposition: form-data; name="photo"; filename="chart.png"\r\n'.encode('utf-8'))
    body.extend(b'Content-Type: image/png\r\n\r\n')
    body.extend(file_bytes)
    body.extend(f"\r\n--{boundary}--\r\n".encode('utf-8'))

    req = urllib.request.Request(url, data=bytes(body), headers={
        "Content-Type": f"multipart/form-data; boundary={boundary}"
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status == 200
    except Exception as e:
        print("Telegram Photo Error:", e)
        return False

def scan_for_fvg_signal(bars):
    """
    Scans recent candles for SMC Fair Value Gap (FVG) and Retest setups
    aligned with London and New York Killzones.
    """
    if len(bars) < 6:
        return None

    # Focus on the most recent 3-5 completed bars
    for idx in range(len(bars) - 5, len(bars) - 1):
        b0 = bars[idx - 2]
        b1 = bars[idx - 1]  # Displacement
        b2 = bars[idx]      # Gap formation

        # Check Killzone: London (7-11 UTC) or New York (13-17 UTC)
        is_killzone = (7 <= b2['hour'] <= 11) or (13 <= b2['hour'] <= 17)
        if not is_killzone:
            continue

        # Bullish FVG
        if b2['l'] > b0['h'] + 2.0 and b1['c'] > b1['o'] and (b1['c'] - b1['o']) >= 8.0:
            fvg_top = b2['l']
            fvg_bottom = b0['h']
            
            # Check if recent candle retested the FVG
            current_bar = bars[-1]
            if current_bar['l'] <= fvg_top and current_bar['c'] >= fvg_bottom:
                entry = fvg_top
                sl = b1['l'] - 1.5
                risk_pts = round(entry - sl, 2)
                if 2.5 <= risk_pts <= 15.0:
                    tp1 = round(entry + 1.0 * risk_pts, 2)
                    tp2 = round(entry + 2.5 * risk_pts, 2)
                    return {
                        'direction': 'BUY / LONG',
                        'symbol': 'XAUUSD (GOLD)',
                        'time': current_bar['dt'].strftime('%Y-%m-%d %H:%M UTC'),
                        'entry': entry,
                        'sl': sl,
                        'tp1': tp1,
                        'tp2': tp2,
                        'risk_pts': risk_pts,
                        'candles': bars[-15:]
                    }

        # Bearish FVG
        elif b2['h'] < b0['l'] - 2.0 and b1['c'] < b1['o'] and (b1['o'] - b1['c']) >= 8.0:
            fvg_bottom = b2['h']
            fvg_top = b0['l']
            
            current_bar = bars[-1]
            if current_bar['h'] >= fvg_bottom and current_bar['c'] <= fvg_top:
                entry = fvg_bottom
                sl = b1['h'] + 1.5
                risk_pts = round(sl - entry, 2)
                if 2.5 <= risk_pts <= 15.0:
                    tp1 = round(entry - 1.0 * risk_pts, 2)
                    tp2 = round(entry - 2.5 * risk_pts, 2)
                    return {
                        'direction': 'SELL / SHORT',
                        'symbol': 'XAUUSD (GOLD)',
                        'time': current_bar['dt'].strftime('%Y-%m-%d %H:%M UTC'),
                        'entry': entry,
                        'sl': sl,
                        'tp1': tp1,
                        'tp2': tp2,
                        'risk_pts': risk_pts,
                        'candles': bars[-15:]
                    }
    return None

def build_signal_caption(signal):
    direction_emoji = "🟢" if "BUY" in signal['direction'] else "🔴"
    return (
        f"🚨 <b>XAUUSD SMC KILLZONE SIGNAL</b> 🚨\n\n"
        f"📊 <b>Symbol:</b> {signal['symbol']}\n"
        f"⏰ <b>Time:</b> {signal['time']}\n"
        f"{direction_emoji} <b>Direction:</b> <code>{signal['direction']}</code>\n\n"
        f"🎯 <b>Entry Price:</b> <code>${signal['entry']}</code>\n"
        f"🛑 <b>Stop Loss:</b> <code>${signal['sl']}</code> (Risk: ${signal['risk_pts']})\n"
        f"🎯 <b>Take Profit 1 (1:1):</b> <code>${signal['tp1']}</code> (70% Partial & Move SL to BE)\n"
        f"🚀 <b>Take Profit 2 (1:2.5):</b> <code>${signal['tp2']}</code> (Runner 30%)\n\n"
        f"💡 <b>Strategy Rule:</b>\n"
        f"• Risk max 1.5% - 2% of capital.\n"
        f"• When TP1 is achieved, lock 70% and shift Stop Loss to Entry (Break-Even)!"
    )

def run_test_simulation():
    """Runs a dry-run test with mock data to demonstrate chart creation and message structure."""
    print("Testing signal generator and candlestick chart engine...")
    mock_candles = [
        {'o': 2640.0, 'h': 2644.5, 'l': 2638.2, 'c': 2643.0},
        {'o': 2643.0, 'h': 2646.0, 'l': 2641.5, 'c': 2645.2},
        {'o': 2645.2, 'h': 2659.8, 'l': 2644.0, 'c': 2658.0}, # Displacement
        {'o': 2658.0, 'h': 2661.2, 'l': 2653.0, 'c': 2655.4}, # Gap formation
        {'o': 2655.4, 'h': 2657.0, 'l': 2651.0, 'c': 2652.5}, # Retest into FVG
    ]
    test_signal = {
        'direction': 'BUY / LONG',
        'symbol': 'XAUUSD (GOLD)',
        'time': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC'),
        'entry': 2653.0,
        'sl': 2644.0,
        'tp1': 2662.0,
        'tp2': 2675.5,
        'risk_pts': 9.0,
        'candles': mock_candles
    }
    chart_path = generate_candlestick_chart(
        "test_signal_chart.png",
        test_signal['candles'],
        entry=test_signal['entry'],
        sl=test_signal['sl'],
        tp1=test_signal['tp1'],
        tp2=test_signal['tp2']
    )
    caption = build_signal_caption(test_signal)
    print("\n--- SAMPLE TELEGRAM ALERT MESSAGE ---")
    print(caption)
    print(f"\n[OK] Chart generated at: {chart_path}")

if __name__ == "__main__":
    import sys
    if "--test" in sys.argv:
        run_test_simulation()
    else:
        print("Starting XAUUSD SMC Killzone Telegram Automation Bot...")
        last_alert_time = None
        while True:
            try:
                candles = fetch_gold_candles(interval="1h", range_period="5d")
                signal = scan_for_fvg_signal(candles)
                if signal and signal['time'] != last_alert_time:
                    chart_img = generate_candlestick_chart(
                        "live_signal_chart.png",
                        signal['candles'],
                        entry=signal['entry'],
                        sl=signal['sl'],
                        tp1=signal['tp1'],
                        tp2=signal['tp2']
                    )
                    caption = build_signal_caption(signal)
                    send_telegram_photo(BOT_TOKEN, CHAT_ID, chart_img, caption)
                    last_alert_time = signal['time']
                    print(f"[{datetime.now()}] Signal Dispatched: {signal['direction']} at {signal['entry']}")
                else:
                    print(f"[{datetime.now()}] Scanning... No new Killzone FVG setup. Waiting for next cycle.")
            except Exception as e:
                print("Error during scan cycle:", e)
            time.sleep(60)
