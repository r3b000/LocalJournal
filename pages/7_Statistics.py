"""
Statistics Page
Comprehensive performance analytics with optimized data loading pipeline
"""



import streamlit as st
import pandas as pd
import calendar
from datetime import datetime, timedelta
from pathlib import Path
import plotly.graph_objects as go
from utils.paths import get_database_path
from database.statistics_db import (
    get_performance_metrics,
    get_daily_pnl_calendar,
    get_trade_distribution,
    get_performance_by_symbol,
    get_performance_by_strategy,
    get_performance_by_direction,
    get_all_closed_trades
)
from components.account_selector import render_account_selector
from utils.formatters import format_currency, format_percentage, format_r_multiple, format_duration
import logging



logger = logging.getLogger(__name__)



st.set_page_config(page_title="Statistics", page_icon="📈", layout="wide")



# Minimal, clean CSS
st.markdown("""
<style>
    /* Remove heavy styling for better readability */
    .stMetric {
        background-color: transparent;
        padding: 8px;
    }


    /* Clean table styling */
    .metrics-table {
        width: 100%;
        border-collapse: collapse;
        margin: 10px 0;
    }
    .metrics-table th {
        text-align: left;
        padding: 8px;
        border-bottom: 2px solid #444;
        color: #888;
        font-weight: 600;
        font-size: 14px;
    }
    .metrics-table td {
        padding: 8px;
        border-bottom: 1px solid #333;
        font-size: 16px;
    }


    /* Calendar styling */
    .calendar-day {
        padding: 12px 8px;
        border-radius: 4px;
        text-align: center;
        font-weight: 500;
        margin: 2px;
        font-size: 13px;
        min-height: 60px;
    }
    .calendar-day-green {
        background-color: #10b981;
        color: white;
    }
    .calendar-day-red {
        background-color: #ef4444;
        color: white;
    }
    .calendar-day-neutral {
        background-color: #6b7280;
        color: white;
    }
    .calendar-day-empty {
        background-color: transparent;
        color: #555;
    }


    /* Section headers */
    .section-header {
        font-size: 18px;
        font-weight: 600;
        margin: 20px 0 10px 0;
        color: #ddd;
    }
</style>
""", unsafe_allow_html=True)



# =============================================================================
# CONFIGURATION & CONSTANTS
# =============================================================================



CALENDAR_YEAR_RANGE = (2000, 2100)  # Year range for calendar selector



# =============================================================================
# HELPER FUNCTIONS
# =============================================================================



@st.cache_data(ttl=30, show_spinner=False)
def load_all_statistics(db_path_str: str, acc_id: int, date_from: str = None, date_to: str = None, breakeven_threshold: float = 1.0):
    """
    Centralized data loading with caching for better performance


    Args:
        db_path_str: Database path as string
        acc_id: Account ID
        date_from: Optional start date filter
        date_to: Optional end date filter
        breakeven_threshold: Threshold for breakeven trades


    Returns:
        Dictionary containing all statistics data
    """
    try:
        db_path_obj = Path(db_path_str)


        data = {
            'metrics': get_performance_metrics(db_path_obj, acc_id, date_from, date_to),
            'distribution': get_trade_distribution(db_path_obj, acc_id, breakeven_threshold),
            'symbol_perf': get_performance_by_symbol(db_path_obj, acc_id),
            'strategy_perf': get_performance_by_strategy(db_path_obj, acc_id),
            'direction_perf': get_performance_by_direction(db_path_obj, acc_id),
            'all_trades': get_all_closed_trades(db_path_obj, acc_id)
        }
        return data
    except Exception as e:
        logger.error(f"Failed to load statistics: {e}")
        return None




def get_date_range_from_filter(filter_option: str, custom_from=None, custom_to=None):
    """
    Calculate date range based on filter selection


    Args:
        filter_option: Selected filter option
        custom_from: Custom from date (for Custom option)
        custom_to: Custom to date (for Custom option)


    Returns:
        Tuple of (date_from, date_to) as strings or (None, None)
    """
    if filter_option == "All Time":
        return None, None


    today = datetime.now().date()


    if filter_option == "Custom":
        return custom_from, custom_to


    date_ranges = {
        "Last 7 Days": timedelta(days=7),
        "Last 30 Days": timedelta(days=30),
        "This Month": None,
        "This Year": None
    }


    if filter_option in ["Last 7 Days", "Last 30 Days"]:
        delta = date_ranges[filter_option]
        return (today - delta).strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")


    elif filter_option == "This Month":
        return today.replace(day=1).strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")


    elif filter_option == "This Year":
        return today.replace(month=1, day=1).strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")


    return None, None




