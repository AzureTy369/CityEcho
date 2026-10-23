# Checklist nghiệm thu CityEcho

## MVP bắt buộc

- [x] Frontend React/TypeScript chạy được.
- [x] Backend FastAPI chạy được.
- [x] Danh sách POI công khai.
- [x] Tìm kiếm và lọc POI.
- [x] Bản đồ minh họa và marker POI.
- [x] Trang chi tiết POI.
- [x] Thuyết minh bằng SpeechSynthesis tiếng Việt.
- [x] Hỗ trợ `audio_url` nếu POI có file audio.
- [x] Tạm dừng, tiếp tục và kết thúc narration.
- [x] Geolocation và Haversine.
- [x] Geofence tự động bằng GPS.
- [x] Chế độ mô phỏng GPS cho demo.
- [x] Cooldown chống phát lặp 5 phút.
- [x] QR landing page.
- [x] Tạo và tải QR PNG.
- [x] Ghi nhận lượt nghe theo GPS/QR/MANUAL.
- [x] Đăng nhập CMS bằng JWT.
- [x] Phân quyền Admin/Editor.
- [x] Tạo POI bản nháp.
- [x] Chỉnh sửa POI.
- [x] Gửi duyệt, xuất bản, yêu cầu chỉnh sửa, lưu trữ.
- [x] Dashboard analytics cơ bản.
- [x] Audit log trong backend.
- [x] Backend regression tests.
- [x] Frontend production build.

## Còn cần hoàn thiện trước nghiệm thu

- [ ] Lưu POI, tài khoản, narration event và audit log bằng PostgreSQL thay vì bộ nhớ tạm.
- [ ] Hash mật khẩu lấy từ cấu hình/database thay vì tài khoản demo trong mã nguồn.
- [ ] Upload audio/image multipart và lưu trữ file thật.
- [ ] Test E2E bằng Playwright cho khám phá, CMS, QR và narration.
- [ ] Cấu hình HTTPS/LAN để demo GPS trên điện thoại.
- [ ] Thêm dữ liệu mẫu đã kiểm chứng tọa độ/hình ảnh.

## Thứ tự phát triển tiết kiệm

1. PostgreSQL + migration + seed dữ liệu.
2. Tách cấu hình bí mật khỏi mã nguồn.
3. Upload media.
4. E2E và kịch bản demo.
5. Docker/HTTPS/LAN và tài liệu nghiệm thu.

## Lệnh kiểm tra nhanh

```powershell
$env:PYTHONPATH="backend"
python -m pytest backend\tests -q
npm --prefix frontend run build
```
