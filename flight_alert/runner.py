import time
from datetime import date, datetime, timedelta

from .config import MonitorConfig
from .ctrip import CtripClient
from .monitoring import (
    PriceHistory,
    monitor_certain_dates,
    monitor_two_month_weekends,
)
from .notifiers import Notifier


def run_once(
    config: MonitorConfig,
    client: CtripClient,
    notifier: Notifier,
    history: PriceHistory | None = None,
) -> bool:
    history = history or PriceHistory()

    if config.mode == 1:
        leave_prices = collect_lowest_prices(
            client,
            config.place_from,
            config.place_to,
            _parse_yyyymmdd_dates(config.date_to_go),
        )
        return_prices = collect_lowest_prices(
            client,
            config.place_to,
            config.place_from,
            _parse_yyyymmdd_dates(config.date_back),
        )
        message = monitor_certain_dates(
            leave_prices,
            return_prices,
            config.price_step,
            config.date_to_go,
            config.date_back,
            history,
            (config.place_from, config.place_to),
        )
    elif config.mode == 2:
        dates = weekend_dates(datetime.today().date(), days=60)
        leave_prices = collect_lowest_prices(client, config.place_from, config.place_to, dates)
        return_prices = collect_lowest_prices(client, config.place_to, config.place_from, dates)
        message = monitor_two_month_weekends(
            leave_prices,
            return_prices,
            config.target_price,
            (config.place_from, config.place_to),
        )
    else:
        raise ValueError(f"unsupported monitor mode: {config.mode}")

    if message.should_send:
        notifier.send(message.title, message.content)
    return message.should_send


def collect_lowest_prices(
    client: CtripClient,
    origin: str,
    destination: str,
    flight_dates: list[date],
) -> dict[str, int]:
    prices = {}
    for flight_date in flight_dates:
        price = client.get_lowest_price(origin, destination, flight_date)
        if price is not None:
            prices[flight_date.strftime("%Y%m%d")] = price
    return prices


def weekend_dates(start: date, days: int = 60) -> list[date]:
    dates = []
    for offset in range(days):
        candidate = start + timedelta(days=offset)
        weekday = candidate.weekday() + 1
        if weekday >= 4:
            dates.append(candidate)
    return dates


def _parse_yyyymmdd_dates(values: list[str]) -> list[date]:
    parsed = []
    for value in values:
        try:
            parsed.append(datetime.strptime(value, "%Y%m%d").date())
        except ValueError as exc:
            raise ValueError(f"date must be in YYYYMMDD format: {value}") from exc
    return parsed


def run_forever(config: MonitorConfig, client: CtripClient, notifier: Notifier) -> None:
    history = PriceHistory()
    while True:
        try:
            run_once(config, client, notifier, history)
        except Exception as exc:
            notifier.send(
                "Failed to retrieve flight ticket information.",
                f"### {time.strftime('%Y-%m-%d %H:%M')}\n\n{exc}",
            )

        print(f"{time.strftime('%Y-%m-%d %H:%M')} finished. Waiting for tomorrow.")
        time.sleep(seconds_until(config.poll_time))


def seconds_until(clock_time: str) -> int:
    target = datetime.strptime(clock_time, "%H:%M:%S").time()
    now = datetime.now()
    next_run = now.replace(hour=target.hour, minute=target.minute, second=target.second, microsecond=0)
    seconds = int((next_run - now).total_seconds())
    if seconds <= 0:
        seconds += 24 * 60 * 60
    return seconds
