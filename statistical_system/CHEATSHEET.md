# ⚡ Statistical System - Шпаргалка Команд

## 🏃 Быстрый Старт

```powershell
# Activate venv (PowerShell)
& .venv/Scripts/Activate.ps1

# Тест системы
python test_statistical_system.py

# Первый скан
python run_statistical_scanner.py --symbols BTCUSDT ETHUSDT SOLUSDT
```

---

## 📊 Сканирование

### Одноразовое сканирование
```powershell
# Топ-5 монет
python run_statistical_scanner.py --symbols BTCUSDT ETHUSDT SOLUSDT BNBUSDT XRPUSDT --max-signals 5

# Ваш watchlist (20 монет)
python run_statistical_scanner.py --symbols BTCUSDT ETHUSDT BNBUSDT SOLUSDT XRPUSDT ADAUSDT DOGEUSDT DOTUSDT LINKUSDT LTCUSDT NEARUSDT UNIUSDT ATOMUSDT AVAXUSDT OPUSDT ARBUSDT SUIUSDT APTUSDT AAVEUSDT INJUSDT

# С разными пресетами
python run_statistical_scanner.py --preset conservative --max-signals 5
python run_statistical_scanner.py --preset balanced --max-signals 10
python run_statistical_scanner.py --preset aggressive --max-signals 15
```

### Непрерывное сканирование
```powershell
# Каждые 30 минут
python run_statistical_scanner.py --mode continuous --interval 1800

# С Telegram уведомлениями
python run_statistical_scanner.py --mode continuous --telegram --interval 1800

# Кастомный список монет + Telegram
python run_statistical_scanner.py --mode continuous --symbols BTCUSDT ETHUSDT SOLUSDT NEARUSDT ADAUSDT --telegram --interval 1800
```

---

## 🧪 Бэктест

### Одна монета
```powershell
# BTC, 90 дней, 30m
python run_statistical_backtest.py --symbol BTCUSDT --days 90 --timeframe 30m

# ETH, 180 дней, 1h
python run_statistical_backtest.py --symbol ETHUSDT --days 180 --timeframe 1h

# SOL, 180 дней, 30m, консервативный
python run_statistical_backtest.py --symbol SOLUSDT --days 180 --timeframe 30m --preset conservative
```

### Мультивалютный портфель
```powershell
# Топ-5
python run_statistical_backtest.py --mode multi --days 180 --symbols BTCUSDT ETHUSDT BNBUSDT SOLUSDT XRPUSDT

# Топ-10
python run_statistical_backtest.py --mode multi --days 180 --symbols BTCUSDT ETHUSDT BNBUSDT SOLUSDT XRPUSDT ADAUSDT DOGEUSDT DOTUSDT LINKUSDT AVAXUSDT

# Ваш полный watchlist
python run_statistical_backtest.py --mode multi --days 180 --symbols BTCUSDT ETHUSDT BNBUSDT SOLUSDT XRPUSDT ADAUSDT DOGEUSDT DOTUSDT LINKUSDT LTCUSDT NEARUSDT UNIUSDT ATOMUSDT AVAXUSDT OPUSDT ARBUSDT SUIUSDT APTUSDT AAVEUSDT INJUSDT
```

### С кастомными параметрами
```powershell
# Больше капитала, меньше риска
python run_statistical_backtest.py --capital 50000 --risk-pct 0.01 --max-positions 3

# Агрессивный TP/SL
python run_statistical_backtest.py --tp-mult 3.0 --sl-mult 0.8

# Полная кастомизация
python run_statistical_backtest.py --mode multi --days 180 --capital 20000 --risk-pct 0.015 --max-positions 5 --tp-mult 2.5 --sl-mult 1.0 --preset balanced
```

---

## 🎚️ Параметры

### Пресеты
```powershell
--preset conservative    # Строгие критерии, меньше сигналов
--preset balanced        # По умолчанию, сбалансированный
--preset aggressive      # Мягкие критерии, больше сигналов
```

### Confidence (уверенность)
```powershell
--min-confidence 0.25    # Минимум 1 сетап
--min-confidence 0.50    # Минимум 2 сетапа (default)
--min-confidence 0.75    # Минимум 3 сетапа (high quality)
```

### Таймфреймы
```powershell
--timeframe 15m          # Быстрая торговля
--timeframe 30m          # Оптимальный (default)
--timeframe 1h           # Стабильнее
--timeframe 4h           # Swing trading
```

