import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

def _infer_price_unit(ticker: str) -> str:
    """根据代码推断计价货币和单位，返回如 'USD/桶'、'HKD/股' 的字符串。"""
    t = ticker.upper()

    # 期货（优先匹配已知品种）
    futures_map = {
        "CL=F": "USD/桶", "BZ=F": "USD/桶",
        "NG=F": "USD/MMBtu", "HO=F": "USD/加仑", "RB=F": "USD/加仑",
        "GC=F": "USD/盎司", "SI=F": "USD/盎司",
        "PL=F": "USD/盎司", "PA=F": "USD/盎司",
        "HG=F": "USD/磅",
        "ZC=F": "USc/蒲式耳", "ZS=F": "USc/蒲式耳", "ZW=F": "USc/蒲式耳",
        "ZM=F": "USD/短吨", "ZL=F": "USc/磅",
        "KC=F": "USc/磅", "SB=F": "USc/磅",
        "CC=F": "USD/吨", "CT=F": "USc/磅",
        "ZN=F": "USD/点", "ZB=F": "USD/点",
        "ZF=F": "USD/点", "ZT=F": "USD/点",
        "ES=F": "USD/点", "NQ=F": "USD/点",
        "YM=F": "USD/点", "RTY=F": "USD/点",
    }
    if t in futures_map:
        return futures_map[t]
    if t.endswith("=F"):
        return "USD/合约"

    # 加密货币
    if t.endswith("-USD"):
        return "USD/枚"

    # 股票（按交易所后缀）
    if t.endswith((".SS", ".SZ", ".BJ")):
        return "CNY/股"
    if t.endswith(".HK"):
        return "HKD/股"
    if t.endswith(".T"):
        return "JPY/股"
    if t.endswith((".DE", ".PA", ".AS", ".BR", ".LS", ".MI", ".MC")):
        return "EUR/股"
    if t.endswith((".TO", ".V")):
        return "CAD/股"
    if t.endswith(".AX"):
        return "AUD/股"
    if t.endswith((".KS", ".KQ")):
        return "KRW/股"
    if t.endswith((".TW", ".TWO")):
        return "TWD/股"
    if t.endswith((".NS", ".BO")):
        return "INR/股"
    if t.endswith(".L"):
        return "GBp/股"   # 伦交所多数以便士（pence）报价
    if t.endswith(".SI"):
        return "SGD/股"

    # 默认按美股
    return "USD/股"

def plot_normalized_comparison(data_dict: dict, mobile_mode: bool = False) -> go.Figure:
    """归一化价格走势对比（基准=100）"""
    fig = go.Figure()
    for ticker, df in data_dict.items():
        if df.empty:
            continue
        normalized = df["Close"] / df["Close"].iloc[0] * 100
        fig.add_trace(go.Scatter(
            x=df.index, y=normalized,
            name=ticker, mode="lines", line=dict(width=2)
        ))

    fig.update_layout(
        title=dict(
            text="归一化价格走势对比（基准=100）",
            font=dict(size=13 if mobile_mode else 16),
            x=0.5 if mobile_mode else 0,
            xanchor="center" if mobile_mode else "left",
        ),
        xaxis_title="" if mobile_mode else "日期",
        yaxis_title="" if mobile_mode else "归一化价格",
        template="plotly_white",
        hovermode="x unified",
        height=320 if mobile_mode else 500,
        margin=dict(
            l=40 if mobile_mode else 60,
            r=15 if mobile_mode else 30,
            t=55 if mobile_mode else 80,
            b=35 if mobile_mode else 60,
        ),
        font=dict(size=10 if mobile_mode else 12),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center" if mobile_mode else "left",
            x=0.5 if mobile_mode else 0,
            font=dict(size=9 if mobile_mode else 11),
        ),
        autosize=True,
    )
    return fig


