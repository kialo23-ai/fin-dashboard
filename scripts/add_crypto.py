"""
补充主流加密货币到 instrument_master.csv。
运行一次即可，可重复执行（自动去重覆盖）。
"""

import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "data" / "instrument_master.csv"

# ---------- 主流加密货币列表 (yfinance代码, 中文名, 英文名) ----------
CRYPTO_LIST = [
    # 主流币
    ("BTC-USD", "比特币", "Bitcoin"),
    ("ETH-USD", "以太坊", "Ethereum"),
    ("BNB-USD", "币安币", "Binance Coin"),
    ("SOL-USD", "Solana", "Solana"),
    ("XRP-USD", "瑞波币", "Ripple"),
    ("ADA-USD", "艾达币", "Cardano"),
    ("DOGE-USD", "狗狗币", "Dogecoin"),
    ("DOT-USD", "波卡", "Polkadot"),
    ("MATIC-USD", "马蹄", "Polygon"),
    ("LTC-USD", "莱特币", "Litecoin"),
    # 其他知名币种
    ("AVAX-USD", "雪崩", "Avalanche"),
    ("LINK-USD", "链环", "Chainlink"),
    ("ATOM-USD", "宇宙", "Cosmos"),
    ("XLM-USD", "恒星币", "Stellar"),
    ("BCH-USD", "比特现金", "Bitcoin Cash"),
    ("TRX-USD", "波场", "TRON"),
    ("ETC-USD", "以太经典", "Ethereum Classic"),
    ("FIL-USD", "文件币", "Filecoin"),
    ("NEAR-USD", "Near", "Near Protocol"),
    ("ALGO-USD", "阿尔戈兰", "Algorand"),
    # 热门/Meme币
    ("SHIB-USD", "柴犬币", "Shiba Inu"),
    ("PEPE-USD", "佩佩币", "Pepe"),
    ("ARB-USD", "Arbitrum", "Arbitrum"),
    ("OP-USD", "Optimism", "Optimism"),
    ("SUI-USD", "Sui", "Sui"),
    ("APT-USD", "Aptos", "Aptos"),
    ("INJ-USD", "Injective", "Injective"),
    ("RUNE-USD", "Thorchain", "THORChain"),
    ("ICP-USD", "互联网计算机", "Internet Computer"),
    ("THETA-USD", "Theta", "Theta Network"),
]


def main():
    if not CSV_PATH.exists():
        print(f"[错误] CSV 文件不存在: {CSV_PATH}")
        return

    existing = pd.read_csv(CSV_PATH, dtype=str)
    print(f"现有条数: {len(existing)}")

    # 构建加密货币记录
    new_rows = []
    for yf_symbol, cn_name, en_name in CRYPTO_LIST:
        name = f"{cn_name} {en_name}" if cn_name else en_name
        new_rows.append({
            "symbol": yf_symbol.replace("-USD", ""),   # 如 BTC
            "name": name,
            "exchange": "CRYPTO",
            "type": "crypto",
            "yf_symbol": yf_symbol,                    # 如 BTC-USD
            "country": "GLOBAL",
            "currency": "USD",
        })

    new_df = pd.DataFrame(new_rows)
    print(f"准备补充加密货币: {len(new_df)} 条")

    # 合并并去重（保留新数据覆盖旧数据）
    combined = pd.concat([existing, new_df], ignore_index=True)
    combined = combined.drop_duplicates(subset=["yf_symbol"], keep="last")
    print(f"去重后: {len(combined)}")

    combined.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")

    # 验证
    print()
    print("--- 验证 ---")
    for kw in ["比特币", "以太坊", "BTC", "狗狗币", "ETH"]:
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