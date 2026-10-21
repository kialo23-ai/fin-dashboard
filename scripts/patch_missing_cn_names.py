"""
补充所有缺失中文名的 A 股（沪深北）和港股。
多数据源依次尝试：东方财富实时行情 -> 新浪实时行情 -> 深交所接口 -> 手动清单。
只更新 name 为空或纯英文的记录，已有中文的跳过。
可重复运行。
"""

import re
import time
import pandas as pd
import akshare as ak
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "data" / "instrument_master.csv"


def _has_chinese(s) -> bool:
    return bool(re.search(r'[\u4e00-\u9fff]', str(s)))


def _norm_a_code(c) -> str:
    c = str(c).strip()
    c = re.sub(r'^(sh|sz|bj)', '', c, flags=re.IGNORECASE)
    c = re.sub(r'\.(SS|SZ|BJ)$', '', c, flags=re.IGNORECASE)
    return c.zfill(6)


def _norm_hk_code(c) -> str:
    c = str(c).strip()
    c = re.sub(r'^hk', '', c, flags=re.IGNORECASE)
    c = re.sub(r'\.HK$', '', c, flags=re.IGNORECASE)
    try:
        return str(int(c)).zfill(5)
    except ValueError:
        return c


def _extract(df, code_candidates, name_candidates):
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
# A 股：多数据源
# ============================================================

def try_eastmoney() -> pd.DataFrame:
    """东方财富实时行情，一次拿到全A股。"""
    try:
        df = ak.stock_zh_a_spot_em()
        out = _extract(df, ["代码", "证券代码"], ["名称", "证券简称"])
        if not out.empty:
            out["code"] = out["code"].apply(_norm_a_code)
            print(f"    [OK] 东方财富: {len(out)} 条")
            return out.drop_duplicates(subset=["code"])
    except Exception as e:
        print(f"    [跳过] 东方财富: {str(e)[:80]}")
    return pd.DataFrame(columns=["code", "cn_name"])


def try_sina() -> pd.DataFrame:
    """新浪实时行情。"""
    try:
        df = ak.stock_zh_a_spot()
        out = _extract(df, ["代码", "symbol", "code"], ["名称", "name"])
        if not out.empty:
            out["code"] = out["code"].apply(_norm_a_code)
            print(f"    [OK] 新浪: {len(out)} 条")
            return out.drop_duplicates(subset=["code"])
    except Exception as e:
        print(f"    [跳过] 新浪: {str(e)[:80]}")
    return pd.DataFrame(columns=["code", "cn_name"])


def try_szse_retry() -> pd.DataFrame:
    """深交所接口重试（最多3次）。"""
    for attempt in range(3):
        try:
            df = ak.stock_info_sz_name_code(symbol="A股列表")
            out = _extract(df, ["A股代码", "证券代码", "代码"],
                            ["A股简称", "证券简称", "简称", "名称"])
            if not out.empty:
                out["code"] = out["code"].apply(_norm_a_code)
                print(f"    [OK] 深交所(第{attempt+1}次): {len(out)} 条")
                return out.drop_duplicates(subset=["code"])
        except Exception as e:
            print(f"    [重试 {attempt+1}/3] 深交所: {str(e)[:60]}")
            time.sleep(3)
    print("    [失败] 深交所 3 次重试均失败")
    return pd.DataFrame(columns=["code", "cn_name"])


def try_sse() -> pd.DataFrame:
    """上交所（补漏，虽然上次成功了，但可能是部分）。"""
    results = []
    for sym in ["主板A股", "科创板"]:
        try:
            df = ak.stock_info_sh_name_code(symbol=sym)
            out = _extract(df, ["证券代码", "A股代码", "代码"],
                            ["证券简称", "A股简称", "简称", "名称"])
            if not out.empty:
                results.append(out)
        except Exception:
            pass
    if results:
        df = pd.concat(results, ignore_index=True)
        df["code"] = df["code"].apply(_norm_a_code)
        print(f"    [OK] 上交所: {len(df)} 条")
        return df.drop_duplicates(subset=["code"])
    return pd.DataFrame(columns=["code", "cn_name"])


def try_bse() -> pd.DataFrame:
    try:
        df = ak.stock_info_bj_name_code()
        out = _extract(df, ["证券代码", "代码"], ["证券简称", "简称", "名称"])
        if not out.empty:
            out["code"] = out["code"].apply(_norm_a_code)
            print(f"    [OK] 北交所: {len(out)} 条")
            return out.drop_duplicates(subset=["code"])
    except Exception as e:
        print(f"    [跳过] 北交所: {str(e)[:60]}")
    return pd.DataFrame(columns=["code", "cn_name"])


