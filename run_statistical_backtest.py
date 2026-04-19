"""
Бэктест статистической торговой системы

Тестирует систему на исторических данных
"""

import argparse
import sys
import json
import copy
import ccxt
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict

sys.path.append(str(Path(__file__).parent))

from statistical_system import (
    StatisticalSignalGenerator,
    BacktestEngine,
    SignalConfig,
    BacktestConfig,
    get_preset
)


def fetch_historical_data(symbol: str, timeframe: str, days: int) -> pd.DataFrame:
    """Загружает исторические данные"""
    print(f"📥 Loading {days} days of {timeframe} data for {symbol}...")
    
    exchange = ccxt.binance({'enableRateLimit': True})
    
    # Вычисляем количество свечей
    timeframe_minutes = {
        '15m': 15, '30m': 30, '1h': 60, '4h': 240, '1d': 1440
    }
    
    minutes = timeframe_minutes.get(timeframe, 30)
    candles_needed = (days * 24 * 60) // minutes
    
    # Загружаем батчами (макс 1000 за раз)
    all_data = []
    since = exchange.parse8601(
        (datetime.now() - timedelta(days=days)).isoformat()
    )
    
    while len(all_data) < candles_needed:
        try:
            ohlcv = exchange.fetch_ohlcv(
                symbol,
                timeframe=timeframe,
                since=since,
                limit=1000
            )
            
            if not ohlcv:
                break
            
            all_data.extend(ohlcv)
            since = ohlcv[-1][0] + 1  # следующая свеча
            
            print(f"   Loaded {len(all_data)} candles...", end='\r')
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            break
    
    print(f"\n✅ Loaded {len(all_data)} candles")
    
    # Конвертация в DataFrame
    df = pd.DataFrame(
        all_data,
        columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
    )
    
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    
    return df


def load_multiple_symbols(symbols: list, timeframe: str, days: int) -> Dict[str, pd.DataFrame]:
    """Загружает данные для нескольких монет"""
    data = {}
    
    for symbol in symbols:
        try:
            df = fetch_historical_data(symbol, timeframe, days)
            if df is not None and len(df) > 200:
                data[symbol] = df
        except Exception as e:
            print(f"❌ Failed to load {symbol}: {e}")
    
    return data


def parse_args():
    parser = argparse.ArgumentParser(
        description='Backtest Statistical Trading System'
    )
    
    # Данные
    parser.add_argument('--symbol',
                       default='BTCUSDT',
                       help='Монета для тестирования (для single mode)')
    
    parser.add_argument('--symbols',
                       nargs='+',
                       help='Список монет (для multi mode)')
    
    parser.add_argument('--timeframe',
                       default='30m',
                       help='Таймфрейм (15m, 30m, 1h, 4h)')
    
    parser.add_argument('--days',
                       type=int,
                       default=180,
                       help='Количество дней истории для теста')
    
    # Конфигурация сигналов
    parser.add_argument('--preset',
                       choices=['conservative', 'balanced', 'aggressive'],
                       default='balanced',
                       help='Пресет для генерации сигналов')
    
    parser.add_argument('--min-confidence',
                       type=float,
                       default=0.5,
                       help='Минимальная уверенность сигнала')

    # Тренд-фильтр и ADX
    trend_group = parser.add_mutually_exclusive_group()
    trend_group.add_argument('--trend-filter', dest='trend_filter', action='store_true', help='Включить тренд-фильтр EMA')
    trend_group.add_argument('--no-trend-filter', dest='trend_filter', action='store_false', help='Отключить тренд-фильтр EMA')
    parser.set_defaults(trend_filter=True)

    parser.add_argument('--require-adx', action='store_true', default=False, help='Требовать силу тренда по ADX')
    parser.add_argument('--adx-min', type=float, default=20.0, help='Минимальное значение ADX')
    parser.add_argument('--adx-period', type=int, default=14, help='Период ADX')
    
    # Конфигурация бэктеста
    parser.add_argument('--capital',
                       type=float,
                       default=10000,
                       help='Начальный капитал')
    
    parser.add_argument('--risk-pct',
                       type=float,
                       default=0.02,
                       help='Риск на сделку (0.02 = 2%)')
    
    parser.add_argument('--max-positions',
                       type=int,
                       default=5,
                       help='Максимум одновременных позиций')
    
    parser.add_argument('--tp-mult',
                       type=float,
                       default=2.0,
                       help='Take Profit множитель ATR')
    
    parser.add_argument('--sl-mult',
                       type=float,
                       default=1.0,
                       help='Stop Loss множитель ATR')

    # Time-based exit
    time_exit_group = parser.add_mutually_exclusive_group()
    time_exit_group.add_argument('--enable-time-exit', dest='enable_time_exit', action='store_true', help='Включить закрытие по времени')
    time_exit_group.add_argument('--no-time-exit', dest='enable_time_exit', action='store_false', help='Отключить закрытие по времени')
    parser.set_defaults(enable_time_exit=True)
    parser.add_argument('--time-exit-candles', type=int, default=48, help='Число свечей до закрытия по времени')
    
    # Режим
    parser.add_argument('--mode',
                       choices=['single', 'multi'],
                       default='single',
                       help='Single asset или multi asset backtest')
    
    # Сохранение
    parser.add_argument('--save-results',
                       action='store_true',
                       default=True,
                       help='Сохранить результаты в JSON')

    parser.add_argument('--log-signals',
                       action='store_true',
                       default=False,
                       help='Сохранять детальный журнал сигналов в CSV/JSON')

    parser.add_argument('--signals-log-dir',
                       default=None,
                       help='Каталог для сохранения журналов сигналов')

    parser.add_argument('--analyze-setups',
                       action='store_true',
                       default=False,
                       help='Выполнить отдельные бэктесты по каждому сетапу')
    
    return parser.parse_args()


