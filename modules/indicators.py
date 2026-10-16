import pandas as pd
import numpy as np

def compute_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    基于OHLCV数据计算全套技术指标。
    输入df需要包含 Open, High, Low, Close, Volume 列。
    """
    import ta

    result = df.copy()
    close = result["Close"]
    high = result["High"]
    low = result["Low"]
    volume = result["Volume"]

    # ===== 趋势指标 =====
    result["SMA_20"] = close.rolling(window=20).mean()
    result["SMA_50"] = close.rolling(window=50).mean()
    result["EMA_12"] = close.ewm(span=12, adjust=False).mean()
    result["EMA_26"] = close.ewm(span=26, adjust=False).mean()

    # ===== MACD =====
    macd_obj = ta.trend.MACD(close, window_slow=26, window_fast=12, window_sign=9)
    result["MACD"] = macd_obj.macd()
    result["MACD_Signal"] = macd_obj.macd_signal()
    result["MACD_Hist"] = macd_obj.macd_diff()

    # ===== RSI =====
    result["RSI_14"] = ta.momentum.RSIIndicator(close, window=14).rsi()

    # ===== 随机指标 KDJ =====
    stoch = ta.momentum.StochasticOscillator(high, low, close, window=9)
    result["STOCH_K"] = stoch.stoch()
    result["STOCH_D"] = stoch.stoch_signal()

    # ===== 布林带 =====
    bb = ta.volatility.BollingerBands(close, window=20, window_dev=2)
    result["BB_Upper"] = bb.bollinger_hband()
    result["BB_Middle"] = bb.bollinger_mavg()
    result["BB_Lower"] = bb.bollinger_lband()

    # ===== ATR 波动率 =====
    result["ATR_14"] = ta.volatility.AverageTrueRange(
        high, low, close, window=14
    ).average_true_range()

    # ===== OBV 能量潮 =====
    result["OBV"] = ta.volume.OnBalanceVolumeIndicator(
        close, volume
    ).on_balance_volume()

    # ===== 收益率 =====
    result["Daily_Return"] = close.pct_change()

    return result