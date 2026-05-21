import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from urllib.parse import quote

import requests


USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)
CTRIP_TZ = timezone(timedelta(hours=8))
MOBILE_URL = "https://m.ctrip.com/html5/flight/{origin}-{destination}-day-{offset}.html"


@dataclass(frozen=True)
class FlightOption:
    flight_numbers: str
    departure_time: str
    arrival_time: str
    price: int | float
    currency: str
    has_transit: bool
    transit_count: int
    origin: str
    destination: str
    route_type: str | None = None


class CtripClient:
    def __init__(self, timeout: int = 30, session: requests.Session | None = None) -> None:
        self.timeout = timeout
        self.session = session or requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})

    def search_flights(self, origin: str, destination: str, flight_date: date) -> dict:
        html = self._fetch_mobile_html(origin, destination, flight_date)
        list_data = self._extract_list_data(html)
        flights = [self._summarize_route(entry) for entry in list_data.get("flights", [])]
        flights = [item for item in flights if item.price is not None]
        flights.sort(key=lambda item: (item.price, item.departure_time, item.flight_numbers))
        return {
            "query": {
                "origin": list_data.get("dcityName", origin),
                "destination": list_data.get("acityName", destination),
                "date": list_data.get("ddate", flight_date.isoformat()),
            },
            "count": len(flights),
            "results": flights,
        }

    def get_lowest_price(self, origin: str, destination: str, flight_date: date) -> int | None:
        result = self.search_flights(origin, destination, flight_date)
        prices = [item.price for item in result["results"] if item.price is not None]
        return int(min(prices)) if prices else None

    def _fetch_mobile_html(self, origin: str, destination: str, flight_date: date) -> str:
        today_in_ctrip_tz = datetime.now(CTRIP_TZ).date()
        offset = (flight_date - today_in_ctrip_tz).days
        if offset < 0:
            raise ValueError("date must not be in the past")

        url = MOBILE_URL.format(origin=quote(origin), destination=quote(destination), offset=offset)
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        return response.text

    @staticmethod
    def _extract_list_data(html: str) -> dict:
        marker = '"listData":'
        start = html.find(marker)
        if start == -1:
            raise RuntimeError("could not find embedded flight data in the Ctrip page")

        payload_start = html.find("{", start)
        if payload_start == -1:
            raise RuntimeError("could not find listData payload start")

        decoder = json.JSONDecoder()
        try:
            data, _ = decoder.raw_decode(html[payload_start:])
        except json.JSONDecodeError as exc:
            raise RuntimeError("failed to parse embedded flight data") from exc
        return data

    @staticmethod
    def _format_hhmm(timestamp: str) -> str:
        try:
            return datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S").strftime("%H:%M")
        except ValueError:
            return timestamp

    @classmethod
    def _summarize_route(cls, entry: dict) -> FlightOption:
        flight_item = entry.get("flightItem", {})
        segments = flight_item.get("flights", [])
        policy = entry.get("policy") or (flight_item.get("pl") or [{}])[0]

        flight_numbers = [segment.get("flightNo", "") for segment in segments if segment.get("flightNo")]
        transit_count = entry.get("transitCount")
        if transit_count is None:
            transit_count = max(len(segments) - 1, 0)
        has_transit = bool(entry.get("isTransit") or transit_count > 0 or len(segments) > 1)

        return FlightOption(
            flight_numbers="/".join(flight_numbers) or "N/A",
            departure_time=cls._format_hhmm(segments[0].get("dtime", "")) if segments else "",
            arrival_time=cls._format_hhmm(segments[-1].get("atime", "")) if segments else "",
            price=policy.get("price"),
            currency=policy.get("currency", "CNY"),
            has_transit=has_transit,
            transit_count=transit_count,
            origin=flight_item.get("departCity", {}).get("name", ""),
            destination=flight_item.get("arriveCity", {}).get("name", ""),
            route_type=flight_item.get("routeType"),
        )
