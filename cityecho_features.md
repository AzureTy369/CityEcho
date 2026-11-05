# 🏙️ CityEcho — Chức năng chính, Công nghệ & Tư tưởng thiết kế

---

## 1. 🗺️ Bản đồ tương tác (Interactive Map)

**Sử dụng:** `MapLibre GL JS`, `ESRI World Imagery tiles`, `OpenStreetMap tiles`

**Tư tưởng chính:**
Thay vì nhúng iframe Google Maps (tốn phí, không tùy biến được), hệ thống dùng **MapLibre GL JS** — một thư viện bản đồ mã nguồn mở — để render bản đồ vector trực tiếp trên canvas của trình duyệt. Bản đồ được tải theo dạng **tile** (ô lưới 256×256px), mỗi tile là ảnh từ server ESRI (vệ tinh) hoặc OpenStreetMap (đường phố). Người dùng có thể **chuyển đổi giữa hai chế độ** (vệ tinh ↔ đường phố) ngay trên giao diện mà không cần tải lại trang. Các POI được vẽ lên bản đồ dưới dạng **HTML Marker** tùy chỉnh, click vào để hiện popup thông tin.

---

## 2. 📍 Chọn vị trí POI trực tiếp trên bản đồ (Location Picker)

**Sử dụng:** `MapLibre GL JS`, `Nominatim API (OpenStreetMap)`, `React state`

**Tư tưởng chính:**
Thay vì bắt người dùng tự copy-paste tọa độ từ Google Maps, hệ thống tích hợp một **map picker tương tác** ngay trong form tạo/chỉnh sửa POI. Khi người dùng **click hoặc kéo marker** trên bản đồ, tọa độ `lat/lng` được cập nhật tự động vào form thông qua React state (luồng dữ liệu một chiều). Tính năng **autocomplete tìm kiếm địa danh** gọi API Nominatim (miễn phí, không cần key) để gợi ý khi người dùng gõ tên địa điểm, giống trải nghiệm Google Maps.

---

## 3. 🔍 Tìm kiếm & Gợi ý địa danh (Search Autocomplete)

**Sử dụng:** `Nominatim REST API`, `debounce`, `React useState/useEffect`

**Tư tưởng chính:**
Khi người dùng gõ vào ô tìm kiếm, hệ thống không gọi API ngay mà áp dụng kỹ thuật **debounce** (đợi 300ms sau lần gõ cuối) để tránh spam request. Nominatim nhận chuỗi tìm kiếm và trả về danh sách địa điểm phù hợp kèm toạ độ. Người dùng click vào gợi ý → bản đồ **"bay đến"** vị trí đó bằng `map.flyTo()` với hiệu ứng animation mượt. Kết quả được giới hạn trong Việt Nam (`countrycodes=vn`) để tránh kết quả nước ngoài.

---

## 4. 🎵 Thuyết minh âm thanh tự động (Audio Narration)

**Sử dụng:** `HTML5 Audio API`, `FastAPI file upload`, `SQLAlchemy (bảng POIAudio)`

**Tư tưởng chính:**
Mỗi POI có thể đính kèm file audio MP3/WAV được upload lên server và lưu đường dẫn vào database. Khi người dùng click vào POI trên bản đồ hoặc quét mã QR, frontend gọi API lấy thông tin POI (bao gồm URL audio) rồi dùng **Web Audio API** để phát tự động. Mỗi lần phát được ghi nhận vào bảng `PlaybackLog` (timestamp, user_id, poi_id) để phục vụ thống kê. Tư tưởng giống **audio guide** tại bảo tàng nhưng chạy hoàn toàn trên điện thoại.

---

## 5. 📱 Quét mã QR để mở POI (QR Code Workflow)

**Sử dụng:** `qrcode` (Python library), `FastAPI`, `React Router`

**Tư tưởng chính:**
Mỗi POI được gán một **mã QR duy nhất** chứa đường dẫn URL đến trang chi tiết của POI đó (ví dụ: `cityecho.app/poi/123`). QR được sinh tự động bằng thư viện Python `qrcode` khi POI được tạo. Người dùng dùng camera điện thoại quét → trình duyệt mở URL → trang POI hiển thị ảnh, thông tin và **tự động phát audio thuyết minh**. Tư tưởng là **"Zero-friction access"** — không cần cài app, chỉ cần camera.

