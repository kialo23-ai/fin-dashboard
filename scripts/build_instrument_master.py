"""
构建全局金融工具代码库。
运行一次即可生成 data/instrument_master.csv。
之后 ticker_search.py 直接读取本地文件，不再依赖网络。

数据源：
  1. HuggingFace free-global-stock-ticker-database (全球股票+ETF)
  2. GitHub irachex/open-stock-data (CN/HK/US 交易所代码)
  3. 硬编码期货品种 (COMEX/NYMEX/CBOT/CME/ICE)
  4. 硬编码债券/利率品种 (美债收益率指数 + 债券ETF)
  5. akshare A股+港股 (可选，失败不影响主流程)
"""

import os
import sys
import ssl
import io
import time
import pandas as pd
import requests
from pathlib import Path

# ---- 修复 SSL 证书验证问题 ----
ssl._create_default_https_context = ssl._create_unverified_context

# 项目根目录
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)
OUTPUT_FILE = DATA_DIR / "instrument_master.csv"


# ============================================================
# 代码转换规则
# ============================================================

EXCHANGE_SUFFIX_MAP = {
    # 欧洲
    "LSE": ".L", "LON": ".L",
    "FSE": ".DE", "XETRA": ".DE", "GER": ".DE", "FRA": ".DE",
    "EURONEXT": ".PA", "PAR": ".PA",
    "AMS": ".AS", "BRU": ".BR", "LIS": ".LS",
    # 北美
    "TSX": ".TO", "TSE": ".TO",
    # 亚太
    "ASX": ".AX",
    "JPX": ".T", "TSE_JP": ".T",
    "HKEX": ".HK", "HKG": ".HK",
    "NSE": ".NS", "BSE": ".BO",
    "KRX": ".KS", "KOSDAQ": ".KQ",
    "SSE": ".SS", "SZSE": ".SZ", "BSE_CN": ".BJ",
    # 南美
    "B3": ".SA", "BVMF": ".SA",
}

US_EXCHANGES = {"NYSE", "NASDAQ", "AMEX", "NYQ", "NMS", "NGM", "NCM", "PCX", "BATS"}

YF_SUFFIXES = (".SS", ".SZ", ".BJ", ".HK", ".L", ".TO", ".DE", ".AX",
               ".T", ".SA", ".PA", ".AS", ".BR", ".LS", ".NS", ".BO",
               ".KS", ".KQ", ".US")


def convert_to_yfinance(raw_code: str, exchange: str = "", market: str = "") -> str:
    """将原始代码转换为 yfinance 格式。"""
    if not raw_code or pd.isna(raw_code):
        return ""
    code = str(raw_code).strip().upper()

    # 期货：已经带 =F
    if code.endswith("=F"):
        return code

    # 已带 yfinance 后缀
    if any(code.endswith(s) for s in YF_SUFFIXES):
        return code

    # A 股
    if market == "A":
        pure = code.zfill(6)
        if pure.startswith(("6", "9")):
            return f"{pure}.SS"
        if pure.startswith(("0", "3")):
            return f"{pure}.SZ"
        if pure.startswith(("4", "8")):
            return f"{pure}.BJ"

    # 港股
    if market == "HK":
        try:
            # 港股代码是 5 位数字，如 "00700"、"00981"
            # yfinance 要求：去掉前导零后补 4 位，加 .HK
            # 例: "00700" -> 700 -> "0700" -> "0700.HK"
            #     "09988" -> 9988 -> "9988" -> "9988.HK"
            pure = str(int(code))
            # 只保留 4 位以内（衍生品代码可能很长）
            if len(pure) <= 4:
                return f"{pure.zfill(4)}.HK"
            else:
                return None   # 衍生品直接跳过
        except ValueError:
            return None

    exch = str(exchange).strip().upper()
    if exch in US_EXCHANGES:
        return code
    if exch in EXCHANGE_SUFFIX_MAP:
        return f"{code}{EXCHANGE_SUFFIX_MAP[exch]}"

    return code


# ============================================================
# 数据源 1：HuggingFace 全球股票数据库
# ============================================================

def fetch_huggingface_tickers() -> pd.DataFrame:
    """
    从 HuggingFace 下载 free-global-stock-ticker-database 的 tickers.csv。
    包含 54,037 条股票和 ETF 数据。
    """
    url = (
        "https://huggingface.co/datasets/adanosorg/"
        "free-global-stock-ticker-database/resolve/main/tickers.csv"
    )

    try:
        print(f"  正在下载: {url}")
        response = requests.get(url, timeout=120)
        response.raise_for_status()

        df = pd.read_csv(io.StringIO(response.text), dtype=str)
        print(f"  [OK] 下载成功，共 {len(df)} 条数据")
        print(f"  原始列名: {list(df.columns)[:10]}")

        # 统一列名转为小写
        df.columns = [c.lower().strip() for c in df.columns]
        return df

    except Exception as e:
        print(f"  [失败] HuggingFace: {e}")
        return pd.DataFrame()


