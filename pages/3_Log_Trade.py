"""
Log Trade Page - With Smart Number Inputs + Multi-Screenshot Support
ALL FIXES APPLIED:
  1) SHORT direction -> target is optional (no forced validation)
  2) Fresh session state after every open/close (no stale data)
  3) Navigation buttons corrected to actual page filenames
  4) Commission field added (open + close), Net PnL = PnL - Commission
  5) Trading Environment dropdown: added Trending UP, Trending DOWN, Trend Shift
"""

import streamlit as st
from datetime import datetime, date
from utils.paths import get_database_path, get_trade_screenshot_dir
from database.accounts_db import get_all_accounts
from database.strategies_db import get_all_strategies
from database.trades_db import create_trade, add_screenshot, get_all_trades, update_trade_exit, get_trade_by_id
from utils.calculations import (
    calculate_position_size,
    calculate_prospective_r,
    calculate_pnl,
    calculate_total_r,
    calculate_roe_percentage,
    calculate_trade_duration
)
from utils.validators import (
    validate_symbol,
    validate_price,
    validate_time_format,
    validate_trade_logic,
    validate_stop_loss_direction
)
from config.constants import TRADE_DIRECTIONS, TRADING_ENVIRONMENTS, GRADE_OPTIONS
from PIL import Image
from utils.cache_manager import clear_cache_after_trade_operation
from utils.screenshot_manager import ScreenshotUploader, save_screenshots
from typing import Optional
from utils.png_icons import *
import logging

logger = logging.getLogger(__name__)

st.set_page_config(page_title="Log Trade", page_icon="📝", layout="wide")

# =============================================================================
# FIX 5: Extended trading environments (covers constants.py not yet updated)
# These are merged with whatever TRADING_ENVIRONMENTS has, deduplication safe.
# =============================================================================
_EXTRA_ENVS = ["Trending UP", "Trending DOWN", "Trend Shift"]
EXTENDED_TRADING_ENVIRONMENTS = TRADING_ENVIRONMENTS + [
    e for e in _EXTRA_ENVS if e not in TRADING_ENVIRONMENTS
]

# =============================================================================
# FIX 2: Session state clearing helper
# Clears ALL smart_input_ keys, known widget keys, and screenshot keys
# so the form is completely fresh after every open/close action.
# =============================================================================
def clear_log_trade_session_state():
    """Wipe all log-trade related session state for a clean fresh form."""
    keys_to_delete = []
    for key in list(st.session_state.keys()):
        # Smart number input backing store
        if key.startswith("smart_input_"):
            keys_to_delete.append(key)
        # Widget keys used in this page (open trade form)
        if key.startswith("open_") or key.startswith("close_") or key.startswith("text_open_") or key.startswith("text_close_"):
            keys_to_delete.append(key)
        # Screenshot uploader state
        if key.startswith("screenshots_"):
            keys_to_delete.append(key)
    for key in keys_to_delete:
        try:
            del st.session_state[key]
        except KeyError:
            pass


# ============================================================================
# SMART NUMBER INPUT FUNCTIONS (Inline)
# ============================================================================

def format_number_display(value: Optional[float], max_decimals: int = 8) -> str:
    """Format number for display by removing unnecessary trailing zeros"""
    if value is None or value == 0:
        return ""
    formatted = f"{value:.{max_decimals}f}"
    if '.' in formatted:
        formatted = formatted.rstrip('0').rstrip('.')
    return formatted


def parse_number_input(text: str) -> Optional[float]:
    """Parse user input text to float"""
    if not text or text.strip() == "":
        return None
    try:
        value = float(text.strip())
        return value if value != 0 else None
    except ValueError:
        return None


def smart_number_input(
    label: str,
    key: str,
    placeholder: str = "Enter value...",
    min_value: Optional[float] = None,
    max_value: Optional[float] = None,
    max_decimals: int = 8,
    help_text: Optional[str] = None,
    required: bool = False
) -> Optional[float]:
    """Smart number input that avoids ugly 0.00000000 defaults"""
    display_label = f"{label}*" if required else label
    session_key = f"smart_input_{key}"
    current_text = st.session_state.get(session_key, "")

    user_input = st.text_input(
        display_label,
        value=current_text,
        placeholder=placeholder,
        key=f"text_{key}",
        help=help_text
    )

    parsed_value = parse_number_input(user_input)

    if user_input.strip() != "":
        if parsed_value is None:
            st.error(f"[ X ] Invalid number format")
            return None
        if min_value is not None and parsed_value < min_value:
            st.error(f"[ X ] Value must be at least {min_value}")
            return None
        if max_value is not None and parsed_value > max_value:
            st.error(f"[ X ] Value must not exceed {max_value}")
            return None

    st.session_state[session_key] = user_input
    return parsed_value


def smart_percentage_input(
    label: str,
    key: str,
    placeholder: str = "Enter percentage...",
    help_text: Optional[str] = None,
    required: bool = False
) -> Optional[float]:
    """Smart percentage input (0-100%)"""
    return smart_number_input(
        label=label,
        key=key,
        placeholder=placeholder,
        min_value=0.0,
        max_value=100.0,
        max_decimals=2,
        help_text=help_text,
        required=required
    )