### Капитал и Риск
```powershell
--capital 10000          # Начальный капитал в USDT
--risk-pct 0.01          # 1% риска на сделку
--risk-pct 0.02          # 2% риска (default)
--risk-pct 0.03          # 3% риска (агрессивно)
--max-positions 3        # Макс 3 позиции одновременно
--max-positions 5        # Макс 5 (default)
--max-positions 10       # Макс 10 (для больших портфелей)
```

### TP/SL
```powershell
--tp-mult 1.5            # TP = 1.5x ATR (консервативно)
--tp-mult 2.0            # TP = 2x ATR (default)
--tp-mult 3.0            # TP = 3x ATR (агрессивно)
--sl-mult 0.8            # SL = 0.8x ATR (тайтовый)
--sl-mult 1.0            # SL = 1x ATR (default)
--sl-mult 1.5            # SL = 1.5x ATR (широкий)
```

---

## 📋 Готовые Сценарии

### Сценарий 1: Консервативная стратегия
**Для новичков, низкий риск**
```powershell
python run_statistical_backtest.py `
    --mode multi `
    --symbols BTCUSDT ETHUSDT BNBUSDT SOLUSDT XRPUSDT `
    --days 180 `
    --timeframe 1h `
    --preset conservative `
    --min-confidence 0.75 `
    --capital 10000 `
    --risk-pct 0.01 `
    --max-positions 3 `
    --tp-mult 2.0 `
    --sl-mult 1.0
```

### Сценарий 2: Сбалансированная стратегия
**Для большинства случаев**
```powershell
python run_statistical_backtest.py `
    --mode multi `
    --symbols BTCUSDT ETHUSDT SOLUSDT NEARUSDT ADAUSDT AVAXUSDT UNIUSDT XRPUSDT ATOMUSDT TONUSDT `
    --days 180 `
    --timeframe 30m `
    --preset balanced `
    --min-confidence 0.50 `
    --capital 10000 `
    --risk-pct 0.02 `
    --max-positions 5
```

### Сценарий 3: Агрессивная стратегия
**Для опытных, высокий риск**
```powershell
python run_statistical_backtest.py `
    --mode multi `
    --days 180 `
    --timeframe 15m `
    --preset aggressive `
    --min-confidence 0.25 `
    --capital 10000 `
    --risk-pct 0.03 `
    --max-positions 10 `
    --tp-mult 3.0 `
    --sl-mult 0.8
```

### Сценарий 4: Production Scanner
**Для реальной торговли**
```powershell
python run_statistical_scanner.py `
    --mode continuous `
    --symbols BTCUSDT ETHUSDT BNBUSDT SOLUSDT XRPUSDT ADAUSDT DOGEUSDT DOTUSDT LINKUSDT LTCUSDT NEARUSDT UNIUSDT ATOMUSDT AVAXUSDT OPUSDT ARBUSDT SUIUSDT APTUSDT AAVEUSDT INJUSDT `
    --timeframe 30m `
    --preset balanced `
    --min-confidence 0.50 `
    --max-signals 10 `
    --interval 1800 `
    --telegram `
    --save-results
```

---

## 🔍 Диагностика

```powershell
# Проверка работы
python test_statistical_system.py

# Verbose режим (детальный вывод)
python run_statistical_scanner.py --verbose

# Сохранение результатов
python run_statistical_backtest.py --save-results
# Результаты в: statistical_system/results/
```

---

## 📊 Интерпретация Метрик

### Хорошие результаты:
- Win Rate > 55%
- Profit Factor > 1.5
- Max Drawdown < 15%
- Sharpe Ratio > 1.0

### Отличные результаты:
- Win Rate > 60%
- Profit Factor > 2.0
- Max Drawdown < 10%
- Sharpe Ratio > 2.0

### Плохие результаты:
- Win Rate < 50%
- Profit Factor < 1.3
- Max Drawdown > 20%
- Sharpe Ratio < 0.5

---

## 💡 Советы

1. **Начните с теста:** `test_statistical_system.py`
2. **Бэктест перед live:** Сначала 180 дней истории
3. **Используйте balanced:** Оптимальный баланс
4. **Тестируйте на 30m:** Баланс частоты/качества
5. **Портфель > 1 монета:** Диверсификация рисков
6. **Сохраняйте результаты:** `--save-results` для анализа

---

## 📚 Документация

- **Полная документация:** `statistical_system/README.md`
- **Быстрый старт:** `statistical_system/QUICK_START.md`
- **Резюме:** `statistical_system/START_HERE.md`
- **Команды:** `Info/Commands.txt`

---

**Версия:** 1.0.0 | **Дата:** 2025-10-31