# ============================================================
# 数据源 2：GitHub open-stock-data（CN/HK/US 交易所）
# ============================================================

def fetch_open_stock_data() -> pd.DataFrame:
    """
    从 GitHub irachex/open-stock-data 下载各交易所代码列表。
    仓库每日更新，文件路径稳定。
    每个 CSV 列: code, region, name, exchange, type
    """
    base = "https://raw.githubusercontent.com/irachex/open-stock-data/main/symbols/"
    files = {
        "NASDAQ.csv": "NASDAQ",
        "NYSE.csv": "NYSE",
        "AMEX.csv": "AMEX",
        "HKEX.csv": "HKEX",
        "SSE.csv": "SSE",
        "SZSE.csv": "SZSE",
        "BSE.csv": "BSE_CN",
    }

    frames = []
    for fname, exch in files.items():
        url = base + fname
        try:
            df = pd.read_csv(url, dtype=str)
            if "code" in df.columns and "name" in df.columns:
                sub = df[["code", "name"]].copy()
                sub.columns = ["symbol", "name"]
                sub["exchange"] = exch
                sub["type"] = "stock"
                sub["country"] = ""
                sub["currency"] = ""
                sub["market"] = ""
                frames.append(sub)
                print(f"  [OK] {exch}: {len(sub)} 条")
            else:
                print(f"  [跳过] {exch}: 列名不匹配 ({list(df.columns)[:5]})")
        except Exception as e:
            print(f"  [跳过] {exch}: {e}")

    if frames:
        return pd.concat(frames, ignore_index=True)
    return pd.DataFrame()


# ============================================================
# 数据源 3：期货（硬编码主流品种）
# ============================================================

def get_futures_instruments() -> pd.DataFrame:
    """硬编码主流期货合约。yfinance 用 =F 后缀表示连续合约。"""
    futures = [
        # 贵金属
        ("GC=F", "Gold Futures", "COMEX", "USD"),
        ("SI=F", "Silver Futures", "COMEX", "USD"),
        ("PL=F", "Platinum Futures", "NYMEX", "USD"),
        ("PA=F", "Palladium Futures", "NYMEX", "USD"),
        ("HG=F", "Copper Futures", "COMEX", "USD"),
        # 能源
        ("CL=F", "WTI Crude Oil Futures", "NYMEX", "USD"),
        ("BZ=F", "Brent Crude Oil Futures", "NYMEX", "USD"),
        ("NG=F", "Natural Gas Futures", "NYMEX", "USD"),
        ("HO=F", "Heating Oil Futures", "NYMEX", "USD"),
        ("RB=F", "RBOB Gasoline Futures", "NYMEX", "USD"),
        # 农产品
        ("ZC=F", "Corn Futures", "CBOT", "USD"),
        ("ZS=F", "Soybean Futures", "CBOT", "USD"),
        ("ZW=F", "Wheat Futures", "CBOT", "USD"),
        ("ZM=F", "Soybean Meal Futures", "CBOT", "USD"),
        ("ZL=F", "Soybean Oil Futures", "CBOT", "USD"),
        ("KC=F", "Coffee Futures", "ICE", "USD"),
        ("SB=F", "Sugar Futures", "ICE", "USD"),
        ("CC=F", "Cocoa Futures", "ICE", "USD"),
        ("CT=F", "Cotton Futures", "ICE", "USD"),
        # 利率/债券期货
        ("ZN=F", "10-Year T-Note Futures", "CBOT", "USD"),
        ("ZB=F", "30-Year T-Bond Futures", "CBOT", "USD"),
        ("ZF=F", "5-Year T-Note Futures", "CBOT", "USD"),
        ("ZT=F", "2-Year T-Note Futures", "CBOT", "USD"),
        # 股指期货
        ("ES=F", "E-mini S&P 500 Futures", "CME", "USD"),
        ("NQ=F", "E-mini Nasdaq-100 Futures", "CME", "USD"),
        ("YM=F", "E-mini Dow Futures", "CBOT", "USD"),
        ("RTY=F", "E-mini Russell 2000 Futures", "CME", "USD"),
    ]
    rows = [
        {
            "symbol": sym, "name": name, "exchange": exch,
            "type": "futures", "country": "US", "currency": curr,
            "market": "",
        }
        for sym, name, exch, curr in futures
    ]
    return pd.DataFrame(rows)


# ============================================================
# 数据源 4：债券/利率指数
# ============================================================

