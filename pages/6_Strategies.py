"""
Strategies Page
Create and manage trading strategies
"""

import streamlit as st
from utils.paths import get_database_path
from database.strategies_db import (
    create_strategy,
    get_all_strategies,
    delete_strategy,
    get_strategy_statistics
)
from utils.validators import validate_strategy_name
from utils.formatters import format_currency, format_percentage

st.set_page_config(page_title="Strategies", page_icon="🎯", layout="wide")

####### ICONS

from utils.png_icons import icon_header


icon_header("icons/strategy.png", "Trading Strategies", level="h1")



st.markdown("Define and manage your trading strategies")
st.markdown("---")

db_path = get_database_path()

# Create Strategy Section
icon_header("icons/new_strategy.png", "Create New Strategy", level="h3")

with st.form("create_strategy_form"):
    strategy_name = st.text_input("Strategy Name*", placeholder="e.g., Breakout Strategy")
    
    description = st.text_area(
        "Description (Optional)",
        placeholder="Describe your strategy rules, entry criteria, exit rules, etc..."
    )
    
    submitted = st.form_submit_button("Create Strategy", type="primary")
    
    if submitted:
        valid, error = validate_strategy_name(strategy_name)
        
        if not valid:
            st.error(f"[ X ] {error}")
        else:
            strategy_id = create_strategy(db_path, strategy_name, description)
            
            if strategy_id:
                st.success(f"[ ✔ ] Strategy '{strategy_name}' created successfully!")
                from utils.cache_manager import clear_cache_after_strategy_operation
                clear_cache_after_strategy_operation()
                st.rerun()
            else:
                st.error("[ X ] Failed to create strategy. Strategy name might already exist.")

st.markdown("---")

# View Strategies Section
icon_header("icons/your_strategies.png", "Your Strategies", level="h3")

strategies = get_all_strategies(db_path)

if strategies:
    for strategy in strategies:
        with st.expander(f"**{strategy['strategy_name']}**", expanded=False):
            
            # Get strategy statistics
            stats = get_strategy_statistics(db_path, strategy['strategy_id'])
            
            col_strat1, col_strat2 = st.columns(2)
            
            with col_strat1:
                st.markdown("**Strategy Details**")
                st.write(f"**Strategy ID:** {strategy['strategy_id']}")
                st.write(f"**Strategy Name:** {strategy['strategy_name']}")
                st.write(f"**Created:** {strategy['created_at']}")
                
                if strategy['description']:
                    st.markdown("---")
                    st.markdown("**Description:**")
                    st.info(strategy['description'])
            
            with col_strat2:
                st.markdown("**Performance**")
                st.write(f"**Total Trades:** {stats['total_trades']}")
                st.write(f"**Closed Trades:** {stats['closed_trades']}")
                st.write(f"**Winning Trades:** {stats['winning_trades']}")
                st.write(f"**Losing Trades:** {stats['losing_trades']}")
                st.write(f"**Win Rate:** {format_percentage(stats['win_rate'])}")
                st.write(f"**Total P&L:** {format_currency(stats['total_pnl'])}")
                st.write(f"**Average P&L:** {format_currency(stats['avg_pnl'])}")
            
            # Delete button
            st.markdown("---")
            col_del1, col_del2, col_del3 = st.columns([2, 1, 2])
            
            with col_del2:
                if st.button(f"Delete Strategy", key=f"delete_strat_{strategy['strategy_id']}", type="secondary"):
                    st.session_state[f"confirm_delete_strat_{strategy['strategy_id']}"] = True
            
            # Confirmation
            if st.session_state.get(f"confirm_delete_strat_{strategy['strategy_id']}", False):
                st.warning("⚠ Are you sure? This will remove the strategy from all associated trades (trades will remain).")
                
                col_conf1, col_conf2 = st.columns(2)
                
                with col_conf1:
                    if st.button(f"[ ✔ ] Yes, Delete", key=f"confirm_strat_yes_{strategy['strategy_id']}", type="primary"):
                        if delete_strategy(db_path, strategy['strategy_id']):
                            st.success("Strategy deleted successfully!")
                            st.session_state[f"confirm_delete_strat_{strategy['strategy_id']}"] = False
                            clear_cache_after_strategy_operation()
                            st.session_state[f'confirm_delete_strat_{strategy["strategy_id"]}'] = False
                            st.rerun()
                        else:
                            st.error("Failed to delete strategy.")
                
                with col_conf2:
                    if st.button(f"[ X ] Cancel", key=f"confirm_strat_no_{strategy['strategy_id']}"):
                        st.session_state[f"confirm_delete_strat_{strategy['strategy_id']}"] = False
                        st.rerun()
else:
    st.info("[ ! ] No strategies found. Create your first strategy above!")

st.markdown("---")
st.caption("💡 Tip: Define clear strategies to track which setups work best for you.")
