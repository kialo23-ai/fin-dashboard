import io
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio


def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    """DataFrame 转 CSV 字节流"""
    return df.to_csv().encode("utf-8")


def df_to_excel_bytes(sheets: dict) -> bytes:
    """
    将多个DataFrame写入一个Excel文件。
    sheets = {"Sheet名称": df, ...}
    """
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for sheet_name, df in sheets.items():
           # 建议加这一步：清洗非法字符
            safe_name = re.sub(r'[:\\/?*\[\]]', '_', str(sheet_name))[:31]
            df.to_excel(writer, sheet_name=safe_name, index=True)
    return output.getvalue()


def charts_to_html_bytes(charts: dict) -> bytes:
    """
    将多个Plotly图表拼接为一个HTML文件。
    charts = {"图表标题": go.Figure, ...}
    """
    html_parts = [
        "<html><head><meta charset='utf-8'>",
        "<title>金融指标对比分析报告</title>",
        "<style>body{font-family:Arial,sans-serif;margin:40px;}"
        "h1{color:#1a237e;}h2{color:#283593;border-bottom:2px solid #e8eaf6;padding-bottom:8px;}"
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