def get_bond_instruments() -> pd.DataFrame:
    """硬编码常用债券收益率指数和债券 ETF。"""
    rows = []

    # 美国国债收益率指数
    for sym, name, exch, typ in [
        ("^IRX", "13-Week Treasury Yield", "CBOE", "bond_index"),
        ("^FVX", "5-Year Treasury Yield", "CBOE", "bond_index"),
        ("^TNX", "10-Year Treasury Yield", "CBOE", "bond_index"),
        ("^TYX", "30-Year Treasury Yield", "CBOE", "bond_index"),
    ]:
        rows.append({
            "symbol": sym, "name": name, "exchange": exch,
            "type": typ, "country": "US", "currency": "USD", "market": "",
        })

    # 主流债券 ETF
    for sym, name, exch in [
        ("TLT", "iShares 20+ Year Treasury Bond ETF", "NASDAQ"),
        ("IEF", "iShares 7-10 Year Treasury Bond ETF", "NASDAQ"),
        ("SHY", "iShares 1-3 Year Treasury Bond ETF", "NASDAQ"),
        ("LQD", "iShares iBoxx Investment Grade Corporate Bond ETF", "NYSE"),
        ("HYG", "iShares iBoxx High Yield Corporate Bond ETF", "NYSE"),
        ("JNK", "SPDR Bloomberg High Yield Bond ETF", "NYSE"),
        ("AGG", "iShares Core U.S. Aggregate Bond ETF", "NYSE"),
        ("BND", "Vanguard Total Bond Market ETF", "NASDAQ"),
        ("TIP", "iShares TIPS Bond ETF", "NYSE"),
        ("MUB", "iShares National Muni Bond ETF", "NYSE"),
        ("EMB", "iShares J.P. Morgan USD Emerging Markets Bond ETF", "NASDAQ"),
        ("BNDX", "Vanguard Total International Bond ETF", "NASDAQ"),
    ]:
        rows.append({
            "symbol": sym, "name": name, "exchange": exch,
            "type": "bond_etf", "country": "US", "currency": "USD", "market": "",
        })

    return pd.DataFrame(rows)


# ============================================================
# 数据源 5：A 股 + 港股（可选，akshare）
# ============================================================

def fetch_a_hk_shares() -> pd.DataFrame:
    """尝试用 akshare 获取 A 股和港股列表。失败则跳过。"""
    try:
        import akshare as ak
    except ImportError:
        print("  [跳过] akshare 未安装，A股/港股将不包含在代码库中")
        return pd.DataFrame()

    frames = []

    # A 股
    try:
        df = ak.stock_info_a_code_name()
        df = df.iloc[:, :2].copy()
        df.columns = ["symbol", "name"]
        df["exchange"] = "SSE"
        df["type"] = "stock"
        df["country"] = "CN"
        df["currency"] = "CNY"
        df["market"] = "A"
        frames.append(df)
        print(f"  [OK] A股: {len(df)} 条")
    except Exception as e:
        print(f"  [跳过] A股: {e}")

    # 港股
    try:
        df_hk = ak.stock_hk_spot_em()
        if "代码" in df_hk.columns and "名称" in df_hk.columns:
            df_hk = df_hk[["代码", "名称"]].copy()
        else:
            df_hk = df_hk.iloc[:, 1:3].copy()
        df_hk.columns = ["symbol", "name"]
        df_hk["exchange"] = "HKEX"
        df_hk["type"] = "stock"
        df_hk["country"] = "HK"
        df_hk["currency"] = "HKD"
        df_hk["market"] = "HK"
        frames.append(df_hk)
        print(f"  [OK] 港股: {len(df_hk)} 条")
    except Exception as e:
        print(f"  [跳过] 港股: {e}")

    if frames:
        return pd.concat(frames, ignore_index=True)
    return pd.DataFrame()


# ============================================================
# 列名适配
# ============================================================

def adapt_columns(df: pd.DataFrame, source_name: str) -> pd.DataFrame:
    """将不同数据源的列名统一为 symbol, name, exchange, type, country, currency, market。"""
    if df.empty:
        return df

    # 每个目标列名只映射第一个匹配的原始列，避免重名
    target_cols = ["symbol", "name", "exchange", "type", "country", "currency", "market"]
    col_aliases = {
        "symbol": ["symbol", "ticker", "code", "stock code", "isin"],
        "name": ["name", "company_name", "short_name", "long_name",
                 "company", "company name", "security name"],
        "exchange": ["exchange", "exch"],
        "type": ["type", "quote_type", "instrument_type", "asset_type"],
        "country": ["country", "region"],
        "currency": ["currency", "curr"],
        "market": ["market"],
    }

    rename_map = {}
    used_targets = set()

    for c in df.columns:
        cl = str(c).lower().strip()
        for target in target_cols:
            if target in used_targets:
                continue
            if cl in col_aliases[target]:
                rename_map[c] = target
                used_targets.add(target)
                break

    df = df.rename(columns=rename_map)

    # 如果重命名后仍然有重复列名（罕见情况），只保留第一个
    if df.columns.duplicated().any():
        df = df.loc[:, ~df.columns.duplicated()]

    # 确保必要列存在
    for col, default in [
        ("symbol", ""),
        ("name", ""),
        ("exchange", ""),
        ("type", "stock"),
        ("country", ""),
        ("currency", ""),
        ("market", ""),
    ]:
        if col not in df.columns:
            df[col] = default

    # 只保留目标列（按标准顺序）
    df = df[target_cols].copy()

    return df

