import React, { useEffect, useMemo, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import QRCode from "qrcode";
import { ArrowLeft, Compass, Headphones, LocateFixed, MapPin, Menu, Play, QrCode, Search, ShieldCheck, Sparkles, X } from "lucide-react";
import { mapPinStyle, mediaUrl, samplePois, type Poi, type Status } from "./samplePois";
import "./styles.css";

type Analytics = { total_plays: number; completed_plays: number; completion_rate: number; total_duration: number; sources: Record<string, number>; top_pois: { poi_id: string; name: string; plays: number }[] };
const API = import.meta.env.VITE_API_URL || "";
const fallback = samplePois;
const img = (poi: Poi) => mediaUrl(API, poi.image_url);
const audioSrc = (poi: Poi) => mediaUrl(API, poi.audio_url || "");

async function loadPois(): Promise<Poi[]> { try { const res = await fetch(`${API}/api/v1/pois`); if (!res.ok) throw new Error("API unavailable"); return (await res.json()).items; } catch { return fallback; } }

function App() {
  const [pois, setPois] = useState<Poi[]>(fallback);
  const [selected, setSelected] = useState<Poi | null>(null);
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("all");
  const [locating, setLocating] = useState(false);
  const [nearby, setNearby] = useState<Poi[]>([]);
  const [playing, setPlaying] = useState(false);
  const [paused, setPaused] = useState(false);
  const [view, setView] = useState<"explore" | "admin">("explore");
  const [menuOpen, setMenuOpen] = useState(false);
  const [qrPoi, setQrPoi] = useState<Poi | null>(null);
  const [qrError, setQrError] = useState("");
  const [qrLoading, setQrLoading] = useState(false);
  const [narrationNotice, setNarrationNotice] = useState("");
  const [qrImage, setQrImage] = useState("");
  const [autoNarration, setAutoNarration] = useState(false);
  const [autoMessage, setAutoMessage] = useState("");
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const playingRef = useRef(false);
  const speechRef = useRef<SpeechSynthesisUtterance | null>(null);
  const cooldownRef = useRef(new Map<string, number>());
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
  useEffect(() => {
    if (!selected) {
      setQrImage("");
      return;
    }
    const url = `${window.location.origin}/?qr=${encodeURIComponent(selected.qr_code)}`;
    QRCode.toDataURL(url, { width: 220, margin: 2, color: { dark: "#102a43", light: "#ffffff" } })
      .then(setQrImage)
      .catch(() => setQrImage(""));
  }, [selected]);
  const recordNarration = (poi: Poi, source: string, eventType: "start" | "finish") => {
    fetch(`${API}/api/v1/narration-events`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ poi_id: poi.id, source, event_type: eventType, duration_seconds: eventType === "finish" ? 72 : 0, completed: eventType === "finish", session_id: sessionStorage.getItem("cityecho-session") || "web-demo" }),
    }).catch(() => undefined);
  };
  const playNarration = async (poi: Poi, nextPlaying: boolean, source = "MANUAL") => {
    setPlaying(nextPlaying);
    playingRef.current = nextPlaying;
    if (!nextPlaying) {
      audioRef.current?.pause();
      window.speechSynthesis.pause();
      setPaused(true);
      return;
    }
    if (paused && speechRef.current) {
      audioRef.current?.play().catch(() => undefined);
      window.speechSynthesis.resume();
      setPaused(false);
      return;
    }
    if (!nextPlaying) {
      recordNarration(poi, source, "finish");
      return;
    }
    setPaused(false);
    recordNarration(poi, source, "start");
    setNarrationNotice("");
    if (poi.audio_url) {
      const audio = audioRef.current || new Audio();
      audioRef.current = audio;
      audio.src = audioSrc(poi);
      audio.onended = () => { setPlaying(false); setPaused(false); recordNarration(poi, source, "finish"); };
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
    speechRef.current = utterance;
    utterance.lang = "vi-VN";
    utterance.rate = 0.95;
    utterance.onend = () => { setPlaying(false); setPaused(false); speechRef.current = null; recordNarration(poi, source, "finish"); };
    utterance.onerror = () => { setPlaying(false); setNarrationNotice("Không thể phát thuyết minh trên thiết bị này."); };
    window.speechSynthesis.speak(utterance);
  };
  const stopNarration = (poi: Poi, source = "MANUAL") => {
    audioRef.current?.pause();
    window.speechSynthesis.cancel();
    speechRef.current = null;
    setPlaying(false);
    setPaused(false);
    recordNarration(poi, source, "finish");
  };
  const toggleNarration = (poi: Poi, source = "MANUAL") => {
    if (playing && !paused) return playNarration(poi, false, source);
    if (paused) return playNarration(poi, true, source);
    return playNarration(poi, true, source);
  };
  useEffect(() => {
    playingRef.current = playing;
  }, [playing]);
  useEffect(() => {
    if (!autoNarration) return;
    if (!navigator.geolocation) {
      setAutoMessage("Thiết bị không hỗ trợ định vị GPS.");
      setAutoNarration(false);
      return;
    }
    setAutoMessage("Đang theo dõi vị trí. Hãy cho phép GPS trên trình duyệt.");
    const watchId = navigator.geolocation.watchPosition(async ({ coords }) => {
      try {
        const response = await fetch(`${API}/api/v1/pois/nearby?lat=${coords.latitude}&lng=${coords.longitude}`);
        if (!response.ok) throw new Error("Không thể tải POI gần vị trí");
        const candidates: Poi[] = await response.json();
        const now = Date.now();
        const candidate = candidates.find((poi) => (poi.distance_m ?? Infinity) <= poi.radius_m && now - (cooldownRef.current.get(poi.id) || 0) >= 5 * 60 * 1000);
        if (!candidate || playingRef.current) return;
        cooldownRef.current.set(candidate.id, now);
        setSelected(candidate);
        setAutoMessage(`Đã phát tự động: ${candidate.translation.name}`);
        await playNarration(candidate, true, "GPS");
      } catch (error) {
        setAutoMessage(error instanceof Error ? error.message : "Không thể kiểm tra geofence");
      }
    }, () => setAutoMessage("Chưa được cấp quyền GPS. Bạn vẫn có thể nghe thủ công hoặc quét QR."), { enableHighAccuracy: true, maximumAge: 10000, timeout: 10000 });
    return () => navigator.geolocation.clearWatch(watchId);
  }, [autoNarration]);
  const locate = () => {
    setLocating(true);
    navigator.geolocation?.getCurrentPosition(async ({ coords }) => { try { const res = await fetch(`${API}/api/v1/pois/nearby?lat=${coords.latitude}&lng=${coords.longitude}`); setNearby(res.ok ? await res.json() : []); } catch { setNearby([]); } finally { setLocating(false); } }, () => setLocating(false));
  };
  const simulateGps = async (poiId = "sgu-main") => {
    const poi = pois.find((item) => item.id === poiId) || pois[0];
    if (!poi) return;
    setLocating(true);
    try {
      const response = await fetch(`${API}/api/v1/geofence/evaluate?lat=${poi.latitude}&lng=${poi.longitude}`);
      if (!response.ok) throw new Error("Không thể mô phỏng vị trí");
      const result = await response.json();
      setNearby(result.candidates || []);
      const candidate = result.candidate as Poi | null;
      if (candidate) {
        setSelected(candidate);
        setAutoMessage(`Mô phỏng GPS đã vào vùng: ${candidate.translation.name}`);
        await playNarration(candidate, true, "GPS");
      } else {
        setAutoMessage("Vị trí mô phỏng chưa nằm trong geofence.");
      }
    } catch (error) {
      setAutoMessage(error instanceof Error ? error.message : "Không thể mô phỏng GPS");
    } finally {
      setLocating(false);
    }
  };
  if (new URLSearchParams(window.location.search).has("qr")) return <div className="app"><header className="topbar"><div className="brand"><span className="brand-mark"><Compass size={22}/></span><span>City<span>Echo</span><small>Âm vang thành phố</small></span></div></header><main className="qr-page">{qrLoading ? <div className="qr-state"><QrCode size={42}/><h1>Đang mở câu chuyện...</h1><p>CityEcho đang tìm nội dung từ mã QR.</p></div> : qrError ? <div className="qr-state error"><X size={42}/><h1>Không thể mở QR Code</h1><p>{qrError}</p><button className="primary" onClick={() => { window.location.href = "/"; }}>Về trang khám phá</button></div> : qrPoi ? <div className="qr-story"><span className="eyebrow"><QrCode size={14}/> CITYECHO · QR STORY</span><img src={img(qrPoi)} alt={qrPoi.translation.name}/><span className="tag">{qrPoi.category}</span><h1>{qrPoi.translation.name}</h1><p className="qr-description">{qrPoi.translation.description}</p><div className="qr-narration"><Headphones size={22}/><div><b>Thuyết minh tiếng Việt</b><small>Đã mở bằng QR Code · Không cần GPS</small></div><button className="play" onClick={() => toggleNarration(qrPoi, "QR")}>{playing && !paused ? "Ⅱ" : <Play size={17} fill="currentColor"/>}</button></div><button className="primary full" onClick={() => toggleNarration(qrPoi, "QR")}>{playing && !paused ? "Tạm dừng" : paused ? "Tiếp tục" : "Nghe câu chuyện"}</button>{playing && <button className="secondary full stop-button" onClick={() => stopNarration(qrPoi, "QR")}>Kết thúc thuyết minh</button>}{narrationNotice && <p className="narration-notice">{narrationNotice}</p>}<button className="secondary qr-back" onClick={() => { window.location.href = "/"; }}><ArrowLeft size={16}/> Khám phá các địa điểm khác</button></div> : null}</main><footer><span>© 2026 CityEcho</span><span>Khám phá có trách nhiệm · Bảo tồn ký ức địa phương</span></footer></div>;
  return <div className="app">
    <header className="topbar"><div className="brand"><span className="brand-mark"><Compass size={22}/></span><span>City<span>Echo</span><small>Âm vang thành phố</small></span></div><nav><button className={view === "explore" ? "active" : ""} onClick={() => setView("explore")}><Compass size={16}/> Khám phá</button><button className={view === "admin" ? "active" : ""} onClick={() => setView("admin")}><ShieldCheck size={16}/> CMS quản trị</button></nav><button className="menu" onClick={() => setMenuOpen(!menuOpen)}><Menu/></button></header>
    {view === "admin" ? <Admin pois={pois} setPois={setPois} onBack={() => setView("explore")} /> : <main>
      <section className="hero"><div><p className="eyebrow"><Sparkles size={14}/> CITYECHO · SGU COLLECTION</p><h1>Đi chậm lại.<br/><em>Nghe thành phố kể.</em></h1><p className="hero-copy">Khám phá những câu chuyện văn hóa, lịch sử quanh Sài Gòn qua bản đồ tương tác và thuyết minh thông minh.</p><div className="hero-actions"><button className="primary" onClick={locate}><LocateFixed size={17}/> {locating ? "Đang tìm vị trí..." : "Tìm địa điểm quanh tôi"}</button><button className={`secondary gps-toggle ${autoNarration ? "enabled" : ""}`} onClick={() => setAutoNarration((value) => !value)}><Headphones size={16}/> {autoNarration ? "Tắt thuyết minh GPS" : "Bật thuyết minh GPS"}</button><button className="secondary demo-gps" onClick={() => simulateGps()}><MapPin size={16}/> Mô phỏng GPS</button><button className="secondary" onClick={() => document.getElementById("poi-list")?.scrollIntoView({ behavior: "smooth" })}>Xem tất cả POI <ArrowLeft size={16} className="rotate"/></button></div>{autoMessage && <p className="gps-message">{autoMessage}</p>}</div><div className="hero-art"><div className="sun"/><div className="hero-card"><MapPin size={18}/><span>10.7591° N<br/><b>106.6823° E</b></span></div><div className="hero-label">SÀI GÒN<br/><strong>DI SẢN SỐ</strong></div></div></section>
      {nearby.length > 0 && <section className="nearby"><b><LocateFixed size={16}/> {nearby.length} địa điểm gần bạn</b><span>Đã sắp xếp theo ưu tiên và khoảng cách</span><button onClick={() => setNearby([])}><X size={16}/></button></section>}
      <section className="explore" id="poi-list"><div className="section-head"><div><p className="eyebrow">BẢN ĐỒ CÂU CHUYỆN</p><h2>Chọn một điểm để bắt đầu</h2></div><div className="filters"><div className="search"><Search size={17}/><input placeholder="Tìm kiếm địa điểm..." value={query} onChange={(e) => setQuery(e.target.value)}/></div><select value={category} onChange={(e) => setCategory(e.target.value)}>{categories.map((c) => <option key={c} value={c}>{c === "all" ? "Tất cả danh mục" : c}</option>)}</select></div></div><div className="content-grid"><div className="map-panel"><div className="map-grid"/>{visible.map((poi, index) => <button key={poi.id} style={mapPinStyle(poi)} className={`map-pin ${selected?.id === poi.id ? "chosen" : ""}`} onClick={() => setSelected(poi)}><MapPin size={21}/><span>{index + 1}</span></button>)}<div className="map-controls"><button onClick={locate}><LocateFixed size={17}/></button><button onClick={() => setSelected(null)}>＋</button></div><div className="map-legend"><span className="legend-dot"/><span>Điểm đã xuất bản</span></div></div><div className="poi-list">{visible.map((poi) => <article className={`poi-card ${selected?.id === poi.id ? "selected" : ""}`} key={poi.id} onClick={() => setSelected(poi)}><img src={img(poi)} alt=""/><div className="poi-body"><div className="poi-top"><span className="tag">{poi.category}</span><span className="poi-number">0{visible.indexOf(poi) + 1}</span></div><h3>{poi.translation.name}</h3><p>{poi.translation.description}</p><div className="poi-meta"><span><Headphones size={14}/> Thuyết minh</span><span><QrCode size={14}/> QR</span></div></div></article>)}</div></div></section>
      {selected && <aside className="detail-drawer"><button className="close" onClick={() => setSelected(null)}><X/></button><img src={img(selected)} alt=""/><div className="drawer-content"><span className="tag">{selected.category}</span><h2>{selected.translation.name}</h2><p>{selected.translation.description}</p><div className="audio-box"><div className="audio-icon"><Headphones/></div><div><b>Thuyết minh tiếng Việt</b><small>{selected.audio_url ? "Audio file đã tải lên" : "Đọc tự động bằng trình duyệt"}</small></div><button className="play" onClick={() => toggleNarration(selected)}>{playing && !paused ? "Ⅱ" : <Play size={17} fill="currentColor"/>}</button></div><button className="primary full" onClick={() => toggleNarration(selected)}>{playing && !paused ? "Tạm dừng" : paused ? "Tiếp tục" : "Nghe câu chuyện"}</button>{playing && <button className="secondary full stop-button" onClick={() => stopNarration(selected)}>Kết thúc thuyết minh</button>}{narrationNotice && <p className="narration-notice">{narrationNotice}</p>}<div className="coordinates"><MapPin size={16}/> {selected.latitude.toFixed(4)}° N · {selected.longitude.toFixed(4)}° E <span>QR: {selected.qr_code}</span></div>{qrImage && <div className="qr-download"><img src={qrImage} alt={`QR Code ${selected.translation.name}`}/><div><b>QR Code thuyết minh</b><small>Quét để mở không cần GPS</small><a href={qrImage} download={`cityecho-${selected.id}-qr.png`}>Tải QR để in</a></div></div>}</div></aside>}
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
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const filtered = pois.filter((p) => status === "ALL" || p.status === status);
  const request = async (path: string, options: RequestInit = {}) => {
    const headers = new Headers(options.headers || {});
    if (!(options.body instanceof FormData) && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
    if (token) headers.set("Authorization", `Bearer ${token}`);
    const response = await fetch(`${API}${path}`, { ...options, headers });
    if (!response.ok) {
      const payload = await response.json().catch(() => ({ detail: "Thao tác thất bại" }));
      throw new Error(typeof payload.detail === "string" ? payload.detail : "Thao tác thất bại");
    }
    return response.json();
  };
  const uploadMedia = async (poiId: string) => {
    let latest: Poi | null = null;
    if (imageFile) {
      const body = new FormData();
      body.append("file", imageFile);
      latest = await request(`/api/v1/admin/pois/${poiId}/images`, { method: "POST", body });
    }
    if (audioFile) {
      const body = new FormData();
      body.append("file", audioFile);
      latest = await request(`/api/v1/admin/pois/${poiId}/audios`, { method: "POST", body });
    }
    setImageFile(null);
    setAudioFile(null);
    return latest;
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
      const allPois = await fetch(`${API}/api/v1/admin/pois`, { headers: { Authorization: `Bearer ${data.access_token}` } });
      if (allPois.ok) setPois(await allPois.json());
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
    if (!token) return;
    request("/api/v1/admin/pois").then(setPois).catch((error) => setMessage(error instanceof Error ? error.message : "Không thể tải danh sách CMS"));
  }, [token]);
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
      const withMedia = await uploadMedia(created.id);
      setPois((current) => [withMedia || created, ...current]);
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
      const withMedia = await uploadMedia(updated.id);
      setPois((current) => current.map((item) => item.id === updated.id ? (withMedia || updated) : item));
      setEditingPoi(null);
      setMessage("Đã cập nhật POI");
    } catch (error) { setMessage(error instanceof Error ? error.message : "Không thể cập nhật POI"); }
  };
  if (!token) return <main className="admin-page"><button className="back-link" onClick={onBack}><ArrowLeft size={16}/> Quay lại khám phá</button><div className="login-card"><p className="eyebrow"><ShieldCheck size={14}/> CMS CONTROL ROOM</p><h1>Đăng nhập quản trị</h1><p>Sử dụng tài khoản CMS để quản lý và xuất bản POI.</p><form onSubmit={signIn}><label>Email<input value={login.username} onChange={(e) => setLogin({ ...login, username: e.target.value })}/></label><label>Mật khẩu<input type="password" value={login.password} onChange={(e) => setLogin({ ...login, password: e.target.value })}/></label><button className="primary full">Đăng nhập</button></form>{message && <div className="form-message">{message}</div>}</div></main>;
  return <main className="admin-page"><button className="back-link" onClick={onBack}><ArrowLeft size={16}/> Quay lại khám phá</button><div className="admin-heading"><div><p className="eyebrow"><ShieldCheck size={14}/> CMS CONTROL ROOM</p><h1>Quản trị CityEcho</h1><p>Quản lý nội dung, quy trình xuất bản và theo dõi trải nghiệm tham quan.</p></div><div className="admin-heading-actions"><button className="primary" onClick={() => setShowCreate(true)}>＋ Tạo POI mới</button><button className="secondary" onClick={() => { sessionStorage.removeItem("cityecho-token"); setToken(""); }}>Đăng xuất</button></div></div>{message && <div className="form-message">{message}</div>}{showCreate && <div className="create-card"><div className="create-card-head"><h2>Tạo POI bản nháp</h2><button onClick={() => setShowCreate(false)}><X size={18}/></button></div><form className="poi-form" onSubmit={createPoi}><label>Tên địa điểm<input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}/></label><label>Danh mục<input required value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}/></label><label>Mô tả<textarea required value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })}/></label><label>Nội dung thuyết minh<textarea required value={form.narration_text} onChange={(e) => setForm({ ...form, narration_text: e.target.value })}/></label><div className="form-grid"><label>Vĩ độ<input required type="number" step="any" value={form.latitude} onChange={(e) => setForm({ ...form, latitude: e.target.value })}/></label><label>Kinh độ<input required type="number" step="any" value={form.longitude} onChange={(e) => setForm({ ...form, longitude: e.target.value })}/></label><label>Bán kính (m)<input required type="number" min="1" value={form.radius_m} onChange={(e) => setForm({ ...form, radius_m: e.target.value })}/></label><label>Ưu tiên (1-5)<input required type="number" min="1" max="5" value={form.priority} onChange={(e) => setForm({ ...form, priority: e.target.value })}/></label></div><label>URL hình ảnh<input type="url" value={form.image_url} onChange={(e) => setForm({ ...form, image_url: e.target.value })}/></label><label>Tải ảnh (jpg, png, webp)<input type="file" accept="image/*" onChange={(e) => setImageFile(e.target.files?.[0] || null)}/></label><label>Tải audio thuyết minh (mp3, wav, ogg)<input type="file" accept="audio/*" onChange={(e) => setAudioFile(e.target.files?.[0] || null)}/></label><button className="primary" type="submit">Lưu bản nháp</button></form></div>}{editingPoi && <div className="create-card"><div className="create-card-head"><h2>Chỉnh sửa POI</h2><button onClick={() => setEditingPoi(null)}><X size={18}/></button></div><form className="poi-form" onSubmit={updatePoi}><label>Tên địa điểm<input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}/></label><label>Danh mục<input required value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}/></label><label>Mô tả<textarea required value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })}/></label><label>Nội dung thuyết minh<textarea required value={form.narration_text} onChange={(e) => setForm({ ...form, narration_text: e.target.value })}/></label><div className="form-grid"><label>Vĩ độ<input required type="number" step="any" value={form.latitude} onChange={(e) => setForm({ ...form, latitude: e.target.value })}/></label><label>Kinh độ<input required type="number" step="any" value={form.longitude} onChange={(e) => setForm({ ...form, longitude: e.target.value })}/></label><label>Bán kính (m)<input required type="number" min="1" value={form.radius_m} onChange={(e) => setForm({ ...form, radius_m: e.target.value })}/></label><label>Ưu tiên (1-5)<input required type="number" min="1" max="5" value={form.priority} onChange={(e) => setForm({ ...form, priority: e.target.value })}/></label></div><label>URL hình ảnh<input type="url" value={form.image_url} onChange={(e) => setForm({ ...form, image_url: e.target.value })}/></label><label>Tải ảnh (jpg, png, webp)<input type="file" accept="image/*" onChange={(e) => setImageFile(e.target.files?.[0] || null)}/></label><label>Tải audio thuyết minh (mp3, wav, ogg)<input type="file" accept="audio/*" onChange={(e) => setAudioFile(e.target.files?.[0] || null)}/></label><button className="primary" type="submit">Lưu thay đổi</button></form></div>}<div className="stats"><div><small>TỔNG POI</small><b>{pois.length}</b><span>Đang quản lý</span></div><div><small>ĐÃ XUẤT BẢN</small><b>{pois.filter(p => p.status === "PUBLISHED").length}</b><span className="green">Sẵn sàng khám phá</span></div><div><small>CHỜ DUYỆT</small><b>{pois.filter(p => p.status === "PENDING").length}</b><span>Cần xử lý</span></div><div><small>LƯỢT NGHE</small><b>{analytics?.total_plays ?? "—"}</b><span>{analytics ? `${analytics.completion_rate}% hoàn tất` : "Mở thống kê để tải"}</span></div></div><div className="admin-tabs"><button className={tab === "pois" ? "active" : ""} onClick={() => setTab("pois")}>Danh sách POI</button><button className={tab === "analytics" ? "active" : ""} onClick={() => setTab("analytics")}>Thống kê</button></div>{tab === "pois" ? <div className="table-card"><div className="table-toolbar"><b>Địa điểm & nội dung</b><select value={status} onChange={(e) => setStatus(e.target.value as Status | "ALL")}><option value="ALL">Tất cả trạng thái</option><option value="PUBLISHED">Đã xuất bản</option><option value="PENDING">Chờ duyệt</option><option value="DRAFT">Bản nháp</option><option value="NEEDS_REVISION">Cần chỉnh sửa</option></select></div><table><thead><tr><th>ĐỊA ĐIỂM</th><th>DANH MỤC</th><th>TRẠNG THÁI</th><th>ƯU TIÊN</th><th>THAO TÁC</th></tr></thead><tbody>{filtered.map((p) => <tr key={p.id}><td><div className="table-poi"><img src={img(p)} alt=""/><span><b>{p.translation.name}</b><small>{p.id}</small></span></div></td><td>{p.category}</td><td><span className={`status ${p.status.toLowerCase()}`}>{p.status === "PUBLISHED" ? "Đã xuất bản" : p.status === "PENDING" ? "Chờ duyệt" : p.status === "NEEDS_REVISION" ? "Cần chỉnh sửa" : "Bản nháp"}</span></td><td>{"★".repeat(p.priority)}<span className="muted">{"★".repeat(5 - p.priority)}</span>  </td><td><div className="row-actions"><button onClick={() => openEdit(p)}>Chỉnh sửa</button>{p.status === "DRAFT" || p.status === "NEEDS_REVISION" ? <button onClick={() => workflow(p, "submit")}>Gửi duyệt</button> : null}{p.status === "PENDING" ? <><button onClick={() => workflow(p, "approve")}>Xuất bản</button><button onClick={() => workflow(p, "request-revision")}>Yêu cầu sửa</button></> : null}{p.status === "PUBLISHED" ? <button onClick={() => workflow(p, "archive")}>Lưu trữ</button> : null}</div></td></tr>)}</tbody></table></div> : <div className="analytics-card"><h2>Hiệu quả thuyết minh</h2>{analytics ? <><div className="chart">{analytics.top_pois.map((item, i) => <div key={item.poi_id} className="bar-wrap"><div className="bar" style={{ height: `${Math.max(item.plays * 20, 8)}%` }}/><small>{i + 1}</small></div>)}</div><div className="analytics-summary"><b>{analytics.total_plays} <small>lượt bắt đầu</small></b><b>{analytics.completed_plays} <small>hoàn tất</small></b><b>{analytics.completion_rate}% <small>tỷ lệ hoàn tất</small></b></div><div className="source-summary">GPS: {analytics.sources.GPS || 0} · QR: {analytics.sources.QR || 0} · Thủ công: {analytics.sources.MANUAL || 0}</div></> : <p>Đang tải dữ liệu thống kê...</p>}</div>}</main>;
}

createRoot(document.getElementById("root")!).render(<React.StrictMode><App /></React.StrictMode>);