def smart_price_input(
    label: str,
    key: str,
    placeholder: str = "Enter price...",
    crypto_precision: bool = True,
    help_text: Optional[str] = None,
    required: bool = False
) -> Optional[float]:
    """Smart price input for trading prices"""
    decimals = 8 if crypto_precision else 2
    return smart_number_input(
        label=label,
        key=key,
        placeholder=placeholder,
        min_value=0.0,
        max_decimals=decimals,
        help_text=help_text,
        required=required
    )


def get_number_or_zero(value: Optional[float]) -> float:
    """Convert None to 0.0 for database operations"""
    return value if value is not None else 0.0


# ============================================================================
# MAIN PAGE
# ============================================================================

icon_header("icons/log_trade.png", "Log Trade", level="h1")
st.markdown("Record new trades or close existing trades")
st.markdown("---")

db_path = get_database_path()


# FIX 2 (REAL FIX): Form version counter — incrementing this forces ALL widget
# keys to change, giving a genuinely blank form on next render.
if 'log_trade_form_version' not in st.session_state:
    st.session_state['log_trade_form_version'] = 0

_fv = st.session_state['log_trade_form_version']  # short alias used in all keys below

accounts = get_all_accounts(db_path)
strategies = get_all_strategies(db_path)

if not accounts:
    st.warning("[ ! ] No accounts found. Please create an account first.")
    st.stop()

account_options = {f"{acc['account_name']} (${acc['current_equity']:,.2f})": acc for acc in accounts}
selected_account_name = st.selectbox("Select Account*", options=list(account_options.keys()))
selected_account = account_options[selected_account_name]

st.markdown("---")

trade_mode = st.radio(
    "Select Action",
    options=["🗎 Log New Trade", "🔒︎ Close Existing Trade"],
    horizontal=True
)

st.markdown("---")

# =============================================================================
# MODE 1: OPEN TRADE
# =============================================================================

