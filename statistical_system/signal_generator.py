"""
Генератор статистических торговых сигналов

Реализует 4 проверенных setup-а:
1. Breakout - прорыв волатильности с объёмом
2. Pullback - откат в тренде
3. Mean Reversion - возврат к средней
4. Volatility Expansion - расширение после сжатия (BB Squeeze)
"""

import pandas as pd
import numpy as np
import ta
from typing import Dict, Tuple, Optional, List
from dataclasses import dataclass
from .config import SignalConfig


@dataclass
class Signal:
    """Торговый сигнал"""
    symbol: str
    timestamp: pd.Timestamp
    direction: str  # 'LONG' или 'SHORT'
    confidence: float  # 0-1
    entry_price: float
    stop_loss: float
    take_profit: float
    atr: float
    
    # Детали сигнала
    active_setups: List[str]  # какие сетапы сработали
    reasons: List[str]  # причины сигнала
    indicators: Dict[str, Optional[float]]
    
    def __str__(self):
        return (
            f"{self.symbol} {self.direction} @{self.entry_price:.4f} "
            f"(conf: {self.confidence:.1%}, setups: {len(self.active_setups)}/4)"
        )
    
    def to_dict(self) -> Dict:
        """Конвертация в словарь для JSON"""
        return {
            'symbol': self.symbol,
            'timestamp': self.timestamp.isoformat(),
            'direction': self.direction,
            'confidence': self.confidence,
            'entry_price': self.entry_price,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'atr': self.atr,
            'active_setups': self.active_setups,
            'reasons': self.reasons,
            'indicators': self.indicators,
        }


