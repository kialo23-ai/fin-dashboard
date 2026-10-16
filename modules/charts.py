import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np


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