# CityEcho

CityEcho là website khám phá văn hóa quanh SGU với bản đồ POI, nội dung thuyết minh, QR, geofence và CMS.

Checklist nghiệm thu và thứ tự phát triển nằm tại [CHECKLIST.md](./CHECKLIST.md). Lệnh kiểm tra nhanh nằm tại [scripts/verify.ps1](./scripts/verify.ps1).

## Chạy nhanh

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

### Backend

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Mở `http://localhost:5173`. Vite proxy `/api` và `/media` sang cổng 8000, nên không cần `VITE_API_URL` khi chạy local. Nếu backend chưa chạy, frontend tự dùng 12 POI mẫu quanh SGU để demo giao diện. Khi backend chạy, trang CMS sử dụng JWT, có thể tải ảnh/audio và lưu trạng thái vào API.

Tài khoản demo:

- Admin: `admin@cityecho.vn` / `admin123`
- Biên tập viên: `editor@cityecho.vn` / `editor123`

## Lưu dữ liệu

Backend tự dùng bộ nhớ tạm khi không có `DATABASE_URL`, phù hợp chạy nhanh và test. Khi đặt `DATABASE_URL`, backend tự tạo các bảng `pois`, `narration_events`, `audit_logs` và `users`, seed dữ liệu nếu database chưa có dữ liệu, rồi đọc dữ liệu lại sau khi restart.

Ví dụ PostgreSQL:

```powershell
$env:DATABASE_URL="postgresql+psycopg://cityecho:cityecho@localhost:5432/cityecho"
```

`CITYECHO_JWT_SECRET` nên là chuỗi ngẫu nhiên dài và không commit vào Git. Khi database đã có user, backend ưu tiên user trong bảng `users`; các biến mật khẩu chỉ dùng để seed lần đầu. Nếu không đặt biến môi trường, tài khoản demo mặc định vẫn hoạt động khi chạy local không có database.

Để chạy local với cấu hình đầy đủ:

```powershell
$env:CITYECHO_JWT_SECRET="thay-bang-secret-ngau-nhien"
$env:CITYECHO_ADMIN_PASSWORD="mat-khau-admin"
$env:CITYECHO_EDITOR_PASSWORD="mat-khau-editor"
```

## Docker Compose

```powershell
docker compose up --build
```

## API chính

- `GET /api/v1/pois`: POI đã xuất bản, tìm kiếm và lọc.
- `GET /api/v1/pois/nearby?lat=...&lng=...`: POI gần vị trí theo Haversine.
- `GET /api/v1/geofence/evaluate?lat=...&lng=...`: chọn POI nằm trong geofence để kích hoạt narration.
- `GET /api/v1/qr/{code}`: mở POI từ QR.
- `GET /api/v1/pois/{id}/narration`: lấy văn bản và audio thuyết minh.
- `POST /api/v1/admin/pois/{id}/images`: upload ảnh multipart.
- `POST /api/v1/admin/pois/{id}/audios`: upload audio multipart.
- `POST /api/v1/narration-events`: ghi nhận lượt nghe.
- `POST /api/v1/admin/pois/{id}/submit|approve|request-revision|archive`: workflow xuất bản.
- `PATCH /api/v1/admin/pois/{id}`: cập nhật nội dung POI.
- `GET /api/v1/admin/analytics/overview`: tổng hợp analytics.

## Luồng demo CMS

1. Chọn **CMS quản trị** trên thanh điều hướng.
2. Đăng nhập bằng tài khoản Admin hoặc Editor.
3. Bấm **Tạo POI mới**, nhập tên, mô tả, nội dung thuyết minh, tọa độ, bán kính geofence và độ ưu tiên để lưu bản nháp.
4. Chọn **Chỉnh sửa** ở bảng POI để cập nhật nội dung, tọa độ, geofence hoặc độ ưu tiên.
5. Editor có thể gửi POI bản nháp để duyệt; Admin có thể xuất bản, yêu cầu chỉnh sửa hoặc lưu trữ.
6. Trên trang khám phá, mở một POI và bấm **Nghe câu chuyện**. API sẽ nhận sự kiện `MANUAL/start`; bấm nút tạm dừng/kết thúc sẽ gửi `MANUAL/finish`.

## Kiểm thử thuyết minh tự động bằng GPS

