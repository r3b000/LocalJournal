"""
Cache management utilities - PERFORMANCE OPTIMIZED
Handles Streamlit cache invalidation after database operations
"""

import streamlit as st
import logging

logger = logging.getLogger(__name__)


class CacheManager:
    """Centralized cache management for the application"""
    
    @staticmethod
    def invalidate_after_trade_open():
        """
        Invalidate caches after opening a new trade
        OPTIMIZED: Only clears account stats and recent trades
        """
        try:
            # Clear specific function caches
            from database.accounts_db import get_account_stats
            from database.trades_db import get_recent_trades, get_all_trades
            
            if hasattr(get_account_stats, 'clear'):
                get_account_stats.clear()
            if hasattr(get_recent_trades, 'clear'):
                get_recent_trades.clear()
            if hasattr(get_all_trades, 'clear'):
                get_all_trades.clear()
            
            logger.info("[ OK ] Cache invalidated after trade open")
        except Exception as e:
            logger.error(f"[ X ] Cache invalidation failed: {e}")
            # Fallback: clear all
            st.cache_data.clear()
    
    @staticmethod
    def invalidate_after_trade_close():
        """
        Invalidate caches after closing a trade
        OPTIMIZED: Clears all statistics and performance data
        """
        try:
            # Import all cached functions
            from database.accounts_db import get_account_stats
            from database.trades_db import get_recent_trades, get_all_trades
            from database.statistics_db import (
                get_performance_metrics,
                get_trade_distribution,
                get_performance_by_symbol,
                get_performance_by_strategy,
                get_performance_by_direction,
                get_all_closed_trades,
                get_all_statistics_batch
            )
            
            # Clear each cached function
            cached_functions = [
                get_account_stats,
                get_recent_trades,
                get_all_trades,
                get_performance_metrics,
                get_trade_distribution,
                get_performance_by_symbol,
                get_performance_by_strategy,
                get_performance_by_direction,
                get_all_closed_trades,
                get_all_statistics_batch
            ]
            
            for func in cached_functions:
                if hasattr(func, 'clear'):
                    func.clear()
            
            logger.info("[ OK ] Cache invalidated after trade close")
        except Exception as e:
            logger.error(f"[ X ] Cache invalidation failed: {e}")
            # Fallback: clear all
            st.cache_data.clear()
    
    @staticmethod
    def invalidate_after_trade_delete():
        """
        Invalidate ALL caches after deleting a trade
        Uses nuclear option to ensure all pages refresh
        """
        try:
            st.cache_data.clear()
            st.cache_resource.clear()
            logger.info("[ OK ] All caches cleared after trade deletion")
        except Exception as e:
            logger.error(f"[ X ] Failed to clear caches after deletion: {e}")

    
    @staticmethod
    def invalidate_all():
        """
        Nuclear option: clear ALL caches
        Use for account operations, data imports, etc.
        """
        try:
            st.cache_data.clear()
            logger.info("[ OK ] All caches cleared")
        except Exception as e:
            logger.error(f"[ X ] Failed to clear all caches: {e}")
    
    @staticmethod
    def invalidate_after_account_operation():
        """
        Invalidate caches after account operations
        (create, delete, equity update)
        """
        CacheManager.invalidate_all()
    
    @staticmethod
    def invalidate_after_strategy_operation():
        """
        Invalidate caches after strategy operations
        OPTIMIZED: Only clears strategy-related caches
        """
        try:
            from database.strategies_db import get_all_strategies, get_strategy_statistics
            from database.statistics_db import get_performance_by_strategy
            
            if hasattr(get_all_strategies, 'clear'):
                get_all_strategies.clear()
            if hasattr(get_strategy_statistics, 'clear'):
                get_strategy_statistics.clear()
            if hasattr(get_performance_by_strategy, 'clear'):
                get_performance_by_strategy.clear()
            
            logger.info("[ OK ] Cache invalidated after strategy operation")
        except Exception as e:
            logger.error(f"[ X ] Cache invalidation failed: {e}")
            st.cache_data.clear()


# Convenience functions (import these in your pages)
def clear_cache_after_trade_operation(operation: str = "generic"):
    """
    Convenience function for trade operations
    PERFORMANCE OPTIMIZED: Smart cache invalidation
    
    Args:
        operation: 'open', 'close', 'delete', or 'generic'
    """
    operation_map = {
        'open': CacheManager.invalidate_after_trade_open,
        'close': CacheManager.invalidate_after_trade_close,
        'delete': CacheManager.invalidate_after_trade_delete,
        'generic': CacheManager.invalidate_all
    }
    
    handler = operation_map.get(operation, CacheManager.invalidate_all)
    handler()


def clear_cache_after_account_operation():
    """Clear cache after account create/delete/update"""
    CacheManager.invalidate_after_account_operation()


def clear_cache_after_strategy_operation():
    """Clear cache after strategy create/delete"""
    CacheManager.invalidate_after_strategy_operation()