def render_metrics_table(metrics: dict):
    """Render performance metrics as clean table"""
    metrics_html = f"""
    <table class="metrics-table">
        <thead>
            <tr>
                <th>Metric</th>
                <th>Value</th>
                <th>Metric</th>
                <th>Value</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Total Trades</td>
                <td><strong>{metrics['total_trades']}</strong></td>
                <td>Win Rate</td>
                <td><strong>{format_percentage(metrics['win_rate'])}</strong></td>
            </tr>
            <tr>
                <td>Avg Win</td>
                <td><strong>{format_currency(metrics['avg_win'])}</strong></td>
                <td>Avg Loss</td>
                <td><strong>{format_currency(metrics['avg_loss'])}</strong></td>
            </tr>
            <tr>
                <td>Profit Factor</td>
                <td><strong>{metrics['profit_factor']:.2f}</strong></td>
                <td>Expectancy</td>
                <td><strong>{format_currency(metrics['expectancy'])}</strong></td>
            </tr>
            <tr>
                <td>Total P&L</td>
                <td><strong>{format_currency(metrics['total_pnl'])}</strong></td>
                <td>Avg R-Multiple</td>
                <td><strong>{format_r_multiple(metrics['avg_r'])}</strong></td>
            </tr>
        </tbody>
    </table>
    """
    st.markdown(metrics_html, unsafe_allow_html=True)




def render_distribution_chart(distribution: dict):
    """Render win/loss distribution pie chart"""
    if distribution['total_trades'] == 0:
        st.info("No trades available for distribution chart")
        return


    labels = []
    values = []
    colors = []


    chart_data = [
        ('Winning', distribution['wins'], '#10b981'),
        ('Losing', distribution['losses'], '#ef4444'),
        ('Breakeven', distribution['breakevens'], '#6b7280')
    ]


    for label, data, color in chart_data:
        if data['count'] > 0:
            labels.append(label)
            values.append(data['count'])
            colors.append(color)


    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        marker=dict(colors=colors),
        hole=0.4,
        textinfo='label+percent',
        textposition='outside',
        showlegend=True
    )])


    fig.update_layout(
        title="Win/Loss Distribution",
        height=400,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white', size=12),
        margin=dict(t=50, b=20, l=20, r=20)
    )


    return fig




def render_calendar(calendar_data: dict, year: int, month: int, breakeven_threshold: float):
    """
    Render trading calendar with P&L


    Args:
        calendar_data: Daily P&L data
        year: Calendar year
        month: Calendar month (1-12)
        breakeven_threshold: Threshold for breakeven


    Returns:
        Tuple of (green_days, red_days, breakeven_days, month_pnl)
    """
    cal = calendar.monthcalendar(year, month)


    st.markdown(f"### {calendar.month_name[month]} {year}")


    # Header row
    header_cols = st.columns(7)
    days_of_week = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    for idx, day_name in enumerate(days_of_week):
        with header_cols[idx]:
            st.markdown(f"**{day_name}**")


    # Initialize counters
    stats = {
        'green_days': 0,
        'red_days': 0,
        'breakeven_days': 0,
        'month_pnl': 0.0
    }


    # Render calendar grid
    for week in cal:
        week_cols = st.columns(7)
        for idx, day in enumerate(week):
            with week_cols[idx]:
                if day == 0:
                    st.write("")  # Empty cell
                else:
                    date_str = f"{year}-{month:02d}-{day:02d}"


                    if date_str in calendar_data:
                        day_data = calendar_data[date_str]
                        pnl = day_data['pnl']
                        trade_count = day_data['trade_count']


                        stats['month_pnl'] += pnl


                        # Determine color based on P&L
                        if pnl > breakeven_threshold:
                            color_class = "calendar-day-green"
                            stats['green_days'] += 1
                        elif pnl < -breakeven_threshold:
                            color_class = "calendar-day-red"
                            stats['red_days'] += 1
                        else:
                            color_class = "calendar-day-neutral"
                            stats['breakeven_days'] += 1


                        # Trade count badge + P&L — only shows on CLOSED days
                        st.markdown(
                            f'<div class="calendar-day {color_class}">'
                            f'{day}'
                            f'<br><small>{format_currency(pnl)}</small>'
                            f'<br><small style="opacity:0.8">({trade_count} trade{"s" if trade_count != 1 else ""})</small>'
                            f'</div>',
                            unsafe_allow_html=True
                        )
                    else:
                        # No closed trades this day — plain day number, no P&L
                        st.markdown(
                            f'<div class="calendar-day calendar-day-empty">{day}</div>',
                            unsafe_allow_html=True
                        )


    return stats




