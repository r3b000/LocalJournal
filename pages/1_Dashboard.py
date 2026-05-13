"""
Dashboard Page
Overview of trading performance with quick navigation
"""


import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.paths import get_database_path
from database.accounts_db import get_account_stats
from database.trades_db import get_recent_trades, get_all_trades
from utils.formatters import format_currency, format_percentage, format_direction
from components.account_selector import render_account_selector
from config.constants import MAX_RECENT_TRADES
from utils.png_icons import *


st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")


icon_header("icons/dashboard.png", "Trading Dashboard", level="h1")


st.markdown("---")


# Account selector
selected_account = render_account_selector()


if not selected_account:
    st.stop()


account_id = selected_account['account_id']
db_path = get_database_path()


# =============================================================================
# BREAKEVEN THRESHOLD INPUT
# =============================================================================

col_thresh1, col_thresh2 = st.columns([4, 1])

with col_thresh2:
    breakeven_threshold = st.number_input(
        "Breakeven Threshold ($)",
        min_value=0.1,
        max_value=10000.0,
        value=1.0,
        step=0.1,
        help="Trades within ±this amount are considered breakeven",
        key="dashboard_breakeven_threshold"
    )

st.caption(f"Breakeven range: -{format_currency(breakeven_threshold)} to +{format_currency(breakeven_threshold)}")
st.markdown("---")


# OPTIMIZED: Single database call for all dashboard data
@st.cache_data(ttl=30, show_spinner=False)
def get_dashboard_data(db_path_str: str, account_id: int):
    """
    Load all dashboard data in single optimized query
    Returns: (account_stats, all_closed_trades, recent_trades)
    """
    from pathlib import Path
    db_path = Path(db_path_str)

    # Get account stats
    account_stats = get_account_stats(db_path, account_id)

    # Get all closed trades (sorted by exit date for equity curve)
    all_closed_trades = get_all_trades(db_path, account_id, status="CLOSED")

    # Get recent trades (last 5)
    recent_trades = get_recent_trades(db_path, account_id, MAX_RECENT_TRADES)

    return account_stats, all_closed_trades, recent_trades


# Load all data with caching
account_stats, all_closed_trades, recent_trades = get_dashboard_data(str(db_path), account_id)


#  ICONS


danger_icon = get_png_icon("icons/danger.png", 42, 42)


# Verify account_stats is valid
if not account_stats:
    st.error(f"Unable to load account statistics. Please check the database.")
    st.stop()


# =============================================================================
# CALCULATE BREAKEVEN TRADES
# =============================================================================

def calculate_trade_categories(trades, threshold):
    """Calculate winning, losing, and breakeven trades based on threshold"""
    wins = 0
    losses = 0
    breakevens = 0

    for trade in trades:
        pnl = trade.get('pnl', 0.0)
        if pnl > threshold:
            wins += 1
        elif pnl < -threshold:
            losses += 1
        else:
            breakevens += 1

    return wins, losses, breakevens


# Calculate categories for closed trades
if all_closed_trades:
    winning_trades, losing_trades, breakeven_trades = calculate_trade_categories(all_closed_trades, breakeven_threshold)
    closed_trades = len(all_closed_trades)
else:
    winning_trades = 0
    losing_trades = 0
    breakeven_trades = 0
    closed_trades = 0


# =============================================================================
# ACCOUNT PERFORMANCE METRICS
# =============================================================================


icon_header("icons/stats.png", "Account Performance", level="h3")


# Extract values with safe defaults
starting_equity = account_stats.get('starting_equity', 0.0)
current_equity = account_stats.get('current_equity', 0.0)
total_pnl = account_stats.get('total_pnl', 0.0)
total_trades = account_stats.get('total_trades', 0)
win_rate = (winning_trades / closed_trades * 100) if closed_trades > 0 else 0.0


# Calculate ROI
if starting_equity > 0:
    roi = ((current_equity - starting_equity) / starting_equity) * 100
else:
    roi = 0.0


# Calculate equity change
equity_change = current_equity - starting_equity


# Display metrics
col1, col2, col3, col4, col5 = st.columns(5)


with col1:
    st.metric(
        label="Current Equity",
        value=format_currency(current_equity),
        delta=format_currency(equity_change)
    )


with col2:
    st.metric(
        label="Total P&L",
        value=format_currency(total_pnl),
        delta="Realized"
    )


with col3:
    st.metric(
        label="ROI",
        value=f"{roi:+.2f}%",
        delta="Since Start"
    )


with col4:
    # Updated to show W/L/BE breakdown
    st.metric(
        label="Total Trades",
        value=str(total_trades),
        delta=f"{winning_trades}W / {losing_trades}L / {breakeven_trades}BE" if closed_trades > 0 else None
    )


