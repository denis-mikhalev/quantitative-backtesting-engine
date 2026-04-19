# Statistical Trading System - Level 1

Система технических и статистических сигналов без машинного обучения.

## 🎯 Основная Идея

Система генерирует торговые сигналы на основе **проверенных технических паттернов** (без ML):

1. **Breakout** - прорыв волатильности с подтверждением объёма
2. **Pullback** - откат в направлении основного тренда
3. **Mean Reversion** - возврат к средней после экстремального движения
4. **Volatility Expansion** - расширение после сжатия (BB Squeeze)

### ✅ Преимущества

- **Прозрачность** - понятно, почему вход/выход
- **Бэктест на истории** - можно протестировать перед реальной торговлей
- **Мультивалютность** - сканирует 20-100 монет одновременно
- **Ранжирование** - выбирает лучшие сигналы по качеству

## 📦 Установка

```bash
# Activate venv (PowerShell)
& .venv/Scripts/Activate.ps1

# Установить зависимости (если нужно)
pip install ccxt ta pandas numpy
```

## 🚀 Быстрый Старт

### 1. Одноразовое сканирование

Сканирует все монеты и выводит топ-10 сигналов:

```bash
python run_statistical_scanner.py --mode scan
```

### 2. Непрерывное сканирование

Сканирует каждые 30 минут и отправляет уведомления:

```bash
python run_statistical_scanner.py --mode continuous --telegram
```

### 3. Бэктест на одной монете

Тестирует систему на исторических данных:

```bash
python run_statistical_backtest.py --symbol BTCUSDT --days 180 --timeframe 30m
```

### 4. Мультивалютный бэктест

Тестирует портфельную торговлю на нескольких монетах:

```bash
python run_statistical_backtest.py --mode multi --days 180 --symbols BTCUSDT ETHUSDT SOLUSDT
```

## ⚙️ Конфигурация

### Пресеты

Система имеет 3 предустановки:

```bash
# Conservative - строгие критерии, меньше сигналов, выше качество
python run_statistical_scanner.py --preset conservative

# Balanced - сбалансированный подход (по умолчанию)
python run_statistical_scanner.py --preset balanced

# Aggressive - мягкие критерии, больше сигналов
python run_statistical_scanner.py --preset aggressive
```

### Основные параметры

```bash
# Минимальная уверенность сигнала (0-1)
--min-confidence 0.75  # только сигналы с 3-4 активными сетапами

# Таймфрейм
--timeframe 1h  # 15m, 30m, 1h, 4h, 1d

# Монеты для сканирования
--symbols BTCUSDT ETHUSDT SOLUSDT ADAUSDT

# Максимум сигналов
--max-signals 5  # показать только топ-5
```

### Параметры бэктеста

```bash
# Начальный капитал
--capital 10000  # $10,000

# Риск на сделку
--risk-pct 0.02  # 2% капитала на сделку

# TP/SL множители
--tp-mult 2.0  # Take Profit = 2x ATR
--sl-mult 1.0  # Stop Loss = 1x ATR

# Макс. одновременных позиций
--max-positions 5
```

## 📊 Примеры Использования

### Пример 1: Консервативный скан топ-20 монет

```bash
python run_statistical_scanner.py \
    --mode scan \
    --preset conservative \
    --min-confidence 0.75 \
    --timeframe 1h \
    --max-signals 5
```

**Результат:** Топ-5 самых надёжных сигналов на часовом таймфрейме

### Пример 2: Агрессивный непрерывный скан с Telegram

```bash
python run_statistical_scanner.py \
    --mode continuous \
    --preset aggressive \
    --min-confidence 0.5 \
    --timeframe 30m \
    --interval 1800 \
    --telegram \
    --max-signals 10
```

**Результат:** Каждые 30 минут сканирует монеты и отправляет топ-10 в Telegram

### Пример 3: Бэктест BTC за 6 месяцев

```bash
python run_statistical_backtest.py \
    --symbol BTCUSDT \
    --timeframe 1h \
    --days 180 \
    --preset balanced \
    --capital 10000 \
    --risk-pct 0.02
```

**Результат:** Детальный отчёт с метриками (Win Rate, Profit Factor, Drawdown)

### Пример 4: Портфельный бэктест на 10 монетах