def render_performance_breakdown(data: list, title: str, key_field: str):
    """
    Generic function to render performance breakdown (Symbol/Strategy/Direction)


    Args:
        data: Performance data list
        title: Section title
        key_field: Field name to use as key (e.g., 'symbol', 'strategy_name')
    """
    if not data:
        st.info(f"No {title.lower()} data available")
        return


    st.markdown(f"**{title}**")


    for item in data:
        key_value = item[key_field]
        trades = item['trades']
        total_pnl = item['total_pnl']
        avg_pnl = item['avg_pnl']
        win_rate = item['win_rate']


        with st.expander(
            f"**{key_value}** | Trades: {trades} | Total: {format_currency(total_pnl)} | "
            f"Avg: {format_currency(avg_pnl)} | Win Rate: {format_percentage(win_rate)}"
        ):
            col1, col2, col3, col4 = st.columns(4)


            col1.markdown(f"**Trades**<br/>{trades}", unsafe_allow_html=True)
            col2.markdown(f"**Total P&L**<br/>{format_currency(total_pnl)}", unsafe_allow_html=True)
            col3.markdown(f"**Avg P&L**<br/>{format_currency(avg_pnl)}", unsafe_allow_html=True)
            col4.markdown(f"**Win Rate**<br/>{format_percentage(win_rate)}", unsafe_allow_html=True)




def group_trades_by_grade(trades: list, grade_field: str):
    """
    Group trades by grade (mental or technical)


    Args:
        trades: List of trade dictionaries
        grade_field: Field name ('grade_mental' or 'grade_technical')


    Returns:
        Dictionary with grade as key and aggregated data as value
    """
    grade_data = {}


    for trade in trades:
        grade = trade.get(grade_field, 'N/A')
        if grade and grade != 'N/A':
            if grade not in grade_data:
                grade_data[grade] = {'trades': [], 'pnls': []}


            grade_data[grade]['trades'].append(trade['trade_id'])
            grade_data[grade]['pnls'].append(trade.get('pnl', 0.0))


    return grade_data




def group_trades_by_pnl_range(trades: list, small_threshold: float, medium_threshold: float, large_threshold: float):
    """
    Group trades into P&L ranges based on user-defined thresholds


    Args:
        trades: List of trade dictionaries
        small_threshold: Upper bound for small wins/losses
        medium_threshold: Upper bound for medium wins/losses
        large_threshold: Lower bound for large wins/losses


    Returns:
        Dictionary with range name as key and trades list as value
    """
    ranges = {}


    # Define ranges dynamically based on user input
    pnl_ranges = [
        ('Large Winners', large_threshold, float('inf')),
        ('Medium Winners', small_threshold, large_threshold),
        ('Small Winners', 0, small_threshold),
        ('Small Losers', -small_threshold, 0),
        ('Medium Losers', -large_threshold, -small_threshold),
        ('Large Losers', float('-inf'), -large_threshold)
    ]


    for trade in trades:
        pnl = trade.get('pnl', 0.0)


        for range_name, min_val, max_val in pnl_ranges:
            if min_val < pnl <= max_val:
                if range_name not in ranges:
                    ranges[range_name] = []
                ranges[range_name].append(trade)
                break


    return ranges





# ============================================================
# ICONS
# ============================================================



