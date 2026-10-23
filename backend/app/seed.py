from typing import Any


def _poi(id: str, category: str, name: str, lat: float, lng: float, qr: str, priority: int = 3) -> dict[str, Any]:
    return {
        "id": id,
        "category": category,
        "latitude": lat,
        "longitude": lng,
        "radius_m": 40,
        "priority": priority,
        "status": "PUBLISHED",
        "translation": {
            "language_code": "vi",
            "name": name,
            "description": f"{name} là một địa điểm văn hóa trong bộ sưu tập CityEcho quanh SGU.",
            "narration_text": f"Bạn đang khám phá {name}. Đây là một điểm dừng giàu câu chuyện trong hành trình CityEcho.",
        },
        "image_url": f"/images/pois/{id}.svg",
        "audio_url": "",
        "audio_duration_seconds": 0,
        "qr_code": qr,
    }


SEED_POIS = {
    "sgu-main": _poi("sgu-main", "campus", "Trường Đại học Sài Gòn", 10.7591, 106.6823, "CITYECHO-SGU", 5),
    "chua-ba": _poi("chua-ba", "religious", "Chùa Bà Thiên Hậu", 10.7542, 106.6636, "CITYECHO-THIENHAU", 5),
    "cho-lon": _poi("cho-lon", "market", "Chợ Bình Tây", 10.7498, 106.6514, "CITYECHO-BINHTAY", 4),
    "nha-tho-cha-tam": _poi("nha-tho-cha-tam", "religious", "Nhà thờ Cha Tam", 10.7499, 106.6664, "CITYECHO-CHATAM", 4),
    "nghia-an": _poi("nghia-an", "religious", "Hội quán Nghĩa An", 10.7531, 106.6619, "CITYECHO-NGHIAAN", 4),
    "chua-ong-bon": _poi("chua-ong-bon", "religious", "Chùa Ông Bổn", 10.7506, 106.6603, "CITYECHO-ONGBON"),
    "cho-an-dong": _poi("cho-an-dong", "market", "Chợ An Đông", 10.7564, 106.6698, "CITYECHO-ANDONG"),
    "cho-ray": _poi("cho-ray", "historical", "Bệnh viện Chợ Rẫy", 10.7574, 106.6598, "CITYECHO-CHORAY"),
    "cau-chu-y": _poi("cau-chu-y", "public-space", "Cầu Chữ Y", 10.7528, 106.6775, "CITYECHO-CHUY"),
    "phung-son": _poi("phung-son", "religious", "Chùa Phụng Sơn", 10.7619, 106.6515, "CITYECHO-PHUNGSON"),
    "bao-tang-my-thuat": _poi("bao-tang-my-thuat", "museum", "Bảo tàng Mỹ thuật Thành phố", 10.7700, 106.6992, "CITYECHO-ARTMUSEUM", 4),
    "ho-con-rua": _poi("ho-con-rua", "public-space", "Hồ Con Rùa", 10.7828, 106.6958, "CITYECHO-HOCRUA"),
}
