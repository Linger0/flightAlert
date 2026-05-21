import json
from pathlib import Path


FALLBACK_CITY_CODES = {
    "北京": "BJS",
    "上海": "SHA",
    "广州": "CAN",
    "深圳": "SZX",
    "成都": "CTU",
    "杭州": "HGH",
    "武汉": "WUH",
    "西安": "SIA",
    "重庆": "CKG",
    "青岛": "TAO",
    "长沙": "CSX",
    "南京": "NKG",
    "厦门": "XMN",
    "昆明": "KMG",
    "大连": "DLC",
    "天津": "TSN",
    "郑州": "CGO",
    "三亚": "SYX",
    "济南": "TNA",
    "福州": "FOC",
    "香港": "HKG",
    "中国香港": "HKG",
    "台北": "TPE",
    "中国台北": "TPE",
    "澳门": "MFM",
    "中国澳门": "MFM",
}


def load_city_codes(path: Path | None = None) -> dict[str, str]:
    codes = dict(FALLBACK_CITY_CODES)
    json_path = path or Path(__file__).resolve().parent / "references" / "city_codes.json"
    if json_path.exists():
        with json_path.open("r", encoding="utf-8") as fh:
            codes.update(json.load(fh))
    return codes


def normalize_city(value: str, codes: dict[str, str] | None = None) -> str:
    value = value.strip()
    if not value:
        raise ValueError("city cannot be empty")

    upper = value.upper()
    if len(upper) == 3 and upper.isalpha():
        return upper

    city_codes = codes or load_city_codes()
    if value in city_codes:
        return city_codes[value]

    raise ValueError(f"unknown city or airport code: {value}")
