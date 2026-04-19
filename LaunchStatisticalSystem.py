"""
🚀 УДОБНЫЙ ЗАПУСК СТАТИСТИЧЕСКОЙ ТОРГОВОЙ СИСТЕМЫ

Этот скрипт предоставляет простой интерфейс для запуска системы
с оптимальными параметрами, найденными в ходе бэктестирования.

РЕЗУЛЬТАТЫ БЭКТЕСТОВ:
- 1d таймфрейм: +24.26% годовых, Win Rate 52.83%, PF 1.92
- 12h таймфрейм: +13.93% за 6 месяцев (~28% годовых), Win Rate 50.98%, PF 1.72

РЕКОМЕНДУЕМЫЕ КОНФИГУРАЦИИ:
1. КОНСЕРВАТИВНАЯ: 1d + balanced preset (20-25% годовых)
2. АГРЕССИВНАЯ: 12h + balanced preset (25-30% годовых)
3. ГИБРИДНАЯ: оба бота одновременно
"""

import argparse
import subprocess
import sys
from pathlib import Path


# === ОПТИМАЛЬНЫЕ КОНФИГУРАЦИИ НА ОСНОВЕ БЭКТЕСТОВ ===

CONFIGURATIONS = {
    'conservative': {
        'name': '🛡️  Консервативная (1d таймфрейм)',
        'timeframe': '1d',
        'preset': 'balanced',
        'expected_return': '20-25% годовых',
        'win_rate': '52.83%',
        'profit_factor': '1.92',
        'max_drawdown': '~7%',
        'trades_per_year': '~50-60',
    },
    'aggressive': {
        'name': '⚡ Агрессивная (12h таймфрейм)',
        'timeframe': '12h',
        'preset': 'balanced',
        'expected_return': '25-30% годовых',
        'win_rate': '50.98%',
        'profit_factor': '1.72',
        'max_drawdown': '~8%',
        'trades_per_year': '~100',
    },
    'experimental_4h': {
        'name': '🧪 Экспериментальная (4h таймфрейм)',
        'timeframe': '4h',
        'preset': 'balanced',
        'expected_return': '~0% (почти безубыточность)',
        'win_rate': '32.71%',
        'profit_factor': '0.94',
        'max_drawdown': '~11%',
        'trades_per_year': '~400',
        'warning': '⚠️  НЕ РЕКОМЕНДУЕТСЯ - низкая прибыльность'
    }
}

