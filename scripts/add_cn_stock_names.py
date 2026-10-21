"""
给 A 股（沪/深/北）和港股补充中文名称。
按代码匹配到 instrument_master.csv，给没有中文名的记录加上「中文名 原英文名」。
可重复运行，已有中文名的记录会跳过。
"""

import re
import pandas as pd
import akshare as ak
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "data" / "instrument_master.csv"


# ============================================================
# 工具函数
# ============================================================

def _has_chinese(s) -> bool:
    return bool(re.search(r'[\u4e00-\u9fff]', str(s)))


def _norm_a_code(c) -> str:
    """A 股代码归一化为 6 位数字。"""
    c = str(c).strip()
    c = re.sub(r'^(sh|sz|bj)', '', c, flags=re.IGNORECASE)
    c = re.sub(r'\.(SS|SZ|BJ)$', '', c, flags=re.IGNORECASE)
    return c.zfill(6)


def _norm_hk_code(c) -> str:
    """港股代码归一化为 5 位数字。"""
    c = str(c).strip()
    c = re.sub(r'^hk', '', c, flags=re.IGNORECASE)
    c = re.sub(r'\.HK$', '', c, flags=re.IGNORECASE)
    try:
        return str(int(c)).zfill(5)
    except ValueError:
        return c


def _extract_code_name(df, code_candidates, name_candidates) -> pd.DataFrame:
    """从 akshare 返回的任意 df 中提取 code/cn_name 两列。"""
    if df is None or df.empty:
        return pd.DataFrame(columns=["code", "cn_name"])

    code_col = next((c for c in df.columns if c in code_candidates), None)
    name_col = next((c for c in df.columns if c in name_candidates), None)
    if code_col is None or name_col is None:
        return pd.DataFrame(columns=["code", "cn_name"])

    out = df[[code_col, name_col]].copy()
    out.columns = ["code", "cn_name"]
    return out


# ============================================================
# 数据源拉取
# ============================================================

def fetch_sse() -> pd.DataFrame:
    """上交所 A 股：主板 + 科创板。"""
    results = []
    for sym in ["主板A股", "科创板"]:
        try:
            df = ak.stock_info_sh_name_code(symbol=sym)
            cleaned = _extract_code_name(
                df,
                code_candidates=["证券代码", "A股代码", "代码"],
                name_candidates=["证券简称", "A股简称", "简称", "名称"],
            )
            if not cleaned.empty:
                results.append(cleaned)
                print(f"    [OK] 上交所 {sym}: {len(cleaned)} 条")
        except Exception as e:
            print(f"    [跳过] 上交所 {sym}: {str(e)[:80]}")
    if results:
        df = pd.concat(results, ignore_index=True)
        df["code"] = df["code"].apply(_norm_a_code)
        return df.drop_duplicates(subset=["code"])
    return pd.DataFrame(columns=["code", "cn_name"])


def fetch_szse() -> pd.DataFrame:
    """深交所 A 股。"""
    try:
        df = ak.stock_info_sz_name_code(symbol="A股列表")
        cleaned = _extract_code_name(
            df,
            code_candidates=["A股代码", "证券代码", "代码"],
            name_candidates=["A股简称", "证券简称", "简称", "名称"],
        )
        if not cleaned.empty:
            cleaned["code"] = cleaned["code"].apply(_norm_a_code)
            print(f"    [OK] 深交所: {len(cleaned)} 条")
            return cleaned.drop_duplicates(subset=["code"])
    except Exception as e:
        print(f"    [跳过] 深交所: {str(e)[:80]}")
    return pd.DataFrame(columns=["code", "cn_name"])


def fetch_bse() -> pd.DataFrame:
    """北交所。"""
    try:
        df = ak.stock_info_bj_name_code()
        cleaned = _extract_code_name(
            df,
            code_candidates=["证券代码", "代码"],
            name_candidates=["证券简称", "简称", "名称"],
        )
        if not cleaned.empty:
            cleaned["code"] = cleaned["code"].apply(_norm_a_code)
            print(f"    [OK] 北交所: {len(cleaned)} 条")
            return cleaned.drop_duplicates(subset=["code"])
    except Exception as e:
        print(f"    [跳过] 北交所: {str(e)[:80]}")
    return pd.DataFrame(columns=["code", "cn_name"])


def fetch_hk() -> pd.DataFrame:
    """港股。"""
    try:
        df = ak.stock_hk_spot_em()
        cleaned = _extract_code_name(
            df,
            code_candidates=["代码", "股票代码"],
            name_candidates=["名称", "中文名称", "简称"],
        )
        if not cleaned.empty:
            cleaned["code"] = cleaned["code"].apply(_norm_hk_code)
            print(f"    [OK] 港股: {len(cleaned)} 条")
            return cleaned.drop_duplicates(subset=["code"])
    except Exception as e:
        print(f"    [跳过] 港股: {str(e)[:80]}")
    return pd.DataFrame(columns=["code", "cn_name"])


# ============================================================
# 降级：常见蓝筹股手动清单
# ============================================================

