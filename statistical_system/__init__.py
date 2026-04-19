"""
Statistical Trading System - Level 1

Система технических и статистических сигналов без ML.
Предназначена для работы с множеством монет одновременно.
"""

__version__ = "1.0.0"

from .signal_generator import StatisticalSignalGenerator, Signal
from .backtest_engine import BacktestEngine, BacktestResult, Trade
from .multi_asset_scanner import MultiAssetScanner
from .signal_ranker import SignalRanker
from .config import SignalConfig, BacktestConfig, ScannerConfig, get_preset

__all__ = [
    'StatisticalSignalGenerator',
    'Signal',
    'SignalConfig',
    'BacktestEngine',
    'BacktestConfig',
    'BacktestResult',
    'Trade',
    'MultiAssetScanner',
    'SignalRanker',
    'ScannerConfig',
    'get_preset',
]