# Топовые монеты на основе бэктестов
RECOMMENDED_COINS = {
    '1d': [
        'DOGEUSDT',  # +1516% в бэктесте, WR 83.3%
        'DOTUSDT',   # +672% в бэктесте, WR 66.7%
        'BTCUSDT',   # +394% в бэктесте, WR 53.8%
        'XRPUSDT',   # +126% в бэктесте, WR 50%
        'SOLUSDT',   # +75% в бэктесте
        'ETHUSDT',
        'BNBUSDT',
        'LINKUSDT',
        'ADAUSDT',
        'AVAXUSDT',
        'SUIUSDT',
        'ARBUSDT',
        'ORDIUSDT',
        'PEPEUSDT',
        'LTCUSDT',
        'POLUSDT',
        'WIFUSDT',
        'ENAUSDT',
        'UNIUSDT',
        'ATOMUSDT',
        'TRXUSDT',
        'XLMUSDT',
        'TONUSDT',
        'NEARUSDT',
        'OPUSDT',
        'AAVEUSDT',
        'APTUSDT',
        'SEIUSDT',
        'FILUSDT',
        'XMRUSDT',
        'INJUSDT',
        'HYPEUSDT',    
        'HBARUSDT',
        'WLDUSDT',
        'SHIBUSDT',
        '1INCHUSDT',
        'TAOUSDT',
        'ACMUSDT',
        'ICPUSDT',
        'ETCUSDT',
        'ONDOUSDT',
        'ALGOUSDT',
        'ALICEUSDT',
        'ANKRUSDT',
        'STRKUSDT',
        'TNSRUSDT',
        'BCHUSDT',
        'WLFIUSDT',
        'PAXGUSDT',
        'DASHUSDT',
        'FETUSDT',
        'ZENUSDT',
        'HFTUSDT',
        'DYMUSDT',
        'BONKUSDT',
        'CRVUSDT',
        'ZKUSDT',
        'CAKEUSDT',
        'LDOUSDT',
        'ETHFIUSDT',
        'ARUSDT',
        'TIAUSDT',
        'SUPERUSDT',
        'HOLOUSDT',
        'MAVUSDT',
        'DYMUSDT',
        'XVGUSDT',
        'SPELLUSDT',
        'WBETHUSDT',
        'LDOUSDT',
        'BATUSDT',
        'FLOKIUSDT',
    ],
    '12h': [
        'DOTUSDT',    # +333% в бэктесте, WR 100%
        'XRPUSDT',    # +316% в бэктесте, WR 50%
        'DOGEUSDT',   # +284% в бэктесте, WR 100%
        'SOLUSDT',    # +279% в бэктесте, WR 60%
        'ETHUSDT',    # +188% в бэктесте, WR 42.9%
        'BTCUSDT',
        'BNBUSDT',
        'LINKUSDT',
        'ADAUSDT',
        'AVAXUSDT',
        'SUIUSDT',
        'ARBUSDT',
        'ORDIUSDT',
        'PEPEUSDT',
        'LTCUSDT',
        'POLUSDT',
        'WIFUSDT',
        'ENAUSDT',
        'UNIUSDT',
        'ATOMUSDT',
        'TRXUSDT',
        'XLMUSDT',
        'TONUSDT',
        'NEARUSDT',
        'OPUSDT',
        'AAVEUSDT',
        'APTUSDT',
        'SEIUSDT',
        'FILUSDT',
        'XMRUSDT',
        'INJUSDT',
        'HYPEUSDT',        
        'HBARUSDT',
        'WLDUSDT',
        'SHIBUSDT',
        '1INCHUSDT',
        'TAOUSDT',
        'ACMUSDT',
        'ICPUSDT',
        'ETCUSDT',
        'ONDOUSDT',
        'ALGOUSDT',
        'ALICEUSDT',
        'ANKRUSDT',
        'STRKUSDT',
        'TNSRUSDT',
        'BCHUSDT',
        'WLFIUSDT',
        'PAXGUSDT',
        'DASHUSDT',
        'FETUSDT',
        'ZENUSDT',
        'HFTUSDT',
        'DYMUSDT',
        'BONKUSDT',
        'CRVUSDT',
        'ZKUSDT',
        'CAKEUSDT',
        'LDOUSDT',
        'ETHFIUSDT',
        'ARUSDT',
        'TIAUSDT',
        'SUPERUSDT',
        'HOLOUSDT',
        'MAVUSDT',
        'DYMUSDT',
        'XVGUSDT',
        'SPELLUSDT',
        'WBETHUSDT',
        'LDOUSDT',
        'BATUSDT',
        'FLOKIUSDT',
    ],
    'default': [
        'BTCUSDT' 
    ]
}


def show_configurations():
    """Показать доступные конфигурации"""
    print("\n" + "="*70)
    print("📊 ДОСТУПНЫЕ КОНФИГУРАЦИИ (на основе бэктестов)")
    print("="*70)
    
    for key, config in CONFIGURATIONS.items():
        print(f"\n{config['name']}")
        print(f"   ID: {key}")
        print(f"   Таймфрейм: {config['timeframe']}")
        print(f"   Preset: {config['preset']}")
        print(f"   Ожидаемая доходность: {config['expected_return']}")
        print(f"   Win Rate: {config['win_rate']}")
        print(f"   Profit Factor: {config['profit_factor']}")
        print(f"   Max Drawdown: {config['max_drawdown']}")
        print(f"   Сделок в год: {config['trades_per_year']}")
        if 'warning' in config:
            print(f"   {config['warning']}")
    
    print("\n" + "="*70)