FALLBACK_A = {
    "600519": "贵州茅台", "601899": "紫金矿业", "600036": "招商银行",
    "601318": "中国平安", "000001": "平安银行", "000002": "万科A",
    "000333": "美的集团", "000651": "格力电器", "002594": "比亚迪",
    "300750": "宁德时代", "300059": "东方财富", "600030": "中信证券",
    "601398": "工商银行", "601288": "农业银行", "601988": "中国银行",
    "601939": "建设银行", "601857": "中国石油", "600028": "中国石化",
    "601088": "中国神华", "600900": "长江电力", "601166": "兴业银行",
    "600276": "恒瑞医药", "600887": "伊利股份", "600690": "海尔智家",
    "600585": "海螺水泥", "601012": "隆基绿能", "601888": "中国中免",
    "600309": "万华化学", "600050": "中国联通", "601728": "中国电信",
    "600941": "中国移动", "601628": "中国人寿", "601601": "中国太保",
    "600048": "保利发展", "601633": "长城汽车", "600104": "上汽集团",
    "000858": "五粮液", "000568": "泸州老窖", "002415": "海康威视",
    "002304": "洋河股份", "002352": "顺丰控股", "002142": "宁波银行",
    "300760": "迈瑞医疗", "300124": "汇川技术", "300015": "爱尔眼科",
    "300274": "阳光电源",
}

FALLBACK_HK = {
    "00700": "腾讯控股", "09988": "阿里巴巴", "03690": "美团",
    "01810": "小米集团", "09618": "京东集团", "09888": "百度集团",
    "09999": "网易", "01024": "快手", "00981": "中芯国际",
    "02382": "舜宇光学", "00388": "香港交易所", "00939": "建设银行",
    "01398": "工商银行", "03988": "中国银行", "01288": "农业银行",
    "02318": "中国平安", "02628": "中国人寿", "01299": "友邦保险",
    "00005": "汇丰控股", "02020": "安踏体育", "02331": "李宁",
    "06862": "海底捞", "01093": "石药集团", "01177": "中国生物制药",
    "00857": "中国石油", "00386": "中国石化", "00883": "中国海洋石油",
    "01088": "中国神华", "02899": "紫金矿业", "01211": "比亚迪股份",
    "00941": "中国移动", "00762": "中国联通", "00728": "中国电信",
    "02015": "理想汽车", "09866": "蔚来", "09868": "小鹏汽车",
    "02388": "中银香港",
}


# ============================================================
# 主流程
# ============================================================

def main():
    if not CSV_PATH.exists():
        print(f"[错误] 文件不存在: {CSV_PATH}")
        return

    master = pd.read_csv(CSV_PATH, dtype=str)
    print(f"原始条数: {len(master)}\n")

    print("拉取中文名映射...")
    sse = fetch_sse()
    szse = fetch_szse()
    bse = fetch_bse()
    hk = fetch_hk()

    # 合并 A 股映射（沪 + 深 + 北）
    a_map = {}
    for df in [sse, szse, bse]:
        if not df.empty:
            for _, row in df.iterrows():
                code = row["code"]
                cn = str(row["cn_name"]).strip()
                if code and cn and cn.lower() != "nan":
                    a_map[code] = cn

    hk_map = {}
    if not hk.empty:
        for _, row in hk.iterrows():
            code = row["code"]
            cn = str(row["cn_name"]).strip()
            if code and cn and cn.lower() != "nan":
                hk_map[code] = cn

    # akshare 失败时降级到手动清单
    fallback_a_count = 0
    fallback_hk_count = 0
    if not a_map:
        a_map = dict(FALLBACK_A)
        fallback_a_count = len(a_map)
    if not hk_map:
        hk_map = dict(FALLBACK_HK)
        fallback_hk_count = len(hk_map)

    print(f"\n映射表: A股 {len(a_map)} 条, 港股 {len(hk_map)} 条")
    if fallback_a_count or fallback_hk_count:
        print(f"  降级为手动清单: A股 {fallback_a_count} 条, 港股 {fallback_hk_count} 条")

    # 遍历更新
    print("\n更新名称...")
    updated = 0
    skipped_has_cn = 0
    skipped_not_found = 0

    for idx, row in master.iterrows():
        yf = str(row.get("yf_symbol", "")).upper()
        name = str(row.get("name", ""))

        market = None
        code = None
        if yf.endswith((".SS", ".SZ", ".BJ")):
            market = "A"
            code = _norm_a_code(yf.rsplit(".", 1)[0])
        elif yf.endswith(".HK"):
            market = "HK"
            code = _norm_hk_code(yf.rsplit(".", 1)[0])
        else:
            continue

        if _has_chinese(name):
            skipped_has_cn += 1
            continue

        cn = a_map.get(code) if market == "A" else hk_map.get(code)
        if not cn:
            skipped_not_found += 1
            continue

        master.at[idx, "name"] = f"{cn} {name}".strip()
        updated += 1

    print(f"  新增中文名: {updated} 条")
    print(f"  已有中文跳过: {skipped_has_cn} 条")
    print(f"  未匹配到中文: {skipped_not_found} 条")

    master.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")
    print(f"\n已保存: {CSV_PATH}")

    # 抽样验证
    print("\n抽样验证:")
    for kw in ["茅台", "紫金", "宁德", "腾讯", "美团", "小米", "比亚迪"]:
        hits = master[
            master["name"].str.contains(kw, case=False, na=False)
            | master["symbol"].str.contains(kw, case=False, na=False)
        ]
        print(f"  搜索 '{kw}': {len(hits)} 条")


if __name__ == "__main__":
    main()