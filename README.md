# CityEcho

CityEcho là website khám phá văn hóa quanh SGU với bản đồ POI, nội dung thuyết minh, QR, geofence và CMS.

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

Mở `http://localhost:5173`. Nếu backend chưa chạy, frontend tự dùng dữ liệu mẫu để có thể demo giao diện. Khi backend chạy, trang CMS sử dụng JWT và các thao tác trạng thái được lưu vào API.

Tài khoản demo:

- Admin: `admin@cityecho.vn` / `admin123`
- Biên tập viên: `editor@cityecho.vn` / `editor123`

## Docker Compose

```powershell
docker compose up --build
```

## API chính

- `GET /api/v1/pois`: POI đã xuất bản, tìm kiếm và lọc.
- `GET /api/v1/pois/nearby?lat=...&lng=...`: POI gần vị trí theo Haversine.
- `GET /api/v1/qr/{code}`: mở POI từ QR.
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

API docs có tại `http://localhost:8000/docs`.
