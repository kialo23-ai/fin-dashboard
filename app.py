import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

from modules.data_fetcher import fetch_stock_data
from modules.indicators import compute_all_indicators
from modules.charts import (
    plot_normalized_comparison,
    plot_candlestick_panel,
    plot_indicator_comparison,
    plot_correlation_heatmap,
    plot_ma5_dual_axis,
)
from modules.exporter import df_to_csv_bytes, df_to_excel_bytes, charts_to_html_bytes
from modules.ticker_search import search_ticker, get_database_stats

# ===== 页面配置 =====
st.set_page_config(
    page_title="金融指标对比分析",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ===== 【放这里】响应式 CSS =====
st.markdown("""
<style>
/* 基础视口设置 */
@viewport {
    width: device-width;
    zoom: 1.0;
}

/* 平板断点：最大宽度 1024px（MediaPad 可能触发） */
@media screen and (max-width: 1024px) {
    .main .block-container {
        padding: 1rem 1.2rem;
        max-width: 100% !important;
    }
    /* 强制列在平板上堆叠，避免过于拥挤 */
    div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
        min-width: 100% !important;
        flex: 1 1 100% !important;
    }
}

/* 手机断点：最大宽度 768px（P70 Pro 等手机） */
@media screen and (max-width: 768px) {
    .main .block-container {
        padding: 0.8rem 0.8rem;
    }
    /* 缩小标题字号 */
    h1 { font-size: 1.4rem !important; }
    h2 { font-size: 1.1rem !important; }
    h3 { font-size: 0.95rem !important; }
    /* 确保所有图表宽度100% */
    .js-plotly-plot, .plot-container {
        width: 100% !important;
        min-height: 300px;
    }
    /* 表格允许横向滚动 */
    .stDataFrame {
        overflow-x: auto !important;
        font-size: 0.8rem !important;
    }
    /* 隐藏 Streamlit 默认的装饰性元素 */
    .stDeployButton { display: none; }
    /* 按钮和输入框增大点击区域 */
    button, .stTextInput input, .stSelectbox select {
        min-height: 44px !important;
        font-size: 1rem !important;
    }
}

/* 超窄屏：最大宽度 480px（手机竖屏） */
@media screen and (max-width: 480px) {
    .main .block-container {
        padding: 0.5rem;
    }
    h1 { font-size: 1.2rem !important; }
    /* 进一步压缩列间距 */
    div[data-testid="stHorizontalBlock"] { gap: 0.3rem !important; }
}
</style>
""", unsafe_allow_html=True)

st.title("📈 金融指标对比分析看板")
st.caption("拉取历史行情 · 计算技术指标 · 生成对比图表 · 导出分析报告")

# ===== 初始化分析队列 =====
if "watchlist" not in st.session_state:
    st.session_state.watchlist = []

# ===== 初始化 session_state =====
if "data_dict" not in st.session_state:
    st.session_state.data_dict = {}
if "last_params" not in st.session_state:
    st.session_state.last_params = None

# ===== 【新增】回调函数 =====
def _add_to_watchlist(yf_code: str):
    """加入队列。"""
    if yf_code not in st.session_state.watchlist:
        st.session_state.watchlist.append(yf_code)
    # 不清空搜索框

# # ===== 侧边栏：参数输入 =====
with st.sidebar:
    st.header("⚙️ 参数配置")

    # ---------- 搜索与添加 ----------
    with st.expander("🔍 搜索并添加股票", expanded=True):
        # 显示代码库概况
        stats = get_database_stats()
        if stats["total"] > 0:
            st.caption(
                f"本地代码库：**{stats['total']:,}** 条  ·  "
                f"股票/ETF/期货/债券  ·  支持中英文模糊查询"
            )
        else:
            st.warning("本地代码库为空，请先运行 scripts/build_instrument_master.py")

        search_query = st.text_input(
            "输入股票名称或代码",
            placeholder="例如：紫金矿业、Apple、GC=F、TLT",
            key="search_input",
        )

        if search_query:
            with st.spinner("搜索中..."):
                results = search_ticker(search_query)

            if not results.empty:
                st.caption(f"找到 {len(results)} 条结果，点击「➕」加入队列")
                for idx, row in results.iterrows():
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.markdown(
                            f"**{row['name']}**  \n"
                            f"`{row['yf_code']}` · {row['市场']}"
                        )
                    with col2:
                        if st.button(
                            "➕",
                            key=f"add_{row['yf_code']}_{idx}",
                            help=f"添加 {row['name']}",
                            width='stretch',
                        ):
                            if row["yf_code"] not in st.session_state.watchlist:
                                st.session_state.watchlist.append(row["yf_code"])
                                st.rerun()
            else:
                st.info("未找到匹配的代码，请尝试其他关键词")

    st.divider()

    # ---------- 分析队列展示 ----------
    st.subheader("📋 分析队列")
    if st.session_state.watchlist:
        for i, code in enumerate(st.session_state.watchlist):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.code(code, language=None)
            with col2:
                if st.button("✕", key=f"remove_{i}_{code}",
                             width='stretch'):
                    st.session_state.watchlist.pop(i)
                    st.rerun()
        if st.button("🗑️ 清空队列", width='stretch', key="clear_queue"):
            st.session_state.watchlist = []
            st.session_state.last_params = None
            st.rerun()
    else:
        st.caption("队列为空，请搜索并添加股票")

    # ---------- 手动输入（备用） ----------
    st.divider()
    with st.expander("✏️ 手动输入代码", expanded=False):
        manual_input = st.text_input(
            "代码（逗号分隔）",
            placeholder="AAPL, 0700.HK, 601899.SS",
            key="manual_ticker_input",
        )
        if st.button("添加到队列", key="add_manual", width='stretch'):
            if manual_input:
                for t in manual_input.split(","):
                    t = t.strip().upper()
                    if t and t not in st.session_state.watchlist:
                        st.session_state.watchlist.append(t)
                st.rerun()

    # ---------- 日期与频率 ----------
    st.divider()
    st.subheader("📅 时间范围")
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "开始日期", value=datetime.now() - timedelta(days=365)
        )
    with col2:
        end_date = st.date_input("结束日期", value=datetime.now())

    interval = st.selectbox(
        "数据频率",
        options=["1d", "1wk", "1mo"],
        format_func=lambda x: {"1d": "日线", "1wk": "周线", "1mo": "月线"}[x],
    )

    # ---------- 移动端适配 ----------
    st.divider()
    mobile_mode = st.toggle(
        "📱 移动端适配",
        value=False,
        help="开启后图表更紧凑，适合手机/平板查看",
        key="mobile_mode",
    )
