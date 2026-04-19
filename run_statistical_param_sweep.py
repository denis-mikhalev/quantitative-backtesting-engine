"""
Параметрический прогон конфигураций Statistical System

- Загружает данные один раз
- Прогоняет несколько наборов параметров
- Выводит сводную таблицу и сохраняет результаты в JSON/CSV
"""

import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

import ccxt
import pandas as pd

from statistical_system import (
    StatisticalSignalGenerator,
    BacktestEngine,
    SignalConfig,
    BacktestConfig,
    get_preset,
)


def fetch_historical_data(symbol: str, timeframe: str, days: int) -> pd.DataFrame:
    """Загружает исторические данные через ccxt (аналогично run_statistical_backtest)."""
    print(f"📥 Loading {days} days of {timeframe} data for {symbol}...")

    exchange = ccxt.binance({'enableRateLimit': True})

    timeframe_minutes = {
        '15m': 15, '30m': 30, '1h': 60, '4h': 240, '1d': 1440
    }
    minutes = timeframe_minutes.get(timeframe, 30)
    candles_needed = (days * 24 * 60) // minutes

    all_data: List[List[float]] = []
    since = exchange.parse8601(
        (datetime.now() - timedelta(days=days)).isoformat()
    )

    while len(all_data) < candles_needed:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, since=since, limit=1000)
        if not ohlcv:
            break
        all_data.extend(ohlcv)
        since = ohlcv[-1][0] + 1
        print(f"   Loaded {len(all_data)} candles...", end='\r')

    print(f"\n✅ Loaded {len(all_data)} candles")
    df = pd.DataFrame(all_data, columns=['timestamp','open','high','low','close','volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    return df


def build_grid() -> List[Dict]:
    """Формирует сетку для узконаправленного поиска вокруг лучших найденных значений."""
    grid: List[Dict] = []
    min_conf_list = [0.75]  # Фиксируем лучшую уверенность
    tp_sl_list: List[Tuple[float, float]] = [
        (2.0, 1.8), (2.2, 1.8),
        (2.5, 2.0), (2.8, 2.0),
        (3.0, 2.2), (3.2, 2.2),
    ]
    time_exit_list = [72, 96] # Увеличиваем время жизни сделки
    adx_options = [
        {'require_adx': True,  'adx_min': 20.0}, # Фиксируем фильтр ADX
    ]

    for min_conf in min_conf_list:
        for tp_mult, sl_mult in tp_sl_list:
            for time_exit in time_exit_list:
                for adx in adx_options:
                    cfg = {
                        'min_conf': min_conf,
                        'tp_mult': tp_mult,
                        'sl_mult': sl_mult,
                        'time_exit_candles': time_exit,
                        'trend_filter': True,
                        'require_adx': adx['require_adx'],
                        'adx_min': adx['adx_min'] if adx['require_adx'] else None,
                        'adx_period': 14,
                    }
                    grid.append(cfg)
    return grid


def run_one(df: pd.DataFrame, symbol: str, timeframe: str, days: int, cfg: Dict) -> Dict:
    """Запускает один прогон и возвращает метрики + конфиг."""
    signal_config = get_preset('balanced')
    signal_config.min_confidence = cfg['min_conf']
    signal_config.trend_filter_enabled = True
    signal_config.require_adx = cfg['require_adx']
    if cfg['require_adx']:
        signal_config.adx_min = cfg['adx_min']
        signal_config.adx_period = cfg['adx_period']

    backtest_config = BacktestConfig(
        initial_capital=10000.0,
        position_size_pct=0.02,
        max_positions=5,
        tp_atr_mult=cfg['tp_mult'],
        sl_atr_mult=cfg['sl_mult'],
        min_confidence=cfg['min_conf'],
        enable_time_exit=True,
        time_exit_candles=cfg['time_exit_candles'],
    )

    engine = BacktestEngine(StatisticalSignalGenerator(signal_config), backtest_config)
    result = engine.run(df, symbol)

    # собрать ключевые метрики
    by_exit = result.by_exit_reason or {}
    return {
        'symbol': symbol,
        'timeframe': timeframe,
        'days': days,
        'min_conf': cfg['min_conf'],
        'tp_mult': cfg['tp_mult'],
        'sl_mult': cfg['sl_mult'],
        'time_exit_candles': cfg['time_exit_candles'],
        'trend_filter': True,
        'require_adx': cfg['require_adx'],
        'adx_min': cfg['adx_min'] if cfg['require_adx'] else None,
        'total_trades': result.total_trades,
        'win_rate': round(result.win_rate, 2),
        'profit_factor': round(result.profit_factor, 3) if result.profit_factor != float('inf') else float('inf'),
        'total_return_pct': round(result.total_return, 2),
        'max_drawdown': round(result.max_drawdown, 2),
        'avg_duration_candles': round(result.avg_duration_candles or 0, 2),
        'SL': by_exit.get('SL', 0),
        'TP': by_exit.get('TP', 0),
        'TIME': by_exit.get('TIME', 0),
    }


def main():
    parser = argparse.ArgumentParser(description='Parameter sweep for Statistical System')
    parser.add_argument('--symbol', default='BTC/USDT')
    parser.add_argument('--timeframe', default='30m')
    parser.add_argument('--days', type=int, default=60)
    parser.add_argument('--limit', type=int, default=0, help='Ограничить кол-во конфигураций для прогона (0=все)')
    args = parser.parse_args()

    print("\n" + "="*70)
    print("🧪 PARAMETER SWEEP - Statistical System")
    print("="*70)
    print(f"Symbol: {args.symbol}, Timeframe: {args.timeframe}, Days: {args.days}")

    df = fetch_historical_data(args.symbol, args.timeframe, args.days)
    if df is None or len(df) < 200:
        print("❌ Not enough data")
        return

    grid = build_grid()
    if args.limit and args.limit > 0:
        grid = grid[:args.limit]

    print(f"Running {len(grid)} configurations...\n")

    results: List[Dict] = []
    for i, cfg in enumerate(grid, 1):
        print(f"[{i}/{len(grid)}] min_conf={cfg['min_conf']} tp/sl={cfg['tp_mult']}/{cfg['sl_mult']} time_exit={cfg['time_exit_candles']} adx={'on' if cfg['require_adx'] else 'off'}")
        row = run_one(df, args.symbol, args.timeframe, args.days, cfg)
        results.append(row)

    res_df = pd.DataFrame(results)

    # Сортировки
    by_pf = res_df.sort_values(by=['profit_factor','win_rate','total_trades'], ascending=[False, False, False])
    by_wr = res_df.sort_values(by=['win_rate','profit_factor','total_trades'], ascending=[False, False, False])

    # Вывод топов
    print("\nTop by Profit Factor (top 5):")
    print(by_pf.head(5).to_string(index=False))

    print("\nTop by Win Rate (top 5):")
    print(by_wr.head(5).to_string(index=False))

    # Сохранение
    out_dir = Path('statistical_system/results')
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')

    csv_path = out_dir / f'sweep_{ts}.csv'
    json_path = out_dir / f'sweep_{ts}.json'

    res_df.to_csv(csv_path, index=False)
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump({'config_count': len(results), 'results': results}, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Saved: {csv_path}")
    print(f"💾 Saved: {json_path}")


if __name__ == '__main__':
    main()
