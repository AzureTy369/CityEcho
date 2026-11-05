# CityEcho

CityEcho là website khám phá văn hóa quanh SGU với bản đồ POI, nội dung thuyết minh, QR, geofence và CMS.

Checklist nghiệm thu và thứ tự phát triển nằm tại [CHECKLIST.md](./CHECKLIST.md). Lệnh kiểm tra nhanh nằm tại [scripts/verify.ps1](./scripts/verify.ps1).

Tài liệu sản phẩm và sơ đồ database:

- [PRD.md](./PRD.md): yêu cầu sản phẩm theo chức năng hiện có.
- [CITYECHO_ERD.dbml](./CITYECHO_ERD.dbml): DBML phản ánh 11 bảng PostgreSQL hiện tại; dán vào dbdiagram.io để render.

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

Backend tự dùng bộ nhớ tạm khi không có `DATABASE_URL`, phù hợp chạy nhanh và test. Khi đặt `DATABASE_URL`, backend tạo các bảng nghiệp vụ như `roles`, `users`, `pois`, `narration_events`, `audit_logs` và `visitor_sessions`; dữ liệu mẫu được seed khi database chưa có POI.

`roles` là bảng phân quyền, không nên xóa. Khi backend khởi động, bảng được seed các vai trò `admin` và `editor`, sau đó liên kết tài khoản trong `users.role_id`.

`visitor_sessions` lưu mã trình duyệt ẩn danh, thời điểm truy cập đầu/cuối, trang cuối và nguồn vào. Trang web gửi heartbeat mỗi 10 giây; phiên được coi là **Active** nếu heartbeat gần nhất trong 1 phút. Bảng thiết bị trên dashboard cũng tự làm mới mỗi 10 giây. Không lưu địa chỉ IP hoặc thông tin cá nhân. Mỗi profile/trình duyệt được tính riêng; một người dùng mở nhiều profile có thể được tính thành nhiều thiết bị.

## Backend 3 lớp

Backend được chia theo luồng **API/Presentation → Service → Repository**:

1. **API/Presentation** — `backend/app/main.py`: khai báo endpoint FastAPI, kiểm tra request, xác thực JWT và trả HTTP response. Các schema request/response nằm ở `backend/app/schemas.py`.
2. **Service/Business** — `backend/app/services/cityecho_service.py`: xử lý quy tắc POI, workflow duyệt, narration, analytics và điều phối dữ liệu.
3. **Repository/Data** — `backend/app/storage.py`: SQLAlchemy models và các thao tác đọc/ghi PostgreSQL. Khi không có `DATABASE_URL`, service vẫn chạy với dữ liệu mẫu trong bộ nhớ để demo/test.

Luồng ví dụ: `PATCH /api/v1/admin/pois/{id}` → API kiểm tra quyền và schema → `CityEchoService.update_poi()` xử lý nghiệp vụ → `PersistentStore.save_poi()` ghi PostgreSQL.

## Thao tác và chạy query PostgreSQL

Ví dụ bên dưới dùng PostgreSQL từ Docker Compose. Các thông tin đăng nhập mặc định trong `docker-compose.yml` chỉ dành cho máy local/demo; hãy thay mật khẩu trước khi triển khai thật.

### 1. Cài và mở Docker Desktop (Windows)