# ===== 主逻辑（注意：这里退出侧边栏缩进，回到顶层） =====
tickers = st.session_state.watchlist

if not tickers:
    st.info("👈 请在左侧搜索并添加股票到分析队列")
    st.stop()

current_params = (tuple(tickers), str(start_date), str(end_date), interval)

if st.session_state.last_params != current_params:
    with st.spinner("正在拉取数据并计算指标..."):
        raw_data = fetch_stock_data(tickers, str(start_date), str(end_date), interval)
        data_dict = {t: compute_all_indicators(df) for t, df in raw_data.items()}
        st.session_state.data_dict = data_dict
        st.session_state.last_params = current_params
else:
    data_dict = st.session_state.data_dict

if not data_dict:
    st.error("未获取到任何数据，请检查股票代码和日期范围。")
    st.stop()

st.success(f"已成功加载 {len(data_dict)} 只标的的数据")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 归一化对比",
    "🕯️ K线分析",
    "📉 指标对比",
    "🔥 相关性",
    "📥 数据导出",
])
# --- Tab1: 归一化对比 ---
with tab1:
    fig = plot_normalized_comparison(data_dict, mobile_mode=mobile_mode)
    st.plotly_chart(
        fig,
        width='stretch',
        config={"responsive": True},
        key="chart_normalized",
    )
