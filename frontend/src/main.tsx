import React, { useEffect, useMemo, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import QRCode from "qrcode";
import { ArrowLeft, Compass, Headphones, Layers, LocateFixed, MapPin, Menu, Play, QrCode, Search, ShieldCheck, Sparkles, X } from "lucide-react";
import { mapPinStyle, mediaUrl, samplePois, type Poi, type Status } from "./samplePois";
import { categoryLabel, languageLabel, translate } from "./i18n";
import { MapLibreView } from "./components/MapLibreView";
import { LocationPickerMap } from "./components/LocationPickerMap";
import AnalyticsDashboard from "./components/AnalyticsDashboard";
import "./styles.css";

type Analytics = { total_plays: number; completed_plays: number; completion_rate: number; total_duration: number; sources: Record<string, number>; top_pois: { poi_id: string; name: string; plays: number }[]; total_pois?: number; published_pois?: number; draft_pois?: number; pending_pois?: number; };
const API = import.meta.env.VITE_API_URL || "";
const fallback = samplePois;
const img = (poi: Poi) => mediaUrl(API, poi.image_url);
const audioSrc = (poi: Poi) => mediaUrl(API, poi.audio_url || "");

async function loadPois(language: string): Promise<Poi[]> {
  const pageSize = 100;
  const pois: Poi[] = [];
  let total = 0;
  let page = 1;

  try {
    do {
      const params = new URLSearchParams({ page: String(page), limit: String(pageSize), lang: language });
      const response = await fetch(`${API}/api/v1/pois?${params}`);
      if (!response.ok) throw new Error(`Không thể tải POI (HTTP ${response.status})`);

      const result = (await response.json()) as { items: Poi[]; total: number };
      if (!Array.isArray(result.items) || !Number.isInteger(result.total)) {
        throw new Error("Dữ liệu danh sách POI từ máy chủ không hợp lệ");
      }
      if (result.items.length === 0 && pois.length < result.total) {
        throw new Error("Máy chủ trả về trang POI rỗng trước khi tải đủ dữ liệu");
      }

      pois.push(...result.items);
      total = result.total;
      page += 1;
    } while (pois.length < total);

    return pois;
  } catch (error) {
    console.error("Không thể tải toàn bộ POI từ API; đang dùng dữ liệu mẫu.", error);
    return fallback;
  }
}

function getVisitorDeviceId(): string {
  const key = "cityecho-visitor-id";
  const bytes = new Uint8Array(16);
  if (typeof crypto !== "undefined" && typeof crypto.getRandomValues === "function") {
    crypto.getRandomValues(bytes);
  } else {
    for (let index = 0; index < bytes.length; index += 1) {
      bytes[index] = Math.floor(Math.random() * 256);
    }
  }
  bytes[6] = (bytes[6] & 0x0f) | 0x40;
  bytes[8] = (bytes[8] & 0x3f) | 0x80;
  const hex = Array.from(bytes, (value) => value.toString(16).padStart(2, "0")).join("");
  const id = `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
  try {
    const stored = localStorage.getItem(key);
    if (stored && /^[a-f0-9-]{36}$/.test(stored)) return stored;
    localStorage.setItem(key, id);
    return id;
  } catch {
    return id;
  }
}

function getSavedLanguage(): string {
  const requested = new URLSearchParams(window.location.search).get("lang");
  if (requested && /^[a-zA-Z-]{2,10}$/.test(requested)) return requested.toLowerCase();
  try {
    const saved = localStorage.getItem("cityecho-language");
    if (saved) return saved;
  } catch {
    // Continue with the browser's locale when storage is unavailable.
  }
  return navigator.language.toLowerCase().startsWith("vi") ? "vi" : "en";
}

function LanguageSelector({
  language,
  languages,
  onChange,
}: {
  language: string;
  languages: string[];
  onChange: (language: string) => void;
}) {
  return (
    <label className="language-picker">
      <span className="sr-only">{translate(language, "language")}</span>
      <select aria-label={translate(language, "language")} value={language} onChange={(event) => onChange(event.target.value)}>
        {languages.map((code) => <option key={code} value={code}>{languageLabel(code)}</option>)}
      </select>
    </label>
  );
}

function App() {
  const [language, setLanguage] = useState(getSavedLanguage);
  const [availableLanguages, setAvailableLanguages] = useState<string[]>(["vi", "en"]);
  const [pois, setPois] = useState<Poi[]>(fallback);
  const [selected, setSelected] = useState<Poi | null>(null);
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("all");
  const [poiPage, setPoiPage] = useState(1);
  const [locating, setLocating] = useState(false);
  const [userCoords, setUserCoords] = useState<{ latitude: number; longitude: number } | null>(null);
  const [mapType, setMapType] = useState<"maplibre" | "artistic">("maplibre");
  const [nearby, setNearby] = useState<Poi[]>([]);
  const [playing, setPlaying] = useState(false);
  const [paused, setPaused] = useState(false);
  const [activePoiId, setActivePoiId] = useState<string | null>(null);
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
  const currentPoiIdRef = useRef<string | null>(null);
  const cooldownRef = useRef(new Map<string, number>());
  const narrationStartedAtRef = useRef<number | null>(null);
  const narrationElapsedMsRef = useRef(0);
  const text = (key: Parameters<typeof translate>[1], values?: Record<string, string | number>) =>
    translate(language, key, values);
  const narrationLabel = (poi: Poi) => {
    const narrationLanguage = poi.translation.language_code || "vi";
    if (narrationLanguage.toLowerCase().startsWith("vi")) return text("vietnameseNarration");
    if (narrationLanguage.toLowerCase() === "en") return text("englishNarration");
    return text("narrationInLanguage", { language: narrationLanguage.toUpperCase() });
  };
  const changeLanguage = (nextLanguage: string) => {
    const activePoi = qrPoi?.id === activePoiId
      ? qrPoi
      : selected?.id === activePoiId ? selected : pois.find((poi) => poi.id === activePoiId);
    if (activePoi) stopNarration(activePoi);
    setLanguage(nextLanguage);
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has("qr")) {
      urlParams.set("lang", nextLanguage);
      window.history.replaceState(null, "", `${window.location.pathname}?${urlParams}`);
    }
    try {
      localStorage.setItem("cityecho-language", nextLanguage);
    } catch {
      console.warn("Không thể lưu ngôn ngữ đã chọn vào trình duyệt.");
    }
  };
  useEffect(() => {
    loadPois(language).then((loadedPois) => {
      setPois(loadedPois);
      setSelected((current) => current ? loadedPois.find((poi) => poi.id === current.id) ?? current : null);
    });
  }, [language]);
  useEffect(() => {
    fetch(`${API}/api/v1/languages`)
      .then((response) => {
        if (!response.ok) throw new Error(`Không thể tải danh sách ngôn ngữ (HTTP ${response.status})`);
        return response.json() as Promise<string[]>;
      })
      .then((languages) => setAvailableLanguages(Array.from(new Set(["vi", "en", ...languages]))))
      .catch((error) => console.error("Không thể tải danh sách ngôn ngữ.", error));
  }, []);
  useEffect(() => {
    const deviceId = getVisitorDeviceId();
    const params = new URLSearchParams(window.location.search);
    const source = params.has("join") || params.has("qr") ? "QR" : "DIRECT";
    const heartbeat = () => {
      fetch(`${API}/api/v1/visitor-sessions/heartbeat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          device_id: deviceId,
          path: `${window.location.pathname}${window.location.search}`,
          source,
        }),
      }).catch(() => undefined);
    };
    const refreshWhenVisible = () => {
      if (document.visibilityState === "visible") heartbeat();
    };
    heartbeat();
    const intervalId = window.setInterval(heartbeat, 10_000);
    document.addEventListener("visibilitychange", refreshWhenVisible);
    return () => {
      window.clearInterval(intervalId);
      document.removeEventListener("visibilitychange", refreshWhenVisible);
    };
  }, []);
  useEffect(() => {
    const code = new URLSearchParams(window.location.search).get("qr");
    if (!code) return;
    setQrLoading(true);
    setQrError("");
    fetch(`${API}/api/v1/qr/${encodeURIComponent(code)}?lang=${encodeURIComponent(language)}`)
      .then((response) => {
        if (!response.ok) throw new Error("QR Code không hợp lệ hoặc POI chưa xuất bản");
        return response.json();
      })
      .then(setQrPoi)
      .catch((error) => setQrError(error instanceof Error ? error.message : "Không thể mở QR Code"))
      .finally(() => setQrLoading(false));
  }, [language]);
  const categories = useMemo(() => ["all", ...Array.from(new Set(pois.map((p) => p.category)))], [pois]);
  const visible = pois.filter((p) => (category === "all" || p.category === category) && `${p.translation.name} ${p.translation.description}`.toLowerCase().includes(query.toLowerCase()));
  const poisPerPage = 12;
  const totalPoiPages = Math.max(1, Math.ceil(visible.length / poisPerPage));
  const currentPoiPage = Math.min(poiPage, totalPoiPages);
  const pagedVisible = visible.slice((currentPoiPage - 1) * poisPerPage, currentPoiPage * poisPerPage);
  useEffect(() => {
    setPoiPage(1);
  }, [query, category, language]);
  useEffect(() => {
    if (!selected) {
      setQrImage("");
      return;
    }
    const url = `${window.location.origin}/?qr=${encodeURIComponent(selected.qr_code)}&lang=${encodeURIComponent(language)}`;
    QRCode.toDataURL(url, { width: 220, margin: 2, color: { dark: "#102a43", light: "#ffffff" } })
      .then(setQrImage)
      .catch(() => setQrImage(""));
  }, [selected, language]);
  const recordNarration = (poi: Poi, source: string, eventType: "start" | "finish", durationSeconds = 0, completed = false) => {
    fetch(`${API}/api/v1/narration-events`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ poi_id: poi.id, source, event_type: eventType, duration_seconds: durationSeconds, completed, session_id: sessionStorage.getItem("cityecho-session") || "web-demo" }),
    }).catch(() => undefined);
  };
  const startNarrationTimer = () => {
    narrationStartedAtRef.current = performance.now();
  };
  const pauseNarrationTimer = () => {
    if (narrationStartedAtRef.current !== null) {
      narrationElapsedMsRef.current += performance.now() - narrationStartedAtRef.current;
      narrationStartedAtRef.current = null;
    }
  };
  const finishNarration = (poi: Poi, source: string, completed: boolean) => {
    pauseNarrationTimer();
    const durationSeconds = Math.floor(narrationElapsedMsRef.current / 1000);
    narrationElapsedMsRef.current = 0;
    recordNarration(poi, source, "finish", durationSeconds, completed);
  };
  const playNarration = async (poi: Poi, nextPlaying: boolean, source = "MANUAL") => {
    if (!nextPlaying) {
      pauseNarrationTimer();
      audioRef.current?.pause();
      window.speechSynthesis.pause();
      setPlaying(false);
      playingRef.current = false;
      setPaused(true);
      return;
    }
    if (paused && activePoiId === poi.id) {
      startNarrationTimer();
      if (poi.audio_url && audioRef.current) {
        audioRef.current.play().catch(() => undefined);
      } else {
        window.speechSynthesis.resume();
      }
      setPlaying(true);
      playingRef.current = true;
      setPaused(false);
      return;
    }
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
    }
    if (speechRef.current) {
      speechRef.current.onend = null;
      speechRef.current.onerror = null;
      speechRef.current = null;
    }
    window.speechSynthesis.cancel();
    currentPoiIdRef.current = poi.id;
    setActivePoiId(poi.id);
    setPlaying(true);
    playingRef.current = true;
    setPaused(false);
    narrationElapsedMsRef.current = 0;
    startNarrationTimer();
    recordNarration(poi, source, "start");
    setNarrationNotice("");
    if (poi.audio_url && (poi.translation.language_code || "vi").toLowerCase().startsWith("vi")) {
      const audio = audioRef.current || new Audio();
      audioRef.current = audio;
      audio.src = audioSrc(poi);
      audio.currentTime = 0;
      audio.onended = () => {
        setPlaying(false);
        setPaused(false);
        setActivePoiId(null);
        currentPoiIdRef.current = null;
        finishNarration(poi, source, true);
      };
      try {
        await audio.play();
      } catch {
        setNarrationNotice(text("audioAutoplayBlocked"));
        setPlaying(false);
        setPaused(false);
        setActivePoiId(null);
        currentPoiIdRef.current = null;
      }
      return;
    }
    if (!("speechSynthesis" in window)) {
      setPlaying(false);
      setPaused(false);
      setActivePoiId(null);
      currentPoiIdRef.current = null;
      setNarrationNotice(text("unsupportedSpeech"));
      return;
    }
    const utterance = new SpeechSynthesisUtterance(poi.translation.narration_text);
    speechRef.current = utterance;
    const narrationLanguage = poi.translation.language_code || language;
    utterance.lang = narrationLanguage.toLowerCase().startsWith("vi")
      ? "vi-VN"
      : narrationLanguage.toLowerCase() === "en" ? "en-US" : narrationLanguage;
    utterance.rate = 0.95;
    utterance.onend = () => {
      if (currentPoiIdRef.current === poi.id) {
        setPlaying(false);
        setPaused(false);
        setActivePoiId(null);
        currentPoiIdRef.current = null;
        speechRef.current = null;
        finishNarration(poi, source, true);
      }
    };
    utterance.onerror = (e: SpeechSynthesisErrorEvent) => {
      if (e.error === "canceled" || e.error === "interrupted") return;
      if (currentPoiIdRef.current === poi.id) {
        setPlaying(false);
        setPaused(false);
        setActivePoiId(null);
        currentPoiIdRef.current = null;
        setNarrationNotice(text("speechUnavailable"));
      }
    };
    setTimeout(() => {
      if (currentPoiIdRef.current === poi.id) {
        window.speechSynthesis.speak(utterance);
      }
    }, 40);
  };
  const stopNarration = (poi: Poi, source = "MANUAL") => {
    pauseNarrationTimer();
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
    }
    if (speechRef.current) {
      speechRef.current.onend = null;
      speechRef.current.onerror = null;
      speechRef.current = null;
    }
    window.speechSynthesis.cancel();
    currentPoiIdRef.current = null;
    setActivePoiId(null);
    setPlaying(false);
    setPaused(false);
    finishNarration(poi, source, false);
  };
  const toggleNarration = (poi: Poi, source = "MANUAL") => {
    if (playing && !paused && activePoiId === poi.id) return playNarration(poi, false, source);
    if (paused && activePoiId === poi.id) return playNarration(poi, true, source);
    return playNarration(poi, true, source);
  };
  useEffect(() => {
    playingRef.current = playing;
  }, [playing]);
  useEffect(() => {
    if (!autoNarration) return;
    if (!navigator.geolocation) {
      setAutoMessage(text("gpsUnsupported"));
      setAutoNarration(false);
      return;
    }
    setAutoMessage(text("gpsTracking"));
    const watchId = navigator.geolocation.watchPosition(async ({ coords }) => {
      setUserCoords({ latitude: coords.latitude, longitude: coords.longitude });
      try {
        const response = await fetch(`${API}/api/v1/pois/nearby?lat=${coords.latitude}&lng=${coords.longitude}&lang=${encodeURIComponent(language)}`);
        if (!response.ok) throw new Error(text("gpsLoadError"));
        const candidates: Poi[] = await response.json();
        const now = Date.now();
        const candidate = candidates.find((poi) => (poi.distance_m ?? Infinity) <= poi.radius_m && now - (cooldownRef.current.get(poi.id) || 0) >= 5 * 60 * 1000);
        if (!candidate || playingRef.current) return;
        cooldownRef.current.set(candidate.id, now);
        setSelected(candidate);
        setAutoMessage(text("gpsAutoPlay", { name: candidate.translation.name }));
        await playNarration(candidate, true, "GPS");
      } catch (error) {
        setAutoMessage(error instanceof Error ? error.message : text("geofenceUnavailable"));
      }
    }, () => setAutoMessage(text("gpsNoPermission")), { enableHighAccuracy: true, maximumAge: 10000, timeout: 10000 });
    return () => navigator.geolocation.clearWatch(watchId);
  }, [autoNarration, language]);
  const locate = () => {
    setLocating(true);
    setAutoMessage("");
    navigator.geolocation?.getCurrentPosition(async ({ coords }) => {
      setUserCoords({ latitude: coords.latitude, longitude: coords.longitude });
      try {
        const res = await fetch(`${API}/api/v1/pois/nearby?lat=${coords.latitude}&lng=${coords.longitude}&max_distance_m=50000&lang=${encodeURIComponent(language)}`);
        if (res.ok) {
          const nearPois: Poi[] = await res.json();
          setNearby(nearPois);
          const distanceMap = new Map<string, number>(nearPois.map(p => [p.id, p.distance_m ?? 0]));
          setPois(current => {
            const updated = current.map(p => ({
              ...p,
              distance_m: distanceMap.get(p.id)
            }));
            return [...updated].sort((a, b) => {
              if (a.distance_m !== undefined && b.distance_m !== undefined) {
                return a.distance_m - b.distance_m;
              }
              return a.distance_m !== undefined ? -1 : 1;
            });
          });
          if (nearPois.length > 0) {
            const closest = nearPois[0];
            const distFormatted = closest.distance_m !== undefined
              ? (closest.distance_m < 1000 ? `${Math.round(closest.distance_m)}m` : `${(closest.distance_m / 1000).toFixed(1)}km`)
              : "";
            setAutoMessage(text("gpsFoundNearest", { count: nearPois.length, name: closest.translation.name, distance: distFormatted }));
            setSelected(closest);
          } else {
            setAutoMessage(text("noNearby"));
          }
          setTimeout(() => {
            document.getElementById("poi-list")?.scrollIntoView({ behavior: "smooth" });
          }, 120);
        } else {
          setNearby([]);
          setAutoMessage(text("nearbyUnavailable"));
        }
      } catch {
        setNearby([]);
        setAutoMessage(text("locateError"));
      } finally {
        setLocating(false);
      }
    }, (err) => {
      setLocating(false);
      setAutoMessage(text("gpsError", { message: err.message || text("gpsNoPermission") }));
    }, { enableHighAccuracy: true, timeout: 10000 });
  };
  const simulateGps = async (poiId = "sgu-main") => {
    const poi = pois.find((item) => item.id === poiId) || pois[0];
    if (!poi) return;
    setLocating(true);
    setUserCoords({ latitude: poi.latitude, longitude: poi.longitude });
    try {
      const response = await fetch(`${API}/api/v1/geofence/evaluate?lat=${poi.latitude}&lng=${poi.longitude}&lang=${encodeURIComponent(language)}`);
      if (!response.ok) throw new Error(text("gpsSimulationError"));
      const result = await response.json();
      setNearby(result.candidates || []);
      const candidate = result.candidate as Poi | null;
      if (candidate) {
        setSelected(candidate);
        setAutoMessage(text("gpsSimulationActive", { name: candidate.translation.name }));
        await playNarration(candidate, true, "GPS");
      } else {
        setAutoMessage(text("gpsSimulationOutside"));
      }
    } catch (error) {
      setAutoMessage(error instanceof Error ? error.message : text("gpsSimulationError"));
    } finally {
      setLocating(false);
    }
  };
  if (new URLSearchParams(window.location.search).has("qr")) {
    const isQrPlaying = qrPoi ? activePoiId === qrPoi.id && playing && !paused : false;
    const isQrPaused = qrPoi ? activePoiId === qrPoi.id && paused : false;
    const isQrActive = qrPoi ? activePoiId === qrPoi.id && (playing || paused) : false;
    return (
      <div className="app">
        <header className="topbar">
          <div className="brand"><span className="brand-mark"><Compass size={22} /></span><span>City<span>Echo</span><small>{text("tagline")}</small></span></div>
          <LanguageSelector language={language} languages={availableLanguages} onChange={changeLanguage} />
        </header>
        <main className="qr-page">
          {qrLoading ? <div className="qr-state"><QrCode size={42} /><h1>{text("qrLoading")}</h1><p>{text("qrLoadingDescription")}</p></div>
            : qrError ? <div className="qr-state error"><X size={42} /><h1>{text("qrOpenFailed")}</h1><p>{qrError}</p><button className="primary" onClick={() => { window.location.href = "/"; }}>{text("backToExplore")}</button></div>
              : qrPoi ? <div className="qr-story">
                <span className="eyebrow"><QrCode size={14} /> {text("qrStory")}</span>
                <img src={img(qrPoi)} alt={qrPoi.translation.name} />
                <span className="tag">{qrPoi.category}</span>
                <h1>{qrPoi.translation.name}</h1>
                <p className="qr-description">{qrPoi.translation.description}</p>
                <div className="qr-narration"><Headphones size={22} /><div><b>{narrationLabel(qrPoi)}</b><small>{text("qrOpened")}</small></div><button className="play" onClick={() => toggleNarration(qrPoi, "QR")}>{isQrPlaying ? "Ⅱ" : <Play size={17} fill="currentColor" />}</button></div>
                <button className="primary full" onClick={() => toggleNarration(qrPoi, "QR")}>{isQrPlaying ? text("pause") : isQrPaused ? text("resume") : text("listenStory")}</button>
                {isQrActive && <button className="secondary full stop-button" onClick={() => stopNarration(qrPoi, "QR")}>{text("stopNarration")}</button>}
                {narrationNotice && <p className="narration-notice">{narrationNotice}</p>}
                <button className="secondary qr-back" onClick={() => { window.location.href = "/"; }}><ArrowLeft size={16} /> {text("otherPlaces")}</button>
              </div> : null}
        </main>
        <footer><span>© 2026 CityEcho</span><span>{text("footer")}</span></footer>
      </div>
    );
  }
  const isSelectedPlaying = selected ? activePoiId === selected.id && playing && !paused : false;
  const isSelectedPaused = selected ? activePoiId === selected.id && paused : false;
  const isSelectedActive = selected ? activePoiId === selected.id && (playing || paused) : false;
  return (
    <div className="app">
      <header className="topbar">
        <div className="brand"><span className="brand-mark"><Compass size={22} /></span><span>City<span>Echo</span><small>{text("tagline")}</small></span></div>
        <nav>
          <button className={view === "explore" ? "active" : ""} onClick={() => setView("explore")}><Compass size={16} /> {text("explore")}</button>
          <button className={view === "admin" ? "active" : ""} onClick={() => setView("admin")}><ShieldCheck size={16} /> {text("admin")}</button>
        </nav>
        <LanguageSelector language={language} languages={availableLanguages} onChange={changeLanguage} />
        {view === "admin" && <span className="cms-language-hint">{text("cmsLanguageHint")}</span>}
        <button className="menu" onClick={() => setMenuOpen(!menuOpen)}><Menu /></button>
      </header>
      {view === "admin" ? <Admin pois={pois} setPois={setPois} onBack={() => setView("explore")} language={language} /> : <main>
        <section className="hero">
          <div>
            <p className="eyebrow"><Sparkles size={14} /> CITYECHO · SGU COLLECTION</p>
            <h1>{text("heroTitle")}<br /><em>{text("heroTitleSecond")}</em></h1>
            <p className="hero-copy">{text("heroCopy")}</p>
            <div className="hero-actions">
              <button className="primary" onClick={locate}><LocateFixed size={17} /> {locating ? text("findingLocation") : text("findNearby")}</button>
              <button className={`secondary gps-toggle ${autoNarration ? "enabled" : ""}`} onClick={() => setAutoNarration((value) => !value)}><Headphones size={16} /> {autoNarration ? text("disableGpsNarration") : text("enableGpsNarration")}</button>
              <button className="secondary demo-gps" onClick={() => simulateGps()}><MapPin size={16} /> {text("simulateGps")}</button>
              <button className="secondary" onClick={() => document.getElementById("poi-list")?.scrollIntoView({ behavior: "smooth" })}>{text("allPois")} <ArrowLeft size={16} className="rotate" /></button>
            </div>
            {autoMessage && <p className="gps-message">{autoMessage}</p>}
          </div>
          <div className="hero-art"><div className="sun" /><div className="hero-card"><MapPin size={18} /><span>10.7591° N<br /><b>106.6823° E</b></span></div><div className="hero-label">SÀI GÒN<br /><strong>DI SẢN SỐ</strong></div></div>
        </section>
        {nearby.length > 0 && <section className="nearby"><b><LocateFixed size={16} /> {text("nearbyPois", { count: nearby.length })}</b><span>{text("nearbySorted")}</span><button onClick={() => setNearby([])}><X size={16} /></button></section>}
        <section className="explore" id="poi-list">
          <div className="section-head">
            <div><p className="eyebrow">{text("storyMap")}</p><h2>{text("choosePlace")}</h2></div>
            <div className="filters">
              <div className="search"><Search size={17} /><input placeholder={text("searchPlaceholder")} value={query} onChange={(event) => setQuery(event.target.value)} /></div>
              <select value={category} onChange={(event) => setCategory(event.target.value)}>{categories.map((item) => <option key={item} value={item}>{item === "all" ? text("allCategories") : categoryLabel(item, language)}</option>)}</select>
              <button type="button" className={`maplibre-toggle-view ${mapType === "maplibre" ? "active" : ""}`} onClick={() => setMapType((mode) => mode === "maplibre" ? "artistic" : "maplibre")} title={text("mapMode")}><Layers size={14} /> {mapType === "maplibre" ? "MapLibre" : text("artisticMap")}</button>
            </div>
          </div>
          <div className="content-grid">
            <div className="map-panel">{mapType === "maplibre" ? <MapLibreView pois={visible} selected={selected} onSelectPoi={setSelected} userCoords={userCoords} onLocateUser={locate} /> : <>
              <div className="map-grid" />
              {visible.map((poi, index) => <button key={poi.id} style={mapPinStyle(poi)} className={`map-pin ${selected?.id === poi.id ? "chosen" : ""}`} onClick={() => setSelected(poi)}><MapPin size={21} /><span>{index + 1}</span></button>)}
              <div className="map-controls"><button onClick={locate}><LocateFixed size={17} /></button><button onClick={() => setSelected(null)}>＋</button></div>
              <div className="map-legend"><span className="legend-dot" /><span>{text("publishedPoint")}</span></div>
            </>}</div>
            <div className="poi-list">{pagedVisible.map((poi, index) => <article className={`poi-card ${selected?.id === poi.id ? "selected" : ""}`} key={poi.id} onClick={() => setSelected(poi)}>
              <img src={img(poi)} alt="" />
              <div className="poi-body"><div className="poi-top"><span className="tag">{categoryLabel(poi.category, language)}</span><span className="poi-number">0{index + 1}</span></div><h3>{poi.translation.name}</h3><p>{poi.translation.description}</p>
                <div className="poi-meta"><span><Headphones size={14} /> {text("narration")}</span><span><QrCode size={14} /> QR</span>{poi.distance_m !== undefined && <span className="poi-distance-badge"><MapPin size={12} /> {text("distance")} {poi.distance_m < 1000 ? `${Math.round(poi.distance_m)}m` : `${(poi.distance_m / 1000).toFixed(1)}km`}</span>}</div>
              </div>
            </article>)}</div>
          </div>
          <div className="poi-pagination" aria-label="Pagination">
            <button type="button" className="secondary" disabled={currentPoiPage === 1} onClick={() => setPoiPage((page) => Math.max(1, page - 1))}>{text("previousPage")}</button>
            <span>{text("pageOf", { page: currentPoiPage, total: totalPoiPages })}</span>
            <button type="button" className="secondary" disabled={currentPoiPage === totalPoiPages} onClick={() => setPoiPage((page) => Math.min(totalPoiPages, page + 1))}>{text("nextPage")}</button>
          </div>
        </section>
        {selected && <aside className="detail-drawer">
          <button className="close" onClick={() => setSelected(null)}><X /></button><img src={img(selected)} alt="" />
          <div className="drawer-content"><span className="tag">{categoryLabel(selected.category, language)}</span><h2>{selected.translation.name}</h2><p>{selected.translation.description}</p>
            <div className="audio-box"><div className="audio-icon"><Headphones /></div><div><b>{narrationLabel(selected)}</b><small>{selected.audio_url && (selected.translation.language_code || "vi").toLowerCase().startsWith("vi") ? text("uploadedAudio") : text("browserSpeech")}</small></div><button className="play" onClick={() => toggleNarration(selected)}>{isSelectedPlaying ? "Ⅱ" : <Play size={17} fill="currentColor" />}</button></div>
            <button className="primary full" onClick={() => toggleNarration(selected)}>{isSelectedPlaying ? text("pause") : isSelectedPaused ? text("resume") : text("listenStory")}</button>
            {isSelectedActive && <button className="secondary full stop-button" onClick={() => stopNarration(selected)}>{text("stopNarration")}</button>}
            {narrationNotice && <p className="narration-notice">{narrationNotice}</p>}
            <div className="coordinates"><MapPin size={16} /> {selected.latitude.toFixed(4)}° N · {selected.longitude.toFixed(4)}° E <span>QR: {selected.qr_code}</span></div>
            {qrImage && <div className="qr-download"><img src={qrImage} alt={`QR Code ${selected.translation.name}`} /><div><b>{text("qrNarration")}</b><small>{text("scanWithoutGps")}</small><a href={qrImage} download={`cityecho-${selected.id}-qr.png`}>{text("downloadQr")}</a></div></div>}
          </div>
        </aside>}
      </main>}
      {menuOpen && <div className="mobile-menu"><button onClick={() => { setView("explore"); setMenuOpen(false); }}>{text("explore")}</button><button onClick={() => { setView("admin"); setMenuOpen(false); }}>{text("admin")}</button></div>}
      <footer><span>© 2026 CityEcho</span><span>{text("footer")}</span></footer>
    </div>
  );
}