if trade_mode == "🗎 Log New Trade":

    st.subheader("🗎 Log New Trade")

    icon_header("icons/trade_details.png", "Trade Details", level="h3")

    col1, col2 = st.columns(2)

    with col1:
        symbol = st.text_input("Symbol*", placeholder="BTCUSDT", key="open_symbol").upper()
        direction = st.selectbox("Direction*", options=TRADE_DIRECTIONS, key="open_direction")

    with col2:
        entry_date = st.date_input("Entry Date*", value=date.today(), key="open_date")
        entry_time = st.text_input("Entry Time* (HH:MM)", placeholder="14:30", key="open_time")

    st.markdown("---")

    # =========================================================================
    # FIX 5: Trade Setup — extended Trading Environment dropdown
    # =========================================================================
    icon_header("icons/trade_setup.png", "Trade Setup", level="h3")

    col_s1, col_s2 = st.columns(2)

    with col_s1:
        trading_env = st.selectbox(
            "Trading Environment",
            options=[""] + EXTENDED_TRADING_ENVIRONMENTS,
            key="open_env"
        )
        strategy_options = ["No Strategy"] + [s['strategy_name'] for s in strategies]
        selected_strategy = st.selectbox("Strategy", options=strategy_options, key="open_strat")

    with col_s2:
        trigger = st.text_input("Trigger", placeholder="e.g., Breakout", key="open_trigger")

    setup_idea = st.text_area("Setup Idea", placeholder="Describe your setup...", key="open_idea")

    st.markdown("---")

    icon_header("icons/prices.png", "Entry Prices & Position Allocation", level="h3")

    num_entries = st.number_input("Number of Entry Levels", min_value=1, max_value=10, value=1, step=1, key="open_num_entries")

    entry_list = []
    total_entry_allocation = 0.0

    for idx in range(int(num_entries)):
        st.markdown(f"**Entry Level #{idx + 1}**")

        col_e1, col_e2 = st.columns([3, 1])

        with col_e1:
            e_price = smart_price_input(
                label="Entry Price",
                key=f"open_entry_p_{idx}",
                placeholder="Enter entry price...",
                crypto_precision=True,
                help_text="Price at which you entered this portion"
            )

        with col_e2:
            e_alloc = smart_percentage_input(
                label="Allocation %",
                key=f"open_entry_a_{idx}",
                placeholder="Enter %...",
                help_text="Percentage of total position"
            )

        if e_price is not None and e_alloc is not None:
            entry_list.append({'price': e_price, 'allocation': e_alloc})
            total_entry_allocation += e_alloc

        if e_alloc is not None:
            remaining = 100.0 - total_entry_allocation
            if remaining < 0:
                st.error(f"[ ! ] Over-allocated! {abs(remaining):.2f}% over limit")
            elif remaining > 0:
                st.info(f"Allocation left: {remaining:.2f}%")
            else:
                st.success(f"[ OK ] Fully allocated (100%)")

    st.markdown("---")

    if total_entry_allocation > 100.0:
        st.error(f"[ X ] **Total Allocation: {total_entry_allocation:.2f}%** - Exceeds 100%!")
    elif abs(total_entry_allocation - 100.0) < 0.01:
        st.success(f"[ OK ] **Total Allocation: {total_entry_allocation:.2f}%** - Complete")
    elif total_entry_allocation > 0:
        st.warning(f"[ ! ] **Total Allocation: {total_entry_allocation:.2f}%** - Incomplete")
    else:
        st.info("Total Allocation: 0.00%")

    weighted_avg_entry = 0.0

    if entry_list and total_entry_allocation > 0:
        weighted_sum = sum(e['price'] * e['allocation'] for e in entry_list)
        weighted_avg_entry = weighted_sum / total_entry_allocation
        st.info(f"**Weighted Average Entry Price:** ${weighted_avg_entry:.8f}")

    st.markdown("---")

    icon_header("icons/balance.png", "Risk Management", level="h3")

    col_r1, col_r2, col_r3 = st.columns(3)

    with col_r1:
        stop_loss = smart_price_input(
            label="Stop Loss",
            key="open_stop",
            placeholder="Enter stop loss...",
            required=True
        )

    with col_r2:
        # FIX 1: Target is always optional — label reflects this, no asterisk
        target = smart_price_input(
            label="Target (optional)",
            key="open_target",
            placeholder="Enter target..."
        )

    with col_r3:
        fta = smart_price_input(
            label="FTA",
            key="open_fta",
            placeholder="Enter FTA..."
        )

    col_r4, col_r5 = st.columns(2)

    with col_r4:
        risk_type = st.radio("Risk Type", ["Percentage", "Dollar Amount"], key="open_risk_type")

        if risk_type == "Percentage":
            risk_pct = st.number_input("Risk %*", min_value=0.0, max_value=100.0, value=1.0, step=0.01, key="open_risk_pct")
            risk_amt = selected_account['current_equity'] * (risk_pct / 100.0)
        else:
            risk_amt = st.number_input("Risk Amount ($)*", min_value=0.0, value=100.0, step=1.0, key="open_risk_amt")
            risk_pct = (risk_amt / selected_account['current_equity'] * 100.0) if selected_account['current_equity'] > 0 else 0.0

    with col_r5:
        st.markdown("**Calculated Values**")
        st.write(f"Risk Amount: ${risk_amt:,.2f}")
        st.write(f"Risk %: {risk_pct:.2f}%")

        # Prospective R only shown when target is actually provided
        if (weighted_avg_entry is not None and weighted_avg_entry > 0 and
                stop_loss is not None and stop_loss > 0 and
                target is not None and target > 0):
            prosp_r = calculate_prospective_r(weighted_avg_entry, target, stop_loss, direction)
            st.write(f"**Prospective R:** {prosp_r:.2f}R")
        else:
            st.write("Prospective R: N/A (no target set)")
            prosp_r = 0.0

    within_risk = st.checkbox("Within Overall Risk Limit", value=True, key="open_within_risk")

    st.markdown("---")

    icon_header("icons/calculator.png", "Position Size Calculator", level="h3")

    col_calc1, col_calc2, col_calc3 = st.columns(3)

    with col_calc1:
        st.caption("**Entry Price**")
        if weighted_avg_entry is not None and weighted_avg_entry > 0:
            st.code(f"${weighted_avg_entry:.8f}")
        else:
            st.warning("Not set")

    with col_calc2:
        st.caption("**Stop Loss**")
        if stop_loss is not None and stop_loss > 0:
            st.code(f"${stop_loss:.8f}")
        else:
            st.warning("Not set")

    with col_calc3:
        st.caption("**Risk Amount**")
        st.code(f"${risk_amt:.2f}")

    calculated_pos = 0.0

    if (weighted_avg_entry is not None and weighted_avg_entry > 0 and
            stop_loss is not None and stop_loss > 0 and risk_amt > 0):
        calculated_pos = calculate_position_size(
            selected_account['current_equity'],
            risk_pct,
            weighted_avg_entry,
            stop_loss,
            direction
        )

        if calculated_pos > 0:
            st.success(f"[ OK ] **Recommended Position Size:** {calculated_pos:.8f} units")
        else:
            st.error("[ X ] Cannot calculate - invalid inputs")
            calculated_pos = 0.0
    else:
        st.warning("[ ! ] Set entry price, stop loss, and risk to calculate")

    st.markdown("---")

    icon_header("icons/final_pos_size.png", "Final Position Size", level="h3")

    col_pos1, col_pos2 = st.columns([2, 1])

    with col_pos1:
        position_placeholder = f"Recommended: {calculated_pos:.8f}" if calculated_pos > 0 else "Enter position size..."

        position_size = smart_number_input(
            label="Position Size (units)",
            key="open_position",
            placeholder=position_placeholder,
            min_value=0.0,
            max_decimals=8,
            help_text="Total units to trade",
            required=True
        )

        if position_size is None and calculated_pos > 0:
            position_size = calculated_pos

    with col_pos2:
        if calculated_pos > 0:
            if position_size is not None and abs(position_size - calculated_pos) < 0.00000001:
                st.caption("[ OK ] Using calculated")
            else:
                st.caption("[ ! ] Manual override")
        else:
            st.caption("⌨ Manual entry")

    st.markdown("---")

    # =========================================================================
    # FIX 4: Commission field — Open Trade
    # =========================================================================
    icon_header("icons/notes.png", "Trade Notes & Commission", level="h3")

    trade_notes = st.text_area("Trade Notes Before/Entry", placeholder="Your thoughts...", key="open_notes")

    commission_open = smart_number_input(
        label="Commission (optional)",
        key="open_commission",
        placeholder="e.g., 0.10",
        min_value=0.0,
        max_decimals=8,
        help_text="Broker commission/fee for this trade entry"
    )

    st.markdown("---")

    # MULTI-SCREENSHOT UPLOADER
    entry_uploader = ScreenshotUploader(
        key_prefix="entry_open",
        trade_type="ENTRY",
        max_screenshots=5,
        show_preview=True
    )

    entry_screenshots = entry_uploader.render()

    st.markdown("---")

    with st.form("open_trade_submit_form", clear_on_submit=False):
        icon_header("icons/submit.png", "Submit Trade", level="h3")
        st.info("Review all fields above, then click the button below to open the trade")

        col_sb1, col_sb2, col_sb3 = st.columns([1, 1, 1])

        with col_sb2:
            submit_open = st.form_submit_button("OPEN TRADE", type="primary", use_container_width=True)

        if submit_open:
            errors = []

            valid_sym, sym_err = validate_symbol(symbol)
            if not valid_sym:
                errors.append(sym_err)

            if weighted_avg_entry is None or weighted_avg_entry <= 0:
                errors.append("Entry price must be greater than zero")

            if total_entry_allocation > 100.0:
                errors.append(f"Total allocation ({total_entry_allocation:.2f}%) exceeds 100%")
            elif total_entry_allocation <= 0:
                errors.append("Entry allocation cannot be zero")

            if stop_loss is not None and stop_loss > 0 and weighted_avg_entry > 0:
                valid_sl, sl_err = validate_stop_loss_direction(weighted_avg_entry, stop_loss, direction)
                if not valid_sl:
                    errors.append(sl_err)

            valid_time, time_err = validate_time_format(entry_time)
            if not valid_time:
                errors.append(time_err)

            # FIX 1: Only validate trade logic (SL/Target relationship)
            # when a target is actually provided. Target is always optional.
            if target is not None and target > 0 and weighted_avg_entry and stop_loss:
                valid_logic, logic_err = validate_trade_logic(weighted_avg_entry, stop_loss, target, direction)
                if not valid_logic:
                    errors.append(logic_err)

            if position_size is None or position_size <= 0:
                errors.append("Position size must be greater than zero")

            if errors:
                st.error("### [ X ] Validation Errors:")
                for err in errors:
                    st.error(f"• {err}")
            else:
                strat_id = None
                if selected_strategy != "No Strategy":
                    for s in strategies:
                        if s['strategy_name'] == selected_strategy:
                            strat_id = s['strategy_id']
                            break

                trade_data = {
                    'account_id': selected_account['account_id'],
                    'symbol': symbol,
                    'direction': direction,
                    'strategy_id': strat_id,
                    'entry_date': entry_date.strftime("%Y-%m-%d"),
                    'entry_time': entry_time,
                    'entry_price': weighted_avg_entry,
                    'trading_environment': trading_env if trading_env else None,
                    'trigger': trigger if trigger else None,
                    'multi_entry_price': weighted_avg_entry,
                    'stop_loss': stop_loss,
                    'target': target,                          # None is valid
                    'risk_amount': risk_amt,
                    'risk_percentage': risk_pct,
                    'position_size': position_size,
                    'fta': fta,
                    'prospective_r': prosp_r if prosp_r > 0 else None,
                    'within_risk_limit': within_risk,
                    'setup_idea': setup_idea if setup_idea else None,
                    'trade_notes_entry': trade_notes if trade_notes else None,
                    'commission': commission_open if commission_open else None,  # FIX 4
                }

                new_trade_id = create_trade(db_path, trade_data)

                if new_trade_id:
                    st.session_state['just_opened_trade_id'] = new_trade_id

                    if entry_screenshots:
                        st.session_state['pending_entry_ss'] = {
                            'trade_id': new_trade_id,
                            'screenshots': entry_screenshots
                        }

                    clear_cache_after_trade_operation('open')
                    # FIX 2: Clear all form state before rerun
                    clear_log_trade_session_state()
                    st.rerun()
                else:
                    st.error("[ X ] Failed to create trade in database")

    # SUCCESS MESSAGE & SCREENSHOT UPLOAD
    if 'just_opened_trade_id' in st.session_state and st.session_state['just_opened_trade_id']:
        tid = st.session_state['just_opened_trade_id']

        st.success(f"[ OK ] **Trade #{tid} opened successfully!**")

        clear_cache_after_trade_operation(operation='open')

        if 'pending_entry_ss' in st.session_state:
            ss_data = st.session_state['pending_entry_ss']
            ss_dir = get_trade_screenshot_dir(ss_data['trade_id'])

            successful, failed = save_screenshots(
                trade_id=ss_data['trade_id'],
                screenshots=ss_data['screenshots'],
                trade_type='ENTRY',
                screenshot_dir=ss_dir,
                db_add_function=lambda trade_id, screenshot_type, file_path, category:
                    add_screenshot(db_path, trade_id, screenshot_type, file_path, category)
            )

            if successful > 0:
                st.success(f"[ OK ] {successful} screenshot(s) uploaded successfully!")
            if failed > 0:
                st.warning(f"[ ! ] {failed} screenshot(s) failed to upload")

            del st.session_state['pending_entry_ss']

        st.balloons()
        del st.session_state['just_opened_trade_id']

        col_n1, col_n2, col_n3 = st.columns(3)

        with col_n1:
            if st.button("Log Another Trade", use_container_width=True):
                clear_log_trade_session_state()  # FIX 2
                st.rerun()

        with col_n2:
            # FIX 3: Corrected page path (single underscore, matches actual filename)
            if st.button("Dashboard", use_container_width=True):
                st.switch_page("pages/1_Dashboard.py")

        with col_n3:
            # FIX 3: Corrected page path
            if st.button("Mental Dev", use_container_width=True):
                st.switch_page("pages/5_Mental_Development.py")


