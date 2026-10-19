# 金融指标对比分析看板

基于 Streamlit 的金融数据分析工具，支持股票、ETF、期货、债券、加密货币的跨市场指标对比与技术分析。

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.40+-red)
![License](https://img.shields.io/badge/License-MIT-green)

## 功能特性

### 多市场数据覆盖

- **A 股**：上交所、深交所、北交所
- **港股**：港交所
- **美股**：NYSE、NASDAQ、AMEX
- **欧洲**：伦交所、XETRA、Euronext、Borsa Italiana
- **亚太**：东京、韩国、印度、澳大利亚、台湾
- **期货**：COMEX、NYMEX、CBOT、CME、ICE
- **债券**：美债收益率指数、主流债券 ETF
- **加密货币**：BTC、ETH 等主流币种

内置 68,000+ 条金融工具代码库，支持中英文模糊搜索。

### 技术指标

- **趋势类**：SMA、EMA、MACD
- **动量类**：RSI、KDJ（随机指标）
- **波动率**：布林带、ATR
- **成交量**：OBV
- **收益率**：日收益率

### 图表分析

- **归一化价格对比**：多标的走势归一化到基准 100，直观比较相对表现
- **K 线多面板图**：K 线 + 布林带 + 成交量 + MACD + RSI 四面板联动
- **指标对比**：同一指标在多个标的上的横向对比
- **相关性热力图**：多标的收益率相关性矩阵

### 数据导出

- **CSV**：全部原始数据 + 计算后的指标
- **Excel**：按标的分 Sheet 导出，方便二次分析
- **HTML**：交互式报告，可直接分享给他人查看

### 移动端适配

- 响应式布局，自动适配华为 P70 Pro、MediaPad 等设备
- 侧边栏默认折叠，触控目标加大
- 图表高度、字号、边距针对小屏优化
- 一键切换桌面 / 移动端视图

## 快速开始

### 环境要求

- Python 3.11+
- pip

### 安装

```bash
git clone https://github.com/kialo23-ai/fin-dashboard.git
cd fin-dashboard

python3.11 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### 启动应用

```bash
python -m streamlit run app.py
```

浏览器会自动打开 `http://localhost:8501`。

> 仓库已包含预生成的代码库文件 `data/instrument_master.csv`，无需额外步骤。如需更新代码库，见文末「维护代码库」一节。

## 使用说明

### 1. 添加标的到分析队列

侧边栏「🔍 搜索并添加股票」支持三种输入方式：

- **中文名称**：`紫金矿业`、`茅台`、`腾讯`、`比特币`
- **英文名称**：`Apple`、`Tencent`、`Gold`
- **代码**：`AAPL`、`600519`、`0700.HK`、`GC=F`、`BTC-USD`

点击结果行的「➕」加入队列。

### 2. 切换分析视图

主区域分为 5 个 Tab：

| Tab | 内容 |
|-----|------|
| 📊 归一化对比 | 多标的归一化价格走势 |
| 🕯️ K线分析 | 单标的 K 线 + 技术指标多面板 |
| 📉 指标对比 | 同一指标的多标的横向对比 |
| 🔥 相关性 | 收益率相关性热力图 |
| 📥 数据导出 | CSV / Excel / HTML 报告下载 |

### 3. 移动端使用

手机上访问后，展开侧边栏 → 打开「📱 移动端适配」开关，图表会自动压缩布局。

## 代码格式说明

不同市场的代码在 `data/instrument_master.csv` 中已自动转换为 yfinance 可识别格式：

| 市场 | 原始代码 | yfinance 格式 |
|------|---------|--------------|
| 美股 | AAPL | `AAPL` |
| 上交所 | 600519 | `600519.SS` |
| 深交所 | 000001 | `000001.SZ` |
| 港交所 | 00700 | `0700.HK` |
| 期货 | 黄金 | `GC=F` |
| 加密货币 | 比特币 | `BTC-USD` |

## 项目结构

```
fin-dashboard/
├── app.py                          # Streamlit 主入口
├── modules/
│   ├── __init__.py
│   ├── data_fetcher.py             # 数据拉取（yfinance + curl_cffi）
│   ├── indicators.py               # 技术指标计算（ta 库）
│   ├── charts.py                   # Plotly 图表生成
│   ├── exporter.py                 # CSV / Excel / HTML 导出
│   └── ticker_search.py            # 本地代码库模糊搜索
├── scripts/
│   ├── build_instrument_master.py  # 生成全局代码库
│   ├── add_chinese_aliases.py      # 补充中文别名
│   └── add_crypto.py               # 补充加密货币
├── data/
│   └── instrument_master.csv       # 本地代码库
├── requirements.txt
└── README.md
```

## 数据源

- **yfinance**：全球股票、期货、加密货币行情
- **akshare**：A 股、港股列表（可选）
- **HuggingFace** `free-global-stock-ticker-database`：全球股票代码库
- **GitHub** `irachex/open-stock-data`：分交易所代码列表
- 期货、债券、加密货币：硬编码维护

## 维护代码库

如果需要重新生成或更新本地代码库（例如新增交易所、补充别名），依次运行：

```bash
# 1. 重新生成基础代码库（约 68,000 条）
python scripts/build_instrument_master.py

# 2. 补充中文别名（覆盖已有记录的英文名）
python scripts/add_chinese_aliases.py

# 3. 补充加密货币
python scripts/add_crypto.py
```

生成的文件位于 `data/instrument_master.csv`。三个脚本均可重复运行，自动去重。

## 常见问题

### 行情拉取失败

Yahoo Finance 对部分地区有网络限制，建议：

- 使用 `curl_cffi` 模拟浏览器请求（已在 `data_fetcher.py` 中配置）
- 或切换到 akshare 数据源（A 股、港股）

### 搜索不到标的

1. 确认 `data/instrument_master.csv` 存在
2. 尝试搜索英文名或代码（部分标的只有英文名）
3. 如需补充中文名，在 `scripts/add_chinese_aliases.py` 的 `ALIASES` 字典中添加后重新运行

### 部署到 Streamlit Cloud 后代码库为空

如果 `data/instrument_master.csv` 未提交到仓库，云端首次访问时会提示为空。两种解决方式：

- 将 CSV 提交到仓库（文件较小的情况）
- 在 Streamlit Cloud 的启动命令中先执行 `scripts/build_instrument_master.py`

## 技术栈

- **Streamlit**：Web 应用框架
- **yfinance + curl_cffi**：行情数据拉取
- **pandas / numpy**：数据处理
- **ta**：技术指标计算
- **plotly**：交互式图表
- **openpyxl**：Excel 导出

## License

MIT

## MA5 双轴对比

「📉 指标对比」Tab 的下拉框中新增「MA5双轴对比」选项，用于观察**量级差异较大的两个资产**之间的联动关系。

### 适用场景

- **布伦特原油 `BZ=F` vs 中海油 `0883.HK`**：原油以 USD/桶计价，量级 600+；中海油以 HKD/股计价，量级 20+
- **COMEX 黄金 `GC=F` vs 贵州茅台 `600519.SS`**：USD/盎司 vs CNY/股
- **比特币 `BTC-USD` vs 纳斯达克指数 `^IXIC`**：USD/枚 vs 指数点

### 图表特性

- 量级最大的标的自动放在**左轴**，其余放在**右轴**，避免小量级曲线被压平
- 左右轴标题自动标注计价单位（`USD/桶`、`HKD/股`、`CNY/股` 等）
- 恰好两个标的时，标题上方自动显示 **Pearson 相关系数**
- 超过两个标的且右轴单位不一致时，右轴显示「混合单位」提示

### 注意事项

- 建议一次只看两个标的，超过两个时右轴内可能仍有量级差异
- 不做汇率换算，各标的保留原始计价货币；如需统一计价，目前需要单独处理
- 单位推断按代码后缀自动识别，覆盖 A 股、港股、美股、日股、欧股、期货、加密货币等常见市场
