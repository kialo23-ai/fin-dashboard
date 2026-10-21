import os
import pandas as pd
import streamlit as st

# 本地代码库路径（相对项目根目录）
DATA_FILE = "data/instrument_master.csv"

# 类型中文映射
TYPE_MAP = {
    "stock": "股票",
    "etf": "ETF",
    "futures": "期货",
    "bond_index": "债券指数",
    "bond_etf": "债券ETF",
    "crypto": "加密货币",
}


@st.cache_data(ttl=86400, show_spinner=False)
def _load_local_database() -> pd.DataFrame:
    """从本地 CSV 加载全局金融工具代码库。缓存 24 小时。"""
    if not os.path.exists(DATA_FILE):
        st.error(
            f"本地数据文件不存在: {DATA_FILE}\n"
            f"请先运行: python scripts/build_instrument_master.py"
        )
        return pd.DataFrame()

    try:
        df = pd.read_csv(DATA_FILE, dtype=str)
        # 必须列检查
        required = ["symbol", "name", "yf_symbol", "type"]
        missing = [c for c in required if c not in df.columns]
        if missing:
            st.error(f"数据文件缺少必要列: {missing}")
            return pd.DataFrame()

        # 空值填充
        for col in df.columns:
            df[col] = df[col].fillna("").astype(str)

        return df
    except Exception as e:
        st.error(f"读取本地数据文件失败: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=3600, show_spinner=False)
def search_ticker(query: str, max_results: int = 30) -> pd.DataFrame:
    """
    在本地代码库中模糊搜索。

    匹配字段：
      - symbol: 原始代码（如 600519、AAPL、GC=F）
      - name:   名称（中英文）
      - yf_symbol: yfinance 代码

    返回列：code / name / yf_code / 市场
    """
    if not query or not query.strip():
        return pd.DataFrame()

    df = _load_local_database()
    if df.empty:
        return pd.DataFrame()

    q = query.strip()

    # 模糊匹配（不区分大小写，按字面匹配）
    mask = (
        df["symbol"].str.contains(q, case=False, na=False, regex=False)
        | df["name"].str.contains(q, case=False, na=False, regex=False)
        | df["yf_symbol"].str.contains(q, case=False, na=False, regex=False)
    )

    results = df[mask].head(max_results).copy()
    if results.empty:
        return pd.DataFrame()

    # 适配前端列名
    results["code"] = results["symbol"]
    results["yf_code"] = results["yf_symbol"]
    results["市场"] = results["type"].map(TYPE_MAP).fillna(results["type"])
    
    # 新增：按 yf_code 去重，防止同一标的出现多次
    results = results.drop_duplicates(subset=["yf_code"])

    return results[["code", "name", "yf_code", "市场"]].reset_index(drop=True)


def get_database_stats() -> dict:
    """返回代码库的统计信息，用于在界面上显示。"""
    df = _load_local_database()
    if df.empty:
        return {"total": 0, "by_type": {}, "by_exchange": {}}

    return {
        "total": len(df),
        "by_type": df["type"].value_counts().to_dict(),
        "by_exchange": df["exchange"].value_counts().head(10).to_dict(),
    }