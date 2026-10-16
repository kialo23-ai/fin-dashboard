"""
给主流金融工具补充中文别名。
运行一次即可，可重复执行（自动去重覆盖）。
"""

import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "data" / "instrument_master.csv"


# ---------- 别名表 ----------
# 格式: ("yf_symbol", "中文名 英文名")
ALIASES = {
    # ===== A 股 =====
    "600519.SS": "贵州茅台 Kweichow Moutai",
    "601899.SS": "紫金矿业 Zijin Mining",
    "600036.SS": "招商银行 China Merchants Bank",
    "601318.SS": "中国平安 Ping An Insurance",
    "601398.SS": "工商银行 ICBC",
    "601288.SS": "农业银行 ABC",
    "601988.SS": "中国银行 Bank of China",
    "601939.SS": "建设银行 CCB",
    "600030.SS": "中信证券 CITIC Securities",
    "600887.SS": "伊利股份 Yili",
    "600900.SS": "长江电力 Yangtze Power",
    "601012.SS": "隆基绿能 LONGi",
    "600276.SS": "恒瑞医药 Hengrui Pharma",
    "600585.SS": "海螺水泥 Conch Cement",
    "601888.SS": "中国中免 China Tourism",
    "600309.SS": "万华化学 Wanhua Chemical",
    "601166.SS": "兴业银行 Industrial Bank",
    "600028.SS": "中国石化 Sinopec",
    "601857.SS": "中国石油 PetroChina",
    "601088.SS": "中国神华 China Shenhua",
    "600050.SS": "中国联通 China Unicom",
    "601728.SS": "中国电信 China Telecom",
    "600941.SS": "中国移动 China Mobile",
    "601633.SS": "长城汽车 Great Wall Motor",
    "600104.SS": "上汽集团 SAIC Motor",
    "600690.SS": "海尔智家 Haier Smart Home",
    "601668.SS": "中国建筑 China State Construction",
    "601628.SS": "中国人寿 China Life",
    "601601.SS": "中国太保 CPIC",
    "600048.SS": "保利发展 Poly Developments",
    "000001.SZ": "平安银行 Ping An Bank",
    "000002.SZ": "万科A Vanke",
    "000333.SZ": "美的集团 Midea Group",
    "000651.SZ": "格力电器 Gree Electric",
    "000858.SZ": "五粮液 Wuliangye",
    "000568.SZ": "泸州老窖 Luzhou Laojiao",
    "000596.SZ": "古井贡酒 Gujing Distillery",
    "002415.SZ": "海康威视 Hikvision",
    "002594.SZ": "比亚迪 BYD",
    "002304.SZ": "洋河股份 Yanghe",
    "002352.SZ": "顺丰控股 SF Holding",
    "002142.SZ": "宁波银行 Bank of Ningbo",
    "300750.SZ": "宁德时代 CATL",
    "300059.SZ": "东方财富 East Money",
    "300760.SZ": "迈瑞医疗 Mindray",
    "300124.SZ": "汇川技术 Inovance",
    "300015.SZ": "爱尔眼科 Aier Eye Hospital",
    "300274.SZ": "阳光电源 Sungrow Power",

    # ===== 港股 =====
    "0700.HK": "腾讯控股 Tencent Holdings",
    "9988.HK": "阿里巴巴 Alibaba Group",
    "3690.HK": "美团 Meituan",
    "1810.HK": "小米集团 Xiaomi Corporation",
    "9618.HK": "京东集团 JD.com",
    "9888.HK": "百度集团 Baidu",
    "9999.HK": "网易 NetEase",
    "1024.HK": "快手 Kuaishou",
    "0981.HK": "中芯国际 SMIC",
    "2382.HK": "舜宇光学 Sunny Optical",
    "0388.HK": "香港交易所 HKEX",
    "0939.HK": "建设银行 CCB",
    "1398.HK": "工商银行 ICBC",
    "3988.HK": "中国银行 Bank of China",
    "1288.HK": "农业银行 ABC",
    "2318.HK": "中国平安 Ping An Insurance",
    "2628.HK": "中国人寿 China Life",
    "1299.HK": "友邦保险 AIA Group",
    "0005.HK": "汇丰控股 HSBC Holdings",
    "2020.HK": "安踏体育 ANTA Sports",
    "2331.HK": "李宁 Li Ning",
    "6862.HK": "海底捞 Haidilao",
    "1093.HK": "石药集团 CSPC Pharma",
    "1177.HK": "中国生物制药 Sino Biopharm",
    "0857.HK": "中国石油 PetroChina",
    "0386.HK": "中国石化 Sinopec",
    "0883.HK": "中国海洋石油 CNOOC",
    "1088.HK": "中国神华 China Shenhua",
    "2899.HK": "紫金矿业 Zijin Mining",
    "1211.HK": "比亚迪股份 BYD",
    "0941.HK": "中国移动 China Mobile",
    "0762.HK": "中国联通 China Unicom",
    "0728.HK": "中国电信 China Telecom",
    "2015.HK": "理想汽车 Li Auto",
    "9866.HK": "蔚来 NIO",
    "9868.HK": "小鹏汽车 XPeng",

    # ===== 美股 & 中概股 =====
    "AAPL": "苹果 Apple",
    "MSFT": "微软 Microsoft",
    "GOOGL": "谷歌 Google (Class A)",
    "GOOG": "谷歌 Google (Class C)",
    "AMZN": "亚马逊 Amazon",
    "META": "Meta 脸书 Facebook",
    "TSLA": "特斯拉 Tesla",
    "NVDA": "英伟达 NVIDIA",
    "AMD": "AMD 超威半导体",
    "INTC": "英特尔 Intel",
    "NFLX": "奈飞 Netflix",
    "ORCL": "甲骨文 Oracle",
    "CRM": "Salesforce 赛富时",
    "ADBE": "Adobe 奥多比",
    "IBM": "IBM 国际商业机器",
    "QCOM": "高通 Qualcomm",
    "AVGO": "博通 Broadcom",
    "TSM": "台积电 TSMC",
    "JPM": "摩根大通 JPMorgan Chase",
    "BAC": "美国银行 Bank of America",
    "WFC": "富国银行 Wells Fargo",
    "GS": "高盛 Goldman Sachs",
    "MS": "摩根士丹利 Morgan Stanley",
    "BRK-B": "伯克希尔哈撒韦 Berkshire Hathaway B",
    "V": "Visa 维萨",
    "MA": "万事达 Mastercard",
    "JNJ": "强生 Johnson & Johnson",
    "PFE": "辉瑞 Pfizer",
    "MRNA": "莫德纳 Moderna",
    "XOM": "埃克森美孚 ExxonMobil",
    "CVX": "雪佛龙 Chevron",
    "WMT": "沃尔玛 Walmart",
    "COST": "好市多 Costco",
    "KO": "可口可乐 Coca-Cola",
    "PEP": "百事可乐 PepsiCo",
    "MCD": "麦当劳 McDonald's",
    "SBUX": "星巴克 Starbucks",
    "NKE": "耐克 Nike",
    "DIS": "迪士尼 Disney",
    "BA": "波音 Boeing",
    "CAT": "卡特彼勒 Caterpillar",
    "F": "福特 Ford",
    "GM": "通用汽车 General Motors",
    # 中概股
    "BABA": "阿里巴巴 Alibaba Group ADR",
    "JD": "京东 JD.com ADR",
    "PDD": "拼多多 PDD Holdings",
    "BIDU": "百度 Baidu ADR",
    "NTES": "网易 NetEase ADR",
    "NIO": "蔚来 NIO ADR",
    "XPEV": "小鹏汽车 XPeng ADR",
    "LI": "理想汽车 Li Auto ADR",
    "TCOM": "携程 Trip.com ADR",
    "BILI": "哔哩哔哩 Bilibili ADR",
    "IQ": "爱奇艺 iQIYI ADR",
    "EDU": "新东方 New Oriental Education",
    "TAL": "好未来 TAL Education",
    "YUMC": "百胜中国 Yum China Holdings",

    # ===== 期货 =====
    "GC=F": "黄金 Gold Futures",
    "SI=F": "白银 Silver Futures",
    "PL=F": "铂金 Platinum Futures",
    "PA=F": "钯金 Palladium Futures",
    "HG=F": "铜 Copper Futures",
    "CL=F": "WTI原油 WTI Crude Oil Futures",
    "BZ=F": "布伦特原油 Brent Crude Oil Futures",
    "NG=F": "天然气 Natural Gas Futures",
    "HO=F": "取暖油 Heating Oil Futures",
    "RB=F": "汽油 RBOB Gasoline Futures",
    "ZC=F": "玉米 Corn Futures",
    "ZS=F": "大豆 Soybean Futures",
    "ZW=F": "小麦 Wheat Futures",
    "KC=F": "咖啡 Coffee Futures",
    "SB=F": "糖 Sugar Futures",
    "CC=F": "可可 Cocoa Futures",
    "CT=F": "棉花 Cotton Futures",
    "ZN=F": "10年期美债期货 10-Year T-Note Futures",
    "ZB=F": "30年期美债期货 30-Year T-Bond Futures",
    "ES=F": "标普500期货 E-mini S&P 500 Futures",
    "NQ=F": "纳斯达克100期货 E-mini Nasdaq-100 Futures",
    "YM=F": "道指期货 E-mini Dow Futures",
    "RTY=F": "罗素2000期货 E-mini Russell 2000 Futures",

    # ===== 债券 =====
    "TLT": "20年期美债ETF iShares 20+ Year Treasury Bond ETF",
    "IEF": "7-10年期美债ETF iShares 7-10 Year Treasury Bond ETF",
    "SHY": "1-3年期美债ETF iShares 1-3 Year Treasury Bond ETF",
    "LQD": "投资级公司债ETF iShares Investment Grade Corporate Bond ETF",
    "HYG": "高收益公司债ETF iShares High Yield Corporate Bond ETF",
    "JNK": "高收益债券ETF SPDR Bloomberg High Yield Bond ETF",
    "AGG": "综合债券ETF iShares Core U.S. Aggregate Bond ETF",
    "BND": "全债市ETF Vanguard Total Bond Market ETF",
    "TIP": "通胀保值债券ETF iShares TIPS Bond ETF",
    "EMB": "新兴市场债券ETF iShares J.P. Morgan USD Emerging Markets Bond ETF",
    "^TNX": "10年期美债收益率 10-Year Treasury Yield",
    "^TYX": "30年期美债收益率 30-Year Treasury Yield",
    "^FVX": "5年期美债收益率 5-Year Treasury Yield",
    "^IRX": "13周美债收益率 13-Week Treasury Yield",
}


