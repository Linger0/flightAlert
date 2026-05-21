from dataclasses import dataclass
from datetime import datetime


@dataclass
class PriceHistory:
    min_leav: int = 9999
    prev_leav: int = 0
    min_back: int = 9999
    prev_back: int = 0


@dataclass(frozen=True)
class MonitorMessage:
    title: str
    content: str
    should_send: bool


def monitor_certain_dates(
    leave_prices: dict[str, int],
    return_prices: dict[str, int],
    price_step: int,
    dates_to_go: list[str],
    dates_back: list[str],
    history: PriceHistory,
    cities: tuple[str, str],
) -> MonitorMessage:
    city_from, city_to = cities
    leave_dates = _select_prices(leave_prices, dates_to_go, "dateToGo")
    return_dates = _select_prices(return_prices, dates_back, "dateBack")

    min_leave_price = min(leave_dates.values())
    min_return_price = min(return_dates.values())
    should_send = False

    if abs(min_leave_price - history.prev_leav) >= price_step:
        history.prev_leav = min_leave_price
        should_send = True
    if abs(min_return_price - history.prev_back) >= price_step:
        history.prev_back = min_return_price
        should_send = True

    history.min_leav = min(history.min_leav, min_leave_price)
    history.min_back = min(history.min_back, min_return_price)

    content = f"*{city_from}-{city_to}:*\n\n"
    for day, price in leave_dates.items():
        content += f"**{day[4:6]}-{day[6:8]}: {price}**\n\n"
    content += f"History lowest: {history.min_leav}\n\n"
    content += "---\n\n"
    content += f"*{city_to}-{city_from}:*\n\n"
    for day, price in return_dates.items():
        content += f"**{day[4:6]}-{day[6:8]}: {price}**\n\n"
    content += f"History lowest: {history.min_back}"

    return MonitorMessage(
        title=f" Price to {city_to}: {min_leave_price} <-> {min_return_price}",
        content=content,
        should_send=should_send,
    )


def monitor_two_month_weekends(
    leave_prices: dict[str, int],
    return_prices: dict[str, int],
    target_price: int,
    cities: tuple[str, str],
    today: datetime | None = None,
) -> MonitorMessage:
    city_from, city_to = cities
    today = today or datetime.today()
    leave_weekend_prices: dict[str, int] = {}
    return_weekend_prices: dict[str, int] = {}

    for day_key in sorted(leave_prices):
        day = datetime.strptime(day_key, "%Y%m%d")
        if (day - today).days >= 60:
            break
        weekday = day.weekday() + 1
        if weekday >= 4 and day_key in return_prices:
            label = f"{day:%m-%d}({weekday})"
            leave_weekend_prices[label] = leave_prices[day_key]
            return_weekend_prices[label] = return_prices[day_key]

    if not leave_weekend_prices or not return_weekend_prices:
        raise ValueError("no weekend prices found in the next 60 days")

    min_leave_price = min(leave_weekend_prices.values())
    min_return_price = min(return_weekend_prices.values())
    max_min_price = max(min_leave_price, min_return_price)
    dates_min_leave = [day for day, price in leave_weekend_prices.items() if price == min_leave_price]
    dates_min_return = [day for day, price in return_weekend_prices.items() if price == min_return_price]

    content = f"### {min_leave_price} ({city_from}-{city_to}): " + " ".join(dates_min_leave)
    content += f"\n\n### {min_return_price} ({city_to}-{city_from}): " + " ".join(dates_min_return)
    content += f"\n\nPrice list:\n\n    {city_from}-{city_to}    {city_to}-{city_from}\n\n---"
    for label in leave_weekend_prices:
        leave_price = leave_weekend_prices[label]
        return_price = return_weekend_prices[label]
        content += "\n\n"
        content += label + ":  "
        content += _bold_if(leave_price, leave_price <= max_min_price)
        content += "    "
        content += _bold_if(return_price, return_price <= max_min_price)
        if label.endswith("(7)"):
            content += "\n\n---"

    return MonitorMessage(
        title=f" Lowest: {min_leave_price} ({city_from}-{city_to}) <-> {min_return_price}",
        content=content,
        should_send=max_min_price <= target_price,
    )


def _select_prices(prices: dict[str, int], dates: list[str], label: str) -> dict[str, int]:
    selected = {}
    missing = []
    for day in dates:
        if day in prices:
            selected[day] = prices[day]
        else:
            missing.append(day)
    if missing:
        raise ValueError(f"{label} contains dates missing from Ctrip response: {', '.join(missing)}")
    if not selected:
        raise ValueError(f"{label} must contain at least one date")
    return selected


def _bold_if(value: int, should_bold: bool) -> str:
    text = str(value)
    return f"**{text}**" if should_bold else text
