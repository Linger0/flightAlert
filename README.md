# Flight Ticket Price Monitor

[简体中文](README.zh-CN.md)

Flight Alert monitors Ctrip flight prices and can search one-way flight options for a specific date. Monitoring and search share the same Ctrip mobile page data source, so the project has one path for fetching flight number, departure time, arrival time, price, and transfer status.

This project is for learning purposes only and should not be used commercially.

## Features

- Search one-way flights by Chinese city name or 3-letter city/airport code.
- Monitor selected outbound and return dates for price changes.
- Monitor the next 60 days of Thursday-to-Sunday fares against a target price.
- Send notifications through ServerChan, or print locally with `--dry-run`.

## Install

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Usage

Run the monitor with `config.json`:

```bash
python3 flight_alert_cli.py
```

Run one cycle without sending ServerChan messages:

```bash
python3 flight_alert_cli.py monitor --config config.json --once --dry-run
```

Search one date:

```bash
python3 flight_alert_cli.py search 上海 北京 2026-06-01 --limit 10
python3 flight_alert_cli.py search SHA BJS 2026-06-01 --format json
```

## Configuration

Copy the example config, then edit the route, dates, thresholds, and ServerChan token:

```bash
cp config.example.json config.json
```

`config.example.json`:

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

Fields:

- `mode`: `1` monitors specific dates; `2` monitors Thursday-to-Sunday fares in the next 60 days.
- `dateToGo` / `dateBack`: dates in `YYYYMMDD` format, used by mode 1.
- `placeFrom` / `placeTo`: Chinese city names or 3-letter city/airport codes.
- `targetPrice`: notification threshold for mode 2.
- `priceStep`: minimum price movement that triggers mode 1 notifications.
- `pollTime`: daily monitor time, defaults to `10:00:00`.
- `ftqq_SCKEY`: ServerChan tokens.

City-code mappings live in `flight_alert/references/city_codes.json`.

## Data Source

The project reads embedded flight data from Ctrip mobile pages:

```text
https://m.ctrip.com/html5/flight/{origin}-{destination}-day-{offset}.html
```

`offset` is the number of days from today in the Ctrip timezone.

## Project Layout

- `flight_alert_cli.py`: command-line entrypoint.
- `flight_alert/cli.py`: CLI command handling.
- `flight_alert/ctrip.py`: Ctrip mobile flight client.
- `flight_alert/monitoring.py`: monitoring rules and notification message formatting.
- `flight_alert/runner.py`: polling workflow.
- `flight_alert/notifiers.py`: console and ServerChan notifiers.
- `flight_alert/references/city_codes.json`: city-name to code mapping.

## Tests

```bash
python3 -m unittest discover -s tests
```

## Acknowledgments

This project was originally based on https://github.com/omegatao/flightAlert. Thanks to the author.
