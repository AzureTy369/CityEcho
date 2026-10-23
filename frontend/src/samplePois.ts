export type Status = "DRAFT" | "PENDING" | "NEEDS_REVISION" | "PUBLISHED" | "ARCHIVED";
export type Poi = {
  id: string; category: string; latitude: number; longitude: number; radius_m: number; priority: number; status: Status;
  translation: { language_code?: string; name: string; description: string; narration_text: string };
  image_url: string; audio_url?: string; audio_duration_seconds?: number; qr_code: string; distance_m?: number;
};

const names: Array<[string, string, string, number, number, string]> = [
  ["sgu-main", "campus", "Trường Đại học Sài Gòn", 10.7591, 106.6823, "CITYECHO-SGU"],
  ["chua-ba", "religious", "Chùa Bà Thiên Hậu", 10.7542, 106.6636, "CITYECHO-THIENHAU"],
  ["cho-lon", "market", "Chợ Bình Tây", 10.7498, 106.6514, "CITYECHO-BINHTAY"],
  ["nha-tho-cha-tam", "religious", "Nhà thờ Cha Tam", 10.7499, 106.6664, "CITYECHO-CHATAM"],
  ["nghia-an", "religious", "Hội quán Nghĩa An", 10.7531, 106.6619, "CITYECHO-NGHIAAN"],
  ["chua-ong-bon", "religious", "Chùa Ông Bổn", 10.7506, 106.6603, "CITYECHO-ONGBON"],
  ["cho-an-dong", "market", "Chợ An Đông", 10.7564, 106.6698, "CITYECHO-ANDONG"],
  ["cho-ray", "historical", "Bệnh viện Chợ Rẫy", 10.7574, 106.6598, "CITYECHO-CHORAY"],
  ["cau-chu-y", "public-space", "Cầu Chữ Y", 10.7528, 106.6775, "CITYECHO-CHUY"],
  ["phung-son", "religious", "Chùa Phụng Sơn", 10.7619, 106.6515, "CITYECHO-PHUNGSON"],
  ["bao-tang-my-thuat", "museum", "Bảo tàng Mỹ thuật Thành phố", 10.77, 106.6992, "CITYECHO-ARTMUSEUM"],
  ["ho-con-rua", "public-space", "Hồ Con Rùa", 10.7828, 106.6958, "CITYECHO-HOCRUA"],
];
export const samplePois: Poi[] = names.map(([id, category, name, latitude, longitude, qr]) => ({
  id, category, latitude, longitude, radius_m: 40, priority: category === "campus" ? 5 : 3, status: "PUBLISHED",
  qr_code: qr, image_url: `/images/pois/${id}.svg`,
  translation: { language_code: "vi", name, description: `${name} là một địa điểm văn hóa quanh SGU.`, narration_text: `Bạn đang khám phá ${name}. Đây là một điểm dừng trong hành trình CityEcho.` },
}));
export function mediaUrl(api: string, url = "") { if (!url) return ""; if (/^(https?:|data:|\/images\/)/.test(url)) return url; return url.startsWith("/media") ? `${api}${url}` : url; }
export function mapPinStyle(poi: Poi) { return { top: `${Math.min(Math.max(((10.79 - poi.latitude) / 0.045) * 80 + 8, 6), 88)}%`, left: `${Math.min(Math.max(((poi.longitude - 106.645) / 0.06) * 80 + 8, 6), 88)}%` }; }
