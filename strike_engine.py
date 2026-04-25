import time, requests

def get_live_data(ticker):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1m&range=1d"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        data = requests.get(url, headers=headers).json()
        prices = data['chart']['result'][0]['indicators']['quote'][0]['close']
        return [p for p in prices if p is not None]
    except: return []

def calculate_ema(prices, period=9):
    if not prices: return 0
    multiplier = 2 / (period + 1)
    ema = prices[0]
    for p in prices[1:]:
        ema = (p - ema) * multiplier + ema
    return round(ema, 3)

def calculate_rsi(prices, period=14):
    if len(prices) < period + 1: return 50
    gains, losses = [], []
    for i in range(1, len(prices)):
        diff = prices[i] - prices[i-1]
        gains.append(max(diff, 0))
        losses.append(max(-diff, 0))
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0: return 100
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)

if __name__ == "__main__":
    ticker = "GPRO"
    print(f"!! HEALY VECTOR LABS: PURE-LOGIC LIVE STRIKE [{ticker}] !!")
    while True:
        try:
            prices = get_live_data(ticker)
            if prices:
                p, rsi, ema = round(prices[-1], 2), calculate_rsi(prices), calculate_ema(prices)
                msg = "[STRIKE]: ALIGNMENT" if (rsi > 40 and p > ema) else "[WAIT]: MOMENTUM LEAK"
                print(f"P: {p} | R: {rsi} | E: {ema} | {msg}")
            time.sleep(60)
        except Exception as err:
            print(f"[ERROR]: {err}"); time.sleep(10)