def plot_candlestick_panel(df: pd.DataFrame, ticker: str,
                            mobile_mode: bool = False) -> go.Figure:
    """K线 + 布林带 + 成交量 + MACD + RSI 多面板图"""
    if mobile_mode:
        height = 700
        row_heights = [0.48, 0.12, 0.24, 0.16]
        subplot_title_size = 11
        marker_size = 9
    else:
        height = 900
        row_heights = [0.5, 0.15, 0.2, 0.15]
        subplot_title_size = 13
        marker_size = 12

    fig = make_subplots(
        rows=4, cols=1, shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=row_heights,
        subplot_titles=[f"{ticker} 价格走势", "成交量", "MACD", "RSI(14)"]
    )

    # --- 主图：K线 + 布林带 + SMA ---
    fig.add_trace(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"],
        low=df["Low"], close=df["Close"], name="K线",
        increasing_line_color="#ef5350", decreasing_line_color="#26a69a"
    ), row=1, col=1)

    if "BB_Upper" in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["BB_Upper"],
            line=dict(color="rgba(150,150,150,0.6)", dash="dash"),
            name="布林上轨", showlegend=True
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=df.index, y=df["BB_Lower"],
            line=dict(color="rgba(150,150,150,0.6)", dash="dash"),
            fill="tonexty", fillcolor="rgba(150,150,150,0.08)",
            name="布林下轨"
        ), row=1, col=1)

    if "SMA_20" in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["SMA_20"],
            line=dict(color="orange", width=1.5), name="SMA20"
        ), row=1, col=1)

    # --- 成交量 ---
    colors = ["#ef5350" if c >= o else "#26a69a"
              for c, o in zip(df["Close"], df["Open"])]
    fig.add_trace(go.Bar(
        x=df.index, y=df["Volume"],
        marker_color=colors, name="成交量", showlegend=False
    ), row=2, col=1)

    # --- MACD ---
    if "MACD" in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["MACD"],
            line=dict(color="#2196f3", width=1.5), name="MACD"
        ), row=3, col=1)
        fig.add_trace(go.Scatter(
            x=df.index, y=df["MACD_Signal"],
            line=dict(color="orange", width=1.5), name="Signal"
        ), row=3, col=1)
        hist_colors = ["#ef5350" if v >= 0 else "#26a69a"
                       for v in df["MACD_Hist"].fillna(0)]
        fig.add_trace(go.Bar(
            x=df.index, y=df["MACD_Hist"],
            marker_color=hist_colors, name="MACD柱", showlegend=False
        ), row=3, col=1)

    # --- RSI ---
    if "RSI_14" in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["RSI_14"],
            line=dict(color="#9c27b0", width=1.5), name="RSI"
        ), row=4, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="red",
                      opacity=0.5, row=4, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green",
                      opacity=0.5, row=4, col=1)

    fig.update_layout(
        height=height,
        template="plotly_white",
        xaxis_rangeslider_visible=False,
        hovermode="x unified",
        margin=dict(
            l=40 if mobile_mode else 60,
            r=15 if mobile_mode else 30,
            t=50 if mobile_mode else 80,
            b=35 if mobile_mode else 60,
        ),
        font=dict(size=10 if mobile_mode else 12),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.01,
            xanchor="center" if mobile_mode else "left",
            x=0.5 if mobile_mode else 0,
            font=dict(size=9 if mobile_mode else 11),
        ),
        autosize=True,
    )

    # 调整子图标题字号（make_subplots 的 subplot_titles 需要单独设置）
    for annotation in fig.layout.annotations:
        annotation.font.size = subplot_title_size

    return fig


def plot_indicator_comparison(data_dict: dict,
                               indicator_col: str,
                               title: str,
                               mobile_mode: bool = False) -> go.Figure:
    """同一指标的多标的对比"""
    fig = go.Figure()
    for ticker, df in data_dict.items():
        if indicator_col not in df.columns:
            continue
        fig.add_trace(go.Scatter(
            x=df.index, y=df[indicator_col],
            name=ticker, mode="lines", line=dict(width=2)
        ))

    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=13 if mobile_mode else 16),
            x=0.5 if mobile_mode else 0,
            xanchor="center" if mobile_mode else "left",
        ),
        template="plotly_white",
        hovermode="x unified",
        height=300 if mobile_mode else 450,
        margin=dict(
            l=40 if mobile_mode else 60,
            r=15 if mobile_mode else 30,
            t=55 if mobile_mode else 80,
            b=35 if mobile_mode else 60,
        ),
        font=dict(size=10 if mobile_mode else 12),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center" if mobile_mode else "left",
            x=0.5 if mobile_mode else 0,
            font=dict(size=9 if mobile_mode else 11),
        ),
        autosize=True,
    )
    return fig