```bash
python run_statistical_backtest.py \
    --mode multi \
    --symbols BTCUSDT ETHUSDT BNBUSDT SOLUSDT XRPUSDT ADAUSDT DOGEUSDT DOTUSDT LINKUSDT AVAXUSDT \
    --timeframe 4h \
    --days 180 \
    --preset balanced \
    --capital 10000 \
    --max-positions 3
```

**Результат:** Симуляция портфельной торговли с ротацией позиций

## 📈 Интерпретация Результатов

### Метрики Бэктеста

```
📊 BACKTEST RESULTS
================================================
📈 Performance:
   Total Return:     +15.23% ($1,523.45)
   Final Capital:   $11,523.45
   Max Drawdown:    -8.45%
   Sharpe Ratio:     1.85

📊 Trading Stats:
   Total Trades:      45
   Win Rate:         57.78%
   Profit Factor:     1.65

💰 Averages:
   Avg Win:          +2.35%
   Avg Loss:        -1.12%
   Avg Trade:        +0.34%
   Avg Duration:     12.5 candles

🎯 Exit Types:
       TP:   23 (51.1%)
       SL:   18 (40.0%)
     TIME:    4 ( 8.9%)
```

### Что Считается Хорошим Результатом?

| Метрика | Отлично | Хорошо | Плохо |
|---------|---------|--------|-------|
| **Win Rate** | > 60% | 50-60% | < 50% |
| **Profit Factor** | > 2.0 | 1.5-2.0 | < 1.5 |
| **Max Drawdown** | < 10% | 10-20% | > 20% |
| **Sharpe Ratio** | > 2.0 | 1.0-2.0 | < 1.0 |
| **Total Return** (6 мес) | > 20% | 10-20% | < 10% |

### Интерпретация Exit Types

- **TP > 50%** - система хорошо определяет цели
- **SL > 50%** - слишком тайтовые стопы или плохие сигналы
- **TIME > 20%** - сигналы "зависают", нужен механизм выхода по времени

## 🔧 Продвинутая Настройка

### Создание Кастомного Конфига

```python
from statistical_system import SignalConfig, BacktestConfig

# Кастомная конфигурация сигналов
custom_signal_config = SignalConfig(
    # Breakout
    bb_period=20,
    bb_std=2.5,
    volume_threshold=2.0,
    
    # Pullback
    ema_fast=50,
    ema_slow=200,
    rsi_oversold=35,
    rsi_overbought=65,
    
    # Mean Reversion
    rsi_extreme_low=25,
    rsi_extreme_high=75,
    
    # Фильтры
    min_confidence=0.75,  # минимум 3 из 4 сетапов
    
    # Какие сетапы использовать
    enabled_setups=['breakout', 'pullback']  # только 2 сетапа
)

# Кастомная конфигурация бэктеста
custom_backtest_config = BacktestConfig(
    initial_capital=50000,
    position_size_pct=0.01,  # 1% риска
    max_positions=10,
    tp_atr_mult=3.0,  # агрессивный TP
    sl_atr_mult=0.8,  # тайтовый SL
)
```

### Использование в Коде

```python
from statistical_system import (
    StatisticalSignalGenerator,
    BacktestEngine
)

# Инициализация
generator = StatisticalSignalGenerator(custom_signal_config)
engine = BacktestEngine(generator, custom_backtest_config)

# Бэктест
result = engine.run(df, 'BTCUSDT')
result.print_summary()
```

## 🎓 Понимание Сетапов

### 1. Breakout (Прорыв)

**Логика:**
- Цена выходит за Bollinger Bands
- Объём значительно выше среднего
- Направленное движение свечи

**Когда работает:**
- Начало нового тренда
- Импульсные движения
- Новости / события

**Риски:**
- Ложные пробои
- Откаты после импульса

### 2. Pullback (Откат в тренде)

**Логика:**
- Есть чёткий тренд (EMA50 > EMA200)
- RSI откатывает в зону перепроданности/перекупленности
- Вход на коррекции в направлении тренда

**Когда работает:**
- Сильные тренды
- Коррекции в тренде
- После консолидации

**Риски:**
- Разворот тренда
- Слишком глубокий откат

### 3. Mean Reversion (Возврат к средней)

**Логика:**
- Цена сильно отклонилась от BB
- RSI в экстремальной зоне
- Ожидание возврата к средней

**Когда работает:**
- Боковой рынок
- Перепроданность/перекупленность
- Панические движения

