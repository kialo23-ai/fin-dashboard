import yfinance as yf
import pandas as pd
import streamlit as st
from curl_cffi import requests as cffi_requests  # 导入 curl_cffi

@st.cache_data(ttl=300)
def fetch_stock_data(tickers: list, start: str, end: str, interval: str = "1d"):
    """
    拉取多只标的的历史OHLCV数据。
    使用 curl_cffi 会话绕过 Yahoo 的机器人检测。
    """
    if isinstance(tickers, str):
        tickers = [tickers]

    # 创建一个模拟 Chrome 浏览器的会话
    session = cffi_requests.Session(impersonate="chrome")

    all_data = {}
    for ticker in tickers:
        try:
            # 将 session 参数传递给 yf.download
            df = yf.download(
                ticker,
                start=start,
                end=end,
                interval=interval,
                progress=False,
                auto_adjust=True,
                session=session,  # 关键：使用自定义 session
            )
            if df.empty:
                st.warning(f"未获取到 {ticker} 的数据，请检查代码是否正确")
                continue
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df.index.name = "Date"
            all_data[ticker] = df
        except Exception as e:
            st.error(f"拉取 {ticker} 数据失败: {e}")

    return all_data