with col5:
    st.metric(
        label="Win Rate",
        value=format_percentage(win_rate),
        delta="Closed Trades"
    )


st.markdown("---")


# =============================================================================
# EQUITY CURVE
# =============================================================================


icon_header("icons/chart.png", "Equity Curve", level="h3")


if all_closed_trades and len(all_closed_trades) > 0:
    # Sort trades by exit date
    sorted_trades = sorted(
        all_closed_trades,
        key=lambda x: (x.get('exit_date', '9999-12-31'), x.get('exit_time', '23:59:59'))
    )


    # Build equity curve data
    equity_data = [{'Trade': 0, 'Equity': starting_equity, 'Date': 'Start'}]


    running_equity = starting_equity


    for idx, trade in enumerate(sorted_trades, 1):
        pnl = trade.get('pnl', 0.0)
        running_equity += pnl


        # Create label with trade info
        exit_date = trade.get('exit_date', 'N/A')
        symbol = trade.get('symbol', 'N/A')


        equity_data.append({
            'Trade': idx,
            'Equity': running_equity,
            'Date': f"{exit_date} - {symbol}"
        })


    # Create DataFrame
    df_equity = pd.DataFrame(equity_data)


    # Calculate y-axis range with dynamic scaling
    equity_values = df_equity['Equity'].values
    min_equity = equity_values.min()
    max_equity = equity_values.max()
    equity_range = max_equity - min_equity

    # Add 10% padding above and below for better visibility
    # Minimum 1% of starting equity as range to avoid flat lines
    min_range = starting_equity * 0.01 if starting_equity > 0 else 100
    if equity_range < min_range:
        equity_range = min_range

    padding = equity_range * 0.1
    y_min = min_equity - padding
    y_max = max_equity + padding


    # Create Plotly chart with custom y-axis range
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df_equity['Trade'],
        y=df_equity['Equity'],
        mode='lines+markers',
        name='Equity',
        line=dict(color='#7e3abe', width=2),
        marker=dict(size=6, color='#7e3abe'),
        hovertemplate='<b>Trade %{x}</b><br>Equity: $%{y:,.2f}<extra></extra>'
    ))


    fig.update_layout(
        yaxis=dict(
            range=[y_min, y_max],
            tickformat='$,.2f',
            title='Equity'
        ),
        xaxis=dict(
            title='Trade Number',
            tickmode='linear',
            dtick=1 if len(df_equity) <= 20 else max(1, len(df_equity) // 20)
        ),
        hovermode='x unified',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        height=400,
        margin=dict(l=60, r=20, t=20, b=40)
    )


    fig.update_xaxes(showgrid=True, gridcolor='rgba(255,255,255,0.1)')
    fig.update_yaxes(showgrid=True, gridcolor='rgba(255,255,255,0.1)')


    st.plotly_chart(fig, use_container_width=True)


    # Show key stats below chart
    col_eq1, col_eq2, col_eq3, col_eq4 = st.columns(4)


    with col_eq1:
        st.metric("Starting Equity", format_currency(starting_equity))


    with col_eq2:
        st.metric("Current Equity", format_currency(current_equity))


    with col_eq3:
        peak_equity = max(item['Equity'] for item in equity_data)
        st.metric("Peak Equity", format_currency(peak_equity))


    with col_eq4:
        total_return = ((current_equity - starting_equity) / starting_equity * 100) if starting_equity > 0 else 0
        st.metric("Total Return", f"{total_return:+.2f}%")


else:
    st.info("No closed trades yet. The equity curve will appear after you close your first trade.")


st.markdown("---")


# =============================================================================
# RECENT TRADES SECTION
# =============================================================================


st.subheader(f"Recent Trades (Last {MAX_RECENT_TRADES})")


if recent_trades:
    # Header
    col_h1, col_h2, col_h3, col_h4, col_h5 = st.columns([1, 2, 2, 2, 2])


    with col_h1:
        st.markdown("**ID**")


    with col_h2:
        st.markdown("**Symbol**")


    with col_h3:
        st.markdown("**Direction**")


    with col_h4:
        st.markdown("**Date**")


    with col_h5:
        st.markdown("**Result**")


    st.markdown("---")


    # Trade rows
    for trade in recent_trades:
        col_t1, col_t2, col_t3, col_t4, col_t5 = st.columns([1, 2, 2, 2, 2])


        with col_t1:
            st.write(f"#{trade['trade_id']}")


        with col_t2:
            st.write(trade['symbol'])


        with col_t3:
            st.write(format_direction(trade['direction']))


        with col_t4:
            entry_date = trade.get('entry_date', 'N/A')
            entry_time = trade.get('entry_time', '')
            st.write(f"{entry_date} {entry_time}")


        with col_t5:
            trade_status = trade.get('status', 'UNKNOWN')


            if trade_status == 'CLOSED':
                pnl = trade.get('pnl', 0.0)


                if pnl > breakeven_threshold:
                    st.success(f"🟢 {format_currency(pnl)}")
                elif pnl < -breakeven_threshold:
                    st.error(f"🔴 {format_currency(pnl)}")
                else:
                    st.info(f"⚪ {format_currency(pnl)}")
            else:
                st.info("🟢 Open")


        st.markdown("---")
else:
    st.info("No trades logged yet. Go to **Log Trade** page to record your first trade!")


st.markdown("---")


# =============================================================================
# QUICK ACTIONS
# =============================================================================


icon_header("icons/bolt.png", "Quick Actions", level="h3")


col_a1, col_a2, col_a3, col_a4 = st.columns(4)


with col_a1:
    if st.button("Log New Trade", use_container_width=True, key="action_log"):
        st.switch_page("pages/3_Log_Trade.py")


with col_a2:
    if st.button("View Trade History", use_container_width=True, key="action_history"):
        st.switch_page("pages/4_Trade_History.py")


with col_a3:
    if st.button("View Statistic", use_container_width=True, key="action_stats"):
        st.switch_page("pages/7_Statistics.py")


with col_a4:
    if st.button("Mental Development", use_container_width=True, key="action_mental"):
        st.switch_page("pages/5_Mental_Development.py")


st.markdown("---")


# =============================================================================
# OVERALL PERFORMANCE SECTION
# =============================================================================


icon_header("icons/performance.png", "Overall Performance", level="h3")


if all_closed_trades:
    # Calculate metrics using breakeven threshold
    total_closed = len(all_closed_trades)

    # wins, losses, and breakevens already calculated above using threshold


    # Calculate win rate
    calculated_win_rate = (winning_trades / total_closed * 100) if total_closed > 0 else 0.0


    # Calculate average R
    r_values = [t.get('total_r', 0) for t in all_closed_trades if t.get('total_r') is not None]
    avg_r = sum(r_values) / len(r_values) if r_values else 0.0


    # Calculate profit factor
    total_wins = sum(t.get('pnl', 0) for t in all_closed_trades if t.get('pnl', 0) > breakeven_threshold)
    total_losses = abs(sum(t.get('pnl', 0) for t in all_closed_trades if t.get('pnl', 0) < -breakeven_threshold))
    profit_factor = total_wins / total_losses if total_losses > 0 else 0.0


    # Display metrics
    col_p1, col_p2, col_p3, col_p4, col_p5, col_p6 = st.columns(6)


    with col_p1:
        st.metric(
            label="Closed Trades",
            value=str(total_closed)
        )


    with col_p2:
        st.metric(
            label="Winning Trades",
            value=str(winning_trades),
            delta=f"{calculated_win_rate:.1f}% Win Rate"
        )


    with col_p3:
        st.metric(
            label="Losing Trades",
            value=str(losing_trades)
        )


    with col_p4:
        st.metric(
            label="Breakeven Trades",
            value=str(breakeven_trades)
        )


    with col_p5:
        st.metric(
            label="Average R",
            value=f"{avg_r:.2f}R"
        )


    with col_p6:
        st.metric(
            label="Profit Factor",
            value=f"{profit_factor:.2f}"
        )


    st.markdown("---")


    # Performance breakdown
    if winning_trades > 0 or losing_trades > 0:
        icon_header("icons/performance.png", "Performance Breakdown", level="h3")


        col_b1, col_b2, col_b3 = st.columns(3)


        with col_b1:
            avg_win = total_wins / winning_trades if winning_trades > 0 else 0.0
            st.metric(
                label="Average Win",
                value=format_currency(avg_win)
            )


        with col_b2:
            avg_loss = total_losses / losing_trades if losing_trades > 0 else 0.0
            st.metric(
                label="Average Loss",
                value=format_currency(avg_loss)
            )


        with col_b3:
            expectancy = (calculated_win_rate / 100 * avg_win) - ((100 - calculated_win_rate) / 100 * avg_loss)
            st.metric(
                label="Expectancy",
                value=format_currency(expectancy)
            )
else:
    st.info("No closed trades yet. Close some trades to see overall performance metrics.")


st.markdown("---")


# Footer
st.caption("💡 Tip: Keep your win rate above 50% and maintain positive R-multiples for consistent profitability")
