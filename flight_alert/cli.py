import argparse
import json
import sys
from dataclasses import asdict, is_dataclass
from datetime import datetime

from .city_codes import load_city_codes, normalize_city
from .config import load_config
from .ctrip import CtripClient
from .notifiers import ConsoleNotifier, ServerChanNotifier
from .runner import run_forever, run_once


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Monitor and search Ctrip flight prices.")
    subparsers = parser.add_subparsers(dest="command")

    monitor = subparsers.add_parser("monitor", help="Run the configured price monitor")
    monitor.add_argument("--config", default="config.json", help="Path to config.json")
    monitor.add_argument("--once", action="store_true", help="Run a single polling cycle")
    monitor.add_argument("--dry-run", action="store_true", help="Print notifications instead of sending them")

    search = subparsers.add_parser("search", help="Search one-way flight options for one date")
    search.add_argument("origin", help="Departure city name or 3-letter city/airport code")
    search.add_argument("destination", help="Arrival city name or 3-letter city/airport code")
    search.add_argument("date", help="Flight date in YYYY-MM-DD format")
    search.add_argument("--limit", type=int, default=20, help="Number of text results to print")
    search.add_argument("--format", choices=["text", "json"], default="text", help="Output format")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        args.command = "monitor"
        args.config = "config.json"
        args.once = False
        args.dry_run = False

    try:
        if args.command == "monitor":
            return _run_monitor(args)
        if args.command == "search":
            return _run_search(args)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    parser.error(f"unknown command: {args.command}")
    return 2


def _run_monitor(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    client = CtripClient()
    notifier = ConsoleNotifier() if args.dry_run else ServerChanNotifier(config.ftqq_sckey)
    if args.once:
        run_once(config, client, notifier)
    else:
        run_forever(config, client, notifier)
    return 0


def _run_search(args: argparse.Namespace) -> int:
    city_codes = load_city_codes()
    origin = normalize_city(args.origin, city_codes)
    destination = normalize_city(args.destination, city_codes)
    flight_date = _parse_date(args.date)

    result = CtripClient().search_flights(origin, destination, flight_date)
    if args.format == "json":
        print(json.dumps(_to_jsonable(result), ensure_ascii=False, indent=2))
    else:
        _print_search_text(result, max(args.limit, 1))
    return 0


def _parse_date(value: str):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError("date must be in YYYY-MM-DD format") from exc


def _print_search_text(result: dict, limit: int) -> None:
    query = result["query"]
    top_results = _select_display_results(result["results"], limit)
    print(f"{query['origin']}->{query['destination']}  {query['date']}")
    print(f"共 {result['count']} 班，以下显示 {len(top_results)} 班：")
    print()
    for idx, item in enumerate(top_results, start=1):
        transit = "直飞" if not item.has_transit else f"转机{item.transit_count}次"
        print(
            f"{idx}. {item.flight_numbers}\n"
            f"{item.departure_time}-{item.arrival_time}  {item.price}元  {transit}"
        )
        if idx != len(top_results):
            print()


def _select_display_results(results: list, limit: int) -> list:
    if not results:
        return []

    minimum = min(max(limit, 5), len(results))
    cheapest_price = results[0].price
    cutoff_price = min(int(cheapest_price * 1.5), 1000)
    selected = results[:minimum]

    for item in results[minimum:]:
        if item.price > cutoff_price:
            break
        selected.append(item)
    return selected


def _to_jsonable(value):
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, dict):
        return {key: _to_jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_to_jsonable(item) for item in value]
    return value
