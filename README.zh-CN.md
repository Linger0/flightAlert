# 机票价格监控

Flight Alert 可以监控携程机票价格，也可以查询指定日期的单程航班。监控和查询共用同一套携程移动端页面数据源，用一条链路获取航班号、起飞时间、到达时间、价格和中转状态。

本项目仅用于学习用途，请勿用于商业用途。

## 功能

- 支持用中文城市名或 3 位城市/机场代码查询单程航班。
- 监控指定去程和返程日期的价格变化。
- 监控未来 60 天内周四到周日的票价，并和目标价格比较。
- 支持通过 ServerChan 发送通知，也可以用 `--dry-run` 在本地打印。

## 安装

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 使用

使用 `config.json` 启动监控：

```bash
python3 flight_alert_cli.py
```

只运行一次，并在本地打印通知内容：

```bash
python3 flight_alert_cli.py monitor --config config.json --once --dry-run
```

查询指定日期：

```bash
python3 flight_alert_cli.py search 上海 北京 2026-06-01 --limit 10
python3 flight_alert_cli.py search SHA BJS 2026-06-01 --format json
```

## 配置

复制示例配置，然后修改航线、日期、阈值和 ServerChan token：

```bash
cp config.example.json config.json
```

`config.example.json`：

```json
{
  "mode": 1,
  "dateToGo": ["20260601", "20260602"],
  "dateBack": ["20260605"],
  "placeFrom": "SHA",
  "placeTo": "BJS",
  "targetPrice": 1000,
  "priceStep": 20,
  "pollTime": "10:00:00",
  "ftqq_SCKEY": ["SCTxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"]
}
```

字段说明：

- `mode`：`1` 监控指定日期；`2` 监控未来 60 天内周四到周日的票价。
- `dateToGo` / `dateBack`：日期格式为 `YYYYMMDD`，用于 mode 1。
- `placeFrom` / `placeTo`：中文城市名或 3 位城市/机场代码。
- `targetPrice`：mode 2 的通知价格阈值。
- `priceStep`：mode 1 中触发通知的最小价格变化幅度。
- `pollTime`：每日监控时间，默认 `10:00:00`。
- `ftqq_SCKEY`：ServerChan token 列表。

城市代码映射位于 `flight_alert/references/city_codes.json`。

## 数据源

项目读取携程移动端页面中的内嵌航班数据：

```text
https://m.ctrip.com/html5/flight/{origin}-{destination}-day-{offset}.html
```

`offset` 是以携程时区计算的、距离今天的天数。

## 项目结构

- `flight_alert_cli.py`：命令行入口。
- `flight_alert/cli.py`：CLI 命令处理。
- `flight_alert/ctrip.py`：携程移动端航班客户端。
- `flight_alert/monitoring.py`：监控规则和通知消息格式化。
- `flight_alert/runner.py`：轮询流程。
- `flight_alert/notifiers.py`：控制台和 ServerChan 通知。
- `flight_alert/references/city_codes.json`：城市名到代码的映射。

## 测试

```bash
python3 -m unittest discover -s tests
```

## 致谢

本项目最初基于 https://github.com/omegatao/flightAlert。感谢作者。