**Риски:**
- Продолжение тренда
- "Ловля падающих ножей"

### 4. Volatility Expansion (Расширение волатильности)

**Логика:**
- Период низкой волатильности (сжатие)
- Резкий прорыв с объёмом
- BB Squeeze pattern

**Когда работает:**
- После консолидации
- Перед важными движениями
- Накопление энергии рынка

**Риски:**
- Ложный прорыв
- Быстрый откат

## 🔄 Интеграция с Существующей Системой

### Гибридный Подход (Планируется)

```
УРОВЕНЬ 1: Statistical Signals (текущая реализация)
    ↓ генерирует первичные сигналы
УРОВЕНЬ 2: XGBoost Filter (будущее)
    ↓ подтверждает/отклоняет
УРОВЕНЬ 3: SMC Filter (существующий)
    ↓ финальная проверка
```

Пока используйте только **Уровень 1** для генерации сигналов.

## 📝 Структура Проекта

```
statistical_system/
├── __init__.py                 # Экспорты
├── config.py                   # Конфигурации и пресеты
├── signal_generator.py         # Генерация сигналов
├── backtest_engine.py          # Движок бэктеста
├── multi_asset_scanner.py      # Мультивалютный сканер
└── signal_ranker.py            # Ранжирование сигналов

run_statistical_scanner.py      # Главный скрипт сканирования
run_statistical_backtest.py     # Скрипт бэктеста
```

## 🐛 Troubleshooting

### Проблема: "Not enough data"

**Решение:** Увеличьте `--days` или уменьшите `lookback_candles`

### Проблема: "No signals found"

**Решение:** 
- Уменьшите `--min-confidence`
- Используйте `--preset aggressive`
- Проверьте список монет

### Проблема: Telegram не отправляет

**Решение:**
- Убедитесь что `telegram_sender.py` настроен
- Проверьте токен бота
- Используйте флаг `--telegram`

### Проблема: Слишком много сигналов

**Решение:**
- Увеличьте `--min-confidence`
- Используйте `--preset conservative`
- Уменьшите `--max-signals`

## 📚 Дальнейшее Развитие

### Ближайшие планы:

1. ✅ **Базовая система** (готово)
2. ⏳ **Интеграция с XGBoost фильтром**
3. ⏳ **Web dashboard для мониторинга**
4. ⏳ **Автоматическое исполнение сделок**
5. ⏳ **ML для оптимизации параметров**

### Идеи для улучшения:

- Добавить больше сетапов (каналы, треугольники, etc.)
- Трейлинг стоп
- Partial TP (частичная фиксация)
- Адаптивные TP/SL
- Фильтр по времени суток
- Корреляция между монетами

## 💬 Примеры Команд для Вашего Проекта

### Для ваших монет из watchlist:

```bash
# Скан топ-монет из вашего списка
python run_statistical_scanner.py \
    --symbols BTCUSDT ETHUSDT SOLUSDT NEARUSDT ADAUSDT AVAXUSDT UNIUSDT XRPUSDT ATOMUSDT TONUSDT \
    --timeframe 30m \
    --preset balanced \
    --max-signals 10

# Бэктест на ваших монетах
python run_statistical_backtest.py \
    --mode multi \
    --symbols BTCUSDT ETHUSDT SOLUSDT NEARUSDT ADAUSDT \
    --days 180 \
    --timeframe 30m \
    --preset balanced
```

## 📊 Ожидаемые Результаты

На основе бэктестов типичных стратегий:

### Balanced Preset
- Win Rate: **50-60%**
- Profit Factor: **1.5-2.0**
- Max Drawdown: **10-15%**
- Monthly Return: **3-5%**

### Conservative Preset
- Win Rate: **60-70%**
- Profit Factor: **2.0-2.5**
- Max Drawdown: **5-10%**
- Monthly Return: **2-4%**

### Aggressive Preset
- Win Rate: **45-55%**
- Profit Factor: **1.3-1.7**
- Max Drawdown: **15-25%**
- Monthly Return: **4-8%**

**Важно:** Это примерные значения. Реальные результаты зависят от рыночных условий.

---

## 📞 Support

При возникновении вопросов или проблем:

1. Проверьте этот README
2. Запустите с флагом `--verbose` для детального вывода
3. Проверьте логи в `statistical_system/results/`

**Версия:** 1.0.0  
**Дата:** 2025-10-31