# --- Tab2: K线分析 ---
with tab2:
    selected_ticker = st.selectbox(
        "选择标的", list(data_dict.keys()), key="kline_ticker"
    )
    fig = plot_candlestick_panel(
        data_dict[selected_ticker],
        selected_ticker,
        mobile_mode=mobile_mode,
    )
    st.plotly_chart(
        fig,
        width='stretch',
        config={"responsive": True},
        key=f"chart_kline_{selected_ticker}",
    )

# --- Tab3: 指标对比 ---
with tab3:
    indicator_map = {
        "RSI(14)": "RSI_14",
        "MACD": "MACD",
        "ATR(14)": "ATR_14",
        "OBV": "OBV",
        "MA5双轴对比": "__MA5_DUAL__",
    }
    selected_ind = st.selectbox(
        "选择指标", list(indicator_map.keys()), key="ind_selector"
    )

    if selected_ind == "MA5双轴对比":
        st.caption(
            "直接基于原始价格计算 5 日均线，量级大的标的使用左轴，"
            "其余使用右轴。适合对比量级差异大的资产（如原油 vs 股价）。"
        )
        fig = plot_ma5_dual_axis(data_dict, mobile_mode=mobile_mode)
        st.plotly_chart(
            fig,
            width='stretch',
            config={
                "responsive": True,
                # 隐藏自动缩放按钮，防止它破坏左右轴的比例
                "modeBarButtonsToRemove": ["autoScale2d"]
            },
            key="chart_ma5_dual",
        )
    else:
        fig = plot_indicator_comparison(
            data_dict,
            indicator_map[selected_ind],
            f"{selected_ind} 多标的对比",
            mobile_mode=mobile_mode,
        )
        st.plotly_chart(
            fig,
            width='stretch',
            config={"responsive": True},
            key=f"chart_ind_{selected_ind}",
        )
        
# --- Tab4: 相关性 ---
with tab4:
    fig = plot_correlation_heatmap(data_dict, mobile_mode=mobile_mode)
    st.plotly_chart(
        fig,
        width='stretch',
        config={"responsive": True},
        key="chart_corr",
    )

# --- Tab5: 数据导出 ---
with tab5:
    st.subheader("📥 下载分析结果")

    # 合并所有数据为一张表
    combined_rows = []
    for ticker, df in data_dict.items():
        temp = df.copy()
        temp.insert(0, "Ticker", ticker)
        combined_rows.append(temp)
    combined_df = pd.concat(combined_rows)

    col_a, col_b, col_c = st.columns(3)

    with col_a:
        st.download_button(
            "📄 下载 CSV（全部数据）",
            data=df_to_csv_bytes(combined_df),
            file_name="stock_data.csv",
            mime="text/csv",
            width='stretch',
        )

    with col_b:
        st.download_button(
            "📊 下载 Excel（分Sheet）",
            data=df_to_excel_bytes(data_dict),
            file_name="stock_analysis.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            width='stretch',
        )

    with col_c:
        # 导出 HTML 报告：显式使用桌面版图表
        charts = {
            "归一化价格对比": plot_normalized_comparison(data_dict, mobile_mode=False),
            "相关性矩阵": plot_correlation_heatmap(data_dict, mobile_mode=False),
        }
        for t, d in data_dict.items():
            charts[f"{t} K线分析"] = plot_candlestick_panel(d, t, mobile_mode=False)

        st.download_button(
            "🌐 下载 HTML 报告",
            data=charts_to_html_bytes(charts),
            file_name="analysis_report.html",
            mime="text/html",
            width='stretch',
        )

    # 数据预览
    st.subheader("📋 数据预览")
    st.dataframe(combined_df.tail(50), width='stretch')