def main():
    if not CSV_PATH.exists():
        print(f"[错误] 文件不存在: {CSV_PATH}")
        return

    df = pd.read_csv(CSV_PATH, dtype=str)
    print(f"原条数: {len(df)}")

    # 1. 覆盖已有记录的名称
    updated = 0
    for yf_symbol, new_name in ALIASES.items():
        mask = df["yf_symbol"] == yf_symbol
        if mask.any():
            df.loc[mask, "name"] = new_name
            updated += 1
    print(f"已更新名称: {updated} 条")

    # 2. 补充缺失的记录（主要为 A 股）
    existing_symbols = set(df["yf_symbol"].dropna())
    new_rows = []

    for yf_symbol, name in ALIASES.items():
        if yf_symbol in existing_symbols:
            continue

        # 解析出基础信息
        if yf_symbol.endswith(".SS"):
            row = {"symbol": yf_symbol.replace(".SS", ""), "name": name,
                   "exchange": "SSE", "type": "stock", "yf_symbol": yf_symbol,
                   "country": "CN", "currency": "CNY"}
        elif yf_symbol.endswith(".SZ"):
            row = {"symbol": yf_symbol.replace(".SZ", ""), "name": name,
                   "exchange": "SZSE", "type": "stock", "yf_symbol": yf_symbol,
                   "country": "CN", "currency": "CNY"}
        elif yf_symbol.endswith(".HK"):
            row = {"symbol": yf_symbol.replace(".HK", ""), "name": name,
                   "exchange": "HKEX", "type": "stock", "yf_symbol": yf_symbol,
                   "country": "HK", "currency": "HKD"}
        elif yf_symbol.endswith("=F"):
            row = {"symbol": yf_symbol, "name": name,
                   "exchange": "COMEX/NYMEX/CBOT/CME", "type": "futures",
                   "yf_symbol": yf_symbol, "country": "US", "currency": "USD"}
        elif yf_symbol.startswith("^"):
            row = {"symbol": yf_symbol, "name": name,
                   "exchange": "CBOE", "type": "bond_index",
                   "yf_symbol": yf_symbol, "country": "US", "currency": "USD"}
        elif yf_symbol in ("TLT", "IEF", "SHY", "LQD", "HYG", "JNK",
                            "AGG", "BND", "TIP", "EMB"):
            row = {"symbol": yf_symbol, "name": name,
                   "exchange": "NYSE/NASDAQ", "type": "bond_etf",
                   "yf_symbol": yf_symbol, "country": "US", "currency": "USD"}
        else:
            # 美股
            row = {"symbol": yf_symbol, "name": name,
                   "exchange": "NASDAQ/NYSE", "type": "stock",
                   "yf_symbol": yf_symbol, "country": "US", "currency": "USD"}

        new_rows.append(row)

    print(f"补充新记录: {len(new_rows)} 条")
    if new_rows:
        new_df = pd.DataFrame(new_rows)
        df = pd.concat([df, new_df], ignore_index=True)

    # 3. 按 yf_symbol 去重
    df = df.drop_duplicates(subset=["yf_symbol"], keep="first")
    print(f"最终条数: {len(df)}")

    df.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")

    # 4. 验证
    print()
    print("--- 验证 ---")
    for kw in ["茅台", "阿里", "腾讯", "苹果", "黄金", "贵州", "紫金"]:
        hits = df[
            df["name"].str.contains(kw, case=False, na=False)
            | df["symbol"].str.contains(kw, case=False, na=False)
        ]
        print(f"搜索 '{kw}': {len(hits)} 条")
        if not hits.empty:
            print(hits[["symbol", "name", "yf_symbol"]].head(3).to_string(index=False))
        print()


if __name__ == "__main__":
    main()