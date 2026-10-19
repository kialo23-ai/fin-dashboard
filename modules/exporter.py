import io
import re
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio


def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    """DataFrame 转 CSV 字节流"""
    return df.to_csv().encode("utf-8")


def _sanitize_sheet_name(name: str, used: set) -> str:
    """把 sheet 名清洗成 Excel 合法格式，并保证不重复。"""
    # 1. 转字符串
    name = str(name) if name else "Sheet"
    # 2. 去除 Excel 禁止的字符 : \ / ? * [ ]
    name = re.sub(r'[:\\/?*\[\]]', '_', name)
    # 3. Excel sheet 名上限 31 字符
    name = name[:31]
    # 4. 若为空，用默认值
    if not name.strip():
        name = "Sheet"
    # 5. 去重（加 _2、_3 后缀）
    base = name
    i = 1
    while name in used:
        suffix = f"_{i}"
        name = base[: 31 - len(suffix)] + suffix
        i += 1
    used.add(name)
    return name


def df_to_excel_bytes(sheets: dict) -> bytes:
    """
    将多个 DataFrame 写入一个 Excel 文件。
    sheets = {"Sheet 名称": df, ...}
    """
    output = io.BytesIO()
    used_names = set()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        wrote_any = False
        for sheet_name, df in sheets.items():
            if df is None or df.empty:
                continue
            safe_name = _sanitize_sheet_name(sheet_name, used_names)
            df.to_excel(writer, sheet_name=safe_name, index=True)
            wrote_any = True

        # 兜底：如果一个 sheet 都没写进去（全部为空），
        # 写入一个占位表，否则 openpyxl 保存时抛 IndexError
        if not wrote_any:
            pd.DataFrame({"提示": ["没有可导出的数据"]}).to_excel(
                writer, sheet_name="空数据", index=False
            )

    return output.getvalue()


def charts_to_html_bytes(charts: dict) -> bytes:
    """将多个 Plotly 图表拼接为一个 HTML 文件。"""
    html_parts = [
        "<html><head><meta charset='utf-8'>",
        "<title>金融指标对比分析报告</title>",
        "<style>body{font-family:Arial,sans-serif;margin:40px;}"
        "h1{color:#1a237e;}"
        "h2{color:#283593;border-bottom:2px solid #e8eaf6;padding-bottom:8px;}"
        "</style></head><body>",
        "<h1>金融指标对比分析报告</h1>",
    ]
    for title, fig in charts.items():
        html_parts.append(f"<h2>{title}</h2>")
        html_parts.append(
            pio.to_html(fig, full_html=False, include_plotlyjs="cdn")
        )
    html_parts.append("</body></html>")
    return "".join(html_parts).encode("utf-8")