class StatisticalSignalGenerator:
    """
    Генератор статистических торговых сигналов
    Основан на проверенных паттернах без ML
    """
    
    def __init__(self, config: SignalConfig = None):
        self.config = config or SignalConfig()
    
    def generate_signal(self, df: pd.DataFrame, symbol: str) -> Optional[Signal]:
        """
        Генерирует сигнал для одной монеты
        
        Args:
            df: DataFrame со свечами (OHLCV)
            symbol: название монеты
            
        Returns:
            Signal или None если нет сигнала
        """
        # Добавляем индикаторы
        df = self._ensure_indicators(df)
        
        # Генерируем сигналы по каждому сетапу
        df = self._add_setup_signals(df)
        
        # Анализируем последнюю свечу
        last_row = df.iloc[-1]
        
        # Собираем активные сетапы
        active_setups = []
        signal_direction = None

        for setup_name in self.config.enabled_setups:
            col_name = f'signal_{setup_name}'
            if col_name in df.columns:
                signal_value = last_row[col_name]
                if signal_value != 0:
                    active_setups.append((setup_name, signal_value))

        if not active_setups:
            return None
        
        # Определяем направление (большинством голосов)
        long_votes = sum(1 for _, v in active_setups if v == 1)
        short_votes = sum(1 for _, v in active_setups if v == -1)
        total_votes = long_votes + short_votes
        
        if long_votes > short_votes:
            signal_direction = 'LONG'
            confidence = long_votes / max(total_votes, 1)
        elif short_votes > long_votes:
            signal_direction = 'SHORT'
            confidence = short_votes / max(total_votes, 1)
        else:
            return None  # нет консенсуса
        
        # Проверка минимальной уверенности
        if confidence < self.config.min_confidence:
            return None

        # Глобальный тренд-фильтр: торгуем в сторону тренда EMA, опционально требуем силу тренда по ADX
        if self.config.trend_filter_enabled:
            uptrend = last_row['ema_fast'] > last_row['ema_slow']
            downtrend = last_row['ema_fast'] < last_row['ema_slow']
            if signal_direction == 'LONG' and not uptrend:
                return None
            if signal_direction == 'SHORT' and not downtrend:
                return None
            if self.config.require_adx:
                adx_value = last_row['adx'] if 'adx' in df.columns else np.nan
                if not pd.notna(adx_value) or adx_value < self.config.adx_min:
                    return None
        
        # Формируем сигнал
        current_price = last_row['close']
        atr = last_row['atr']
        
        if signal_direction == 'LONG':
            stop_loss = current_price - atr
            take_profit = current_price + (atr * 2.0)
        else:
            stop_loss = current_price + atr
            take_profit = current_price - (atr * 2.0)
        
        indicator_fields = [
            'open', 'high', 'low', 'close', 'volume',
            'rsi', 'ema_fast', 'ema_slow', 'atr', 'atr_percentile',
            'volume_ratio', 'bb_upper', 'bb_lower', 'bb_middle', 'bb_width'
        ]
        indicator_snapshot: Dict[str, Optional[float]] = {}
        for field in indicator_fields:
            if field in last_row.index:
                value = last_row[field]
                if pd.isna(value):
                    indicator_snapshot[field] = None
                else:
                    indicator_snapshot[field] = float(value)

        # Собираем причины
        reasons = []
        for setup_name, _ in active_setups:
            reason = self._get_setup_reason(setup_name, last_row, signal_direction)
            reasons.append(reason)
        # Добавляем причину прохождения тренд-фильтра
        if self.config.trend_filter_enabled:
            if signal_direction == 'LONG':
                reasons.append("✅ Trend filter: EMA-fast > EMA-slow")
            else:
                reasons.append("✅ Trend filter: EMA-fast < EMA-slow")
            if self.config.require_adx:
                reasons.append(f"✅ ADX >= {self.config.adx_min}")
        
        return Signal(
            symbol=symbol,
            timestamp=last_row.name,
            direction=signal_direction,
            confidence=confidence,
            entry_price=current_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            atr=atr,
            active_setups=[s[0] for s in active_setups],
            reasons=reasons,
            indicators=indicator_snapshot
        )
    
    def _ensure_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Добавляет необходимые технические индикаторы"""
        df = df.copy()
        
        # RSI
        if 'rsi' not in df.columns:
            df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
        
        # EMA
        if 'ema_fast' not in df.columns:
            df['ema_fast'] = ta.trend.EMAIndicator(
                df['close'], window=self.config.ema_fast
            ).ema_indicator()
        if 'ema_slow' not in df.columns:
            df['ema_slow'] = ta.trend.EMAIndicator(
                df['close'], window=self.config.ema_slow
            ).ema_indicator()
        
        # Bollinger Bands
        if 'bb_upper' not in df.columns:
            bb = ta.volatility.BollingerBands(
                df['close'], 
                window=self.config.bb_period,
                window_dev=self.config.bb_std
            )
            df['bb_upper'] = bb.bollinger_hband()
            df['bb_lower'] = bb.bollinger_lband()
            df['bb_middle'] = bb.bollinger_mavg()
            df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
        
        # ATR
        if 'atr' not in df.columns:
            df['atr'] = ta.volatility.AverageTrueRange(
                df['high'], df['low'], df['close'],
                window=self.config.atr_lookback
            ).average_true_range()

        # ADX (по требованию)
        if self.config.require_adx and 'adx' not in df.columns:
            try:
                df['adx'] = ta.trend.ADXIndicator(
                    high=df['high'], low=df['low'], close=df['close'], window=self.config.adx_period
                ).adx()
            except Exception:
                # если библиотека/функция недоступна, просто не добавляем
                df['adx'] = np.nan
        
        # Volume
        if 'volume_ma' not in df.columns:
            df['volume_ma'] = df['volume'].rolling(window=20).mean()
        if 'volume_ratio' not in df.columns:
            df['volume_ratio'] = df['volume'] / df['volume_ma']
        
        # ATR percentile для volatility expansion
        if 'atr_percentile' not in df.columns:
            df['atr_percentile'] = df['atr'].rolling(window=100).rank(pct=True)
        
        return df
    
    def _add_setup_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Добавляет сигналы от всех сетапов"""
        df = df.copy()
        
        if 'breakout' in self.config.enabled_setups:
            df['signal_breakout'] = self._breakout_signal(df)
        
        if 'pullback' in self.config.enabled_setups:
            df['signal_pullback'] = self._pullback_signal(df)
        
        if 'mean_reversion' in self.config.enabled_setups:
            df['signal_mean_reversion'] = self._mean_reversion_signal(df)
        
        if 'volatility_expansion' in self.config.enabled_setups:
            df['signal_volatility_expansion'] = self._volatility_expansion_signal(df)
        
        return df
    
    def _breakout_signal(self, df: pd.DataFrame) -> pd.Series:
        """
        Сигнал на прорыв волатильности
        
        Логика:
        - LONG: цена > BB upper + объём > threshold + растущая свеча
        - SHORT: цена < BB lower + объём > threshold + падающая свеча
        """
        signals = pd.Series(0, index=df.index)
        
        volume_spike = df['volume_ratio'] > self.config.volume_threshold
        
        # Long breakout
        long_breakout = (
            (df['close'] > df['bb_upper']) & 
            volume_spike &
            (df['close'] > df['close'].shift(1))  # растущая свеча
        )
        
        # Short breakout
        short_breakout = (
            (df['close'] < df['bb_lower']) & 
            volume_spike &
            (df['close'] < df['close'].shift(1))  # падающая свеча
        )
        
        signals[long_breakout] = 1
        signals[short_breakout] = -1
        
        return signals
    
    def _pullback_signal(self, df: pd.DataFrame) -> pd.Series:
        """
        Сигнал на откат в тренде
        
        Логика:
        - LONG: EMA50 > EMA200 + RSI откатил < oversold
        - SHORT: EMA50 < EMA200 + RSI откатил > overbought
        """
        signals = pd.Series(0, index=df.index)
        
        # Определяем тренд
        uptrend = df['ema_fast'] > df['ema_slow']
        downtrend = df['ema_fast'] < df['ema_slow']
        
        # Long pullback
        long_pullback = (
            uptrend &
            (df['rsi'] < self.config.rsi_oversold) &
            (df['rsi'].shift(1) >= self.config.rsi_oversold)  # только что упал
        )
        
        # Short pullback
        short_pullback = (
            downtrend &
            (df['rsi'] > self.config.rsi_overbought) &
            (df['rsi'].shift(1) <= self.config.rsi_overbought)  # только что поднялся
        )
        
        signals[long_pullback] = 1
        signals[short_pullback] = -1
        
        return signals
    
    def _mean_reversion_signal(self, df: pd.DataFrame) -> pd.Series:
        """
        Сигнал на возврат к средней
        
        Логика:
        - LONG: цена << BB lower + RSI extreme low
        - SHORT: цена >> BB upper + RSI extreme high
        """
        signals = pd.Series(0, index=df.index)
        
        # Расстояние от BB в процентах
        bb_width = df['bb_upper'] - df['bb_lower']
        distance_from_lower = (df['close'] - df['bb_lower']) / bb_width
        distance_from_upper = (df['bb_upper'] - df['close']) / bb_width
        
        # Long mean reversion
        long_reversion = (
            (distance_from_lower < 0) &  # ниже нижней границы
            (df['rsi'] < self.config.rsi_extreme_low)
        )
        
        # Short mean reversion
        short_reversion = (
            (distance_from_upper < 0) &  # выше верхней границы
            (df['rsi'] > self.config.rsi_extreme_high)
        )
        
        signals[long_reversion] = 1
        signals[short_reversion] = -1
        return signals
    
    def _volatility_expansion_signal(self, df: pd.DataFrame) -> pd.Series:
        """
        Сигнал на расширение волатильности (BB Squeeze)
        
        Логика:
        - Волатильность сжалась (низкий ATR percentile)
        - Затем прорыв в любую сторону с объёмом
        """
        signals = pd.Series(0, index=df.index)
        
        # Сжатие: ATR в нижних 20%
        squeeze = df['atr_percentile'] < self.config.volatility_percentile
        
        # Прорыв после сжатия
        volume_spike = df['volume_ratio'] > 1.3
        
        # Long expansion
        long_expansion = (
            squeeze.shift(1) &  # было сжатие
            (df['close'] > df['bb_middle']) &  # прорыв вверх
            volume_spike &
            (df['close'] > df['close'].shift(1))  # растущая свеча
        )
        
        # Short expansion
        short_expansion = (
            squeeze.shift(1) &
            (df['close'] < df['bb_middle']) &  # прорыв вниз
            volume_spike &
            (df['close'] < df['close'].shift(1))  # падающая свеча
        )
        
        signals[long_expansion] = 1
        signals[short_expansion] = -1
        
        return signals
    
    def _get_setup_reason(self, setup_name: str, row: pd.Series, direction: str) -> str:
        """Генерирует текстовое описание причины сигнала"""
        
        if setup_name == 'breakout':
            vol_ratio = row['volume_ratio']
            if direction == 'LONG':
                return f"🔥 Breakout вверх (volume: {vol_ratio:.1f}x)"
            else:
                return f"🔥 Breakout вниз (volume: {vol_ratio:.1f}x)"
        
        elif setup_name == 'pullback':
            rsi = row['rsi']
            if direction == 'LONG':
                return f"📈 Pullback в uptrend (RSI: {rsi:.1f})"
            else:
                return f"📉 Pullback в downtrend (RSI: {rsi:.1f})"
        
        elif setup_name == 'mean_reversion':
            rsi = row['rsi']
            if direction == 'LONG':
                return f"⬆️ Mean reversion от нижней BB (RSI: {rsi:.1f})"
            else:
                return f"⬇️ Mean reversion от верхней BB (RSI: {rsi:.1f})"
        
        elif setup_name == 'volatility_expansion':
            bb_width = row['bb_width']
            if direction == 'LONG':
                return f"💥 Volatility expansion вверх (BB width: {bb_width:.3f})"
            else:
                return f"💥 Volatility expansion вниз (BB width: {bb_width:.3f})"
        
        return f"{setup_name} signal"
