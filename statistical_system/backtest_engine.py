"""
Движок бэктестирования статистической торговой системы

Поддерживает:
- Векторный бэктест (быстро на pandas)
- Симуляцию реальных условий (комиссии, slippage)
- Управление портфелем (несколько позиций)
- Детальные метрики
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from .config import BacktestConfig
from .signal_generator import StatisticalSignalGenerator, Signal


@dataclass
class Trade:
    """Информация о сделке"""
    entry_time: pd.Timestamp
    exit_time: pd.Timestamp
    symbol: str
    direction: str  # 'LONG' or 'SHORT'
    entry_price: float
    exit_price: float
    size: float  # размер позиции в USDT
    pnl: float  # чистая прибыль в USDT
    pnl_pct: float  # доходность в %
    exit_reason: str  # 'TP', 'SL', 'TIME'
    confidence: float  # уверенность сигнала
    duration_candles: int  # длительность в свечах
    atr: Optional[float]
    sl_distance_pct: Optional[float]
    tp_distance_pct: Optional[float]
    risk_reward: Optional[float]
    atr_percentile: Optional[float]
    
    def to_dict(self) -> Dict:
        return {
            **asdict(self),
            'entry_time': self.entry_time.isoformat(),
            'exit_time': self.exit_time.isoformat(),
        }


@dataclass
class BacktestResult:
    """Результаты бэктеста"""
    
    # === Основные метрики ===
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float  # %
    
    # === Прибыльность ===
    total_return: float  # % от начального капитала
    total_return_usdt: float  # в USDT
    profit_factor: float
    
    # === Средние значения ===
    avg_win: float  # средний выигрыш в %
    avg_loss: float  # средний проигрыш в %
    avg_trade: float  # средний результат в %
    avg_duration_candles: float  # средняя длительность сделки
    
    # === Риски ===
    max_drawdown: float  # максимальная просадка в %
    sharpe_ratio: float
    
    # === Детали ===
    final_capital: float
    trades: List[Trade]
    equity_curve: pd.Series
    
    # === Группировки ===
    by_exit_reason: Dict[str, int]  # сколько сделок на TP/SL/TIME
    by_symbol: Optional[Dict[str, Dict]]  # статистика по монетам
    atr_stats: Dict[str, float]
    sl_distance_stats: Dict[str, float]
    tp_distance_stats: Dict[str, float]
    risk_reward_stats: Dict[str, float]
    signal_log_files: List[str]
    
    def to_dict(self) -> Dict:
        """Конвертация в словарь для JSON"""
        return {
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': self.win_rate,
            'total_return': self.total_return,
            'total_return_usdt': self.total_return_usdt,
            'profit_factor': self.profit_factor,
            'avg_win': self.avg_win,
            'avg_loss': self.avg_loss,
            'avg_trade': self.avg_trade,
            'avg_duration_candles': self.avg_duration_candles,
            'max_drawdown': self.max_drawdown,
            'sharpe_ratio': self.sharpe_ratio,
            'final_capital': self.final_capital,
            'by_exit_reason': self.by_exit_reason,
            'by_symbol': self.by_symbol,
            'atr_stats': self.atr_stats,
            'sl_distance_stats': self.sl_distance_stats,
            'tp_distance_stats': self.tp_distance_stats,
            'risk_reward_stats': self.risk_reward_stats,
            'signal_log_files': self.signal_log_files,
            'trades': [t.to_dict() for t in self.trades],
        }
    
    def print_summary(self):
        """Красивый вывод результатов"""
        print("\n" + "="*70)
        print("📊 BACKTEST RESULTS")
        print("="*70)
        
        print(f"\n📈 Performance:")
        print(f"   Total Return:    {self.total_return:>8.2f}% (${self.total_return_usdt:,.2f})")
        print(f"   Final Capital:   ${self.final_capital:>10,.2f}")
        print(f"   Max Drawdown:    {self.max_drawdown:>8.2f}%")
        print(f"   Sharpe Ratio:    {self.sharpe_ratio:>8.2f}")
        
        print(f"\n📊 Trading Stats:")
        print(f"   Total Trades:    {self.total_trades:>8}")
        print(f"   Win Rate:        {self.win_rate:>8.2f}%")
        print(f"   Profit Factor:   {self.profit_factor:>8.2f}")
        
        print(f"\n💰 Averages:")
        print(f"   Avg Win:         {self.avg_win:>8.2f}%")
        print(f"   Avg Loss:        {self.avg_loss:>8.2f}%")
        print(f"   Avg Trade:       {self.avg_trade:>8.2f}%")
        print(f"   Avg Duration:    {self.avg_duration_candles:>8.1f} candles")

        if self.sl_distance_stats or self.tp_distance_stats:
            print(f"\n⚙️ Risk Profile:")
            if self.atr_stats:
                atr_mean = self.atr_stats.get('mean')
                atr_median = self.atr_stats.get('median')
                if atr_mean is not None and atr_median is not None:
                    print(f"   ATR mean/median: {atr_mean:>8.4f} / {atr_median:>8.4f}")
            if self.sl_distance_stats:
                sl_mean = self.sl_distance_stats.get('mean')
                if sl_mean is not None:
                    print(f"   SL distance avg: {sl_mean:>8.2f}%")
            if self.tp_distance_stats:
                tp_mean = self.tp_distance_stats.get('mean')
                if tp_mean is not None:
                    print(f"   TP distance avg: {tp_mean:>8.2f}%")
            if self.risk_reward_stats:
                rr_mean = self.risk_reward_stats.get('mean')
                rr_median = self.risk_reward_stats.get('median')
                if rr_mean is not None and rr_median is not None:
                    print(f"   RR mean/median:  {rr_mean:>8.2f} / {rr_median:>8.2f}")
        
        print(f"\n🎯 Exit Types:")
        for reason, count in self.by_exit_reason.items():
            pct = (count / self.total_trades * 100) if self.total_trades > 0 else 0
            print(f"   {reason:>6}: {count:>4} ({pct:>5.1f}%)")
        
        if self.by_symbol:
            print(f"\n🪙 By Symbol (Top 5):")
            sorted_symbols = sorted(
                self.by_symbol.items(),
                key=lambda x: x[1]['total_return'],
                reverse=True
            )[:5]
            for symbol, stats in sorted_symbols:
                print(f"   {symbol:>10}: {stats['total_return']:>7.2f}% "
                      f"({stats['trades']} trades, WR: {stats['win_rate']:.1f}%)")
        
        if self.signal_log_files:
            print(f"\n📝 Signal Logs:")
            for path in self.signal_log_files:
                print(f"   {path}")
        
        print("\n" + "="*70)


class BacktestEngine:
    """
    Движок бэктестирования
    
    Принцип работы:
    1. Прогоняет данные свеча за свечой
    2. На каждой свече проверяет сигналы
    3. Управляет открытыми позициями
    4. Считает метрики
    """
    
    def __init__(self, 
                 signal_generator: StatisticalSignalGenerator,
                 config: BacktestConfig = None):
        self.signal_generator = signal_generator
        self.config = config or BacktestConfig()
        
        # Состояние бэктеста
        self.capital = self.config.initial_capital
        self.positions: List[Dict] = []  # открытые позиции
        self.trades: List[Trade] = []
        self.equity_curve: List[Tuple[pd.Timestamp, float]] = []
        self.latest_prices: Dict[str, float] = {}
        self.signal_logs: List[Dict] = []
        self.last_signal_log_files: List[str] = []
        
    def run(self, 
            df: pd.DataFrame, 
            symbol: str = 'BTCUSDT') -> BacktestResult:
        """
        Запускает бэктест на одной монете
        
        Args:
            df: DataFrame со свечами (OHLCV)
            symbol: название монеты
            
        Returns:
            BacktestResult с метриками
        """
        # Сброс состояния
        self._reset()
        
        # Добавляем индикаторы и сигналы
        df = self.signal_generator._ensure_indicators(df)
        df = self.signal_generator._add_setup_signals(df)
        
        # Основной цикл
        for i in range(len(df)):
            current_row = df.iloc[i]
            current_time = current_row.name

            if 'close' in current_row:
                self.latest_prices[symbol] = current_row['close']
            
            # Управление открытыми позициями
            self._manage_positions(current_row, i)
            
            # Проверка новых сигналов (если есть свободный капитал)
            if len(self.positions) < self.config.max_positions:
                signal = self._check_signal(df.iloc[:i+1], symbol)
                # Входим на следующей свече по цене открытия, чтобы избежать look-ahead bias
                if signal is not None and (i + 1) < len(df):
                    next_row = df.iloc[i + 1]
                    self._open_position(signal, next_row, i + 1)
            
            # Записываем эквити как общую стоимость портфеля
            self.equity_curve.append((current_time, self._get_total_equity()))
            
            # Проверка лимитов риска
            if self._check_risk_limits():
                break
        
        # Закрываем оставшиеся позиции
        self._close_all_positions(df.iloc[-1], len(df)-1)

        if len(df) > 0:
            final_time = df.iloc[-1].name
            self.equity_curve.append((final_time, self._get_total_equity()))

        self._save_signal_logs('single', symbol)

        return self._calculate_results(symbol)
    
    def run_multi_asset(self, 
                       data: Dict[str, pd.DataFrame]) -> BacktestResult:
        """
        Запускает бэктест на нескольких монетах
        
        Args:
            data: {symbol: DataFrame} - данные по каждой монете
            
        Returns:
            BacktestResult с общими метриками
        """
        # Сброс состояния
        self._reset()
        
        # Подготовка данных
        prepared_data = {}
        for symbol, df in data.items():
            df = self.signal_generator._ensure_indicators(df)
            df = self.signal_generator._add_setup_signals(df)
            prepared_data[symbol] = df
        
        # Находим общий временной интервал
        all_timestamps = set()
        for df in prepared_data.values():
            all_timestamps.update(df.index)
        timestamps = sorted(all_timestamps)
        
        # Основной цикл по времени
        for current_time in timestamps:
            # Управление позициями
            for symbol, df in prepared_data.items():
                if current_time not in df.index:
                    continue
                    
                current_row = df.loc[current_time]
                row_index = df.index.get_loc(current_time)

                if 'close' in current_row:
                    self.latest_prices[symbol] = current_row['close']
                
                # Обновляем позиции по этой монете
                self._manage_positions_for_symbol(
                    symbol, current_row, row_index
                )
            
            # Проверка новых сигналов
            if len(self.positions) < self.config.max_positions:
                # Собираем все доступные сигналы
                available_signals = []
                for symbol, df in prepared_data.items():
                    if current_time not in df.index:
                        continue
                    
                    row_index = df.index.get_loc(current_time)
                    signal = self._check_signal(df.iloc[:row_index+1], symbol)
                    if signal is not None:
                        available_signals.append((signal, df.loc[current_time], row_index))
                
                # Берём лучший сигнал (по confidence)
                if available_signals:
                    # сортируем по уверенности
                    available_signals.sort(key=lambda x: x[0].confidence, reverse=True)
                    best_signal, current_row, row_index = available_signals[0]
                    # открываем на следующей свече, если она доступна для этого символа
                    symbol_df = prepared_data[best_signal.symbol]
                    if (row_index + 1) < len(symbol_df):
                        next_row = symbol_df.iloc[row_index + 1]
                        self._open_position(best_signal, next_row, row_index + 1)
            
            # Записываем эквити
            self.equity_curve.append((current_time, self._get_total_equity()))
            
            # Проверка лимитов риска
            if self._check_risk_limits():
                break
        
        # Закрываем оставшиеся позиции
        for symbol, df in prepared_data.items():
            last_row = df.iloc[-1]
            last_index = len(df) - 1
            self._close_positions_for_symbol(symbol, last_row, last_index)
            if 'close' in last_row:
                self.latest_prices[symbol] = last_row['close']

        if timestamps:
            final_time = timestamps[-1]
            self.equity_curve.append((final_time, self._get_total_equity()))

        self._save_signal_logs('multi')
        
        return self._calculate_results(multi_asset=True)
    
    def _reset(self):
        """Сброс состояния для нового бэктеста"""
        self.capital = self.config.initial_capital
        self.positions = []
        self.trades = []
        self.equity_curve = []
        self.latest_prices = {}
        self.signal_logs = []
        self.last_signal_log_files = []
    
    def _check_signal(self, df: pd.DataFrame, symbol: str) -> Optional[Signal]:
        """Проверяет наличие сигнала на последней свече"""
        if len(df) < 200:  # минимум данных для индикаторов
            return None
        
        signal = self.signal_generator.generate_signal(df, symbol)
        
        if signal is None:
            return None
        
        # Фильтр по confidence
        if signal.confidence < self.config.min_confidence:
            return None
        
        return signal
    
    def _open_position(self, signal: Signal, current_row: pd.Series, index: int):
        """Открывает новую позицию (по open следующей свечи)"""
        # Входим по цене открытия свечи, на которой совершается вход
        entry_price = current_row['open']
        
        # Применяем slippage (в неблагоприятную сторону)
        if signal.direction == 'LONG':
            entry_price *= (1 + self.config.slippage)
        else:
            entry_price *= (1 - self.config.slippage)
        
        # Рассчитываем уровни SL/TP от цены входа и ATR с множителями из конфигурации
        if signal.direction == 'LONG':
            stop_loss = entry_price - (signal.atr * self.config.sl_atr_mult)
            take_profit = entry_price + (signal.atr * self.config.tp_atr_mult)
        else:
            stop_loss = entry_price + (signal.atr * self.config.sl_atr_mult)
            take_profit = entry_price - (signal.atr * self.config.tp_atr_mult)
        
        # Размер позиции по риску
        sl_distance = abs(entry_price - stop_loss)
        sl_pct = max(sl_distance / entry_price, 1e-12)  # процент риска

        tp_distance = abs(take_profit - entry_price)
        tp_pct = max(tp_distance / entry_price, 1e-12)
        risk_reward = tp_pct / sl_pct if sl_pct > 0 else None

        total_equity = self._get_total_equity()
        risk_amount = total_equity * self.config.position_size_pct  # сколько готовы потерять
        position_size_usdt = risk_amount / sl_pct  # размер позиции в USDT

        available_cash = self.capital
        if available_cash <= 0:
            return

        max_position = total_equity * 0.2  # макс 20% капитала в одной позиции
        affordable_size = available_cash / (1 + self.config.commission)
        position_size_usdt = min(position_size_usdt, max_position, affordable_size)

        if position_size_usdt <= 0:
            return

        entry_commission = position_size_usdt * self.config.commission
        self.capital -= position_size_usdt
        self.capital -= entry_commission

        quantity = position_size_usdt / entry_price if entry_price > 0 else 0.0

        position = {
            'symbol': signal.symbol,
            'entry_index': index,
            'entry_time': current_row.name,
            'entry_price': entry_price,
            'direction': signal.direction,
            'size_usdt': position_size_usdt,
            'quantity': quantity,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'confidence': signal.confidence,
            'commission_paid': entry_commission,
            'atr': signal.atr,
            'sl_distance_pct': sl_pct * 100,
            'tp_distance_pct': tp_pct * 100,
            'risk_reward': risk_reward,
            'atr_percentile': signal.indicators.get('atr_percentile') if signal.indicators else None,
            'signal_timestamp': signal.timestamp,
            'active_setups': signal.active_setups,
            'reasons': signal.reasons,
            'indicator_snapshot': signal.indicators,
        }
        
        if quantity > 0:
            mark_price = current_row['close'] if 'close' in current_row else entry_price
            self.latest_prices[signal.symbol] = mark_price
            self.positions.append(position)
            self._log_signal(signal, position)
        else:
            # Если вдруг рассчитанное количество нулевое (аномалия данных), возвращаем капитал
            self.capital += position_size_usdt
            self.capital += entry_commission
    
    def _manage_positions(self, current_row: pd.Series, index: int):
        """Управляет всеми открытыми позициями"""
        positions_to_close = []
        
        for i, pos in enumerate(self.positions):
            # Проверяем TP/SL
            should_close, exit_reason = self._check_exit_conditions(pos, current_row)
            
            if should_close:
                positions_to_close.append((i, exit_reason))
            else:
                # Проверяем тайм-аут
                if self.config.enable_time_exit and self.config.time_exit_candles > 0:
                    duration = index - pos['entry_index']
                    if duration >= self.config.time_exit_candles:
                        positions_to_close.append((i, 'TIME'))
        
        # Закрываем позиции (в обратном порядке, чтобы не сбить индексы)
        for i, exit_reason in reversed(positions_to_close):
            self._close_position(i, current_row, index, exit_reason)
    
    def _manage_positions_for_symbol(self, symbol: str, current_row: pd.Series, index: int):
        """Управляет позициями по конкретной монете"""
        positions_to_close = []
        
        for i, pos in enumerate(self.positions):
            if pos['symbol'] != symbol:
                continue
            
            should_close, exit_reason = self._check_exit_conditions(pos, current_row)
            if should_close:
                positions_to_close.append((i, exit_reason))
            else:
                # Проверяем тайм-аут
                if self.config.enable_time_exit and self.config.time_exit_candles > 0:
                    duration = index - pos['entry_index']
                    if duration >= self.config.time_exit_candles:
                        positions_to_close.append((i, 'TIME'))
        
        for i, exit_reason in reversed(positions_to_close):
            self._close_position(i, current_row, index, exit_reason)

    def _log_signal(self, signal: Signal, position: Dict):
        """Сохраняет подробную информацию о сигнале"""
        if not self.config.log_signals:
            position.pop('indicator_snapshot', None)
            return

        entry_time = position['entry_time']
        signal_time = position.get('signal_timestamp', signal.timestamp)
        indicator_snapshot = position.get('indicator_snapshot') or {}

        log_entry: Dict[str, Optional[float]] = {
            'signal_time': signal_time.isoformat() if isinstance(signal_time, pd.Timestamp) else str(signal_time),
            'entry_time': entry_time.isoformat() if isinstance(entry_time, pd.Timestamp) else str(entry_time),
            'symbol': position['symbol'],
            'direction': position['direction'],
            'confidence': position['confidence'],
            'entry_price': position['entry_price'],
            'stop_loss': position['stop_loss'],
            'take_profit': position['take_profit'],
            'position_size_usdt': position['size_usdt'],
            'quantity': position['quantity'],
            'atr': position.get('atr'),
            'atr_percentile': position.get('atr_percentile'),
            'sl_distance_pct': position.get('sl_distance_pct'),
            'tp_distance_pct': position.get('tp_distance_pct'),
            'risk_reward': position.get('risk_reward'),
            'active_setups': ','.join(position.get('active_setups', [])),
            'reasons': ' | '.join(position.get('reasons', [])),
        }

        for key, value in indicator_snapshot.items():
            log_entry[f'ind_{key}'] = value

        self.signal_logs.append(log_entry)
        position.pop('indicator_snapshot', None)

    def _save_signal_logs(self, mode: str, identifier: Optional[str] = None) -> List[str]:
        """Сохраняет накопленные логи сигналов в CSV и JSON"""
        self.last_signal_log_files = []
        if not self.config.log_signals or not self.signal_logs:
            return []

        log_dir = Path(self.config.signals_log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        suffix = identifier if identifier else 'multi'
        base_name = f"signals_{mode}_{suffix}_{timestamp}"

        df = pd.DataFrame(self.signal_logs)
        if 'signal_time' in df.columns:
            df = df.sort_values('signal_time')

        csv_path = log_dir / f"{base_name}.csv"
        json_path = log_dir / f"{base_name}.json"

        df.to_csv(csv_path, index=False)
        df.to_json(json_path, orient='records', indent=2)

        self.last_signal_log_files = [str(csv_path), str(json_path)]
        return self.last_signal_log_files

    def _get_total_equity(self) -> float:
        """Возвращает совокупную стоимость портфеля (кэш + открытые позиции)"""
        equity = self.capital

        for pos in self.positions:
            mark_price = self.latest_prices.get(pos['symbol'], pos['entry_price'])
            if mark_price <= 0:
                mark_price = pos['entry_price']

            if pos['direction'] == 'LONG':
                unrealized = pos['size_usdt'] * ((mark_price / pos['entry_price']) - 1)
                equity += pos['size_usdt'] + unrealized
            else:
                margin_value = pos['size_usdt']
                unrealized = pos['size_usdt'] * ((pos['entry_price'] / mark_price) - 1)
                equity += margin_value + unrealized

        return equity
    
    def _check_exit_conditions(self, position: Dict, current_row: pd.Series) -> Tuple[bool, str]:
        """Проверяет условия выхода из позиции с реалистичным разрешением конфликтов TP/SL"""
        high = current_row['high']
        low = current_row['low']
        open_price = current_row['open']

        if position['direction'] == 'LONG':
            if open_price >= position['take_profit']:
                return True, 'TP'
            if open_price <= position['stop_loss']:
                return True, 'SL'

            hit_tp = high >= position['take_profit']
            hit_sl = low <= position['stop_loss']

            if hit_tp and hit_sl:
                tp_distance = abs(position['take_profit'] - open_price)
                sl_distance = abs(open_price - position['stop_loss'])
                if tp_distance < sl_distance:
                    return True, 'TP'
                if sl_distance < tp_distance:
                    return True, 'SL'
                return True, 'TP'  # при равных расстояниях отдаём предпочтение TP

            if hit_sl:
                return True, 'SL'
            if hit_tp:
                return True, 'TP'
        else:  # SHORT
            if open_price <= position['take_profit']:
                return True, 'TP'
            if open_price >= position['stop_loss']:
                return True, 'SL'

            hit_tp = low <= position['take_profit']
            hit_sl = high >= position['stop_loss']

            if hit_tp and hit_sl:
                tp_distance = abs(open_price - position['take_profit'])
                sl_distance = abs(position['stop_loss'] - open_price)
                if tp_distance < sl_distance:
                    return True, 'TP'
                if sl_distance < tp_distance:
                    return True, 'SL'
                return True, 'TP'

            if hit_sl:
                return True, 'SL'
            if hit_tp:
                return True, 'TP'

        return False, ''
    
    def _close_position(self, position_index: int, current_row: pd.Series, 
                       index: int, exit_reason: str):
        """Закрывает позицию"""
        pos = self.positions[position_index]
        
        # Определяем цену выхода
        if exit_reason == 'TP':
            exit_price = pos['take_profit']
        elif exit_reason == 'SL':
            exit_price = pos['stop_loss']
        else:
            exit_price = current_row['close']
        
        # Применяем slippage
        if pos['direction'] == 'LONG':
            exit_price *= (1 - self.config.slippage)
        else:
            exit_price *= (1 + self.config.slippage)
        
        quantity = pos.get('quantity', 0.0)
        if quantity <= 0:
            quantity = pos['size_usdt'] / pos['entry_price'] if pos['entry_price'] > 0 else 0.0

        if pos['direction'] == 'LONG':
            gross_pnl = (exit_price - pos['entry_price']) * quantity
        else:
            gross_pnl = (pos['entry_price'] - exit_price) * quantity

        exit_notional = exit_price * quantity
        exit_commission = exit_notional * self.config.commission

        # Возвращаем заблокированный капитал и учитываем итоговый денежный поток
        self.capital += pos['size_usdt'] + gross_pnl - exit_commission
        self.latest_prices[pos['symbol']] = exit_price
        
        # Сохраняем сделку
        total_commission = pos['commission_paid'] + exit_commission
        net_trade_pnl = gross_pnl - total_commission
        trade = Trade(
            entry_time=pos['entry_time'],
            exit_time=current_row.name,
            symbol=pos['symbol'],
            direction=pos['direction'],
            entry_price=pos['entry_price'],
            exit_price=exit_price,
            size=pos['size_usdt'],
            pnl=net_trade_pnl,
            pnl_pct=(net_trade_pnl / pos['size_usdt']) * 100 if pos['size_usdt'] > 0 else 0.0,
            exit_reason=exit_reason,
            confidence=pos['confidence'],
            duration_candles=index - pos['entry_index'],
            atr=pos.get('atr'),
            sl_distance_pct=pos.get('sl_distance_pct'),
            tp_distance_pct=pos.get('tp_distance_pct'),
            risk_reward=pos.get('risk_reward'),
            atr_percentile=pos.get('atr_percentile')
        )
        self.trades.append(trade)
        
        # Удаляем позицию
        del self.positions[position_index]
    
    def _close_all_positions(self, last_row: pd.Series, last_index: int):
        """Закрывает все оставшиеся позиции"""
        while self.positions:
            self._close_position(0, last_row, last_index, 'TIME')
    
    def _close_positions_for_symbol(self, symbol: str, last_row: pd.Series, last_index: int):
        """Закрывает все позиции по символу"""
        i = 0
        while i < len(self.positions):
            if self.positions[i]['symbol'] == symbol:
                self._close_position(i, last_row, last_index, 'TIME')
            else:
                i += 1
    
    def _check_risk_limits(self) -> bool:
        """Проверяет лимиты риска"""
        if not self.equity_curve:
            return False
        
        equity_series = pd.Series([e[1] for e in self.equity_curve])
        
        # Просадка от начального капитала
        current_equity = equity_series.iloc[-1]
        drawdown = ((current_equity - self.config.initial_capital) /
                    self.config.initial_capital * 100)
        
        if drawdown < -self.config.max_drawdown_pct:
            return True
        
        return False
    
    def _calculate_results(self, symbol: str = None, multi_asset: bool = False) -> BacktestResult:
        """Вычисляет финальные метрики"""
        if not self.trades:
            return self._empty_result()
        
        trades_df = pd.DataFrame([asdict(t) for t in self.trades])

        def describe(series: pd.Series) -> Dict[str, float]:
            series = series.dropna()
            if series.empty:
                return {}
            return {
                'mean': float(series.mean()),
                'median': float(series.median()),
                'p25': float(series.quantile(0.25)),
                'p75': float(series.quantile(0.75)),
                'min': float(series.min()),
                'max': float(series.max()),
            }
        
        winning_trades = trades_df[trades_df['pnl'] > 0]
        losing_trades = trades_df[trades_df['pnl'] <= 0]
        
        win_rate = len(winning_trades) / len(trades_df) * 100
        
        gross_profit = winning_trades['pnl'].sum() if len(winning_trades) > 0 else 0
        gross_loss = abs(losing_trades['pnl'].sum()) if len(losing_trades) > 0 else 0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        total_return_usdt = self.capital - self.config.initial_capital
        total_return = (total_return_usdt / self.config.initial_capital) * 100
        
        # Max drawdown
        equity_series = pd.Series([e[1] for e in self.equity_curve])
        running_max = equity_series.expanding().max()
        drawdown = (equity_series - running_max) / running_max * 100
        max_drawdown = abs(drawdown.min())
        
        # Sharpe ratio (упрощённый)
        returns = equity_series.pct_change().dropna()
        sharpe = (returns.mean() / returns.std() * np.sqrt(252)) if len(returns) > 0 else 0
        
        # Exit reasons
        by_exit_reason = trades_df['exit_reason'].value_counts().to_dict()

        atr_stats = describe(trades_df['atr']) if 'atr' in trades_df else {}
        sl_distance_stats = describe(trades_df['sl_distance_pct']) if 'sl_distance_pct' in trades_df else {}
        tp_distance_stats = describe(trades_df['tp_distance_pct']) if 'tp_distance_pct' in trades_df else {}
        risk_reward_stats = describe(trades_df['risk_reward']) if 'risk_reward' in trades_df else {}
        
        # By symbol (если мультиактив)
        by_symbol = None
        if multi_asset:
            by_symbol = {}
            for sym in trades_df['symbol'].unique():
                sym_trades = trades_df[trades_df['symbol'] == sym]
                sym_wins = sym_trades[sym_trades['pnl'] > 0]
                by_symbol[sym] = {
                    'trades': len(sym_trades),
                    'win_rate': len(sym_wins) / len(sym_trades) * 100,
                    'total_return': sym_trades['pnl'].sum(),
                }
        
        return BacktestResult(
            total_trades=len(trades_df),
            winning_trades=len(winning_trades),
            losing_trades=len(losing_trades),
            win_rate=win_rate,
            total_return=total_return,
            total_return_usdt=total_return_usdt,
            profit_factor=profit_factor,
            avg_win=winning_trades['pnl_pct'].mean() if len(winning_trades) > 0 else 0,
            avg_loss=losing_trades['pnl_pct'].mean() if len(losing_trades) > 0 else 0,
            avg_trade=trades_df['pnl_pct'].mean(),
            avg_duration_candles=trades_df['duration_candles'].mean(),
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe,
            final_capital=self.capital,
            trades=self.trades,
            equity_curve=equity_series,
            by_exit_reason=by_exit_reason,
            by_symbol=by_symbol,
            atr_stats=atr_stats,
            sl_distance_stats=sl_distance_stats,
            tp_distance_stats=tp_distance_stats,
            risk_reward_stats=risk_reward_stats,
            signal_log_files=self.last_signal_log_files
        )
    
    def _empty_result(self) -> BacktestResult:
        """Возвращает пустой результат если не было сделок"""
        return BacktestResult(
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            win_rate=0,
            total_return=0,
            total_return_usdt=0,
            profit_factor=0,
            avg_win=0,
            avg_loss=0,
            avg_trade=0,
            avg_duration_candles=0,
            max_drawdown=0,
            sharpe_ratio=0,
            final_capital=self.config.initial_capital,
            trades=[],
            equity_curve=pd.Series([self.config.initial_capital]),
            by_exit_reason={},
            by_symbol=None,
            atr_stats={},
            sl_distance_stats={},
            tp_distance_stats={},
            risk_reward_stats={},
            signal_log_files=[]
        )