def plot_correlation_heatmap(data_dict: dict, mobile_mode: bool = False) -> go.Figure:
    """多标的收益率相关性热力图"""
    returns = pd.DataFrame({
        t: d["Close"].pct_change()
        for t, d in data_dict.items() if not d.empty
    }).dropna()

    if returns.empty:
        return go.Figure()

    corr = returns.corr()

    # 单元格文字字号：标的越多，字号越小
    n = len(corr)
    if mobile_mode:
        text_size = max(7, min(11, 60 // max(n, 1)))
        height = max(300, 50 * n + 100)
    else:
        text_size = 12
        height = 500

    fig = go.Figure(data=go.Heatmap(
        z=corr.values, x=corr.columns, y=corr.index,
        colorscale="RdBu_r", zmin=-1, zmax=1,
        text=np.round(corr.values, 2),
        texttemplate="%{text}",
        textfont={"size": text_size}
    ))

    fig.update_layout(
        title=dict(
            text="收益率相关性矩阵",
            font=dict(size=13 if mobile_mode else 16),
            x=0.5 if mobile_mode else 0,
            xanchor="center" if mobile_mode else "left",
        ),
        template="plotly_white",
        height=height,
        margin=dict(
            l=50 if mobile_mode else 70,
            r=15 if mobile_mode else 30,
            t=55 if mobile_mode else 80,
            b=50 if mobile_mode else 70,
        ),
        font=dict(size=10 if mobile_mode else 12),
        autosize=True,
    )
    return fig

def plot_ma5_dual_axis(data_dict: dict, mobile_mode: bool = False) -> go.Figure:
    """
    MA5 双 Y 轴对比。
    直接基于原始收盘价计算 5 日均线，不做汇率换算。
    量级最大的标的放左轴，其余放右轴；轴标题标注计价单位。
    """
    fig = go.Figure()

    # 计算每个标的的 MA5
    series_dict = {}
    for ticker, df in data_dict.items():
        if df.empty or "Close" not in df.columns:
            continue
        ma5 = df["Close"].rolling(5).mean()
        if ma5.dropna().empty:
            continue
        series_dict[ticker] = ma5

    if not series_dict:
        fig.add_annotation(
            text="无可用数据", xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=14, color="gray"),
        )
        return fig

    # 量级最大的放左轴
    max_values = {t: s.max() for t, s in series_dict.items()}
    left_ticker = max(max_values, key=max_values.get)

    fig.add_trace(go.Scatter(
        x=series_dict[left_ticker].index,
        y=series_dict[left_ticker],
        name=f"{left_ticker}（左轴）",
        mode="lines", line=dict(width=2),
        yaxis="y",
    ))

    for ticker, s in series_dict.items():
        if ticker == left_ticker:
            continue
        fig.add_trace(go.Scatter(
            x=s.index, y=s,
            name=f"{ticker}（右轴）",
            mode="lines", line=dict(width=2),
            yaxis="y2",
        ))

    # ---- 推断左右轴单位 ----
    left_unit = _infer_price_unit(left_ticker)
    right_tickers = [t for t in series_dict.keys() if t != left_ticker]
    right_units = [_infer_price_unit(t) for t in right_tickers]

    if not right_units:
        right_unit = ""
    elif len(set(right_units)) == 1:
        right_unit = right_units[0]
    else:
        right_unit = "混合单位"

    if mobile_mode:
        left_title = left_unit
        right_title = right_unit
    else:
        left_title = f"价格（{left_unit}）"
        right_title = f"价格（{right_unit}）" if right_unit else "价格"

    # ---- Pearson 相关系数（仅 2 个标的时） ----
    corr_text = ""
    if len(series_dict) == 2:
        try:
            labels = list(series_dict.keys())
            df_pair = pd.DataFrame({
                labels[0]: series_dict[labels[0]],
                labels[1]: series_dict[labels[1]],
            }).dropna()
            if len(df_pair) > 5:
                c = df_pair.corr().iloc[0, 1]
                corr_text = f"MA5 Pearson 相关系数: {c:.3f}"
        except Exception:
            pass

    if corr_text:
        fig.add_annotation(
            text=corr_text,
            xref="paper", yref="paper", x=0.01, y=1.10,
            showarrow=False,
            font=dict(size=11, color="#666"),
            xanchor="left",
        )

    fig.update_layout(
        title=dict(
            text="MA5 双轴对比",
            font=dict(size=13 if mobile_mode else 16),
            x=0.5 if mobile_mode else 0,
            xanchor="center" if mobile_mode else "left",
        ),
        yaxis=dict(title=left_title, side="left"),
        yaxis2=dict(
            title=right_title,
            overlaying="y", side="right", showgrid=False,
        ),
        template="plotly_white",
        hovermode="x unified",
        height=320 if mobile_mode else 500,
        margin=dict(
            l=40 if mobile_mode else 70,
            r=40 if mobile_mode else 70,
            t=55 if mobile_mode else 90,
            b=35 if mobile_mode else 60,
        ),
        font=dict(size=10 if mobile_mode else 12),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02,
            xanchor="center" if mobile_mode else "left",
            x=0.5 if mobile_mode else 0,
            font=dict(size=9 if mobile_mode else 11),
        ),
        autosize=True,
    )
    return fig