function Admin({ pois, setPois, onBack, language }: { pois: Poi[]; setPois: React.Dispatch<React.SetStateAction<Poi[]>>; onBack: () => void; language: string }) {
  const [tab, setTab] = useState<"pois" | "analytics">("pois");
  const [status, setStatus] = useState<Status | "ALL">("ALL");
  const [token, setToken] = useState(() => sessionStorage.getItem("cityecho-token") || "");
  const [currentUser, setCurrentUser] = useState<{ email: string; role: string; full_name: string } | null>(() => {
    try {
      const saved = sessionStorage.getItem("cityecho-user");
      return saved ? JSON.parse(saved) : null;
    } catch { return null; }
  });
  const [login, setLogin] = useState({ username: "admin@cityecho.vn", password: "admin123" });
  const [message, setMessage] = useState("");
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [editingPoi, setEditingPoi] = useState<Poi | null>(null);
  const [translationLanguage, setTranslationLanguage] = useState("vi");
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
      sessionStorage.setItem("cityecho-user", JSON.stringify(data.user));
      setToken(data.access_token);
      setCurrentUser(data.user);
      setMessage(`Xin chào ${data.user.full_name} (${data.user.role === "admin" ? "Quản trị viên" : "Biên tập viên"})`);
      const allPois = await fetch(`${API}/api/v1/admin/pois`, { headers: { Authorization: `Bearer ${data.access_token}` } });
      if (allPois.ok) setPois(await allPois.json());
    } catch (error) { setMessage(error instanceof Error ? error.message : "Đăng nhập thất bại"); }
  };
  const workflow = async (poi: Poi, action: "submit" | "approve" | "request-revision" | "archive") => {
    try {
      const updated = await request(`/api/v1/admin/pois/${poi.id}/${action}`, { method: "POST" });
      setPois((current) => current.map((item) => item.id === poi.id ? updated : item));
      const actionLabels: Record<string, string> = { submit: "Đã gửi duyệt POI", approve: "Đã xuất bản POI thành công", "request-revision": "Đã yêu cầu chỉnh sửa", archive: "Đã lưu trữ POI" };
      setMessage(actionLabels[action] || "Đã cập nhật trạng thái POI");
    } catch (error) { setMessage(error instanceof Error ? error.message : "Không thể cập nhật"); }
  };
  useEffect(() => {
    if (!token) return;
    request("/api/v1/admin/pois").then(setPois).catch((error) => setMessage(error instanceof Error ? error.message : "Không thể tải danh sách CMS"));
    if (!currentUser) {
      request("/api/v1/auth/me").then((user) => { setCurrentUser(user); sessionStorage.setItem("cityecho-user", JSON.stringify(user)); }).catch(() => undefined);
    }
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
          translation: { language_code: translationLanguage, name: form.name, description: form.description, narration_text: form.narration_text },
        }),
      });
      const withMedia = await uploadMedia(created.id);
      setPois((current) => [withMedia || created, ...current]);
      setShowCreate(false);
      setMessage("Đã tạo POI bản nháp. Hãy bấm 'Xuất bản' hoặc 'Gửi duyệt'.");
      setTranslationLanguage("vi");
      setForm({ name: "", description: "", narration_text: "", category: "historical", latitude: "10.7591", longitude: "106.6823", radius_m: "40", priority: "3", image_url: "" });
    } catch (error) { setMessage(error instanceof Error ? error.message : "Không thể tạo POI"); }
  };
  const openEdit = (poi: Poi) => {
    setShowCreate(false);
    setEditingPoi(poi);
    const selectedTranslation = poi.translations?.find((item) => (item.language_code ?? "vi").toLowerCase() === language.toLowerCase());
    setTranslationLanguage(language);
    setForm({ name: selectedTranslation?.name ?? "", description: selectedTranslation?.description ?? "", narration_text: selectedTranslation?.narration_text ?? "", category: poi.category, latitude: String(poi.latitude), longitude: String(poi.longitude), radius_m: String(poi.radius_m), priority: String(poi.priority), image_url: poi.image_url });
    setTimeout(() => {
      document.getElementById("poi-edit-card")?.scrollIntoView({ behavior: "smooth", block: "center" });
    }, 50);
  };
  const openCreate = () => {
    setEditingPoi(null);
    setTranslationLanguage("vi");
    setShowCreate(true);
    setTimeout(() => {
      document.getElementById("poi-create-card")?.scrollIntoView({ behavior: "smooth", block: "center" });
    }, 50);
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
          translation: { language_code: translationLanguage, name: form.name, description: form.description, narration_text: form.narration_text },
        }),
      });
      const withMedia = await uploadMedia(updated.id);
      setPois((current) => current.map((item) => item.id === updated.id ? (withMedia || updated) : item));
      setEditingPoi(null);
      setMessage("Đã cập nhật POI thành công");
    } catch (error) { setMessage(error instanceof Error ? error.message : "Không thể cập nhật POI"); }
  };
  if (!token) return <main className="admin-page"><button className="back-link" onClick={onBack}><ArrowLeft size={16}/> Quay lại khám phá</button><div className="login-card"><p className="eyebrow"><ShieldCheck size={14}/> CMS CONTROL ROOM</p><h1>Đăng nhập quản trị</h1><p>Sử dụng tài khoản CMS để quản lý và xuất bản POI.</p><form onSubmit={signIn}><label>Email<input value={login.username} onChange={(e) => setLogin({ ...login, username: e.target.value })}/></label><label>Mật khẩu<input type="password" value={login.password} onChange={(e) => setLogin({ ...login, password: e.target.value })}/></label><button className="primary full">Đăng nhập</button></form>{message && <div className="form-message">{message}</div>}</div></main>;
  return <main className="admin-page"><button className="back-link" onClick={onBack}><ArrowLeft size={16}/> Quay lại khám phá</button><div className="admin-heading"><div><p className="eyebrow"><ShieldCheck size={14}/> CMS CONTROL ROOM</p><h1>Quản trị CityEcho</h1><p>Quản lý nội dung, quy trình xuất bản và theo dõi trải nghiệm tham quan ({currentUser?.role === "admin" ? "Vai trò: Quản trị viên" : "Vai trò: Biên tập viên"}).</p></div><div className="admin-heading-actions"><button className="primary" onClick={openCreate}>＋ Tạo POI mới</button><button className="secondary" onClick={() => { sessionStorage.removeItem("cityecho-token"); sessionStorage.removeItem("cityecho-user"); setToken(""); setCurrentUser(null); }}>Đăng xuất</button></div></div>{message && <div className={`form-message fixed-toast ${message.includes("thất bại") || message.includes("lỗi") || message.includes("tối thiểu") ? "error-toast" : "success-toast"}`}><span>{message}</span><button type="button" onClick={() => setMessage("")} style={{ marginLeft: "12px", background: "none", border: "none", cursor: "pointer", fontWeight: "bold", fontSize: "16px", color: "inherit" }}>×</button></div>}{showCreate && <div className="create-card" id="poi-create-card"><div className="create-card-head"><h2>Tạo POI bản nháp</h2><button onClick={() => setShowCreate(false)}><X size={18}/></button></div><form className="poi-form" onSubmit={createPoi}><label>Tên địa điểm<input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}/></label><label>Danh mục<input required value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}/></label><label>Mô tả<textarea required value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })}/></label><label>Nội dung thuyết minh (tối thiểu 10 ký tự)<textarea required minLength={10} placeholder="Nhập ít nhất 10 ký tự thuyết minh..." value={form.narration_text} onChange={(e) => setForm({ ...form, narration_text: e.target.value })}/></label><label style={{ display: "block", marginTop: "10px", marginBottom: "2px", fontWeight: "700", color: "#607274", fontSize: "12px" }}>📍 Chọn vị trí trên bản đồ (hoặc tìm tên địa điểm):</label><LocationPickerMap latitude={Number(form.latitude) || 10.7591} longitude={Number(form.longitude) || 106.6823} radius_m={Number(form.radius_m) || 40} onChange={({ latitude, longitude }) => setForm((f) => ({ ...f, latitude: String(latitude), longitude: String(longitude) }))}/><div className="form-grid"><label>Vĩ độ<input required type="number" step="any" value={form.latitude} onChange={(e) => setForm({ ...form, latitude: e.target.value })}/></label><label>Kinh độ<input required type="number" step="any" value={form.longitude} onChange={(e) => setForm({ ...form, longitude: e.target.value })}/></label><label>Bán kính (m)<input required type="number" min="1" value={form.radius_m} onChange={(e) => setForm({ ...form, radius_m: e.target.value })}/></label><label>Ưu tiên (1-5)<input required type="number" min="1" max="5" value={form.priority} onChange={(e) => setForm({ ...form, priority: e.target.value })}/></label></div><label>URL hình ảnh<input type="url" value={form.image_url} onChange={(e) => setForm({ ...form, image_url: e.target.value })}/></label><label>Tải ảnh (jpg, png, webp)<input type="file" accept="image/*" onChange={(e) => setImageFile(e.target.files?.[0] || null)}/></label><label>Tải audio thuyết minh (mp3, wav, ogg)<input type="file" accept="audio/*" onChange={(e) => setAudioFile(e.target.files?.[0] || null)}/></label><button className="primary" type="submit">Lưu bản nháp</button></form></div>}{editingPoi && <div className="create-card" id="poi-edit-card"><div className="create-card-head"><h2>Chỉnh sửa POI ({editingPoi.id})</h2><button onClick={() => setEditingPoi(null)}><X size={18}/></button></div><form className="poi-form" onSubmit={updatePoi}><label>Tên địa điểm<input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}/></label><label>Danh mục<input required value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}/></label><label>Mô tả<textarea required value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })}/></label><label>Nội dung thuyết minh (tối thiểu 10 ký tự)<textarea required minLength={10} placeholder="Nhập ít nhất 10 ký tự thuyết minh..." value={form.narration_text} onChange={(e) => setForm({ ...form, narration_text: e.target.value })}/></label><label style={{ display: "block", marginTop: "10px", marginBottom: "2px", fontWeight: "700", color: "#607274", fontSize: "12px" }}>📍 Chọn vị trí trên bản đồ (hoặc tìm tên địa điểm):</label><LocationPickerMap latitude={Number(form.latitude) || 10.7591} longitude={Number(form.longitude) || 106.6823} radius_m={Number(form.radius_m) || 40} onChange={({ latitude, longitude }) => setForm((f) => ({ ...f, latitude: String(latitude), longitude: String(longitude) }))}/><div className="form-grid"><label>Vĩ độ<input required type="number" step="any" value={form.latitude} onChange={(e) => setForm({ ...form, latitude: e.target.value })}/></label><label>Kinh độ<input required type="number" step="any" value={form.longitude} onChange={(e) => setForm({ ...form, longitude: e.target.value })}/></label><label>Bán kính (m)<input required type="number" min="1" value={form.radius_m} onChange={(e) => setForm({ ...form, radius_m: e.target.value })}/></label><label>Ưu tiên (1-5)<input required type="number" min="1" max="5" value={form.priority} onChange={(e) => setForm({ ...form, priority: e.target.value })}/></label></div><label>URL hình ảnh<input type="url" value={form.image_url} onChange={(e) => setForm({ ...form, image_url: e.target.value })}/></label><label>Tải ảnh (jpg, png, webp)<input type="file" accept="image/*" onChange={(e) => setImageFile(e.target.files?.[0] || null)}/></label><label>Tải audio thuyết minh (mp3, wav, ogg)<input type="file" accept="audio/*" onChange={(e) => setAudioFile(e.target.files?.[0] || null)}/></label><button className="primary" type="submit">Lưu thay đổi</button></form></div>}<div className="stats"><div><small>TỔNG POI</small><b>{pois.length}</b><span>Đang quản lý</span></div><div><small>ĐÃ XUẤT BẢN</small><b>{pois.filter(p => p.status === "PUBLISHED").length}</b><span className="green">Sẵn sàng khám phá</span></div><div><small>CHỜ DUYỆT</small><b>{pois.filter(p => p.status === "PENDING").length}</b><span>Cần xử lý</span></div><div><small>LƯỢT NGHE</small><b>{analytics?.total_plays ?? "—"}</b><span>{analytics ? `${analytics.completion_rate}% hoàn tất` : "Mở thống kê để tải"}</span></div></div><div className="admin-tabs"><button className={tab === "pois" ? "active" : ""} onClick={() => setTab("pois")}>Danh sách POI</button><button className={tab === "analytics" ? "active" : ""} onClick={() => setTab("analytics")}>Thống kê Recharts</button></div>{tab === "pois" ? <div className="table-card"><div className="table-toolbar"><b>Địa điểm & nội dung</b><select value={status} onChange={(e) => setStatus(e.target.value as Status | "ALL")}><option value="ALL">Tất cả trạng thái</option><option value="PUBLISHED">Đã xuất bản</option><option value="PENDING">Chờ duyệt</option><option value="DRAFT">Bản nháp</option><option value="NEEDS_REVISION">Cần chỉnh sửa</option></select></div><table><thead><tr><th>ĐỊA ĐIỂM</th><th>DANH MỤC</th><th>TRẠNG THÁI</th><th>ƯU TIÊN</th><th>THAO TÁC</th></tr></thead><tbody>{filtered.map((p) => <tr key={p.id}><td><div className="table-poi"><img src={img(p)} alt=""/><span><b>{p.translation.name}</b><small>{p.id}</small></span></div></td><td>{p.category}</td><td><span className={`status ${p.status.toLowerCase()}`}>{p.status === "PUBLISHED" ? "Đã xuất bản" : p.status === "PENDING" ? "Chờ duyệt" : p.status === "NEEDS_REVISION" ? "Cần chỉnh sửa" : "Bản nháp"}</span></td><td>{"★".repeat(p.priority)}<span className="muted">{"★".repeat(5 - p.priority)}</span></td><td><div className="row-actions"><button onClick={() => openEdit(p)}>Chỉnh sửa</button>{currentUser?.role === "admin" ? <>{p.status !== "PUBLISHED" ? <button className="btn-approve" onClick={() => workflow(p, "approve")}>Xuất bản</button> : <button className="btn-archive" onClick={() => workflow(p, "archive")}>Lưu trữ</button>}{(p.status === "DRAFT" || p.status === "NEEDS_REVISION") && <button onClick={() => workflow(p, "submit")}>Gửi duyệt</button>}{p.status === "PENDING" && <button className="btn-revision" onClick={() => workflow(p, "request-revision")}>Yêu cầu sửa</button>}</> : <>{(p.status === "DRAFT" || p.status === "NEEDS_REVISION") && <button onClick={() => workflow(p, "submit")}>Gửi duyệt</button>}</>}</div></td></tr>)}</tbody></table></div> : <AnalyticsDashboard token={token} onError={setMessage} />}</main>;
}

createRoot(document.getElementById("root")!).render(<React.StrictMode><App /></React.StrictMode>);
