# 🚀 Quick Start Guide - Statistical System

## ⚡ За 5 минут - запустить и протестировать

### Шаг 1: Проверка окружения

```powershell
# Activate venv (PowerShell)
& .venv/Scripts/Activate.ps1

# Проверить зависимости
python -c "import ccxt, ta, pandas; print('✅ All dependencies OK')"
```

### Шаг 2: Первый скан (тест работы)

```powershell
# Простой скан 5 монет
python run_statistical_scanner.py --symbols BTCUSDT ETHUSDT SOLUSDT BNBUSDT ADAUSDT --max-signals 5
```

**Ожидаемый результат:** Список сигналов с confidence, TP/SL

### Шаг 3: Бэктест на BTC

```powershell
# Тест на 90 днях истории
python run_statistical_backtest.py --symbol BTCUSDT --days 90 --timeframe 30m
```

**Ожидаемый результат:** Детальный отчёт с метриками

### Шаг 4: Бэктест портфеля

```powershell
# Тест на 10 монетах
python run_statistical_backtest.py --mode multi --days 90 --symbols BTCUSDT ETHUSDT SOLUSDT BNBUSDT XRPUSDT ADAUSDT DOGEUSDT DOTUSDT LINKUSDT AVAXUSDT
```

---

## 📋 Готовые Команды для Вашего Проекта

### 1. Скан Топ-20 монет (ваш watchlist)

```powershell
python run_statistical_scanner.py `
    --symbols BTCUSDT ETHUSDT BNBUSDT SOLUSDT XRPUSDT ADAUSDT DOGEUSDT DOTUSDT LINKUSDT LTCUSDT NEARUSDT UNIUSDT ATOMUSDT AVAXUSDT OPUSDT ARBUSDT SUIUSDT APTUSDT AAVEUSDT INJUSDT `
    --timeframe 30m `
    --preset balanced `
    --max-signals 10
```

### 2. Непрерывный скан с Telegram (каждые 30 мин)

```powershell
python run_statistical_scanner.py `
    --mode continuous `
    --symbols BTCUSDT ETHUSDT SOLUSDT NEARUSDT ADAUSDT AVAXUSDT UNIUSDT XRPUSDT ATOMUSDT TONUSDT `
    --timeframe 30m `
    --interval 1800 `
    --telegram `
    --preset balanced
```

### 3. Бэктест вашего портфеля (6 месяцев)

```powershell
python run_statistical_backtest.py `
    --mode multi `
    --symbols BTCUSDT ETHUSDT SOLUSDT NEARUSDT ADAUSDT AVAXUSDT UNIUSDT XRPUSDT ATOMUSDT TONUSDT `
    --days 180 `
    --timeframe 30m `
    --preset balanced `
    --capital 10000 `
    --save-results
```

### 4. Консервативная стратегия (меньше риска)

```powershell
python run_statistical_backtest.py `
    --mode multi `
    --symbols BTCUSDT ETHUSDT SOLUSDT BNBUSDT XRPUSDT `
    --days 180 `
    --timeframe 1h `
    --preset conservative `
    --min-confidence 0.75 `
    --capital 10000 `
    --risk-pct 0.01 `
    --max-positions 3
```

### 5. Агрессивная стратегия (больше сделок)

```powershell
python run_statistical_backtest.py `
    --mode multi `
    --days 180 `
    --timeframe 15m `
    --preset aggressive `
    --min-confidence 0.25 `
    --capital 10000 `
    --risk-pct 0.03 `
    --max-positions 10
```

---

## 🎯 Что Делать Дальше?

### Если бэктест показал ХОРОШИЕ результаты:

✅ Win Rate > 55%  
✅ Profit Factor > 1.5  
✅ Max Drawdown < 15%

**Следующие шаги:**

1. **Тест на других таймфреймах**
   ```powershell
   python run_statistical_backtest.py --timeframe 1h ...
   python run_statistical_backtest.py --timeframe 4h ...
   ```

2. **Тест на других периодах**
   ```powershell
   python run_statistical_backtest.py --days 90 ...
   python run_statistical_backtest.py --days 365 ...
   ```

3. **Запуск в реальном времени (без торговли)**
   ```powershell
   python run_statistical_scanner.py --mode continuous --telegram
   ```

4. **Интеграция с XGBoost фильтром** (следующий шаг)

### Если бэктест показал ПЛОХИЕ результаты:

❌ Win Rate < 50%  
❌ Profit Factor < 1.3  
❌ Max Drawdown > 20%

**Попробуйте:**

1. **Изменить preset:**
   ```powershell
   --preset conservative  # меньше сигналов, выше качество
   ```

2. **Изменить TP/SL:**
   ```powershell
   --tp-mult 3.0 --sl-mult 0.8  # более агрессивный профит
   ```

3. **Изменить таймфрейм:**
   ```powershell
   --timeframe 1h  # более стабильные сигналы
   ```

4. **Отключить слабые сетапы** (в коде):
   ```python
   signal_config.enabled_setups = ['breakout', 'pullback']  # только 2 лучших
   ```

---

## 🔍 Быстрая Диагностика

### Команда для быстрой проверки текущего состояния рынка:

```powershell
# Скан 5 главных монет
python run_statistical_scanner.py --symbols BTCUSDT ETHUSDT BNBUSDT SOLUSDT XRPUSDT --preset balanced
```

**Интерпретация:**

- **Нет сигналов** → Рынок в боковике или неопределённость
- **1-3 сигнала** → Нормально, можно торговать
- **5+ сигналов** → Высокая активность рынка
- **Все сигналы LONG** → Сильный бычий тренд
- **Все сигналы SHORT** → Сильный медвежий тренд

---

## 📊 Сравнение Пресетов

| Параметр | Conservative | Balanced | Aggressive |
|----------|-------------|----------|------------|
| Сигналов в день | 1-3 | 3-5 | 5-10 |
| Confidence | ≥ 0.75 | ≥ 0.50 | ≥ 0.25 |
| Win Rate | 60-70% | 50-60% | 45-55% |
| Риск | Низкий | Средний | Высокий |
| Подходит для | Новички | Все | Опытные |

---

## 💡 Советы

1. **Начните с balanced preset** - оптимальный баланс
2. **Тестируйте на 180+ днях** - достаточно данных для выводов
3. **Используйте 30m таймфрейм** - баланс частоты и качества
4. **Мультивалютный подход** - диверсификация рисков
5. **Сохраняйте результаты** - анализируйте историю

---

## ❓ FAQ

**Q: Сколько монет сканировать?**  
A: 10-20 для старта, можно до 50-100 когда освоитесь

**Q: Какой таймфрейм лучше?**  
A: 30m-1h для дневной торговли, 4h для swing

**Q: Как часто обновлять сканирование?**  
A: Каждые 30 минут для 30m, каждый час для 1h

**Q: Нужно ли использовать все 4 сетапа?**  
A: Нет, можете отключить слабые в `enabled_setups`

**Q: Что делать если все метрики плохие?**  
A: Попробуйте другой таймфрейм или период, или дождитесь более благоприятных рыночных условий

---

**Готовы начать? Запустите первую команду! 🚀**
