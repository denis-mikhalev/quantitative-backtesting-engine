"""
Главный скрипт для запуска статистической торговой системы

Режимы работы:
1. Одноразовое сканирование
2. Непрерывное сканирование
3. Бэктест
"""

import argparse
import sys
from pathlib import Path

# Добавляем путь к проекту
sys.path.append(str(Path(__file__).parent))

from statistical_system import (
    MultiAssetScanner,
    ScannerConfig,
    SignalConfig,
    get_preset
)


def parse_args():
    parser = argparse.ArgumentParser(
        description='Statistical Trading System - Level 1'
    )
    
    # Режим работы
    parser.add_argument('--mode', 
                       choices=['scan', 'continuous', 'backtest'],
                       default='scan',
                       help='Режим работы')
    
    # Параметры сигналов
    parser.add_argument('--preset',
                       choices=['conservative', 'balanced', 'aggressive'],
                       default='balanced',
                       help='Пресет для генерации сигналов')
    
    parser.add_argument('--min-confidence',
                       type=float,
                       default=0.5,
                       help='Минимальная уверенность сигнала (0-1)')
    
    # Параметры сканера
    parser.add_argument('--symbols',
                       nargs='+',
                       help='Список монет для сканирования (по умолчанию из конфига)')
    
    parser.add_argument('--timeframe',
                       default='30m',
                       help='Таймфрейм (15m, 30m, 1h, 4h)')
    
    parser.add_argument('--max-signals',
                       type=int,
                       default=10,
                       help='Максимум сигналов для отображения')
    
    # Непрерывный режим
    parser.add_argument('--interval',
                       type=int,
                       default=1800,
                       help='Интервал обновления в секундах (для continuous режима)')
    
    # Telegram
    parser.add_argument('--telegram',
                       action='store_true',
                       help='Отправлять уведомления в Telegram')
    
    parser.add_argument('--telegram-high-conf-only',
                       action='store_true',
                       default=True,
                       help='Отправлять только высоко-уверенные сигналы')
    
    # Общие
    parser.add_argument('--verbose',
                       action='store_true',
                       default=True,
                       help='Подробный вывод')
    
    parser.add_argument('--save-results',
                       action='store_true',
                       default=True,
                       help='Сохранять результаты в JSON')
    
    return parser.parse_args()


def main():
    args = parse_args()
    
    # Конфигурация сигналов
    signal_config = get_preset(args.preset)
    if args.min_confidence:
        signal_config.min_confidence = args.min_confidence
    
    # Конфигурация сканера
    scanner_config = ScannerConfig(
        timeframe=args.timeframe,
        min_signal_confidence=args.min_confidence,
        max_signals_to_show=args.max_signals,
        update_interval=args.interval,
        send_telegram=args.telegram,
        telegram_only_high_confidence=args.telegram_high_conf_only,
        verbose=args.verbose,
        save_results=args.save_results,
    )
    
    # Переопределяем символы если указаны
    if args.symbols:
        scanner_config.symbols = args.symbols
    
    # Инициализация сканера
    scanner = MultiAssetScanner(scanner_config, signal_config)
    
    # Запуск в зависимости от режима
    if args.mode == 'scan':
        print("\n🔍 Single Scan Mode")
        signals = scanner.scan_and_display()
        
        if scanner_config.save_results and signals:
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filepath = f"statistical_system/results/signals_{timestamp}.json"
            scanner.export_signals(signals, filepath)
    
    elif args.mode == 'continuous':
        print("\n🔄 Continuous Scan Mode")
        scanner.continuous_scan(args.interval)
    
    elif args.mode == 'backtest':
        print("\n📊 Backtest Mode")
        print("❌ Backtest mode: use run_statistical_backtest.py instead")
        sys.exit(1)


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