from utils.png_icons import icon_header



# =============================================================================
# MAIN APPLICATION
# =============================================================================




icon_header("icons/statistics.png", "Trading Statistics",width=51, height=51, level="h1")
st.markdown("Comprehensive Performance Analytics Dashboard")
st.markdown("---")



# Get database path
db_path = get_database_path()



# Account selector
selected_account = render_account_selector()



if not selected_account:
    st.stop()



account_id = selected_account['account_id']
account_name = selected_account['account_name']



st.markdown(f"**Performance Analytics - {account_name}**")
st.markdown("---")



# =============================================================================
# DATE FILTER & BREAKEVEN THRESHOLD
# =============================================================================



col_filter1, col_filter2, col_filter3 = st.columns([3, 1, 1])



with col_filter1:
    date_filter = st.selectbox(
        "📅 Period",
        options=["All Time", "Last 7 Days", "Last 30 Days", "This Month", "This Year", "Custom"],
        key="stats_date_filter"
    )


with col_filter3:
    breakeven_threshold = st.number_input(
        "Breakeven Threshold ($)",
        min_value=0.1,
        max_value=10000.0,
        value=1.0,
        step=0.1,
        help="Trades within ±this amount are considered breakeven",
        key="breakeven_threshold_input"
    )



# Handle custom date inputs
custom_from = None
custom_to = None



if date_filter == "Custom":
    col_date1, col_date2 = st.columns(2)
    with col_date1:
        date_from_input = st.date_input("From Date", key="stats_from_date")
        if date_from_input:
            custom_from = date_from_input.strftime("%Y-%m-%d")


    with col_date2:
        date_to_input = st.date_input("To Date", key="stats_to_date")
        if date_to_input:
            custom_to = date_to_input.strftime("%Y-%m-%d")



# Get date range
date_from, date_to = get_date_range_from_filter(date_filter, custom_from, custom_to)



st.caption(f"Breakeven range: -{format_currency(breakeven_threshold)} to +{format_currency(breakeven_threshold)}")
st.markdown("---")



# =============================================================================
# LOAD ALL DATA WITH CACHING
# =============================================================================


with st.spinner("Loading statistics..."):
    stats_data = load_all_statistics(str(db_path), account_id, date_from, date_to, breakeven_threshold)



if not stats_data:
    st.error("Failed to load statistics data. Please check the database connection.")
    st.stop()



metrics = stats_data['metrics']
distribution = stats_data['distribution']
symbol_perf = stats_data['symbol_perf']
strategy_perf = stats_data['strategy_perf']
direction_perf = stats_data['direction_perf']
all_trades = stats_data['all_trades']



# =============================================================================
# PERFORMANCE METRICS SUMMARY
# =============================================================================



st.markdown('<div class="section-header">𝄜 Performance Metrics</div>', unsafe_allow_html=True)
render_metrics_table(metrics)
st.markdown("---")



# =============================================================================
# WIN/LOSS DISTRIBUTION
# =============================================================================




icon_header("icons/in_out.png", "Win/Loss Distribution", level="h4")



col_chart, col_summary = st.columns([2, 1])



with col_chart:
    fig = render_distribution_chart(distribution)
    if fig:
        st.plotly_chart(fig, use_container_width=True)



with col_summary:
    st.markdown("**Summary**")
    st.markdown(f"""
    - **Winning Trades:** {distribution['wins']['count']}
    - **Losing Trades:** {distribution['losses']['count']}
    - **Breakeven Trades:** {distribution['breakevens']['count']}
    - **Win Rate:** {format_percentage(distribution['wins']['percentage'])}
    """)



st.markdown("---")



# =============================================================================
# TRADING CALENDAR
# =============================================================================



icon_header("icons/calendar.png", "Trading Calendar", level="h4")



# Month/Year selector
today = datetime.now()
col_month, col_year = st.columns([2, 1])



with col_month:
    selected_month = st.selectbox(
        "Select Month",
        options=list(range(1, 13)),
        index=today.month - 1,
        format_func=lambda x: calendar.month_name[x],
        key="calendar_month"
    )



