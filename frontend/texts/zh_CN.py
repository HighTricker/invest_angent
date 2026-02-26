"""
中文文案配置。

所有前端界面显示的文字都集中在这里，
修改文案时只需编辑此文件，无需改动任何代码逻辑。
"""

# ============================================================
# 全局
# ============================================================
APP_TITLE = "Invest Agent - 投资追踪"
APP_ICON = "📊"

# 侧边栏导航
NAV_DASHBOARD = "投资总览"
NAV_MANAGE = "标的管理"
NAV_HISTORY = "变动记录"

# ============================================================
# 投资总览页面
# ============================================================
DASHBOARD_TITLE = "投资总览"
DASHBOARD_SELECT_DATE = "选择查看月份"
DASHBOARD_NO_DATA = "该月份暂无价格数据，请先进行数据采集。"
DASHBOARD_NO_ASSETS = "暂无投资标的，请先在「标的管理」中添加。"

# 关键指标卡片
METRIC_TOTAL_INVESTED = "总投入"
METRIC_TOTAL_VALUE = "总当前价值"
METRIC_TOTAL_RETURN = "总收益率"
METRIC_PROFIT_LOSS = "盈亏"

# 标的明细表格
TABLE_TITLE = "标的明细"
TABLE_COL_NAME = "标的名称"
TABLE_COL_TICKER = "代码"
TABLE_COL_TYPE = "资产类别"
TABLE_COL_BASE_PRICE = "基准价格"
TABLE_COL_CURRENT_PRICE = "当前价格"
TABLE_COL_INVESTED = "投入金额"
TABLE_COL_CURRENT_VALUE = "当前价值"
TABLE_COL_CUMULATIVE = "累计涨跌幅"
TABLE_COL_MONTHLY = "月度涨跌幅"
TABLE_COL_PROFIT_LOSS = "盈亏"

# 图表
CHART_TITLE = "各标的累计收益率对比"
CHART_Y_LABEL = "累计涨跌幅 (%)"
CHART_X_LABEL = "月份"

# 最佳/最差
BEST_PERFORMER = "本月最佳"
WORST_PERFORMER = "本月最差"

# ============================================================
# 标的管理页面
# ============================================================
MANAGE_TITLE = "标的管理"

# 添加标的
ADD_SECTION = "添加新标的"
ADD_NAME = "标的名称"
ADD_NAME_PLACEHOLDER = "如：Google"
ADD_TICKER = "交易代码"
ADD_TICKER_PLACEHOLDER = "如：GOOGL"
ADD_TYPE = "资产类别"
ADD_TYPE_OPTIONS = ["美股", "港股", "中概", "大宗商品", "债券", "加密货币"]
ADD_BASE_PRICE = "基准价格"
ADD_BASE_DATE = "基准日期"
ADD_BUTTON = "添加标的"
ADD_SUCCESS = "标的「{name}」添加成功！"
ADD_ERROR_DUPLICATE = "交易代码「{ticker}」已存在。"
ADD_ERROR_EMPTY = "请填写所有必填项。"

# 设置投资金额
INVEST_SECTION = "设置投资金额"
INVEST_SELECT_ASSET = "选择标的"
INVEST_AMOUNT = "投资金额（美元）"
INVEST_NOTE = "备注"
INVEST_NOTE_PLACEHOLDER = "如：首次建仓、定投加仓"
INVEST_BUTTON_ADD = "加仓"
INVEST_BUTTON_REDUCE = "减仓"
INVEST_SUCCESS_ADD = "已为「{name}」加仓 ${amount:.2f}"
INVEST_SUCCESS_REDUCE = "已为「{name}」减仓 ${amount:.2f}"
INVEST_ERROR_EXCEED = "减仓金额不能超过当前持仓 ${current:.2f}"
INVEST_ERROR_ZERO = "金额必须大于 0"

# 当前持仓列表
POSITION_SECTION = "当前持仓一览"
POSITION_COL_NAME = "标的名称"
POSITION_COL_TICKER = "代码"
POSITION_COL_INVESTED = "累计投入"

# ============================================================
# 变动记录页面
# ============================================================
HISTORY_TITLE = "仓位变动记录"
HISTORY_EMPTY = "暂无变动记录。"
HISTORY_COL_DATE = "日期"
HISTORY_COL_ASSET = "标的"
HISTORY_COL_TYPE = "类型"
HISTORY_COL_AMOUNT = "金额"
HISTORY_COL_PRICE = "当时价格"
HISTORY_COL_NOTE = "备注"