# =============================================================================
# MODE 2: CLOSE TRADE
# =============================================================================

else:

    st.subheader("🔒︎ Close Existing Trade")

    # =========================================================================
    # STEP 1: SUCCESS MESSAGE (executes AFTER form submission and rerun)
    # =========================================================================

    if st.session_state.get('show_close_success', False) and 'trade_close_success' in st.session_state:

        success_data = st.session_state['trade_close_success']

        closed_trade_id  = success_data['trade_id']
        closed_symbol    = success_data['symbol']
        closed_direction = success_data['direction']
        closed_pnl       = success_data['pnl']
        closed_commission = success_data.get('commission', 0.0) or 0.0   # FIX 4
        closed_net_pnl   = success_data.get('net_pnl', closed_pnl)        # FIX 4
        closed_r         = success_data['r_value']
        closed_roe       = success_data['roe']

        st.markdown("---")
        st.success("[ OK ] Trade Closed Successfully!")

        col_success1, col_success2, col_success3, col_success4 = st.columns(4)

        with col_success1:
            st.metric(label="Trade ID", value=f"#{closed_trade_id}")
        with col_success2:
            st.metric(label="Symbol", value=closed_symbol)
        with col_success3:
            st.metric(label="Direction", value=closed_direction)
        with col_success4:
            st.metric(label="R-Multiple", value=f"{closed_r:.2f}R", delta="Result" if closed_r >= 0 else "Loss")

        st.markdown("---")

        # FIX 4: Show PnL breakdown with commission
        col_finance1, col_finance2, col_finance3, col_finance4 = st.columns(4)

        with col_finance1:
            delta_pnl = f"+${closed_pnl:,.2f}" if closed_pnl > 0 else f"${closed_pnl:,.2f}"
            st.metric(label="Gross P&L", value=f"${closed_pnl:,.2f}", delta=delta_pnl)

        with col_finance2:
            st.metric(label="Commission", value=f"-${closed_commission:,.2f}")

        with col_finance3:
            delta_net = f"+${closed_net_pnl:,.2f}" if closed_net_pnl > 0 else f"${closed_net_pnl:,.2f}"
            st.metric(label="Net P&L", value=f"${closed_net_pnl:,.2f}", delta=delta_net)

        with col_finance4:
            st.metric(label="ROE", value=f"{closed_roe:+.2f}%")

        st.info("Account equity has been updated automatically with this P&L")

        clear_cache_after_trade_operation('close')

        # UPLOAD EXIT SCREENSHOTS
        if 'pending_exit_ss' in st.session_state:
            ss_data = st.session_state['pending_exit_ss']
            ss_dir = get_trade_screenshot_dir(ss_data['trade_id'])

            logger.info(f"Uploading {len(ss_data['screenshots'])} exit screenshot(s) for trade {ss_data['trade_id']}")

            successful, failed = save_screenshots(
                trade_id=ss_data['trade_id'],
                screenshots=ss_data['screenshots'],
                trade_type='EXIT',
                screenshot_dir=ss_dir,
                db_add_function=lambda trade_id, screenshot_type, file_path, category:
                    add_screenshot(db_path, trade_id, screenshot_type, file_path, category)
            )

            if successful > 0:
                st.success(f"[ OK ] {successful} exit screenshot(s) uploaded successfully!")
            if failed > 0:
                st.warning(f"[ ! ] {failed} screenshot(s) failed to upload")

            del st.session_state['pending_exit_ss']

        st.balloons()
        st.markdown("---")
        st.markdown("### Next Action")

        col_action1, col_action2, col_action3, col_action4 = st.columns(4)

        with col_action1:
            if st.button("Close Another Trade", type="primary", use_container_width=True, key="btn_close_another"):
                st.session_state['show_close_success'] = False
                if 'trade_close_success' in st.session_state:
                    del st.session_state['trade_close_success']
                # FIX 2: clear form state
                clear_log_trade_session_state()
                st.rerun()

        with col_action2:
            if st.button("Log New Trade", use_container_width=True, key="btn_log_new"):
                st.session_state['show_close_success'] = False
                if 'trade_close_success' in st.session_state:
                    del st.session_state['trade_close_success']
                # FIX 2: clear form state
                clear_log_trade_session_state()
                st.rerun()

        with col_action3:
            # FIX 3: Corrected page path
            if st.button("View Dashboard", use_container_width=True, key="btn_view_dashboard"):
                st.session_state['show_close_success'] = False
                if 'trade_close_success' in st.session_state:
                    del st.session_state['trade_close_success']
                st.switch_page("pages/1_Dashboard.py")

        with col_action4:
            # FIX 3: Corrected page path
            if st.button("View Statistics", use_container_width=True, key="btn_view_statistics"):
                st.session_state['show_close_success'] = False
                if 'trade_close_success' in st.session_state:
                    del st.session_state['trade_close_success']
                st.switch_page("pages/7_Statistics.py")

        st.stop()

    # =========================================================================
    # STEP 2: GET OPEN TRADES
    # =========================================================================

    open_trades = get_all_trades(db_path, selected_account['account_id'], status='OPEN')

    if not open_trades:
        st.info("[ ! ] No open trades for this account")
        st.stop()

    trade_opts = {
        f"#{t['trade_id']} - {t['symbol']} {t['direction']} | Entry: ${t['entry_price']:.4f} | {t['entry_date']}": t['trade_id']
        for t in open_trades
    }

    sel_trade_str = st.selectbox("Select Trade to Close", options=list(trade_opts.keys()))
    sel_trade_id = trade_opts[sel_trade_str]

    trade = get_trade_by_id(db_path, sel_trade_id)

    if not trade:
        st.error("[ X ] Trade not found")
        st.stop()

    # =========================================================================
    # STEP 3: TRADE SUMMARY
    # =========================================================================

    with st.expander("Trade Summary", expanded=True):
        col1, col2, col3 = st.columns(3)

        with col1:
            st.write(f"**ID:** #{trade['trade_id']}")
            st.write(f"**Symbol:** {trade['symbol']}")
            st.write(f"**Direction:** {trade['direction']}")

        with col2:
            st.write(f"**Entry:** ${trade['entry_price']:.8f}")
            st.write(f"**Date:** {trade['entry_date']} {trade['entry_time']}")
            st.write(f"**Position:** {trade['position_size']:.8f}")

        with col3:
            st.write(f"**Stop:** ${trade['stop_loss']:.8f}")
            st.write(f"**Target:** ${trade['target']:.8f}" if trade.get('target') else "**Target:** N/A")
            st.write(f"**Risk:** ${trade['risk_amount']:.2f}")

    st.markdown("---")

    # =========================================================================
    # STEP 4: EXIT DETAILS
    # =========================================================================

    icon_header("icons/exit_details.png", "Exit Details", level="h3")

    col_ex1, col_ex2 = st.columns(2)

    with col_ex1:

        entry_date_parsed = date.fromisoformat(trade['entry_date'])

        exit_date = st.date_input(
            "Exit Date",
            value=max(date.today(), entry_date_parsed),  # default to today but never before entry
            min_value=entry_date_parsed,                  # widget physically blocks earlier dates
            key="close_exit_date"
        )

    with col_ex2:
        exit_time = st.text_input("Exit Time (HH:MM)", placeholder="16:30", key="close_exit_time")

    st.markdown("---")

    # =========================================================================
    # STEP 5: EXIT PRICES & ALLOCATION
    # =========================================================================

    icon_header("icons/prices.png", "Exit Prices & Position Allocation", level="h3")
    st.caption(f"Total Position Size: {trade['position_size']:.8f} units")
    st.caption(f"Average Entry Price: ${trade['entry_price']:.8f}")

    num_exits = st.number_input("Number of Exit Levels", min_value=1, max_value=10, value=1, step=1, key="close_num_exits")

    exit_list = []
    total_exit_allocation = 0.0

    for idx in range(int(num_exits)):
        st.markdown(f"**Exit Level #{idx + 1}**")

        col_x1, col_x2, col_x3, col_x4 = st.columns([2, 1, 1, 1])

        with col_x1:
            x_price = smart_price_input(
                label="Exit Price",
                key=f"close_exit_p_{idx}",
                placeholder="Enter exit price...",
                crypto_precision=True,
                help_text="Price at which this portion was sold"
            )

        with col_x2:
            x_alloc = smart_percentage_input(
                label="Allocation %",
                key=f"close_exit_a_{idx}",
                placeholder="Enter %...",
                help_text="Percentage of total position"
            )

        if x_alloc is not None:
            x_units = (trade['position_size'] * x_alloc) / 100.0
        else:
            x_units = 0.0

        with col_x3:
            st.caption("Units")
            if x_units > 0:
                st.success(f"{x_units:.8f}")
            else:
                st.info("0.00000000")

        with col_x4:
            st.caption("P&L")
            if x_price is not None and x_units > 0:
                level_pnl = calculate_pnl(trade['entry_price'], x_price, x_units, trade['direction'])
                if level_pnl > 0:
                    st.success(f"${level_pnl:,.2f}")
                elif level_pnl < 0:
                    st.error(f"${level_pnl:,.2f}")
                else:
                    st.info(f"${level_pnl:,.2f}")
            else:
                st.info("$0.00")

        if x_price is not None and x_alloc is not None:
            exit_list.append({'price': x_price, 'allocation': x_alloc, 'units': x_units})
            total_exit_allocation += x_alloc

        if x_alloc is not None:
            remaining = 100.0 - total_exit_allocation
            if remaining < 0:
                st.error(f"[ ! ] Over-allocated! {abs(remaining):.2f}% over limit")
            elif remaining > 0:
                st.info(f"Remaining: {remaining:.2f}%")
            else:
                st.success(f"[ OK ] Complete: 100%")

    st.markdown("---")

    if total_exit_allocation > 100.0:
        st.error(f"[ X ] **Total Allocation: {total_exit_allocation:.2f}%** - Exceeds 100%!")
    elif abs(total_exit_allocation - 100.0) < 0.01:
        st.success(f"[ OK ] **Total Allocation: {total_exit_allocation:.2f}%** - Complete exit")
    elif total_exit_allocation > 0:
        st.warning(f"[ ! ] **Total Allocation: {total_exit_allocation:.2f}%** - Partial exit")
    else:
        st.info("Total Allocation: 0.00%")

    weighted_avg_exit = 0.0

    if exit_list and total_exit_allocation > 0:
        weighted_sum = sum(x['price'] * x['allocation'] for x in exit_list)
        weighted_avg_exit = weighted_sum / total_exit_allocation
        st.info(f"**Weighted Average Exit Price:** ${weighted_avg_exit:.8f}")

    st.markdown("---")

    # =========================================================================
    # STEP 6: TRADE RESULTS
    # =========================================================================

    icon_header("icons/list.png", "Trade Results", level="h3")

    col_res1, col_res2 = st.columns(2)

    with col_res1:
        target_hit = st.checkbox("Target Hit", key="close_target_hit")
        stop_hit   = st.checkbox("Stop Loss Hit", key="close_stop_hit")

    with col_res2:
        st.markdown("**MAE/MFE (Optional)**")
        mae = smart_price_input(
            label="MAE (Max Adverse Excursion)",
            key="close_mae",
            placeholder="Enter MAE...",
            help_text="Worst price during trade"
        )
        mfe = smart_price_input(
            label="MFE (Max Favorable Excursion)",
            key="close_mfe",
            placeholder="Enter MFE...",
            help_text="Best price during trade"
        )

    st.markdown("---")

    # =========================================================================
    # FIX 4: Commission field — Close Trade
    # =========================================================================
    icon_header("icons/balance.png", "Commission", level="h3")

    commission_close = smart_number_input(
        label="Commission (optional)",
        key="close_commission",
        placeholder="e.g., 0.10",
        min_value=0.0,
        max_decimals=8,
        help_text="Total broker commission/fees for this exit"
    )

    st.markdown("---")

    # =========================================================================
    # STEP 7: CALCULATED METRICS PREVIEW
    # =========================================================================

    icon_header("icons/calculator.png", "Calculated Metrics (Preview)", level="h3")

    if len(exit_list) > 0 and weighted_avg_exit > 0:

        total_pnl = 0.0

        for exit_level in exit_list:
            level_pnl = calculate_pnl(
                trade['entry_price'],
                exit_level['price'],
                exit_level['units'],
                trade['direction']
            )
            total_pnl += level_pnl

        # FIX 4: Net PnL = Gross PnL - Commission
        commission_val = commission_close if commission_close is not None else 0.0
        net_pnl = total_pnl - commission_val

        total_r = calculate_total_r(
            entry_price=trade['entry_price'],
            exit_price=weighted_avg_exit,
            stop_loss=trade['stop_loss'],
            direction=trade['direction'],
            pnl=net_pnl,
            risk_amount=trade['risk_amount']
        )

        roe = calculate_roe_percentage(total_pnl, trade['risk_amount'])

        duration = 0
        try:
            ent_dt = datetime.strptime(f"{trade['entry_date']} {trade['entry_time']}", "%Y-%m-%d %H:%M")
            ex_dt  = datetime.strptime(f"{exit_date.strftime('%Y-%m-%d')} {exit_time if exit_time else '00:00'}", "%Y-%m-%d %H:%M")
            duration = calculate_trade_duration(ent_dt, ex_dt)
        except Exception:
            duration = 0

        col_c1, col_c2, col_c3, col_c4, col_c5 = st.columns(5)

        with col_c1:
            color = "success" if total_pnl > 0 else ("error" if total_pnl < 0 else "info")
            getattr(st, color)(f"**Gross P&L:** ${total_pnl:,.2f}")

        with col_c2:
            st.warning(f"**Commission:** -${commission_val:,.2f}")

        with col_c3:
            color = "success" if net_pnl > 0 else ("error" if net_pnl < 0 else "info")
            getattr(st, color)(f"**Net P&L:** ${net_pnl:,.2f}")

        with col_c4:
            if total_r >= 1.0:
                st.success(f"**R:** {total_r:.2f}R")
            elif total_r >= 0:
                st.warning(f"**R:** {total_r:.2f}R")
            else:
                st.error(f"**R:** {total_r:.2f}R")

        with col_c5:
            st.info(f"**Duration:** {duration} min")

    else:
        st.warning("[ ! ] Enter exit prices and allocations to see calculations")

    st.markdown("---")

    # =========================================================================
    # STEP 8: TRADE GRADES
    # =========================================================================

    icon_header("icons/grade.png", "Trade Grades", level="h3")

    col_g1, col_g2 = st.columns(2)

    with col_g1:
        grade_mental = st.selectbox("Grade Mentally", ["Not Graded"] + GRADE_OPTIONS, key="close_grade_mental")

    with col_g2:
        grade_tech = st.selectbox("Grade Technically", ["Not Graded"] + GRADE_OPTIONS, key="close_grade_tech")

    st.markdown("---")

    # =========================================================================
    # STEP 9: TRADE NOTES
    # =========================================================================

    icon_header("icons/notes.png", "Trade Notes", level="h3")

    notes_mgmt  = st.text_area("During Management", placeholder="How did you manage?", key="close_notes_mgmt")
    notes_close = st.text_area("Notes For Closing", placeholder="Why close here?", key="close_notes_close")
    reason_close = st.text_input("Reason", placeholder="e.g., Target hit", key="close_reason")
    final_notes = st.text_area("Final Notes", placeholder="Additional thoughts", key="close_final_notes")

    st.markdown("---")

    # =========================================================================
    # STEP 10: EXIT SCREENSHOTS
    # =========================================================================

    exit_uploader = ScreenshotUploader(
        key_prefix="exit_close",
        trade_type="EXIT",
        max_screenshots=5,
        show_preview=True
    )

    exit_screenshots = exit_uploader.render()

    st.markdown("---")

    # =========================================================================
    # STEP 11: FORM SUBMISSION
    # =========================================================================

    with st.form("close_trade_submit_form", clear_on_submit=False):

        icon_header("icons/submit.png", "Close Trade", level="h3")
        st.info("Review all fields above, then click the button below to close the trade")

        col_cs1, col_cs2, col_cs3 = st.columns([1, 1, 1])

        with col_cs2:
            submit_close = st.form_submit_button("CLOSE TRADE", type="primary", use_container_width=True)

        if submit_close:
            errors = []

            if weighted_avg_exit is None or weighted_avg_exit <= 0:
                errors.append("Exit price must be greater than zero")

            if total_exit_allocation > 100.0:
                errors.append(f"Total allocation ({total_exit_allocation:.2f}%) exceeds 100%")
            elif total_exit_allocation <= 0:
                errors.append("Exit allocation cannot be zero")

            if not exit_time:
                errors.append("Exit time is required")
            else:
                v_time, t_err = validate_time_format(exit_time)
                if not v_time:
                    errors.append(t_err)

            if errors:
                st.error("[ X ] Validation Errors:")
                for err in errors:
                    st.error(f"• {err}")
            else:
                # Step 1: gross PnL from all exit levels
                final_pnl = 0.0
                for exit_level in exit_list:
                    level_pnl = calculate_pnl(
                        trade['entry_price'],
                        exit_level['price'],
                        exit_level['units'],
                        trade['direction']
                    )
                    final_pnl += level_pnl

                # Step 2: commission and net PnL
                commission_val = commission_close if commission_close is not None else 0.0
                final_net_pnl  = final_pnl - commission_val

                # Step 3: R using dollar-based formula (immune to tiny stop distances)
                final_r = calculate_total_r(
                    entry_price=trade['entry_price'],
                    exit_price=weighted_avg_exit,
                    stop_loss=trade['stop_loss'],
                    direction=trade['direction'],
                    pnl=final_net_pnl,
                    risk_amount=trade['risk_amount']
                )

                # Step 4: ROE based on net PnL
                final_roe = calculate_roe_percentage(final_net_pnl, trade['risk_amount'])

                # Step 5: duration
                try:
                    ent_dt    = datetime.strptime(f"{trade['entry_date']} {trade['entry_time']}", "%Y-%m-%d %H:%M")
                    ex_dt     = datetime.strptime(f"{exit_date.strftime('%Y-%m-%d')} {exit_time}", "%Y-%m-%d %H:%M")
                    final_dur = calculate_trade_duration(ent_dt, ex_dt)
                except Exception:
                    final_dur = 0

                exit_data = {
                    'exit_date':              exit_date.strftime("%Y-%m-%d"),
                    'exit_time':              exit_time,
                    'multi_exit_price':       weighted_avg_exit,
                    'target_hit':             target_hit,
                    'stop_loss_hit':          stop_hit,
                    'mae':                    mae,
                    'mfe':                    mfe,
                    'trade_duration':         final_dur,
                    'total_r':                final_r,
                    'roe_percentage':         final_roe,
                    'pnl':                    final_net_pnl,   # net stored in DB and applied to equity
                    'commission':             commission_val,  # stored in its own column
                    'grade_mentally':         grade_mental if grade_mental != "Not Graded" else None,
                    'grade_technically':      grade_tech   if grade_tech   != "Not Graded" else None,
                    'trade_notes_management': notes_mgmt   if notes_mgmt   else None,
                    'trade_notes_closing':    notes_close  if notes_close  else None,
                    'reason_for_closing':     reason_close if reason_close else None,
                    'final_notes':            final_notes  if final_notes  else None,
                }

                success = update_trade_exit(db_path, sel_trade_id, exit_data)

                if success:
                    st.session_state['show_close_success'] = True
                    st.session_state['trade_close_success'] = {
                        'trade_id':  sel_trade_id,
                        'symbol':    trade['symbol'],
                        'direction': trade['direction'],
                        'pnl':       final_pnl,       # gross shown in success UI
                        'commission': commission_val,
                        'net_pnl':   final_net_pnl,   # net shown in success UI
                        'r_value':   final_r,
                        'roe':       final_roe,
                    }

                    exit_ss_key = "screenshots_exit_close"
                    if exit_ss_key in st.session_state and len(st.session_state[exit_ss_key]) > 0:
                        st.session_state['pending_exit_ss'] = {
                            'trade_id':    sel_trade_id,
                            'screenshots': st.session_state[exit_ss_key]
                        }
                        logger.info(f"Stored {len(st.session_state[exit_ss_key])} exit screenshot(s) for trade {sel_trade_id}")

                    clear_cache_after_trade_operation('close')
                    clear_log_trade_session_state()
                    st.rerun()

                else:
                    st.error("[ X ] Failed to close trade in database. Please check the logs.")

    st.markdown("---")
    st.caption("💡 Open trades → Record entries | Close trades → Record exits")