with col_year:
    year_options = list(range(CALENDAR_YEAR_RANGE[0], CALENDAR_YEAR_RANGE[1]))
    selected_year = st.selectbox(
        "Select Year",
        options=year_options,
        index=year_options.index(today.year) if today.year in year_options else 0,
        key="calendar_year"
    )



# Load calendar data
try:
    calendar_data = get_daily_pnl_calendar(db_path, account_id, selected_year, selected_month)


    # Render calendar
    cal_stats = render_calendar(calendar_data, selected_year, selected_month, breakeven_threshold)


    st.markdown("---")


    # Calendar summary
    st.markdown(f"""
    **Green Days:** {cal_stats['green_days']} | 
    **Red Days:** {cal_stats['red_days']} | 
    **Breakeven Days:** {cal_stats['breakeven_days']} | 
    **Month P&L:** {format_currency(cal_stats['month_pnl'])}
    """)


except Exception as e:
    logger.error(f"Error loading calendar: {e}")
    st.error("Failed to load trading calendar")



st.markdown("---")



# =============================================================================
# DETAILED PERFORMANCE METRICS
# =============================================================================



icon_header("icons/metrics.png", "Detailed Performance Metrics", level="h4")



col_det1, col_det2, col_det3 = st.columns(3)



with col_det1:
    st.markdown("**Profit & Loss**")
    st.markdown(f"""
    - Total Profit: {format_currency(metrics['total_profit'])}
    - Total Loss: {format_currency(metrics['total_loss'])}
    - Net P&L: {format_currency(metrics['total_pnl'])}
    - Expectancy: {format_currency(metrics['expectancy'])}
    """)



with col_det2:
    st.markdown("**Win/Loss Statistics**")
    st.markdown(f"""
    - Winning Trades: {metrics['winning_trades']}
    - Losing Trades: {metrics['losing_trades']}
    - Breakeven Trades: {metrics['breakeven_trades']}
    - Win Rate: {format_percentage(metrics['win_rate'])}
    """)



with col_det3:
    st.markdown("**Average Performance**")
    st.markdown(f"""
    - Avg Win: {format_currency(metrics['avg_win'])}
    - Avg Loss: {format_currency(metrics['avg_loss'])}
    - Profit Factor: {metrics['profit_factor']:.2f}
    - Avg Duration: {format_duration(metrics['avg_duration'])}
    """)



st.markdown("---")



# =============================================================================
# R-MULTIPLE ANALYSIS
# =============================================================================



icon_header("icons/r_multiple.png", "R-Multiple Analysis", level="h4")



positive_r_ratio = f"{metrics['winning_trades']}/{metrics['total_trades']}" if metrics['total_trades'] > 0 else "0/0"



st.markdown(f"""
**Average R:** {format_r_multiple(metrics['avg_r'])} | 
**Best Trade:** {format_r_multiple(metrics['best_r'])} | 
**Worst Trade:** {format_r_multiple(metrics['worst_r'])} | 
**Positive R Trades:** {positive_r_ratio}
""")



st.markdown("---")



# =============================================================================
# PERFORMANCE ANALYSIS
# =============================================================================




icon_header("icons/stats.png", "Performance Analysis", level="h4")




analysis_filter = st.selectbox(
    "Filter by",
    options=["Symbol", "Strategy", "Direction", "Grade (Mental)", "Grade (Technical)", "P&L Range"],
    key="analysis_filter"
)



# =============================================================================
# P&L RANGE USER INPUTS (Show only when P&L Range is selected)
# =============================================================================


if analysis_filter == "P&L Range":
    st.markdown("---")
    st.markdown("**Configure P&L Ranges**")


    col_thresh1, col_thresh2, col_thresh3 = st.columns(3)


    with col_thresh1:
        small_threshold = st.number_input(
            "Small Threshold ($)",
            min_value=0.1,
            max_value=10000.0,
            value=2.0,
            step=0.1,
            help="Upper bound for small wins/losses",
            key="small_threshold"
        )


    with col_thresh2:
        medium_threshold = st.number_input(
            "Medium Threshold ($)",
            min_value=0.1,
            max_value=10000.0,
            value=3.0,
            step=0.1,
            help="Upper bound for medium wins/losses",
            key="medium_threshold"
        )


    with col_thresh3:
        large_threshold = st.number_input(
            "Large Threshold ($)",
            min_value=0.1,
            max_value=10000.0,
            value=5.0,
            step=0.1,
            help="Lower bound for large wins/losses",
            key="large_threshold"
        )


    st.caption(f"**Ranges:** Small: $0-${small_threshold:.2f} | Medium: ${small_threshold:.2f}-${medium_threshold:.2f} | Large: >${large_threshold:.2f}")
    st.markdown("---")