def main():
    args = parse_args()
    
    print("\n" + "="*70)
    print("📊 STATISTICAL SYSTEM BACKTEST")
    print("="*70)
    
    # Конфигурации
    signal_config = get_preset(args.preset)
    signal_config.min_confidence = args.min_confidence
    # Trend filter & ADX
    signal_config.trend_filter_enabled = args.trend_filter
    signal_config.require_adx = args.require_adx
    signal_config.adx_min = args.adx_min
    signal_config.adx_period = args.adx_period
    
    backtest_config_kwargs = {
        'initial_capital': args.capital,
        'position_size_pct': args.risk_pct,
        'max_positions': args.max_positions,
        'tp_atr_mult': args.tp_mult,
        'sl_atr_mult': args.sl_mult,
        'min_confidence': args.min_confidence,
        'enable_time_exit': args.enable_time_exit,
        'time_exit_candles': args.time_exit_candles,
        'log_signals': args.log_signals,
    }

    if args.signals_log_dir:
        backtest_config_kwargs['signals_log_dir'] = args.signals_log_dir

    backtest_config = BacktestConfig(**backtest_config_kwargs)
    
    print(f"\n⚙️ Configuration:")
    print(f"   Preset:         {args.preset}")
    print(f"   Min Confidence: {args.min_confidence:.0%}")
    print(f"   Capital:        ${args.capital:,.0f}")
    print(f"   Risk per trade: {args.risk_pct:.1%}")
    print(f"   TP/SL:          {args.tp_mult}x / {args.sl_mult}x ATR")
    print(f"   Max positions:  {args.max_positions}")
    print(f"   Trend filter:   {'ON' if args.trend_filter else 'OFF'}")
    if args.trend_filter:
        print(f"   ADX required:   {'YES' if args.require_adx else 'NO'}")
        if args.require_adx:
            print(f"   ADX settings:   period={args.adx_period}, min={args.adx_min}")
    print(f"   Time exit:      {'ON' if args.enable_time_exit else 'OFF'} ({args.time_exit_candles} candles)")
    
    # Инициализация
    signal_generator = StatisticalSignalGenerator(signal_config)
    backtest_engine = BacktestEngine(signal_generator, backtest_config)
    
    # Запуск бэктеста
    raw_df = None
    raw_data = {}
    data = {}

    if args.mode == 'single':
        print(f"\n🪙 Single Asset Mode: {args.symbol}")
        print(f"📊 {args.days} days of {args.timeframe} data")
        
        # Загрузка данных
        df = fetch_historical_data(args.symbol, args.timeframe, args.days)
        
        if df is None or len(df) < 200:
            print("❌ Not enough data")
            sys.exit(1)

        raw_df = df.copy()
        
        # Запуск бэктеста
        print("\n🚀 Running backtest...")
        result = backtest_engine.run(df.copy(), args.symbol)
        
    else:  # multi mode
        print(f"\n🪙 Multi Asset Mode")
        
        # Определяем монеты
        if args.symbols:
            symbols = args.symbols
        else:
            symbols = [
                'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT',
                'ADAUSDT', 'DOGEUSDT', 'DOTUSDT', 'LINKUSDT', 'AVAXUSDT'
            ]
        
        print(f"📊 Testing {len(symbols)} symbols for {args.days} days on {args.timeframe}")
        
        # Загрузка данных
        data = load_multiple_symbols(symbols, args.timeframe, args.days)
        
        if not data:
            print("❌ No data loaded")
            sys.exit(1)
        
        print(f"✅ Loaded data for {len(data)} symbols")
        raw_data = {sym: df.copy() for sym, df in data.items()}
        
        # Запуск бэктеста
        print("\n🚀 Running multi-asset backtest...")
        result = backtest_engine.run_multi_asset({sym: df.copy() for sym, df in data.items()})
    
    # Вывод результатов
    result.print_summary()

    setup_analysis = {}
    if args.analyze_setups:
        print("\n🔬 Per-setup analysis")
        base_setups = list(signal_config.enabled_setups)
        for setup_name in base_setups:
            setup_signal_config = copy.deepcopy(signal_config)
            setup_signal_config.enabled_setups = [setup_name]

            analysis_config = copy.deepcopy(backtest_config)
            analysis_config.log_signals = False

            analysis_generator = StatisticalSignalGenerator(setup_signal_config)
            analysis_engine = BacktestEngine(analysis_generator, analysis_config)

            if args.mode == 'single':
                if raw_df is None:
                    continue
                setup_result = analysis_engine.run(raw_df.copy(), args.symbol)
            else:
                if not raw_data:
                    continue
                setup_result = analysis_engine.run_multi_asset({sym: df.copy() for sym, df in raw_data.items()})

            setup_summary = {
                'total_trades': setup_result.total_trades,
                'win_rate': setup_result.win_rate,
                'profit_factor': setup_result.profit_factor,
                'total_return': setup_result.total_return,
                'by_exit_reason': setup_result.by_exit_reason,
                'atr_stats': setup_result.atr_stats,
                'sl_distance_stats': setup_result.sl_distance_stats,
                'tp_distance_stats': setup_result.tp_distance_stats,
                'risk_reward_stats': setup_result.risk_reward_stats,
            }
            setup_analysis[setup_name] = setup_summary

            print(
                f"   • {setup_name}: trades={setup_summary['total_trades']}, "
                f"WR={setup_summary['win_rate']:.1f}%, "
                f"PF={setup_summary['profit_factor']:.2f}, "
                f"Return={setup_summary['total_return']:.2f}%"
            )
    
    # Сохранение
    if args.save_results:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        mode_str = 'single' if args.mode == 'single' else 'multi'
        filepath = f"statistical_system/results/backtest_{mode_str}_{timestamp}.json"
        
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        payload = {
            'config': {
                'mode': args.mode,
                'symbol': args.symbol if args.mode == 'single' else None,
                'symbols': list(data.keys()) if args.mode == 'multi' else None,
                'timeframe': args.timeframe,
                'days': args.days,
                'preset': args.preset,
                'min_confidence': args.min_confidence,
                'capital': args.capital,
                'trend_filter': args.trend_filter,
                'require_adx': args.require_adx,
                'adx_period': args.adx_period,
                'adx_min': args.adx_min,
                'tp_mult': args.tp_mult,
                'sl_mult': args.sl_mult,
                'enable_time_exit': args.enable_time_exit,
                'time_exit_candles': args.time_exit_candles,
            },
            'results': result.to_dict(),
        }

        if setup_analysis:
            payload['analysis'] = {'per_setup': setup_analysis}

        with open(filepath, 'w') as f:
            json.dump(payload, f, indent=2)
        
        print(f"\n💾 Results saved to: {filepath}")
    
    # Рекомендации
    print("\n" + "="*70)
    print("💡 RECOMMENDATIONS")
    print("="*70)
    
    if result.win_rate < 50:
        print("⚠️  Win rate low - consider:")
        print("   • Using 'conservative' preset")
        print("   • Increasing min-confidence")
        print("   • Adjusting TP/SL multipliers")
    
    if result.profit_factor < 1.5:
        print("⚠️  Profit factor low - consider:")
        print("   • Increasing TP multiplier")
        print("   • Tightening stop loss")
    
    if result.max_drawdown > 20:
        print("⚠️  Drawdown high - consider:")
        print("   • Reducing risk per trade")
        print("   • Reducing max positions")
    
    if result.total_return > 10 and result.win_rate > 55 and result.profit_factor > 1.5:
        print("✅ System looks promising!")
        print("   • Consider paper trading")
        print("   • Test on different timeframes")
        print("   • Test on more symbols")
    
    print("="*70)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⛔ Stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
