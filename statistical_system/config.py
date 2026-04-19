"""
Конфигурация статистической торговой системы
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class SignalConfig:
    """Конфигурация для генерации сигналов"""
    
    # === Breakout Setup ===
    bb_period: int = 20
    bb_std: float = 2.0
    volume_threshold: float = 1.5  # 150% от средней
    
    # === Pullback Setup ===
    ema_fast: int = 50
    ema_slow: int = 200
    rsi_oversold: float = 40
    rsi_overbought: float = 60
    
    # === Mean Reversion Setup ===
    bb_lower_sigma: float = 2.0
    rsi_extreme_low: float = 30
    rsi_extreme_high: float = 70
    
    # === Volatility Expansion Setup ===
    atr_lookback: int = 14
    volatility_percentile: float = 0.2  # 20th percentile = low vol
    
    # === Фильтры ===
    min_confidence: float = 0.5  # минимум 2 из 4 сетапов
    # Глобальный тренд-фильтр
    trend_filter_enabled: bool = True  # требовать торговли по направлению тренда EMA
    require_adx: bool = False  # при включении дополнительно требовать силу тренда по ADX
    adx_period: int = 14
    adx_min: float = 20.0
    
    # === Какие сетапы использовать ===
    enabled_setups: List[str] = field(default_factory=lambda: [
        'breakout',
        'pullback',
        'mean_reversion',
        'volatility_expansion'
    ])


@dataclass
class BacktestConfig:
    """Конфигурация бэктеста"""
    
    # === Капитал ===
    initial_capital: float = 10000
    position_size_pct: float = 0.02  # 2% риска на сделку
    max_positions: int = 5  # макс. одновременных позиций
    
    # === Комиссии ===
    commission: float = 0.001  # 0.1% (Binance spot)
    slippage: float = 0.0005  # 0.05%
    
    # === TP/SL ===
    tp_atr_mult: float = 2.0
    sl_atr_mult: float = 1.0
    trailing_stop: bool = False
    trailing_stop_activation: float = 1.5  # активация трейлинга при +1.5 ATR
    
    # === Фильтры ===
    min_confidence: float = 0.5
    
    # === Управление рисками ===
    max_daily_loss_pct: float = 5.0  # стоп на день при -5%
    max_drawdown_pct: float = 20.0  # стоп при просадке -20%
    
    # === Временной выход ===
    enable_time_exit: bool = True  # включить закрытие по времени
    time_exit_candles: int = 48  # закрывать позицию по истечении N свечей, если нет TP/SL

    # === Логирование ===
    log_signals: bool = False
    signals_log_dir: str = 'statistical_system/signal_logs'


@dataclass
class ScannerConfig:
    """Конфигурация мультивалютного сканера"""
    
    # === Список монет для сканирования ===
    symbols: List[str] = field(default_factory=lambda: [
        'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT',
        'ADAUSDT', 'DOGEUSDT', 'DOTUSDT', 'LINKUSDT', 'LTCUSDT',
        'NEARUSDT', 'UNIUSDT', 'ATOMUSDT', 'AVAXUSDT', 'OPUSDT',
        'ARBUSDT', 'SUIUSDT', 'APTUSDT', 'AAVEUSDT', 'INJUSDT'
    ])
    
    # === Параметры данных ===
    timeframe: str = '30m'
    lookback_candles: int = 500  # сколько свечей загружать для анализа
    
    # === Обновление ===
    update_interval: int = 1800  # обновлять каждые 30 минут (в секундах)
    
    # === Фильтрация сигналов ===
    min_signal_confidence: float = 0.5
    max_signals_to_show: int = 10  # топ-N лучших сигналов
    
    # === Telegram уведомления ===
    send_telegram: bool = True
    telegram_only_high_confidence: bool = True  # только сигналы ≥0.75
    
    # === Logging ===
    verbose: bool = True
    save_results: bool = True
    results_dir: str = 'statistical_system/results'


# Предустановки для разных стилей торговли
PRESETS = {
    'conservative': SignalConfig(
        min_confidence=0.75,
        trend_filter_enabled=True,
        require_adx=True,
        adx_period=14,
        adx_min=20.0,
        enabled_setups=['pullback', 'mean_reversion'], # Оставляем только самые надежные
        # Остальные параметры остаются по умолчанию
    ),
    
    'balanced': SignalConfig(
        min_confidence=0.5,  # минимум 2 из 4 сетапов
        trend_filter_enabled=True,
        require_adx=False,
        # Все сетапы включены по умолчанию
    ),
    
    'aggressive': SignalConfig(
        min_confidence=0.25,  # минимум 1 из 4 сетапов
        trend_filter_enabled=False, # Отключаем фильтр тренда для большего кол-ва сигналов
        require_adx=False,
        # Все сетапы включены по умолчанию
    ),
}


def get_preset(preset_name: str = 'balanced') -> SignalConfig:
    """Получить предустановку конфигурации"""
    if preset_name not in PRESETS:
        raise ValueError(f"Unknown preset: {preset_name}. Available: {list(PRESETS.keys())}")
    return PRESETS[preset_name]