else:
    small_threshold = 2.0
    medium_threshold = 3.0
    large_threshold = 5.0



try:
    if analysis_filter == "Symbol":
        if symbol_perf:
            st.markdown("**Performance by Symbol**")


            for item in symbol_perf:
                symbol = item['symbol']
                trades = item['trades']
                total_pnl = item['total_pnl']
                avg_pnl = item['avg_pnl']
                win_rate = item['win_rate']


                # Get trade IDs for this symbol
                trade_ids = [t['trade_id'] for t in all_trades if t.get('symbol') == symbol]
                trade_ids_str = ", ".join([f"#{tid}" for tid in sorted(trade_ids)])


                with st.expander(
                    f"**{symbol}** | Trades: {trades} | Total: {format_currency(total_pnl)} | "
                    f"Avg: {format_currency(avg_pnl)} | Win Rate: {format_percentage(win_rate)}"
                ):
                    col1, col2, col3, col4 = st.columns(4)


                    col1.markdown(f"**Trades**<br/>{trades}", unsafe_allow_html=True)
                    col2.markdown(f"**Total P&L**<br/>{format_currency(total_pnl)}", unsafe_allow_html=True)
                    col3.markdown(f"**Avg P&L**<br/>{format_currency(avg_pnl)}", unsafe_allow_html=True)
                    col4.markdown(f"**Win Rate**<br/>{format_percentage(win_rate)}", unsafe_allow_html=True)


                    st.markdown("---")
                    st.markdown(f"** Trade IDs:** {trade_ids_str}")
        else:
            st.info("No symbol data available")


    elif analysis_filter == "Strategy":
        if strategy_perf:
            st.markdown("**Performance by Strategy**")


            for item in strategy_perf:
                strategy_name = item['strategy_name']
                strategy_id = item.get('strategy_id')
                trades = item['trades']
                total_pnl = item['total_pnl']
                avg_pnl = item['avg_pnl']
                win_rate = item['win_rate']


                # Get trade IDs for this strategy
                trade_ids = [t['trade_id'] for t in all_trades if t.get('strategy_id') == strategy_id]
                trade_ids_str = ", ".join([f"#{tid}" for tid in sorted(trade_ids)])


                with st.expander(
                    f"**{strategy_name}** | Trades: {trades} | Total: {format_currency(total_pnl)} | "
                    f"Avg: {format_currency(avg_pnl)} | Win Rate: {format_percentage(win_rate)}"
                ):
                    col1, col2, col3, col4 = st.columns(4)


                    col1.markdown(f"**Trades**<br/>{trades}", unsafe_allow_html=True)
                    col2.markdown(f"**Total P&L**<br/>{format_currency(total_pnl)}", unsafe_allow_html=True)
                    col3.markdown(f"**Avg P&L**<br/>{format_currency(avg_pnl)}", unsafe_allow_html=True)
                    col4.markdown(f"**Win Rate**<br/>{format_percentage(win_rate)}", unsafe_allow_html=True)


                    st.markdown("---")
                    st.markdown(f"** Trade IDs:** {trade_ids_str}")
        else:
            st.info("No strategy data available")


    elif analysis_filter == "Direction":
        st.markdown("**Performance by Direction**")


        col_dir1, col_dir2 = st.columns(2)


        for direction, col in [('LONG', col_dir1), ('SHORT', col_dir2)]:
            with col:
                st.markdown(f"### {direction} Trades")


                if direction_perf.get(direction):
                    data = direction_perf[direction]


                    # Get trade IDs for this direction
                    trade_ids = [t['trade_id'] for t in all_trades if t.get('direction') == direction]
                    trade_ids_str = ", ".join([f"#{tid}" for tid in sorted(trade_ids)])


                    st.markdown(f"""
                    - **Trades:** {data['trades']}
                    - **Wins:** {data['wins']}
                    - **Win Rate:** {format_percentage(data['win_rate'])}
                    - **Total P&L:** {format_currency(data['total_pnl'])}
                    - **Avg P&L:** {format_currency(data['avg_pnl'])}
                    """)


                    st.markdown("---")
                    st.markdown(f"** Trade IDs:**")
                    st.caption(trade_ids_str)
                else:
                    st.info(f"No {direction} trades yet")


    elif analysis_filter in ["Grade (Mental)", "Grade (Technical)"]:
        # FIX: Use correct database field names
        grade_field = 'grade_mentally' if analysis_filter == "Grade (Mental)" else 'grade_technically'
        grade_data = group_trades_by_grade(all_trades, grade_field)


        if grade_data:
            st.markdown(f"**{analysis_filter}**")


            for grade in sorted(grade_data.keys()):
                data = grade_data[grade]
                trade_ids = data['trades']  # Already collected in group_trades_by_grade
                trade_count = len(trade_ids)
                total_pnl = sum(data['pnls'])
                avg_pnl = total_pnl / trade_count if trade_count > 0 else 0.0
                wins = sum(1 for p in data['pnls'] if p > 0)
                win_rate = (wins / trade_count * 100) if trade_count > 0 else 0.0


                # Format trade IDs
                trade_ids_str = ", ".join([f"#{tid}" for tid in sorted(trade_ids)])


                with st.expander(
                    f"**Grade {grade}** | Trades: {trade_count} | "
                    f"Total: {format_currency(total_pnl)} | Win Rate: {format_percentage(win_rate)}"
                ):
                    col1, col2, col3, col4 = st.columns(4)
                    col1.markdown(f"**Trades**<br/>{trade_count}", unsafe_allow_html=True)
                    col2.markdown(f"**Total P&L**<br/>{format_currency(total_pnl)}", unsafe_allow_html=True)
                    col3.markdown(f"**Avg P&L**<br/>{format_currency(avg_pnl)}", unsafe_allow_html=True)
                    col4.markdown(f"**Win Rate**<br/>{format_percentage(win_rate)}", unsafe_allow_html=True)


                    st.markdown("---")
                    st.markdown(f"** Trade IDs:** {trade_ids_str}")
        else:
            st.info(f"No {analysis_filter.lower()} data available")


    elif analysis_filter == "P&L Range":
        pnl_ranges = group_trades_by_pnl_range(all_trades, small_threshold, medium_threshold, large_threshold)


        if pnl_ranges:
            st.markdown("**Performance by P&L Range**")


            # Display order for ranges
            range_order = ['Large Winners', 'Medium Winners', 'Small Winners', 'Small Losers', 'Medium Losers', 'Large Losers']


            for range_name in range_order:
                if range_name in pnl_ranges:
                    range_trades = pnl_ranges[range_name]
                    trade_count = len(range_trades)
                    total_pnl = sum(t.get('pnl', 0.0) for t in range_trades)
                    avg_pnl = total_pnl / trade_count if trade_count > 0 else 0.0


                    # Get trade IDs
                    trade_ids = [t['trade_id'] for t in range_trades]
                    trade_ids_str = ", ".join([f"#{tid}" for tid in sorted(trade_ids)])


                    with st.expander(
                        f"**{range_name}** | Trades: {trade_count} | Total: {format_currency(total_pnl)}"
                    ):
                        col1, col2, col3 = st.columns(3)
                        col1.markdown(f"**Trades**<br/>{trade_count}", unsafe_allow_html=True)
                        col2.markdown(f"**Total P&L**<br/>{format_currency(total_pnl)}", unsafe_allow_html=True)
                        col3.markdown(f"**Avg P&L**<br/>{format_currency(avg_pnl)}", unsafe_allow_html=True)


                        st.markdown("---")
                        st.markdown(f"** Trade IDs:** {trade_ids_str}")
        else:
            st.info("No trades available")




except Exception as e:
    logger.error(f"Error in performance analysis: {e}")
    st.error(f"Failed to load {analysis_filter} performance data")
