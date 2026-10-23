import React, { useEffect, useMemo, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import { ArrowLeft, Compass, Headphones, LocateFixed, MapPin, Menu, Play, QrCode, Search, ShieldCheck, Sparkles, X } from "lucide-react";
import "./styles.css";

type Status = "DRAFT" | "PENDING" | "NEEDS_REVISION" | "PUBLISHED" | "ARCHIVED";
type Poi = { id: string; category: string; latitude: number; longitude: number; radius_m: number; priority: number; status: Status; translation: { name: string; description: string; narration_text: string }; image_url: string; audio_url?: string; qr_code: string; distance_m?: number };
type Analytics = { total_plays: number; completed_plays: number; completion_rate: number; total_duration: number; sources: Record<string, number>; top_pois: { poi_id: string; name: string; plays: number }[] };
const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

const fallback: Poi[] = [
  { id: "sgu-main", category: "campus", latitude: 10.7591, longitude: 106.6823, radius_m: 40, priority: 5, status: "PUBLISHED", qr_code: "CITYECHO-SGU", image_url: "https://images.unsplash.com/photo-1564981797816-1043664bf78d?auto=format&fit=crop&w=1200&q=80", translation: { name: "Trường Đại học Sài Gòn", description: "Không gian giáo dục lâu đời giữa lòng Quận 5, gắn với nhiều lớp ký ức đô thị.", narration_text: "Chào mừng bạn đến với CityEcho. Đây là điểm khởi đầu để khám phá những câu chuyện quanh SGU." } },
  { id: "chua-ba", category: "religious", latitude: 10.7548, longitude: 106.6639, radius_m: 40, priority: 5, status: "PUBLISHED", qr_code: "CITYECHO-THIENHAU", image_url: "https://images.unsplash.com/photo-1548013146-72479768bada?auto=format&fit=crop&w=1200&q=80", translation: { name: "Chùa Bà Thiên Hậu", description: "Ngôi chùa người Hoa nổi tiếng với kiến trúc cổ và các mảng chạm tinh xảo.", narration_text: "Bạn đang đứng trước Chùa Bà Thiên Hậu, một điểm giao thoa văn hóa đặc sắc của khu Chợ Lớn." } },
  { id: "cho-lon", category: "market", latitude: 10.7527, longitude: 106.6504, radius_m: 40, priority: 4, status: "PUBLISHED", qr_code: "CITYECHO-BINHTAY", image_url: "https://images.unsplash.com/photo-1518005020951-eccb494ad742?auto=format&fit=crop&w=1200&q=80", translation: { name: "Chợ Bình Tây", description: "Biểu tượng thương mại của Chợ Lớn với tháp đồng hồ và sân trong rộng.", narration_text: "Chợ Bình Tây được xây dựng đầu thế kỷ 20, là nơi lưu giữ nhịp sống thương hồ của thành phố." } },
  { id: "ho-con-rua", category: "public-space", latitude: 10.7827, longitude: 106.6953, radius_m: 40, priority: 3, status: "PUBLISHED", qr_code: "CITYECHO-HOCRUA", image_url: "https://images.unsplash.com/photo-1523731407965-2430cd12f5e4?auto=format&fit=crop&w=1200&q=80", translation: { name: "Hồ Con Rùa", description: "Không gian công cộng quen thuộc, nơi các tuyến đường trung tâm gặp nhau.", narration_text: "Hồ Con Rùa là một lát cắt đời sống đô thị, đặc biệt sôi động vào buổi tối." } },
];

async function loadPois(): Promise<Poi[]> { try { const res = await fetch(`${API}/api/v1/pois`); if (!res.ok) throw new Error("API unavailable"); return (await res.json()).items; } catch { return fallback; } }

function App() {
  const [pois, setPois] = useState<Poi[]>(fallback);
  const [selected, setSelected] = useState<Poi | null>(null);
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("all");
  const [locating, setLocating] = useState(false);
  const [nearby, setNearby] = useState<Poi[]>([]);
  const [playing, setPlaying] = useState(false);
  const [view, setView] = useState<"explore" | "admin">("explore");
  const [menuOpen, setMenuOpen] = useState(false);
  const [qrPoi, setQrPoi] = useState<Poi | null>(null);
  const [qrError, setQrError] = useState("");
  const [qrLoading, setQrLoading] = useState(false);
  const [narrationNotice, setNarrationNotice] = useState("");
  const audioRef = useRef<HTMLAudioElement | null>(null);
  useEffect(() => { loadPois().then(setPois); }, []);
  useEffect(() => {
    const code = new URLSearchParams(window.location.search).get("qr");
    if (!code) return;
    setQrLoading(true);
    fetch(`${API}/api/v1/qr/${encodeURIComponent(code)}`)
      .then((response) => {
        if (!response.ok) throw new Error("QR Code không hợp lệ hoặc POI chưa xuất bản");
        return response.json();
      })
      .then(setQrPoi)
      .catch((error) => setQrError(error instanceof Error ? error.message : "Không thể mở QR Code"))
      .finally(() => setQrLoading(false));
  }, []);
  const categories = useMemo(() => ["all", ...Array.from(new Set(pois.map((p) => p.category)))], [pois]);
  const visible = pois.filter((p) => (category === "all" || p.category === category) && p.translation.name.toLowerCase().includes(query.toLowerCase()));
  const recordNarration = (poi: Poi, source: string, eventType: "start" | "finish") => {
    fetch(`${API}/api/v1/narration-events`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ poi_id: poi.id, source, event_type: eventType, duration_seconds: eventType === "finish" ? 72 : 0, completed: eventType === "finish", session_id: sessionStorage.getItem("cityecho-session") || "web-demo" }),
    }).catch(() => undefined);
  };
  const playNarration = async (poi: Poi, nextPlaying: boolean, source = "MANUAL") => {
    setPlaying(nextPlaying);
    if (!nextPlaying) {
      audioRef.current?.pause();
      window.speechSynthesis.cancel();
      recordNarration(poi, source, "finish");
      return;
    }
    recordNarration(poi, source, "start");
    setNarrationNotice("");
    if (poi.audio_url) {
      const audio = audioRef.current || new Audio();
      audioRef.current = audio;
      audio.src = poi.audio_url;
      audio.onended = () => { setPlaying(false); recordNarration(poi, source, "finish"); };
      try { await audio.play(); } catch { setNarrationNotice("Trình duyệt chặn audio tự động. Hãy bấm nút phát lại."); setPlaying(false); }
      return;
    }
    if (!("speechSynthesis" in window)) {
      setPlaying(false);
      setNarrationNotice("Trình duyệt không hỗ trợ đọc thuyết minh. Hãy dùng Chrome hoặc Edge.");
      return;
    }
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(poi.translation.narration_text);
    utterance.lang = "vi-VN";
    utterance.rate = 0.95;
    utterance.onend = () => { setPlaying(false); recordNarration(poi, source, "finish"); };
    utterance.onerror = () => { setPlaying(false); setNarrationNotice("Không thể phát thuyết minh trên thiết bị này."); };
    window.speechSynthesis.speak(utterance);
  };
  const locate = () => {
    setLocating(true);
    navigator.geolocation?.getCurrentPosition(async ({ coords }) => { try { const res = await fetch(`${API}/api/v1/pois/nearby?lat=${coords.latitude}&lng=${coords.longitude}`); setNearby(res.ok ? await res.json() : []); } catch { setNearby([]); } finally { setLocating(false); } }, () => setLocating(false));
  };
  if (new URLSearchParams(window.location.search).has("qr")) return <div className="app"><header className="topbar"><div className="brand"><span className="brand-mark"><Compass size={22}/></span><span>City<span>Echo</span><small>Âm vang thành phố</small></span></div></header><main className="qr-page">{qrLoading ? <div className="qr-state"><QrCode size={42}/><h1>Đang mở câu chuyện...</h1><p>CityEcho đang tìm nội dung từ mã QR.</p></div> : qrError ? <div className="qr-state error"><X size={42}/><h1>Không thể mở QR Code</h1><p>{qrError}</p><button className="primary" onClick={() => { window.location.href = "/"; }}>Về trang khám phá</button></div> : qrPoi ? <div className="qr-story"><span className="eyebrow"><QrCode size={14}/> CITYECHO · QR STORY</span><img src={qrPoi.image_url} alt={qrPoi.translation.name}/><span className="tag">{qrPoi.category}</span><h1>{qrPoi.translation.name}</h1><p className="qr-description">{qrPoi.translation.description}</p><div className="qr-narration"><Headphones size={22}/><div><b>Thuyết minh tiếng Việt</b><small>Đã mở bằng QR Code · Không cần GPS</small></div><button className="play" onClick={() => playNarration(qrPoi, !playing, "QR")}>{playing ? "Ⅱ" : <Play size={17} fill="currentColor"/>}</button></div><button className="primary full" onClick={() => playNarration(qrPoi, true, "QR")}>{playing ? "Đang phát câu chuyện..." : "Nghe câu chuyện"}</button>{narrationNotice && <p className="narration-notice">{narrationNotice}</p>}<button className="secondary qr-back" onClick={() => { window.location.href = "/"; }}><ArrowLeft size={16}/> Khám phá các địa điểm khác</button></div> : null}</main><footer><span>© 2026 CityEcho</span><span>Khám phá có trách nhiệm · Bảo tồn ký ức địa phương</span></footer></div>;
  return <div className="app">
    <header className="topbar"><div className="brand"><span className="brand-mark"><Compass size={22}/></span><span>City<span>Echo</span><small>Âm vang thành phố</small></span></div><nav><button className={view === "explore" ? "active" : ""} onClick={() => setView("explore")}><Compass size={16}/> Khám phá</button><button className={view === "admin" ? "active" : ""} onClick={() => setView("admin")}><ShieldCheck size={16}/> CMS quản trị</button></nav><button className="menu" onClick={() => setMenuOpen(!menuOpen)}><Menu/></button></header>
    {view === "admin" ? <Admin pois={pois} setPois={setPois} onBack={() => setView("explore")} /> : <main>
      <section className="hero"><div><p className="eyebrow"><Sparkles size={14}/> CITYECHO · SGU COLLECTION</p><h1>Đi chậm lại.<br/><em>Nghe thành phố kể.</em></h1><p className="hero-copy">Khám phá những câu chuyện văn hóa, lịch sử quanh Sài Gòn qua bản đồ tương tác và thuyết minh thông minh.</p><div className="hero-actions"><button className="primary" onClick={locate}><LocateFixed size={17}/> {locating ? "Đang tìm vị trí..." : "Tìm địa điểm quanh tôi"}</button><button className="secondary" onClick={() => document.getElementById("poi-list")?.scrollIntoView({ behavior: "smooth" })}>Xem tất cả POI <ArrowLeft size={16} className="rotate"/></button></div></div><div className="hero-art"><div className="sun"/><div className="hero-card"><MapPin size={18}/><span>10.7591° N<br/><b>106.6823° E</b></span></div><div className="hero-label">SÀI GÒN<br/><strong>DI SẢN SỐ</strong></div></div></section>
      {nearby.length > 0 && <section className="nearby"><b><LocateFixed size={16}/> {nearby.length} địa điểm gần bạn</b><span>Đã sắp xếp theo ưu tiên và khoảng cách</span><button onClick={() => setNearby([])}><X size={16}/></button></section>}
      <section className="explore" id="poi-list"><div className="section-head"><div><p className="eyebrow">BẢN ĐỒ CÂU CHUYỆN</p><h2>Chọn một điểm để bắt đầu</h2></div><div className="filters"><div className="search"><Search size={17}/><input placeholder="Tìm kiếm địa điểm..." value={query} onChange={(e) => setQuery(e.target.value)}/></div><select value={category} onChange={(e) => setCategory(e.target.value)}>{categories.map((c) => <option key={c} value={c}>{c === "all" ? "Tất cả danh mục" : c}</option>)}</select></div></div><div className="content-grid"><div className="map-panel"><div className="map-grid"/>{visible.map((poi, index) => <button key={poi.id} className={`map-pin pin-${index + 1} ${selected?.id === poi.id ? "chosen" : ""}`} onClick={() => setSelected(poi)}><MapPin size={21}/><span>{index + 1}</span></button>)}<div className="map-controls"><button onClick={locate}><LocateFixed size={17}/></button><button onClick={() => setSelected(null)}>＋</button></div><div className="map-legend"><span className="legend-dot"/><span>Điểm đã xuất bản</span></div></div><div className="poi-list">{visible.map((poi) => <article className={`poi-card ${selected?.id === poi.id ? "selected" : ""}`} key={poi.id} onClick={() => setSelected(poi)}><img src={poi.image_url} alt=""/><div className="poi-body"><div className="poi-top"><span className="tag">{poi.category}</span><span className="poi-number">0{visible.indexOf(poi) + 1}</span></div><h3>{poi.translation.name}</h3><p>{poi.translation.description}</p><div className="poi-meta"><span><Headphones size={14}/> Thuyết minh</span><span><QrCode size={14}/> QR</span></div></div></article>)}</div></div></section>
      {selected && <aside className="detail-drawer"><button className="close" onClick={() => setSelected(null)}><X/></button><img src={selected.image_url} alt=""/><div className="drawer-content"><span className="tag">{selected.category}</span><h2>{selected.translation.name}</h2><p>{selected.translation.description}</p><div className="audio-box"><div className="audio-icon"><Headphones/></div><div><b>Thuyết minh tiếng Việt</b><small>{selected.audio_url ? "Audio file · 01:12" : "Đọc tự động bằng trình duyệt"}</small></div><button className="play" onClick={() => playNarration(selected, !playing)}>{playing ? "Ⅱ" : <Play size={17} fill="currentColor"/>}</button></div><button className="primary full" onClick={() => playNarration(selected, true)}>{playing ? "Đang phát thuyết minh..." : "Nghe câu chuyện"}</button>{narrationNotice && <p className="narration-notice">{narrationNotice}</p>}<div className="coordinates"><MapPin size={16}/> {selected.latitude.toFixed(4)}° N · {selected.longitude.toFixed(4)}° E <span>QR: {selected.qr_code}</span></div></div></aside>}
    </main>}
    {menuOpen && <div className="mobile-menu"><button onClick={() => { setView("explore"); setMenuOpen(false); }}>Khám phá</button><button onClick={() => { setView("admin"); setMenuOpen(false); }}>CMS quản trị</button></div>}
    <footer><span>© 2026 CityEcho</span><span>Khám phá có trách nhiệm · Bảo tồn ký ức địa phương</span></footer>
  </div>;
}