1. Mở trang khám phá trên HTTPS hoặc `localhost`.
2. Bấm **Bật thuyết minh GPS** và cho phép quyền vị trí.
3. Khi vị trí nằm trong bán kính geofence của POI, CityEcho chọn POI ưu tiên cao nhất và phát narration với nguồn `GPS`.
4. Mỗi POI có cooldown 5 phút để không tự phát lặp. Nút nghe thủ công và QR vẫn hoạt động độc lập.
5. Khi demo trong phòng học hoặc trình duyệt không có GPS thật, bấm **Mô phỏng GPS**. Hệ thống mô phỏng vị trí tại POI SGU, mở POI tương ứng và phát narration nguồn `GPS`.

Trong khi nghe, nút **Tạm dừng** chỉ tạm dừng giọng đọc/audio; nút **Tiếp tục** phát tiếp từ vị trí đang dừng. Chỉ nút **Kết thúc thuyết minh** mới ghi nhận lượt nghe hoàn tất.

## Mở POI bằng QR

QR Code có thể trỏ tới URL dạng:

```text
http://localhost:5173/?qr=CITYECHO-BINHTAY
```

Trang đích sẽ xác thực mã với backend, chỉ hiển thị POI đã xuất bản, không yêu cầu GPS và ghi nhận lượt nghe với nguồn `QR`.

Trong chi tiết mỗi POI, CityEcho cũng tự tạo QR Code tương ứng. Bấm **Tải QR để in** để lưu ảnh PNG dùng cho poster hoặc bảng giới thiệu tại địa điểm.

## Kiểm thử thuyết minh và QR

1. Chạy backend ở cổng `8000` và frontend ở cổng `5173`.
2. Trên trang khám phá, bấm một POI rồi bấm **Nghe câu chuyện**. Bản demo sẽ đọc `narration_text` bằng giọng đọc tiếng Việt của Chrome/Edge; nếu POI có `audio_url`, hệ thống sẽ phát file audio đó.
3. Kiểm thử QR ngay trên máy tính bằng cách mở:

   ```text
   http://localhost:5173/?qr=CITYECHO-BINHTAY
   ```

4. Trang QR hiện **Chợ Bình Tây**. Bấm **Nghe câu chuyện** để nghe và ghi nhận nguồn `QR`.
5. Kiểm thử mã sai bằng:

   ```text
   http://localhost:5173/?qr=QR-SAI
   ```

   Kết quả mong đợi là trang báo QR không hợp lệ.

`localhost` chỉ dùng được trên chính máy đang chạy frontend. Muốn quét bằng điện thoại trong cùng mạng Wi-Fi, chạy Vite với `--host 0.0.0.0`, dùng địa chỉ IP LAN của máy thay cho `localhost`, và cấu hình `VITE_API_URL` trỏ tới backend IP LAN.

API docs có tại `http://localhost:8000/docs`.

## Dữ liệu mẫu quanh SGU

Bản đầu có 12 POI (đúng phạm vi 10–15 điểm trong bản thiết kế), tọa độ ghi kèm địa chỉ để đối chiếu OSM/thực địa:

SGU, Chùa Bà Thiên Hậu, Hội quán Nghĩa An, Chùa Ông Bổn, Nhà thờ Cha Tam, Chợ An Đông, Bệnh viện Chợ Rẫy, Cầu Chữ Y, Chợ Bình Tây, Chùa Phụng Sơn, Bảo tàng Mỹ thuật TP.HCM, Hồ Con Rùa.

Hình minh họa nội bộ nằm tại `frontend/public/images/pois/`. CMS có thể thay bằng ảnh/audio thật qua form upload.

## Upload media

Trong CMS, sau khi tạo hoặc sửa POI, chọn file ảnh (jpg/png/webp, tối đa 5MB) hoặc audio (mp3/wav/ogg, tối đa 20MB). File lưu tại `backend/media/uploads/` và được phục vụ ở `/media/...`.

## Demo GPS trên điện thoại (HTTPS/LAN)

Trình duyệt chỉ cấp GPS ổn định trên HTTPS hoặc localhost.

1. Chạy backend lắng nghe mọi giao diện: `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
2. Trong terminal khác:

```powershell
$env:CITYECHO_HTTPS="1"
.\scripts\demo-lan.ps1
```

3. Trên điện thoại cùng Wi-Fi, mở `https://<IPv4-LAN>:5173`, chấp nhận chứng chỉ tự ký, rồi bấm **Bật thuyết minh GPS**.

Vite proxy giúp điện thoại chỉ cần một cổng HTTPS; API và file media đi cùng origin.

## Kiểm thử

```powershell
$env:PYTHONPATH="backend"
python -m pytest backend\tests -q
npm --prefix frontend run build
npx --prefix frontend playwright install chromium
npm --prefix frontend run test:e2e
```
