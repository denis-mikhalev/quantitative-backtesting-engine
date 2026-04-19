"""
Ранжирование сигналов по качеству

Помогает выбрать лучшие сигналы когда их много
"""

from typing import List, Dict
from .signal_generator import Signal
import pandas as pd


class SignalRanker:
    """
    Ранжирует сигналы по различным критериям
    
    Критерии оценки:
    1. Confidence (уверенность системы)
    2. Risk/Reward соотношение
    3. Количество активных сетапов
    4. Качество монеты (ликвидность, волатильность)
    """
    
    def __init__(self, 
                 weight_confidence: float = 0.4,
                 weight_rr: float = 0.3,
                 weight_setups: float = 0.2,
                 weight_quality: float = 0.1):
        """
        Args:
            weight_* - веса для каждого критерия (сумма должна = 1.0)
        """
        self.weight_confidence = weight_confidence
        self.weight_rr = weight_rr
        self.weight_setups = weight_setups
        self.weight_quality = weight_quality
        
        # Проверка весов
        total_weight = sum([
            weight_confidence, weight_rr, weight_setups, weight_quality
        ])
        if abs(total_weight - 1.0) > 0.01:
            raise ValueError(f"Weights sum must be 1.0, got {total_weight}")
    
    def rank(self, signals: List[Signal], 
             market_data: Dict[str, pd.DataFrame] = None) -> List[Signal]:
        """
        Ранжирует сигналы по комплексной оценке
        
        Args:
            signals: список сигналов
            market_data: опциональные данные о рынке для каждой монеты
            
        Returns:
            Отсортированный список сигналов (лучшие первыми)
        """
        if not signals:
            return []
        
        # Вычисляем баллы для каждого сигнала
        scored_signals = []
        
        for signal in signals:
            score = self._calculate_score(signal, market_data)
            scored_signals.append((signal, score))
        
        # Сортируем по баллу
        scored_signals.sort(key=lambda x: x[1], reverse=True)
        
        # Возвращаем только сигналы (без баллов)
        return [s[0] for s in scored_signals]
    
    def rank_with_scores(self, signals: List[Signal],
                        market_data: Dict[str, pd.DataFrame] = None) -> List[tuple]:
        """
        То же что rank(), но возвращает (signal, score) для анализа
        """
        if not signals:
            return []
        
        scored_signals = []
        
        for signal in signals:
            score = self._calculate_score(signal, market_data)
            scored_signals.append((signal, score))
        
        scored_signals.sort(key=lambda x: x[1], reverse=True)
        
        return scored_signals
    
    def _calculate_score(self, signal: Signal, 
                        market_data: Dict[str, pd.DataFrame] = None) -> float:
        """
        Вычисляет комплексный балл для сигнала
        
        Returns:
            Балл от 0 до 1
        """
        # 1. Confidence score (уже нормализован 0-1)
        confidence_score = signal.confidence
        
        # 2. Risk/Reward score
        rr_score = self._calc_rr_score(signal)
        
        # 3. Setups score (сколько сетапов активно)
        setups_score = len(signal.active_setups) / 4.0  # макс 4 сетапа
        
        # 4. Quality score (качество монеты)
        quality_score = 0.5  # default
        if market_data and signal.symbol in market_data:
            quality_score = self._calc_quality_score(signal.symbol, market_data[signal.symbol])
        
        # Взвешенная сумма
        total_score = (
            self.weight_confidence * confidence_score +
            self.weight_rr * rr_score +
            self.weight_setups * setups_score +
            self.weight_quality * quality_score
        )
        
        return total_score
    
    def _calc_rr_score(self, signal: Signal) -> float:
        """
        Вычисляет балл Risk/Reward
        
        Нормализация:
        - RR < 1.5 -> 0
        - RR = 2.0 -> 0.5 (базовый)
        - RR = 3.0 -> 0.75
        - RR >= 4.0 -> 1.0
        """
        risk = abs(signal.entry_price - signal.stop_loss)
        reward = abs(signal.take_profit - signal.entry_price)
        
        if risk == 0:
            return 0
        
        rr = reward / risk
        
        # Нормализация
        if rr < 1.5:
            return 0
        elif rr >= 4.0:
            return 1.0
        else:
            # Линейная интерполяция между 1.5 и 4.0
            return (rr - 1.5) / (4.0 - 1.5)
    
    def _calc_quality_score(self, symbol: str, df: pd.DataFrame) -> float:
        """
        Вычисляет балл качества монеты
        
        Критерии:
        - Волатильность (умеренная лучше)
        - Объём (высокий лучше)
        - Тренд (наличие тренда лучше)
        """
        try:
            # Волатильность (стандартное отклонение цены)
            volatility = df['close'].pct_change().std()
            
            # Нормализация: 0.01-0.05 оптимально
            if volatility < 0.01:
                vol_score = 0.3  # слишком низкая
            elif volatility > 0.08:
                vol_score = 0.3  # слишком высокая
            else:
                vol_score = 1.0 - abs(volatility - 0.03) / 0.05
            
            # Объём (средний за последние 20 свечей)
            avg_volume = df['volume'].tail(20).mean()
            volume_score = min(avg_volume / 1000000, 1.0)  # нормализация
            
            # Тренд (наличие направленного движения)
            ema_fast = df['close'].ewm(span=50).mean()
            ema_slow = df['close'].ewm(span=200).mean()
            
            trend_strength = abs((ema_fast.iloc[-1] - ema_slow.iloc[-1]) / ema_slow.iloc[-1])
            trend_score = min(trend_strength * 10, 1.0)
            
            # Комбинируем
            quality_score = (vol_score * 0.4 + volume_score * 0.3 + trend_score * 0.3)
            
            return quality_score
            
        except Exception as e:
            return 0.5  # default если ошибка
    
    def get_top_n(self, signals: List[Signal], n: int = 5,
                  market_data: Dict[str, pd.DataFrame] = None) -> List[Signal]:
        """
        Возвращает топ-N лучших сигналов
        """
        ranked = self.rank(signals, market_data)
        return ranked[:n]
    
    def explain_ranking(self, signal: Signal,
                       market_data: Dict[str, pd.DataFrame] = None) -> Dict:
        """
        Объясняет оценку сигнала (для debugging)
        
        Returns:
            Dict с разбивкой баллов
        """
        confidence_score = signal.confidence
        rr_score = self._calc_rr_score(signal)
        setups_score = len(signal.active_setups) / 4.0
        
        quality_score = 0.5
        if market_data and signal.symbol in market_data:
            quality_score = self._calc_quality_score(signal.symbol, market_data[signal.symbol])
        
        total_score = (
            self.weight_confidence * confidence_score +
            self.weight_rr * rr_score +
            self.weight_setups * setups_score +
            self.weight_quality * quality_score
        )
        
        return {
            'total_score': total_score,
            'confidence_score': confidence_score,
            'confidence_weight': self.weight_confidence,
            'confidence_contribution': self.weight_confidence * confidence_score,
            'rr_score': rr_score,
            'rr_weight': self.weight_rr,
            'rr_contribution': self.weight_rr * rr_score,
            'setups_score': setups_score,
            'setups_weight': self.weight_setups,
            'setups_contribution': self.weight_setups * setups_score,
            'quality_score': quality_score,
            'quality_weight': self.weight_quality,
            'quality_contribution': self.weight_quality * quality_score,
        }
    
    def print_ranking_explanation(self, signal: Signal,
                                 market_data: Dict[str, pd.DataFrame] = None):
        """Красиво выводит объяснение оценки"""
        explanation = self.explain_ranking(signal, market_data)
        
        print(f"\n📊 Ranking Explanation for {signal.symbol}")
        print("="*50)
        print(f"Total Score: {explanation['total_score']:.3f}")
        print("-"*50)
        print(f"Confidence:  {explanation['confidence_score']:.3f} × {explanation['confidence_weight']:.2f} = {explanation['confidence_contribution']:.3f}")
        print(f"Risk/Reward: {explanation['rr_score']:.3f} × {explanation['rr_weight']:.2f} = {explanation['rr_contribution']:.3f}")
        print(f"Setups:      {explanation['setups_score']:.3f} × {explanation['setups_weight']:.2f} = {explanation['setups_contribution']:.3f}")
        print(f"Quality:     {explanation['quality_score']:.3f} × {explanation['quality_weight']:.2f} = {explanation['quality_contribution']:.3f}")
        print("="*50)