function Admin({ pois, setPois, onBack }: { pois: Poi[]; setPois: React.Dispatch<React.SetStateAction<Poi[]>>; onBack: () => void }) {
  const [tab, setTab] = useState<"pois" | "analytics">("pois");
  const [status, setStatus] = useState<Status | "ALL">("ALL");
  const [token, setToken] = useState(() => sessionStorage.getItem("cityecho-token") || "");
  const [login, setLogin] = useState({ username: "admin@cityecho.vn", password: "admin123" });
  const [message, setMessage] = useState("");
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [editingPoi, setEditingPoi] = useState<Poi | null>(null);
  const [form, setForm] = useState({ name: "", description: "", narration_text: "", category: "historical", latitude: "10.7591", longitude: "106.6823", radius_m: "40", priority: "3", image_url: "" });
  const filtered = pois.filter((p) => status === "ALL" || p.status === status);
  const request = async (path: string, options: RequestInit = {}) => {
    const response = await fetch(`${API}${path}`, { ...options, headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}`, ...(options.headers || {}) } });
    if (!response.ok) throw new Error((await response.json()).detail || "Thao tác thất bại");
    return response.json();
  };
  const signIn = async (event: React.FormEvent) => {
    event.preventDefault();
    try {
      const body = new URLSearchParams({ username: login.username, password: login.password });
      const response = await fetch(`${API}/api/v1/auth/login`, { method: "POST", headers: { "Content-Type": "application/x-www-form-urlencoded" }, body });
      if (!response.ok) throw new Error("Email hoặc mật khẩu không đúng");
      const data = await response.json();
      sessionStorage.setItem("cityecho-token", data.access_token);
      setToken(data.access_token);
      setMessage(`Xin chào ${data.user.full_name}`);
    } catch (error) { setMessage(error instanceof Error ? error.message : "Đăng nhập thất bại"); }
  };
  const workflow = async (poi: Poi, action: "submit" | "approve" | "request-revision" | "archive") => {
    try {
      const updated = await request(`/api/v1/admin/pois/${poi.id}/${action}`, { method: "POST" });
      setPois((current) => current.map((item) => item.id === poi.id ? updated : item));
      setMessage("Đã cập nhật trạng thái POI");
    } catch (error) { setMessage(error instanceof Error ? error.message : "Không thể cập nhật"); }
  };
  useEffect(() => {
    if (tab !== "analytics" || !token) return;
    request("/api/v1/admin/analytics/overview").then(setAnalytics).catch((error) => setMessage(error instanceof Error ? error.message : "Không thể tải thống kê"));
  }, [tab, token]);
  const createPoi = async (event: React.FormEvent) => {
    event.preventDefault();
    try {
      const created = await request("/api/v1/admin/pois", {
        method: "POST",
        body: JSON.stringify({
          category: form.category,
          latitude: Number(form.latitude),
          longitude: Number(form.longitude),
          radius_m: Number(form.radius_m),
          priority: Number(form.priority),
          image_url: form.image_url,
          translation: { language_code: "vi", name: form.name, description: form.description, narration_text: form.narration_text },
        }),
      });
      setPois((current) => [created, ...current]);
      setShowCreate(false);
      setMessage("Đã tạo POI bản nháp. Hãy gửi duyệt khi nội dung hoàn tất.");
      setForm({ name: "", description: "", narration_text: "", category: "historical", latitude: "10.7591", longitude: "106.6823", radius_m: "40", priority: "3", image_url: "" });
    } catch (error) { setMessage(error instanceof Error ? error.message : "Không thể tạo POI"); }
  };
  const openEdit = (poi: Poi) => {
    setEditingPoi(poi);
    setForm({ name: poi.translation.name, description: poi.translation.description, narration_text: poi.translation.narration_text, category: poi.category, latitude: String(poi.latitude), longitude: String(poi.longitude), radius_m: String(poi.radius_m), priority: String(poi.priority), image_url: poi.image_url });
  };
  const updatePoi = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!editingPoi) return;
    try {
      const updated = await request(`/api/v1/admin/pois/${editingPoi.id}`, {
        method: "PATCH",
        body: JSON.stringify({
          category: form.category,
          latitude: Number(form.latitude),
          longitude: Number(form.longitude),
          radius_m: Number(form.radius_m),
          priority: Number(form.priority),
          image_url: form.image_url,
          translation: { language_code: "vi", name: form.name, description: form.description, narration_text: form.narration_text },
        }),
      });
      setPois((current) => current.map((item) => item.id === updated.id ? updated : item));
      setEditingPoi(null);
      setMessage("Đã cập nhật POI");
    } catch (error) { setMessage(error instanceof Error ? error.message : "Không thể cập nhật POI"); }
  };
  if (!token) return <main className="admin-page"><button className="back-link" onClick={onBack}><ArrowLeft size={16}/> Quay lại khám phá</button><div className="login-card"><p className="eyebrow"><ShieldCheck size={14}/> CMS CONTROL ROOM</p><h1>Đăng nhập quản trị</h1><p>Sử dụng tài khoản CMS để quản lý và xuất bản POI.</p><form onSubmit={signIn}><label>Email<input value={login.username} onChange={(e) => setLogin({ ...login, username: e.target.value })}/></label><label>Mật khẩu<input type="password" value={login.password} onChange={(e) => setLogin({ ...login, password: e.target.value })}/></label><button className="primary full">Đăng nhập</button></form>{message && <div className="form-message">{message}</div>}</div></main>;
  return <main className="admin-page"><button className="back-link" onClick={onBack}><ArrowLeft size={16}/> Quay lại khám phá</button><div className="admin-heading"><div><p className="eyebrow"><ShieldCheck size={14}/> CMS CONTROL ROOM</p><h1>Quản trị CityEcho</h1><p>Quản lý nội dung, quy trình xuất bản và theo dõi trải nghiệm tham quan.</p></div><div className="admin-heading-actions"><button className="primary" onClick={() => setShowCreate(true)}>＋ Tạo POI mới</button><button className="secondary" onClick={() => { sessionStorage.removeItem("cityecho-token"); setToken(""); }}>Đăng xuất</button></div></div>{message && <div className="form-message">{message}</div>}{showCreate && <div className="create-card"><div className="create-card-head"><h2>Tạo POI bản nháp</h2><button onClick={() => setShowCreate(false)}><X size={18}/></button></div><form className="poi-form" onSubmit={createPoi}><label>Tên địa điểm<input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}/></label><label>Danh mục<input required value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}/></label><label>Mô tả<textarea required value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })}/></label><label>Nội dung thuyết minh<textarea required value={form.narration_text} onChange={(e) => setForm({ ...form, narration_text: e.target.value })}/></label><div className="form-grid"><label>Vĩ độ<input required type="number" step="any" value={form.latitude} onChange={(e) => setForm({ ...form, latitude: e.target.value })}/></label><label>Kinh độ<input required type="number" step="any" value={form.longitude} onChange={(e) => setForm({ ...form, longitude: e.target.value })}/></label><label>Bán kính (m)<input required type="number" min="1" value={form.radius_m} onChange={(e) => setForm({ ...form, radius_m: e.target.value })}/></label><label>Ưu tiên (1-5)<input required type="number" min="1" max="5" value={form.priority} onChange={(e) => setForm({ ...form, priority: e.target.value })}/></label></div><label>URL hình ảnh<input type="url" value={form.image_url} onChange={(e) => setForm({ ...form, image_url: e.target.value })}/></label><button className="primary" type="submit">Lưu bản nháp</button></form></div>}{editingPoi && <div className="create-card"><div className="create-card-head"><h2>Chỉnh sửa POI</h2><button onClick={() => setEditingPoi(null)}><X size={18}/></button></div><form className="poi-form" onSubmit={updatePoi}><label>Tên địa điểm<input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}/></label><label>Danh mục<input required value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}/></label><label>Mô tả<textarea required value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })}/></label><label>Nội dung thuyết minh<textarea required value={form.narration_text} onChange={(e) => setForm({ ...form, narration_text: e.target.value })}/></label><div className="form-grid"><label>Vĩ độ<input required type="number" step="any" value={form.latitude} onChange={(e) => setForm({ ...form, latitude: e.target.value })}/></label><label>Kinh độ<input required type="number" step="any" value={form.longitude} onChange={(e) => setForm({ ...form, longitude: e.target.value })}/></label><label>Bán kính (m)<input required type="number" min="1" value={form.radius_m} onChange={(e) => setForm({ ...form, radius_m: e.target.value })}/></label><label>Ưu tiên (1-5)<input required type="number" min="1" max="5" value={form.priority} onChange={(e) => setForm({ ...form, priority: e.target.value })}/></label></div><label>URL hình ảnh<input type="url" value={form.image_url} onChange={(e) => setForm({ ...form, image_url: e.target.value })}/></label><button className="primary" type="submit">Lưu thay đổi</button></form></div>}<div className="stats"><div><small>TỔNG POI</small><b>{pois.length}</b><span>Đang quản lý</span></div><div><small>ĐÃ XUẤT BẢN</small><b>{pois.filter(p => p.status === "PUBLISHED").length}</b><span className="green">Sẵn sàng khám phá</span></div><div><small>CHỜ DUYỆT</small><b>{pois.filter(p => p.status === "PENDING").length}</b><span>Cần xử lý</span></div><div><small>LƯỢT NGHE</small><b>{analytics?.total_plays ?? "—"}</b><span>{analytics ? `${analytics.completion_rate}% hoàn tất` : "Mở thống kê để tải"}</span></div></div><div className="admin-tabs"><button className={tab === "pois" ? "active" : ""} onClick={() => setTab("pois")}>Danh sách POI</button><button className={tab === "analytics" ? "active" : ""} onClick={() => setTab("analytics")}>Thống kê</button></div>{tab === "pois" ? <div className="table-card"><div className="table-toolbar"><b>Địa điểm & nội dung</b><select value={status} onChange={(e) => setStatus(e.target.value as Status | "ALL")}><option value="ALL">Tất cả trạng thái</option><option value="PUBLISHED">Đã xuất bản</option><option value="PENDING">Chờ duyệt</option><option value="DRAFT">Bản nháp</option><option value="NEEDS_REVISION">Cần chỉnh sửa</option></select></div><table><thead><tr><th>ĐỊA ĐIỂM</th><th>DANH MỤC</th><th>TRẠNG THÁI</th><th>ƯU TIÊN</th><th>THAO TÁC</th></tr></thead><tbody>{filtered.map((p) => <tr key={p.id}><td><div className="table-poi"><img src={p.image_url} alt=""/><span><b>{p.translation.name}</b><small>{p.id}</small></span></div></td><td>{p.category}</td><td><span className={`status ${p.status.toLowerCase()}`}>{p.status === "PUBLISHED" ? "Đã xuất bản" : p.status === "PENDING" ? "Chờ duyệt" : p.status === "NEEDS_REVISION" ? "Cần chỉnh sửa" : "Bản nháp"}</span></td><td>{"★".repeat(p.priority)}<span className="muted">{"★".repeat(5 - p.priority)}</span></td>  <td><div className="row-actions"><button onClick={() => openEdit(p)}>Chỉnh sửa</button>{p.status === "DRAFT" || p.status === "NEEDS_REVISION" ? <button onClick={() => workflow(p, "submit")}>Gửi duyệt</button> : null}{p.status === "PENDING" ? <><button onClick={() => workflow(p, "approve")}>Xuất bản</button><button onClick={() => workflow(p, "request-revision")}>Yêu cầu sửa</button></> : null}{p.status === "PUBLISHED" ? <button onClick={() => workflow(p, "archive")}>Lưu trữ</button> : null}</div></td></tr>)}</tbody></table></div> : <div className="analytics-card"><h2>Hiệu quả thuyết minh</h2>{analytics ? <><div className="chart">{analytics.top_pois.map((item, i) => <div key={item.poi_id} className="bar-wrap"><div className="bar" style={{ height: `${Math.max(item.plays * 20, 8)}%` }}/><small>{i + 1}</small></div>)}</div><div className="analytics-summary"><b>{analytics.total_plays} <small>lượt bắt đầu</small></b><b>{analytics.completed_plays} <small>hoàn tất</small></b><b>{analytics.completion_rate}% <small>tỷ lệ hoàn tất</small></b></div><div className="source-summary">GPS: {analytics.sources.GPS || 0} · QR: {analytics.sources.QR || 0} · Thủ công: {analytics.sources.MANUAL || 0}</div></> : <p>Đang tải dữ liệu thống kê...</p>}</div>}</main>;
}

createRoot(document.getElementById("root")!).render(<React.StrictMode><App /></React.StrictMode>);
