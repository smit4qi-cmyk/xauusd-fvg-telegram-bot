import zlib
import struct

def generate_candlestick_chart(filename, candles, entry=None, sl=None, tp1=None, tp2=None, title="XAUUSD SMC KILLZONE FVG"):
    """
    Pure Python Candlestick chart renderer using PNG specifications (zlib + struct).
    Requires zero external dependencies (no matplotlib, no pillow, works everywhere).
    """
    width = 700
    height = 420
    
    # Dark Mode TradingView palette
    bg_color = (19, 23, 34)
    grid_color = (30, 34, 45)
    bull_color = (8, 153, 129)       # #089981
    bear_color = (242, 54, 69)       # #F23645
    entry_color = (33, 150, 243)     # Blue
    sl_color = (239, 83, 80)         # Red
    tp_color = (38, 166, 154)        # Green
    text_dot_color = (200, 205, 215)
    
    pixels = [[bg_color for _ in range(width)] for _ in range(height)]
    
    min_p = min(c['l'] for c in candles)
    max_p = max(c['h'] for c in candles)
    
    levels = [p for p in [entry, sl, tp1, tp2] if p is not None]
    if levels:
        min_p = min(min_p, min(levels))
        max_p = max(max_p, max(levels))
        
    pad = (max_p - min_p) * 0.12 or 1.0
    min_p -= pad
    max_p += pad
    
    top_margin = 50
    bottom_margin = 40
    chart_h = height - top_margin - bottom_margin
    
    def to_y(price):
        if price is None:
            return None
        y = int(height - bottom_margin - ((price - min_p) / (max_p - min_p)) * chart_h)
        return max(top_margin, min(height - bottom_margin, y))

    # Draw horizontal grid lines
    for i in range(5):
        y_grid = top_margin + int(i * (chart_h / 4))
        for x in range(30, width - 30):
            pixels[y_grid][x] = grid_color

    def draw_level_line(y, color, dash_len=8):
        if y is None or not (0 <= y < height):
            return
        for x in range(40, width - 40):
            if (x // dash_len) % 2 == 0:
                for dy in range(-1, 2):
                    if 0 <= y + dy < height:
                        pixels[y + dy][x] = color

    # Draw Price Levels
    if tp2: draw_level_line(to_y(tp2), tp_color, dash_len=6)
    if tp1: draw_level_line(to_y(tp1), tp_color, dash_len=6)
    if entry: draw_level_line(to_y(entry), entry_color, dash_len=8)
    if sl: draw_level_line(to_y(sl), sl_color, dash_len=4)

    # Draw Candlesticks
    n = len(candles)
    plot_width = width - 120
    step = plot_width / max(1, n)
    bar_w = max(5, int(step * 0.65))

    for idx, c in enumerate(candles):
        cx = int(60 + idx * step + step / 2)
        color = bull_color if c['c'] >= c['o'] else bear_color

        y_high = to_y(c['h'])
        y_low = to_y(c['l'])
        y_open = to_y(c['o'])
        y_close = to_y(c['c'])

        # Wick
        for y in range(min(y_high, y_low), max(y_high, y_low) + 1):
            if 0 <= y < height and 0 <= cx < width:
                pixels[y][cx] = color

        # Body
        body_top = min(y_open, y_close)
        body_bottom = max(y_open, y_close)
        if body_top == body_bottom:
            body_bottom += 1

        for y in range(body_top, body_bottom + 1):
            for x in range(cx - bar_w // 2, cx + bar_w // 2 + 1):
                if 0 <= y < height and 0 <= x < width:
                    pixels[y][x] = color

    # Generate PNG bytes
    raw_data = bytearray()
    for row in pixels:
        raw_data.append(0)  # Filter type 0
        for r, g, b in row:
            raw_data.extend((r, g, b))

    compressed = zlib.compress(bytes(raw_data))

    png = bytearray(b'\x89PNG\r\n\x1a\n')
    ihdr = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    png.extend(struct.pack('>I', len(ihdr)) + b'IHDR' + ihdr + struct.pack('>I', zlib.crc32(b'IHDR' + ihdr)))
    png.extend(struct.pack('>I', len(compressed)) + b'IDAT' + compressed + struct.pack('>I', zlib.crc32(b'IDAT' + compressed)))
    png.extend(struct.pack('>I', 0) + b'IEND' + struct.pack('>I', zlib.crc32(b'IEND')))

    with open(filename, 'wb') as f:
        f.write(png)
        
    return filename
