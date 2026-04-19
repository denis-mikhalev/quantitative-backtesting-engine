"""
Мультивалютный сканер сигналов

Сканирует N монет одновременно и находит лучшие точки входа
"""

import pandas as pd
import ccxt
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import time
from .signal_generator import StatisticalSignalGenerator, Signal
from .config import ScannerConfig, SignalConfig

# Звуковые уведомления
try:
    import winsound  # Доступно на Windows
except Exception:
    winsound = None


def _play_signal_sound():
    """
    Проигрывает звук при обнаружении нового сигнала.
    
    Использует двойной нисходящий бип для статистической системы
    (отличается от XGBoost - одиночный 1000Hz и OptimalPeriod - восходящие).
    """
    try:
        if winsound is not None:
            # Двойной нисходящий бип: "dee-doop" 
            winsound.Beep(1400, 150)  # Высокий короткий
            winsound.Beep(1000, 300)  # Низкий длинный
        else:
            # Фоллбэк для не-Windows (терминальный bell)
            print('\a')
    except Exception:
        # Никогда не ломаем основной поток из-за звука
        pass


class MultiAssetScanner:
    """
    Сканер для множества монет
    
    Функции:
    - Загрузка данных с Binance
    - Генерация сигналов для всех монет
    - Ранжирование по качеству
    - Экспорт результатов
    """
    
    def __init__(self, 
                 scanner_config: ScannerConfig = None,
                 signal_config: SignalConfig = None):
        self.scanner_config = scanner_config or ScannerConfig()
        self.signal_generator = StatisticalSignalGenerator(
            signal_config or SignalConfig()
        )
        
        # Инициализация Binance
        self.exchange = ccxt.binance({
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot',
            }
        })
    
    def scan_all(self) -> List[Signal]:
        """
        Сканирует все монеты из конфига
        
        Returns:
            List[Signal] - отсортированный по confidence список сигналов
        """
        print(f"\n🔍 Scanning {len(self.scanner_config.symbols)} symbols...")
        print(f"⏰ Timeframe: {self.scanner_config.timeframe}")
        print(f"📊 Lookback: {self.scanner_config.lookback_candles} candles")
        print("="*70)
        
        signals = []
        
        for i, symbol in enumerate(self.scanner_config.symbols, 1):
            try:
                if self.scanner_config.verbose:
                    print(f"[{i}/{len(self.scanner_config.symbols)}] {symbol}...", end=' ')
                
                # Загружаем данные
                df = self._fetch_data(symbol)
                
                if df is None or len(df) < 200:
                    if self.scanner_config.verbose:
                        print("❌ Not enough data")
                    continue
                
                # Генерируем сигнал
                signal = self.signal_generator.generate_signal(df, symbol)
                
                if signal is not None:
                    signals.append(signal)
                    if self.scanner_config.verbose:
                        print(f"✅ {signal.direction} (conf: {signal.confidence:.1%})")
                else:
                    if self.scanner_config.verbose:
                        print("⚪ No signal")
                
                # Rate limiting
                time.sleep(0.1)
                
            except Exception as e:
                if self.scanner_config.verbose:
                    print(f"❌ Error: {str(e)}")
                continue
        
        # Сортируем по confidence
        signals.sort(key=lambda s: s.confidence, reverse=True)
        
        # Фильтруем по минимальной уверенности
        signals = [s for s in signals 
                  if s.confidence >= self.scanner_config.min_signal_confidence]
        
        # Ограничиваем количество
        if len(signals) > self.scanner_config.max_signals_to_show:
            signals = signals[:self.scanner_config.max_signals_to_show]
        
        print("="*70)
        print(f"✅ Found {len(signals)} signals")
        
        # Звуковое уведомление если найдены сигналы
        if signals:
            _play_signal_sound()
        
        return signals
    
    def scan_and_display(self) -> List[Signal]:
        """Сканирует и выводит результаты"""
        signals = self.scan_all()
        
        if not signals:
            print("\n❌ No signals found")
            return []
        
        print("\n" + "="*70)
        print(f"🎯 TOP {len(signals)} SIGNALS (sorted by confidence)")
        print("="*70)
        
        for i, signal in enumerate(signals, 1):
            self._print_signal(i, signal)
        
        print("="*70)
        
        return signals
    
    def _fetch_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """Загружает исторические данные с Binance"""
        try:
            # Конвертация таймфрейма
            timeframe = self.scanner_config.timeframe
            
            # Загружаем свечи
            ohlcv = self.exchange.fetch_ohlcv(
                symbol,
                timeframe=timeframe,
                limit=self.scanner_config.lookback_candles
            )
            
            # Конвертация в DataFrame
            df = pd.DataFrame(
                ohlcv,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            return df
            
        except Exception as e:
            if self.scanner_config.verbose:
                print(f"Error fetching {symbol}: {e}")
            return None
    
    def _print_signal(self, rank: int, signal: Signal):
        """Красиво выводит информацию о сигнале"""
        
        # Иконки направления
        direction_icon = "🟢" if signal.direction == "LONG" else "🔴"
        
        # Confidence bar
        conf_bars = int(signal.confidence * 10)
        conf_visual = "█" * conf_bars + "░" * (10 - conf_bars)
        
        print(f"\n#{rank} {direction_icon} {signal.symbol}")
        print(f"   Direction:   {signal.direction}")
        print(f"   Confidence:  {conf_visual} {signal.confidence:.1%}")
        print(f"   Entry:       ${signal.entry_price:.4f}")
        print(f"   Stop Loss:   ${signal.stop_loss:.4f} ({self._calc_distance(signal.entry_price, signal.stop_loss):.2f}%)")
        print(f"   Take Profit: ${signal.take_profit:.4f} ({self._calc_distance(signal.entry_price, signal.take_profit):.2f}%)")
        print(f"   Risk/Reward: 1:{self._calc_rr(signal):.2f}")
        print(f"   Active Setups: {', '.join(signal.active_setups)}")
        
        # Причины
        print(f"   Reasons:")
        for reason in signal.reasons:
            print(f"      • {reason}")
    
    def _calc_distance(self, entry: float, target: float) -> float:
        """Вычисляет расстояние в %"""
        return abs((target - entry) / entry * 100)
    
    def _calc_rr(self, signal: Signal) -> float:
        """Вычисляет Risk/Reward"""
        risk = abs(signal.entry_price - signal.stop_loss)
        reward = abs(signal.take_profit - signal.entry_price)
        return reward / risk if risk > 0 else 0
    
    def export_signals(self, signals: List[Signal], filepath: str):
        """Экспортирует сигналы в JSON"""
        import json
        from pathlib import Path
        
        data = {
            'timestamp': datetime.now().isoformat(),
            'timeframe': self.scanner_config.timeframe,
            'total_signals': len(signals),
            'signals': [s.to_dict() for s in signals]
        }
        
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"\n💾 Signals exported to: {filepath}")
    
    def continuous_scan(self, interval_seconds: int = None):
        """
        Непрерывное сканирование с интервалом
        
        Args:
            interval_seconds: интервал обновления (по умолчанию из конфига)
        """
        interval = interval_seconds or self.scanner_config.update_interval
        
        print(f"\n🔄 Starting continuous scanner...")
        print(f"⏰ Update interval: {interval}s ({interval//60} minutes)")
        print(f"Press Ctrl+C to stop\n")
        
        try:
            while True:
                print(f"\n{'='*70}")
                print(f"🕐 Scan started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"{'='*70}")
                
                signals = self.scan_and_display()
                
                # Сохранение результатов
                if self.scanner_config.save_results and signals:
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filepath = f"{self.scanner_config.results_dir}/signals_{timestamp}.json"
                    self.export_signals(signals, filepath)
                
                # Отправка в Telegram
                if self.scanner_config.send_telegram and signals:
                    self._send_telegram_notification(signals)
                
                print(f"\n⏳ Next scan in {interval}s...")
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n\n⛔ Scanner stopped by user")
    
    def _send_telegram_notification(self, signals: List[Signal]):
        """Отправляет уведомление в Telegram"""
        try:
            from telegram_sender import send_telegram_message
            
            # Фильтруем сигналы высокой уверенности
            if self.scanner_config.telegram_only_high_confidence:
                signals = [s for s in signals if s.confidence >= 0.75]
            
            if not signals:
                return
            
            # Формируем сообщение
            message = "🤖 <b>Statistical System - New Signals</b>\n\n"
            
            for signal in signals[:5]:  # топ-5
                direction_icon = "🟢" if signal.direction == "LONG" else "🔴"
                
                message += (
                    f"{direction_icon} <b>{signal.symbol}</b> {signal.direction}\n"
                    f"   Confidence: {signal.confidence:.1%}\n"
                    f"   Entry: ${signal.entry_price:.4f}\n"
                    f"   SL: ${signal.stop_loss:.4f} | TP: ${signal.take_profit:.4f}\n"
                    f"   Setups: {', '.join(signal.active_setups[:2])}\n\n"
                )
            
            send_telegram_message(message)
            print("✅ Telegram notification sent")
            
        except Exception as e:
            print(f"❌ Telegram error: {e}")