# ============================================================
# 主流程
# ============================================================

def main():
    print("=" * 60)
    print("构建全局金融工具代码库")
    print("=" * 60)

    all_frames = []

    # ---- 1. HuggingFace 全球股票数据库 ----
    print("\n[1/5] 拉取 HuggingFace 全球股票数据库...")
    df1 = fetch_huggingface_tickers()
    if not df1.empty:
        df1 = adapt_columns(df1, "huggingface")
        all_frames.append(df1)

    # ---- 2. GitHub open-stock-data ----
    print("\n[2/5] 拉取 GitHub open-stock-data (CN/HK/US)...")
    df2 = fetch_open_stock_data()
    if not df2.empty:
        df2 = adapt_columns(df2, "open-stock-data")
        all_frames.append(df2)

    # ---- 3. 期货 ----
    print("\n[3/5] 加载期货品种（硬编码）...")
    df3 = get_futures_instruments()
    print(f"  [OK] 期货: {len(df3)} 条")
    all_frames.append(df3)

    # ---- 4. 债券 ----
    print("\n[4/5] 加载债券/利率品种...")
    df4 = get_bond_instruments()
    print(f"  [OK] 债券/利率: {len(df4)} 条")
    all_frames.append(df4)

    # ---- 5. A股 + 港股（可选） ----
    print("\n[5/5] 拉取 A股 + 港股（可选）...")
    df5 = fetch_a_hk_shares()
    if not df5.empty:
        df5 = adapt_columns(df5, "akshare")
        all_frames.append(df5)

    if not all_frames:
        print("\n[错误] 所有数据源均失败，无法生成文件。")
        sys.exit(1)

    # ---- 合并 ----
        print("\n" + "=" * 60)
    print("合并与清洗...")

    # 保险：确保每个 DataFrame 的列名唯一
    cleaned_frames = []
    for i, df in enumerate(all_frames):
        if df.columns.duplicated().any():
            print(f"  [警告] 第 {i+1} 个数据源有重复列名，已自动去重")
            df = df.loc[:, ~df.columns.duplicated()]
        cleaned_frames.append(df)

    master = pd.concat(cleaned_frames, ignore_index=True)
    
    # 确保必要列存在
    for col in ["symbol", "name", "exchange", "type", "country", "currency", "market"]:
        if col not in master.columns:
            master[col] = ""

    # 清洗 symbol：去空格、转大写
    master["symbol"] = master["symbol"].astype(str).str.strip().str.upper()
    master = master[master["symbol"].astype(bool)].copy()

    # 去重（按 symbol 保留第一条）
    before = len(master)
    master = master.drop_duplicates(subset=["symbol"], keep="first")
    print(f"  去重: {before} -> {len(master)}")

    # ---- 转换 yfinance 代码 ----
    print("  转换 yfinance 代码...")
    master["yf_symbol"] = master.apply(
        lambda r: convert_to_yfinance(
            r["symbol"], r.get("exchange", ""), r.get("market", "")
        ),
        axis=1,
    )

    # 过滤掉 yf_symbol 为空的
    master = master[master["yf_symbol"].astype(bool)].copy()

    # ---- 整理列顺序 ----
    final_cols = ["symbol", "name", "exchange", "type", "yf_symbol", "country", "currency"]
    for c in final_cols:
        if c not in master.columns:
            master[c] = ""
    master = master[final_cols]

    # ---- 按类型排序 ----
    type_order = {
        "stock": 0, "etf": 1, "futures": 2,
        "bond_index": 3, "bond_etf": 4,
    }
    master["_sort"] = master["type"].map(type_order).fillna(99)
    master = master.sort_values(["_sort", "symbol"]).drop(columns=["_sort"])

    # ---- 保存 ----
    master.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

    print(f"\n[完成] 已生成: {OUTPUT_FILE}")
    print(f"  总条数: {len(master)}")

    print(f"\n  按类型统计:")
    print(master["type"].value_counts().to_string())

    print(f"\n  按交易所统计（前 15）:")
    print(master["exchange"].value_counts().head(15).to_string())

    print("\n  示例数据:")
    print(master.head(15).to_string(index=False))


if __name__ == "__main__":
    main()