1. Cài **Docker Desktop for Windows** từ [trang chính thức của Docker](https://www.docker.com/products/docker-desktop/). Nếu trình cài đặt yêu cầu WSL 2 hoặc khởi động lại Windows, làm theo hướng dẫn rồi mở Docker Desktop.
2. Chờ Docker Desktop báo **Engine running**. Docker Desktop cần tiếp tục mở trong lúc chạy CityEcho.
3. Mở VS Code tại thư mục dự án `D:\CNPM`, chọn **Terminal → New Terminal**. Đảm bảo terminal đang ở thư mục gốc dự án, nơi có file `docker-compose.yml`:

   ```powershell
   Set-Location D:\CNPM
   Get-Location
   ```

4. Kiểm tra Docker đã sẵn sàng:

   ```powershell
   docker --version
   docker compose version
   docker info
   ```

   Nếu `docker info` báo không kết nối được Docker Engine, hãy mở Docker Desktop và chờ Engine chạy xong rồi thử lại.

### 2. Chạy toàn bộ CityEcho

Từ PowerShell tại `D:\CNPM`, chạy:

```powershell
docker compose up --build -d
```

Lần đầu Docker tải image và build frontend/backend nên có thể mất vài phút. `-d` chạy các container ở nền; cấu hình Compose đợi PostgreSQL sẵn sàng rồi mới khởi động backend.

Kiểm tra trạng thái:

```powershell
docker compose ps
```

Ba dịch vụ `db`, `backend`, `frontend` cần ở trạng thái chạy; `db` sẽ hiện `healthy`. Sau đó mở:

- Website: `http://localhost:5173`
- API health check: `http://localhost:8000/health`
- Tài liệu API: `http://localhost:8000/docs`

Đăng nhập CMS bằng tài khoản demo: `admin@cityecho.vn` / `admin123` hoặc `editor@cityecho.vn` / `editor123`.

### 3. Xem log hoặc khởi động lại

Xem log của cả ba dịch vụ:

```powershell
docker compose logs -f
```

Nhấn `Ctrl+C` để ngừng xem log (các container vẫn chạy). Chỉ xem log backend:

```powershell
docker compose logs -f backend
```

Khởi động lại một dịch vụ sau khi cần:

```powershell
docker compose restart backend
```

### 4. Dừng CityEcho và lưu ý dữ liệu

Dừng các container nhưng giữ nguyên dữ liệu PostgreSQL và media:

```powershell
docker compose down
```

Chạy lại bằng `docker compose up -d`. Dữ liệu được lưu trong Docker volumes có tên `cityecho-db` và `cityecho-media`, nên vẫn còn sau khi dừng hoặc tắt máy.

> **Cẩn thận:** Không thêm `-v` vào `docker compose down` nếu muốn giữ dữ liệu. Lệnh `docker compose down -v` sẽ xóa database và media đã lưu.

### 5. Khởi động database và backend riêng (tùy chọn)

Mở PowerShell tại thư mục gốc dự án:

```powershell
docker compose up -d db
docker compose up -d backend
```

Khi backend khởi động với `DATABASE_URL`, ứng dụng tự tạo bảng từ SQLAlchemy và seed danh mục/POI mẫu nếu database chưa có dữ liệu. Có thể kiểm tra API tại `http://localhost:8000/health`. Nếu muốn dùng website qua Docker, hãy khởi động cả `frontend` như bước 2.

### 6. Mở giao diện chạy query

**Dùng pgAdmin:** tạo server mới với Host `localhost`, Port `5432`, Maintenance database `cityecho`, Username `cityecho`, Password `cityecho` (theo cấu hình local hiện tại trong Compose). Chọn database `cityecho` → **Tools → Query Tool**, nhập SQL ở các ví dụ bên dưới rồi bấm nút Execute.

**Dùng HeidiSQL:** tạo session kiểu **PostgreSQL (TCP/IP)**, Host `127.0.0.1`, Port `5432`, Database `cityecho`, User `cityecho`, Password `cityecho`; chọn database rồi mở tab **Query** để chạy SQL PostgreSQL bên dưới. Không chọn MySQL/MariaDB.

**Dùng `psql` trong container** (không cần cài PostgreSQL client trên Windows):

```powershell
docker compose exec db psql -U cityecho -d cityecho
```

Sau khi thấy dấu nhắc `cityecho=#`, nhập query. Gõ `\q` để thoát. Có thể chạy một query trực tiếp từ PowerShell:

```powershell
docker compose exec -T db psql -U cityecho -d cityecho -c "SELECT id, category, status, latitude, longitude FROM pois ORDER BY id LIMIT 10;"
```

### 7. Query đọc dữ liệu mẫu

Danh sách POI kèm tên tiếng Việt:

```sql
SELECT p.id, t.name, p.category, p.status, p.latitude, p.longitude
FROM pois AS p
LEFT JOIN poi_translations AS t
  ON t.poi_id = p.id AND t.language_code = 'vi'
ORDER BY t.name;
```

Thống kê lượt bắt đầu narration theo nguồn:

```sql
SELECT source, COUNT(*) AS total
FROM narration_events
WHERE event_type = 'start'
GROUP BY source
ORDER BY total DESC;
```

Tổng lượt bắt đầu, lượt nghe hoàn tất và thời lượng nghe:

```sql
SELECT
  COUNT(*) FILTER (WHERE event_type = 'start') AS total_plays,
  COUNT(*) FILTER (WHERE completed) AS completed_plays,
  COALESCE(
    SUM(duration_seconds) FILTER (WHERE event_type = 'finish'),
    0
  ) AS total_listening_seconds
FROM narration_events;
```

Xem trạng thái các trình duyệt đã truy cập gần đây:

```sql
SELECT
  device_id,
  entry_source,
  last_path,
  last_seen_at,
  is_active
FROM visitor_sessions
ORDER BY last_seen_at DESC
LIMIT 50;
```

`is_active` được cập nhật theo heartbeat và khi mở dashboard quản trị; trạng thái active tương ứng heartbeat trong 1 phút gần nhất.

## Đa ngôn ngữ

Trang khám phá và trang mở bằng QR có bộ chọn **Tiếng Việt / English**. Ngôn ngữ được lưu trong trình duyệt; lần đầu mở trang, CityEcho chọn theo ngôn ngữ trình duyệt. API nhận `lang` trên danh sách, chi tiết POI, nearby, geofence, narration và QR. Nếu POI chưa có bản dịch được chọn, API trả bản tiếng Việt; nếu chưa có tiếng Việt thì dùng bản dịch hiện có.

Để thêm bản dịch qua CMS, chọn ngôn ngữ ở thanh đầu trang trước, mở **CMS quản trị**, rồi sửa POI. Nếu bản dịch ngôn ngữ đó chưa có, các ô tên/mô tả/thuyết minh sẽ trống để nhập mới; lưu sẽ thêm bản dịch mà không ghi đè các ngôn ngữ khác. Nội dung dịch cần được biên tập thủ công; ứng dụng không tự động dịch. Mã ngôn ngữ dạng ISO như `vi`, `en`, `ja` được hỗ trợ; giao diện hiện có bản dịch tiếng Việt và tiếng Anh, các mã giao diện khác hiển thị tiếng Anh.

Có thể thêm bản dịch trực tiếp trong HeidiSQL/pgAdmin. Vì backend giữ POI trong bộ nhớ, **dừng backend trước khi sửa và khởi động lại sau khi hoàn tất**:

```powershell
docker compose stop backend
```

```sql
INSERT INTO poi_translations (poi_id, language_code, name, description, narration_text)
VALUES (
  'sgu-main',
  'en',
  'Saigon University',
  'A landmark university in Ho Chi Minh City.',
  'Welcome to Saigon University. Add the reviewed narration text for this place.'
)
ON CONFLICT (poi_id, language_code)
DO UPDATE SET
  name = EXCLUDED.name,
  description = EXCLUDED.description,
  narration_text = EXCLUDED.narration_text;

SELECT poi_id, language_code, name
FROM poi_translations
WHERE poi_id = 'sgu-main'
ORDER BY language_code;
```

Sau khi query thành công:

```powershell
docker compose start backend
```

Kiểm tra phản hồi tiếng Anh tại `http://localhost:8000/api/v1/pois?lang=en` hoặc `http://localhost:8000/api/v1/pois/sgu-main?lang=en`. Có thể xem danh sách mã ngôn ngữ đang dùng tại `http://localhost:8000/api/v1/languages`. Không cần migration/schema mới; `poi_translations` đã có khóa duy nhất `(poi_id, language_code)`.

### 8. Ví dụ cập nhật tên POI bằng SQL

Trước khi query thay đổi dữ liệu, **dừng backend** để ứng dụng không ghi đè thay đổi từ bộ nhớ đang chạy:

```powershell
docker compose stop backend
```

Trong Query Tool của pgAdmin hoặc `psql`, chạy transaction sau:

```sql
BEGIN;

UPDATE poi_translations
SET name = 'Đại học Sài Gòn - tên cập nhật bằng SQL'
WHERE poi_id = 'sgu-main' AND language_code = 'vi';

UPDATE pois
SET payload = jsonb_set(
    payload::jsonb,
    '{translation,name}',
    to_jsonb('Đại học Sài Gòn - tên cập nhật bằng SQL'::text),
    true
)::json,
updated_at = NOW()
WHERE id = 'sgu-main';

COMMIT;
```

Kiểm tra lại bằng query danh sách POI ở bước 3, sau đó chạy:

```powershell
docker compose start backend
```

Ứng dụng hiện nạp POI vào bộ nhớ khi backend khởi động; vì vậy query trực tiếp cần backend dừng và khởi động lại như trên. Với thao tác thường ngày, nên cập nhật qua CMS/API để service đồng bộ các bảng liên quan và ghi audit log. Không chỉnh riêng `payload` hoặc riêng `poi_translations`, vì dữ liệu POI được lưu ở cả hai nơi.

### 9. Kiểm tra ràng buộc và thử xóa POI an toàn

Sau khi áp dụng migration `backend/migrations/20261102_restrict_poi_deletes.sql`, các bảng `poi_translations`, `poi_images`, `poi_audios`, `qr_codes` và `narration_events` tham chiếu `pois.id` bằng FK `ON DELETE RESTRICT`. Vì vậy database từ chối xóa POI khi còn bản dịch, ảnh, audio, QR hoặc lịch sử nghe tham chiếu nó. Đây là quan hệ POI → dữ liệu phụ thuộc, không phải liên kết giữa các POI với nhau. `audit_logs.entity_id` vẫn là ID logic, không có FK tới POI. Xóa các dòng media trong database cũng không tự xóa file ảnh/audio trong Docker media volume.

Migration này đã được áp dụng cho database Docker hiện tại. Với database cũ khác, dừng backend rồi chạy file migration trong tab Query của HeidiSQL, hoặc trong PowerShell từ thư mục dự án:

```powershell
$migration = Get-Content "backend\migrations\20261102_restrict_poi_deletes.sql" -Raw
$migration | docker compose exec -T db psql -v ON_ERROR_STOP=1 -U cityecho -d cityecho
```

Chỉ chạy một lần trên mỗi database. Migration sẽ báo lỗi nếu bảng lịch sử nghe đang có `poi_id` mồ côi; cần đối soát các dòng đó trước khi thêm FK.

Xem quy tắc FK trực tiếp trong HeidiSQL:

```sql
SELECT
  tc.table_name,
  kcu.column_name,
  ccu.table_name AS referenced_table,
  ccu.column_name AS referenced_column,
  rc.delete_rule
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
  ON kcu.constraint_name = tc.constraint_name
 AND kcu.constraint_schema = tc.constraint_schema
JOIN information_schema.constraint_column_usage AS ccu
  ON ccu.constraint_name = tc.constraint_name
 AND ccu.constraint_schema = tc.constraint_schema
JOIN information_schema.referential_constraints AS rc
  ON rc.constraint_name = tc.constraint_name
 AND rc.constraint_schema = tc.constraint_schema
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND tc.table_schema = 'public'
ORDER BY tc.table_name, tc.constraint_name;
```

Trước khi xóa thật, xem POI và các dòng liên quan:

```sql
SELECT
  p.id,
  t.name,
  p.status,
  (SELECT COUNT(*) FROM poi_translations x WHERE x.poi_id = p.id) AS translations,
  (SELECT COUNT(*) FROM poi_images x WHERE x.poi_id = p.id) AS images,
  (SELECT COUNT(*) FROM poi_audios x WHERE x.poi_id = p.id) AS audios,
  (SELECT COUNT(*) FROM qr_codes x WHERE x.poi_id = p.id) AS qr_codes,
  (SELECT COUNT(*) FROM narration_events x WHERE x.poi_id = p.id) AS narration_events
FROM pois AS p
LEFT JOIN poi_translations AS t
  ON t.poi_id = p.id AND t.language_code = 'vi'
ORDER BY p.id;
```

Để xác nhận ràng buộc đang chặn xóa, chọn một POI còn tồn tại và chạy đoạn sau trong HeidiSQL. Ví dụ này bắt lỗi FK có chủ đích; POI không bị xóa:

```sql
DO $$
BEGIN
  DELETE FROM pois WHERE id = 'bao-tang-art-in-paradise';
  RAISE EXCEPTION 'POI unexpectedly deleted; check the FK migration';
EXCEPTION
  WHEN foreign_key_violation THEN
    RAISE NOTICE 'OK: FK RESTRICT prevented deleting a referenced POI';
END
$$;

SELECT id, status
FROM pois
WHERE id = 'bao-tang-art-in-paradise';
```

Kết quả mong đợi là thông báo `OK: FK RESTRICT...` và truy vấn cuối vẫn trả về POI.

Để xóa POI thật, ưu tiên **CMS → Lưu trữ** (`ARCHIVED`) để giữ nội dung và lịch sử. Chỉ hard-delete khi đã sao lưu và có chủ đích xóa cả các dữ liệu liên quan. Dừng backend bằng `docker compose stop backend`, thay ID chính xác, kiểm tra trước trong transaction rồi mới `COMMIT`:

```sql
BEGIN;
DELETE FROM narration_events WHERE poi_id = 'ID_POI_CAN_XOA';
DELETE FROM poi_translations WHERE poi_id = 'ID_POI_CAN_XOA';
DELETE FROM poi_images WHERE poi_id = 'ID_POI_CAN_XOA';
DELETE FROM poi_audios WHERE poi_id = 'ID_POI_CAN_XOA';
DELETE FROM qr_codes WHERE poi_id = 'ID_POI_CAN_XOA';
DELETE FROM pois WHERE id = 'ID_POI_CAN_XOA';
-- Kiểm tra số dòng ảnh hưởng trước khi xác nhận:
-- COMMIT;   -- chỉ bỏ comment nếu chắc chắn muốn xóa vĩnh viễn
ROLLBACK;    -- mặc định an toàn: hoàn tác toàn bộ
```

Thử nghiệm script như đang viết sẽ **ROLLBACK** và không xóa dữ liệu. Chỉ thay `ROLLBACK` bằng `COMMIT` sau khi đã xem số dòng bị tác động và chắc chắn muốn xóa; việc này xóa cả lịch sử nghe, bản dịch, ảnh, audio, QR khỏi database. File ảnh/audio trên volume vẫn cần xử lý riêng. Khởi động backend lại bằng `docker compose start backend`.

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

- `GET /api/v1/pois`: POI đã xuất bản, tìm kiếm và lọc; API mặc định phân trang 20 mục. Trang khám phá tự tải tuần tự tất cả các trang (100 mục mỗi lần) để hiển thị toàn bộ POI.
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
- `POST /api/v1/visitor-sessions/heartbeat`: ghi nhận heartbeat trình duyệt ẩn danh.
- `GET /api/v1/admin/analytics/visitor-sessions`: danh sách phiên và số trình duyệt đang active (Admin).

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

Dashboard tính lượt nghe khi narration bắt đầu, chỉ tính hoàn tất khi audio/giọng đọc chạy hết tự nhiên và cộng thời lượng phát thực tế (không tính thời gian tạm dừng). Nút **Tạm dừng** và **Tiếp tục** giữ nguyên một lượt nghe; bấm **Kết thúc thuyết minh** ghi nhận thời lượng đã nghe nhưng không tính là hoàn tất. Khi đang mở tab Thống kê, các chỉ số tự làm mới mỗi 10 giây.

## Mở POI bằng QR

QR Code có thể trỏ tới URL dạng:

```text
http://localhost:5173/?qr=CITYECHO-BINHTAY
```

Trang đích sẽ xác thực mã với backend, chỉ hiển thị POI đã xuất bản, không yêu cầu GPS và ghi nhận lượt nghe với nguồn `QR`.

Trong chi tiết mỗi POI, CityEcho cũng tự tạo QR Code tương ứng. Bấm **Tải QR để in** để lưu ảnh PNG dùng cho poster hoặc bảng giới thiệu tại địa điểm.

Trong **CMS quản trị → Thống kê**, Admin có thể xem số profile trình duyệt đang active, lần truy cập gần nhất và trạng thái online/offline; heartbeat và danh sách thiết bị tự cập nhật mỗi 10 giây. Trình duyệt không gửi heartbeat trong 1 phút sẽ chuyển sang Offline. Cùng mục này có QR mở trang chủ CityEcho để tải về. QR được tạo theo địa chỉ website hiện tại; nếu muốn người dùng quét bằng điện thoại khi demo LAN, hãy mở website bằng địa chỉ IP LAN của máy chạy Docker thay vì `localhost`. QR `localhost` chỉ mở được trên chính thiết bị đó.

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
