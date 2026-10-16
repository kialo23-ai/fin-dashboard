"""
补充主流港股和美股中概股到 instrument_master.csv。
这些是 open-stock-data 的 HKEX.csv 没覆盖到的主力品种。
运行一次即可，可以重复运行（自动去重）。
"""

import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "data" / "instrument_master.csv"

# ---------- 主流港股 ----------
HK_MAINSTREAM = [
    # 科技
    ("0700", "腾讯控股 Tencent Holdings", "0700.HK"),
    ("9988", "阿里巴巴 Alibaba Group", "9988.HK"),
    ("3690", "美团 Meituan", "3690.HK"),
    ("1810", "小米集团 Xiaomi Corporation", "1810.HK"),
    ("9618", "京东集团 JD.com", "9618.HK"),
    ("9888", "百度集团 Baidu", "9888.HK"),
    ("9999", "网易 NetEase", "9999.HK"),
    ("1024", "快手 Kuaishou", "1024.HK"),
    ("0981", "中芯国际 SMIC", "0981.HK"),
    ("2382", "舜宇光学 Sunny Optical", "2382.HK"),
    ("0268", "金蝶国际 Kingdee", "0268.HK"),
    ("2015", "理想汽车 Li Auto", "2015.HK"),
    ("9866", "蔚来 NIO", "9866.HK"),
    ("9868", "小鹏汽车 XPeng", "9868.HK"),
    # 金融
    ("0388", "香港交易所 HKEX", "0388.HK"),
    ("0939", "建设银行 CCB", "0939.HK"),
    ("1398", "工商银行 ICBC", "1398.HK"),
    ("3988", "中国银行 Bank of China", "3988.HK"),
    ("1288", "农业银行 ABC", "1288.HK"),
    ("2318", "中国平安 Ping An Insurance", "2318.HK"),
    ("2628", "中国人寿 China Life", "2628.HK"),
    ("1299", "友邦保险 AIA Group", "1299.HK"),
    ("0005", "汇丰控股 HSBC Holdings", "0005.HK"),
    # 消费
    ("2020", "安踏体育 ANTA Sports", "2020.HK"),
    ("2331", "李宁 Li Ning", "2331.HK"),
    ("1044", "恒安国际 Hengan", "1044.HK"),
    ("0288", "万洲国际 WH Group", "0288.HK"),
    ("6862", "海底捞 Haidilao", "6862.HK"),
    ("1579", "颐海国际 Yihai", "1579.HK"),
    # 医药
    ("1093", "石药集团 CSPC Pharma", "1093.HK"),
    ("1177", "中国生物制药 Sino Biopharm", "1177.HK"),
    ("0867", "康哲药业 China Medical", "0867.HK"),
    # 能源/资源
    ("0857", "中国石油 PetroChina", "0857.HK"),
    ("0386", "中国石化 Sinopec", "0386.HK"),
    ("0883", "中国海洋石油 CNOOC", "0883.HK"),
    ("1088", "中国神华 China Shenhua", "1088.HK"),
    ("2899", "紫金矿业 Zijin Mining", "2899.HK"),
    ("1211", "比亚迪股份 BYD", "1211.HK"),
    # 电信
    ("0941", "中国移动 China Mobile", "0941.HK"),
    ("0762", "中国联通 China Unicom", "0762.HK"),
    ("0728", "中国电信 China Telecom", "0728.HK"),
]

# ---------- 美股中概股（补充常用） ----------
US_CHINA = [
    ("BABA", "Alibaba Group ADR"),
    ("JD", "JD.com ADR"),
    ("PDD", "PDD Holdings"),
    ("BIDU", "Baidu ADR"),
    ("NTES", "NetEase ADR"),
    ("NIO", "NIO Inc ADR"),
    ("XPEV", "XPeng ADR"),
    ("LI", "Li Auto ADR"),
    ("TCOM", "Trip.com ADR"),
    ("BILI", "Bilibili ADR"),
    ("IQ", "iQIYI ADR"),
    ("EDU", "New Oriental Education"),
    ("TAL", "TAL Education Group"),
    ("YUMC", "Yum China Holdings"),
]


def build_rows():
    rows = []
    # 港股
    for code, name, yf in HK_MAINSTREAM:
        rows.append({
            "symbol": code,
            "name": name,
            "exchange": "HKEX",
            "type": "stock",
            "yf_symbol": yf,
            "country": "HK",
            "currency": "HKD",
        })
    # 美股中概
    for sym, name in US_CHINA:
        rows.append({
            "symbol": sym,
            "name": name,
            "exchange": "NASDAQ",
            "type": "stock",
            "yf_symbol": sym,
            "country": "US",
            "currency": "USD",
        })
    return pd.DataFrame(rows)


def main():
    if not CSV_PATH.exists():
        print(f"[错误] CSV 文件不存在: {CSV_PATH}")
        print("请先运行 scripts/build_instrument_master.py")
        return

    existing = pd.read_csv(CSV_PATH, dtype=str)
    print(f"现有条数: {len(existing)}")

    new_rows = build_rows()
    print(f"准备补充: {len(new_rows)} 条")

    combined = pd.concat([existing, new_rows], ignore_index=True)

    # 去重：优先保留新增的（覆盖原有错误记录）
    # 用 keep='last' 让新数据覆盖旧数据
    combined = combined.drop_duplicates(subset=["yf_symbol"], keep="last")
    print(f"去重后: {len(combined)}")

    combined.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")

    # 验证
    print()
    print("--- 验证 ---")
    for kw in ["腾讯", "Tencent", "0700", "阿里", "Alibaba"]:
        hits = combined[
            combined["name"].str.contains(kw, case=False, na=False)
            | combined["symbol"].str.contains(kw, case=False, na=False)
        ]
        print(f"搜索 '{kw}': {len(hits)} 条")
        if not hits.empty:
            print(hits[["symbol", "name", "yf_symbol"]].head(2).to_string(index=False))
        print()


if __name__ == "__main__":
    main()