def try_hk() -> pd.DataFrame:
    try:
        df = ak.stock_hk_spot_em()
        out = _extract(df, ["代码", "股票代码"], ["名称", "中文名称", "简称"])
        if not out.empty:
            out["code"] = out["code"].apply(_norm_hk_code)
            print(f"    [OK] 港股: {len(out)} 条")
            return out.drop_duplicates(subset=["code"])
    except Exception as e:
        print(f"    [跳过] 港股: {str(e)[:60]}")
    return pd.DataFrame(columns=["code", "cn_name"])


# ============================================================
# 主流程
# ============================================================

def main():
    if not CSV_PATH.exists():
        print(f"[错误] 文件不存在: {CSV_PATH}")
        return

    master = pd.read_csv(CSV_PATH, dtype=str)
    print(f"原始条数: {len(master)}")

    # 统计缺失
    def is_a(yf):
        return str(yf).upper().endswith((".SS", ".SZ", ".BJ"))

    def is_hk(yf):
        return str(yf).upper().endswith(".HK")

    missing_a = master[
        master["yf_symbol"].apply(is_a)
        & ~master["name"].fillna("").apply(_has_chinese)
    ]
    missing_hk = master[
        master["yf_symbol"].apply(is_hk)
        & ~master["name"].fillna("").apply(_has_chinese)
    ]
    print(f"缺中文名: A股 {len(missing_a)} 条, 港股 {len(missing_hk)} 条\n")

    if len(missing_a) == 0 and len(missing_hk) == 0:
        print("无需补充，退出。")
        return

    # ---- 拉取所有映射 ----
    print("拉取 A 股中文名映射...")
    a_frames = []
    for fn in [try_eastmoney, try_sina, try_sse, try_szse_retry, try_bse]:
        df = fn()
        if not df.empty:
            a_frames.append(df)

    a_map = {}
    for df in a_frames:
        for _, row in df.iterrows():
            code = row["code"]
            cn = str(row["cn_name"]).strip()
            if code and cn and cn.lower() != "nan" and code not in a_map:
                a_map[code] = cn
    print(f"  合并后 A 股映射: {len(a_map)} 条\n")

    print("拉取港股中文名映射...")
    hk_df = try_hk()
    hk_map = {}
    for _, row in hk_df.iterrows():
        code = row["code"]
        cn = str(row["cn_name"]).strip()
        if code and cn and cn.lower() != "nan":
            hk_map[code] = cn
    print(f"  合并后港股映射: {len(hk_map)} 条\n")

    # ---- 更新 ----
    print("更新缺失的中文名...")
    updated_a = 0
    updated_hk = 0

    for idx, row in master.iterrows():
        yf = str(row.get("yf_symbol", "")).upper()
        name = str(row.get("name", ""))
        if _has_chinese(name):
            continue

        if is_a(yf):
            code = _norm_a_code(yf.rsplit(".", 1)[0])
            cn = a_map.get(code)
            if cn:
                master.at[idx, "name"] = f"{cn} {name}".strip()
                updated_a += 1
        elif is_hk(yf):
            code = _norm_hk_code(yf.rsplit(".", 1)[0])
            cn = hk_map.get(code)
            if cn:
                master.at[idx, "name"] = f"{cn} {name}".strip()
                updated_hk += 1

    print(f"  A股补充: {updated_a} 条")
    print(f"  港股补充: {updated_hk} 条")

    # 剩余未补
    still_missing = master[
        (master["yf_symbol"].apply(lambda x: is_a(x) or is_hk(x)))
        & ~master["name"].fillna("").apply(_has_chinese)
    ]
    print(f"  仍缺失中文: {len(still_missing)} 条")
    if 0 < len(still_missing) <= 20:
        print("\n  仍未匹配的代码:")
        print(still_missing[["symbol", "name", "yf_symbol"]].to_string(index=False))

    master.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")
    print(f"\n已保存: {CSV_PATH}")

    # 抽样
    print("\n抽样验证:")
    for kw in ["万科", "美的", "格力", "海康", "东方财富", "宁德", "五粮液", "平安"]:
        hits = master[
            master["name"].str.contains(kw, case=False, na=False)
            | master["symbol"].str.contains(kw, case=False, na=False)
        ]
        print(f"  搜索 '{kw}': {len(hits)} 条")


if __name__ == "__main__":
    main()