---

## 6. 🔐 Xác thực & Phân quyền (Authentication & RBAC)

**Sử dụng:** `JWT (JSON Web Token)`, `bcrypt`, `FastAPI Depends`, `React protected routes`

**Tư tưởng chính:**
Hệ thống dùng mô hình **stateless authentication** với JWT. Khi đăng nhập thành công, server ký và trả về một token chứa thông tin user (id, role). Token được lưu ở `localStorage` phía client và đính kèm vào mọi request qua header `Authorization: Bearer <token>`. Server không cần lưu session — chỉ cần xác minh chữ ký của token. Phân quyền theo mô hình **RBAC** (Role-Based Access Control): `admin` có toàn quyền, `editor` chỉ quản lý POI được giao. Password được hash bằng **bcrypt** (one-way, không thể giải mã ngược).

---

## 7. 📊 Dashboard thống kê (Analytics Dashboard)

**Sử dụng:** `Recharts`, `FastAPI aggregate queries`, `SQLAlchemy`

**Tư tưởng chính:**
Backend tổng hợp dữ liệu từ bảng `PlaybackLog` bằng các truy vấn **SQL aggregate** (GROUP BY, COUNT, SUM) và trả về JSON. Frontend dùng thư viện **Recharts** (dựa trên D3.js) để vẽ các biểu đồ trực quan: BarChart (top POI), PieChart (phân bổ danh mục), LineChart (xu hướng theo thời gian). Các **KPI card** (tổng POI, tổng lượt nghe,...) hiển thị số liệu nổi bật. Tư tưởng là **data-driven management** — admin nhìn vào dashboard để biết POI nào đang được quan tâm nhiều nhất.

---

## 8. 🖼️ Quản lý file media (File Storage)

**Sử dụng:** `FastAPI UploadFile`, `SQLAlchemy`, `Base64 encoding`

**Tư tưởng chính:**
Hệ thống hỗ trợ **hai chế độ lưu trữ** (dual-mode storage):
- **File mode**: File được lưu vào thư mục `uploads/` trên server, database chỉ lưu đường dẫn URL. Phù hợp khi có server thật.
- **DB mode**: File được encode sang **Base64** và lưu thẳng vào cột BLOB trong database. Phù hợp khi không có filesystem ổn định (VD: serverless).

Chế độ được chọn qua biến môi trường `STORAGE_MODE`, cho phép **linh hoạt deploy** ở nhiều môi trường khác nhau mà không cần đổi code.

---

## 9. 📍 Định vị GPS người dùng (User Geolocation)

**Sử dụng:** `Browser Geolocation API`, `MapLibre GL JS`

**Tư tưởng chính:**
Khi người dùng nhấn nút "Vị trí của tôi", frontend gọi `navigator.geolocation.getCurrentPosition()` — API có sẵn của trình duyệt, không cần thư viện thêm. Tọa độ trả về được dùng để: (1) vẽ **icon marker GPS** đặc biệt trên bản đồ, (2) vẽ **vòng tròn độ chính xác** (accuracy circle) xung quanh, (3) bay bản đồ đến vị trí đó. Tính năng này yêu cầu **HTTPS** (lý do phải dùng Cloudflare Tunnel hoặc Vercel khi test trên mobile).

---

## 10. 🌐 Đa ngôn ngữ (Multilingual Support)

**Sử dụng:** `SQLAlchemy (bảng Translation)`, `FastAPI`, `React i18n state`

**Tư tưởng chính:**
Thay vì lưu thông tin POI trong một cột đơn, hệ thống tách nội dung theo ngôn ngữ vào bảng `Translation` riêng (quan hệ 1-N: 1 POI → nhiều Translation). Mỗi bản dịch có trường `language_code` (vi/en/fr). Khi frontend yêu cầu thông tin POI kèm tham số ngôn ngữ, backend truy vấn và trả về đúng bản dịch tương ứng. Tư tưởng là **content localization tách biệt với data gốc**, dễ thêm ngôn ngữ mới mà không cần đổi schema.