def launch_scanner(config_name: str, mode: str = 'scan', 
                   custom_coins: list = None, telegram: bool = False):
    """
    Запустить сканер с выбранной конфигурацией
    
    Args:
        config_name: conservative, aggressive, или experimental_4h
        mode: scan (одноразовое), continuous (непрерывное)
        custom_coins: список монет (если не указан - используются рекомендованные)
        telegram: отправлять уведомления в Telegram
    """
    if config_name not in CONFIGURATIONS:
        print(f"❌ Неизвестная конфигурация: {config_name}")
        show_configurations()
        return
    
    config = CONFIGURATIONS[config_name]
    
    print("\n" + "="*70)
    print(f"🚀 ЗАПУСК: {config['name']}")
    print("="*70)
    print(f"Таймфрейм: {config['timeframe']}")
    print(f"Preset: {config['preset']}")
    print(f"Режим: {mode}")
    
    # Определяем монеты
    if custom_coins:
        coins = custom_coins
        print(f"Монеты: {len(coins)} (пользовательский список)")
    else:
        coins = RECOMMENDED_COINS.get(config['timeframe'], RECOMMENDED_COINS['default'])
        print(f"Монеты: {len(coins)} (рекомендованные для {config['timeframe']})")
    
    print(f"Telegram: {'✅ включен' if telegram else '❌ выключен'}")
    print("="*70 + "\n")
    
    # Собираем команду
    python_exe = sys.executable
    script_path = Path(__file__).parent / 'run_statistical_scanner.py'
    
    cmd = [
        python_exe,
        str(script_path),
        '--mode', mode,
        '--timeframe', config['timeframe'],
        '--preset', config['preset'],
        '--symbols', *coins,
        '--max-signals', '15',
    ]
    
    if telegram:
        cmd.append('--telegram')
    
    if mode == 'continuous':
        # Для 1d - проверяем раз в 4 часа
        # Для 12h - проверяем раз в 2 часа
        # Для 4h - проверяем раз в час
        interval_map = {
            '1d': 14400,   # 4 часа
            '12h': 7200,   # 2 часа
            '4h': 3600,    # 1 час
            '8h': 7200,    # 2 часа
        }
        interval = interval_map.get(config['timeframe'], 3600)
        cmd.extend(['--interval', str(interval)])
    
    # Запуск
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n\n⛔ Остановлено пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка запуска: {e}")


def main():
    parser = argparse.ArgumentParser(
        description='🚀 Launcher для статистической торговой системы',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:

1. Показать доступные конфигурации:
   python LaunchStatisticalSystem.py --list

2. Одноразовое сканирование (консервативная):
   python LaunchStatisticalSystem.py conservative

3. Непрерывное сканирование (агрессивная):
   python LaunchStatisticalSystem.py aggressive --continuous

4. С Telegram уведомлениями:
   python LaunchStatisticalSystem.py conservative --continuous --telegram

5. С пользовательским списком монет:
   python LaunchStatisticalSystem.py aggressive --coins BTCUSDT ETHUSDT SOLUSDT

6. Запустить оба бота одновременно (в отдельных терминалах):
   python LaunchStatisticalSystem.py conservative --continuous --telegram
   python LaunchStatisticalSystem.py aggressive --continuous --telegram
        """
    )
    
    parser.add_argument('config',
                       nargs='?',
                       choices=['conservative', 'aggressive', 'experimental_4h'],
                       help='Конфигурация для запуска')
    
    parser.add_argument('--list',
                       action='store_true',
                       help='Показать все доступные конфигурации')
    
    parser.add_argument('--continuous',
                       action='store_true',
                       help='Непрерывное сканирование (вместо одноразового)')
    
    parser.add_argument('--telegram',
                       action='store_true',
                       help='Отправлять уведомления в Telegram')
    
    parser.add_argument('--coins',
                       nargs='+',
                       help='Пользовательский список монет (по умолчанию - рекомендованные)')
    
    args = parser.parse_args()
    
    # Показать конфигурации
    if args.list or not args.config:
        show_configurations()
        if not args.config:
            print("\n💡 Используйте: python LaunchStatisticalSystem.py <config_name>")
            print("   Например: python LaunchStatisticalSystem.py conservative\n")
        return
    
    # Запустить сканер
    mode = 'continuous' if args.continuous else 'scan'
    launch_scanner(
        args.config,
        mode=mode,
        custom_coins=args.coins,
        telegram=args.telegram
    )


if __name__ == '__main__':
    main()
