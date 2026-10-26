import React, { useEffect, useRef, useState, useCallback } from "react";
import * as maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { LocateFixed, MapPin, Search, Layers, Compass, X } from "lucide-react";

interface LocationPickerProps {
  latitude: number;
  longitude: number;
  radius_m?: number;
  onChange: (coords: { latitude: number; longitude: number }) => void;
}

interface Suggestion {
  place_id: string | number;
  display_name: string;
  name?: string;
  lat: string;
  lon: string;
}

const MAP_STYLES = {
  osm: {
    label: "Đường phố",
    style: {
      version: 8 as const,
      sources: {
        "osm-tiles": {
          type: "raster" as const,
          tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
          tileSize: 256,
          attribution: '&copy; OpenStreetMap contributors',
        },
      },
      layers: [
        {
          id: "osm-layer",
          type: "raster" as const,
          source: "osm-tiles",
          minzoom: 0,
          maxzoom: 19,
        },
      ],
    },
  },
  satellite: {
    label: "Ảnh vệ tinh",
    style: {
      version: 8 as const,
      sources: {
        "esri-satellite": {
          type: "raster" as const,
          tiles: [
            "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
          ],
          tileSize: 256,
          attribution: '&copy; Esri & contributors',
        },
      },
      layers: [
        {
          id: "esri-satellite-layer",
          type: "raster" as const,
          source: "esri-satellite",
          minzoom: 0,
          maxzoom: 19,
        },
      ],
    },
  },
};

export const LocationPickerMap: React.FC<LocationPickerProps> = ({
  latitude,
  longitude,
  radius_m = 40,
  onChange,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const markerRef = useRef<maplibregl.Marker | null>(null);

  const [styleMode, setStyleMode] = useState<"osm" | "satellite">("osm");
  const [mapLoaded, setMapLoaded] = useState(false);
  const [query, setQuery] = useState("");
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [searching, setSearching] = useState(false);
  const [locating, setLocating] = useState(false);

  const validLat = Number.isFinite(latitude) && latitude !== 0 ? latitude : 10.7591;
  const validLng = Number.isFinite(longitude) && longitude !== 0 ? longitude : 106.6823;

  // Initialize Map
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    try {
      const map = new maplibregl.Map({
        container: containerRef.current,
        style: MAP_STYLES[styleMode].style,
        center: [validLng, validLat],
        zoom: 15,
        attributionControl: false,
      });

      map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "bottom-right");

      // Custom Draggable Pin
      const pinEl = document.createElement("div");
      pinEl.className = "marker-pin chosen";
      pinEl.style.cursor = "grab";
      pinEl.style.width = "34px";
      pinEl.style.height = "34px";
      pinEl.innerHTML = `<span style="font-size: 14px;">📍</span>`;

      const marker = new maplibregl.Marker({
        element: pinEl,
        draggable: true,
        anchor: "bottom",
      })
        .setLngLat([validLng, validLat])
        .addTo(map);

      // Drag event
      marker.on("dragend", () => {
        const lngLat = marker.getLngLat();
        onChange({
          latitude: Number(lngLat.lat.toFixed(6)),
          longitude: Number(lngLat.lng.toFixed(6)),
        });
      });

      // Click event
      map.on("click", (e) => {
        marker.setLngLat(e.lngLat);
        onChange({
          latitude: Number(e.lngLat.lat.toFixed(6)),
          longitude: Number(e.lngLat.lng.toFixed(6)),
        });
      });

      map.on("load", () => {
        setMapLoaded(true);
      });

      mapRef.current = map;
      markerRef.current = marker;

      return () => {
        map.remove();
        mapRef.current = null;
        markerRef.current = null;
        setMapLoaded(false);
      };
    } catch (err) {
      console.warn("LocationPickerMap init error:", err);
    }
  }, []);

  // Handle Layer Style Changes
  useEffect(() => {
    if (!mapRef.current || !mapLoaded) return;
    mapRef.current.setStyle(MAP_STYLES[styleMode].style);
  }, [styleMode, mapLoaded]);

  // Sync marker position when lat/lng change from outer form
  useEffect(() => {
    if (!markerRef.current) return;
    const current = markerRef.current.getLngLat();
    if (Math.abs(current.lat - validLat) > 0.00001 || Math.abs(current.lng - validLng) > 0.00001) {
      markerRef.current.setLngLat([validLng, validLat]);
      mapRef.current?.panTo([validLng, validLat], { duration: 300 });
    }
  }, [validLat, validLng]);

  // Autocomplete fetch with debounce
  useEffect(() => {
    if (!query.trim() || query.length < 2) {
      setSuggestions([]);
      setShowSuggestions(false);
      return;
    }

    const timer = setTimeout(async () => {
      setSearching(true);
      try {
        const q = encodeURIComponent(`${query.trim()}, Việt Nam`);
        const res = await fetch(
          `https://nominatim.openstreetmap.org/search?format=json&q=${q}&countrycodes=vn&limit=5&addressdetails=1`
        );
        if (res.ok) {
          const data: Suggestion[] = await res.json();
          setSuggestions(data);
          setShowSuggestions(data.length > 0);
        }
      } catch (err) {
        console.warn("Geocoding autocomplete error:", err);
      } finally {
        setSearching(false);
      }
    }, 350);

    return () => clearTimeout(timer);
  }, [query]);

  // Select suggestion
  const handleSelectSuggestion = (item: Suggestion) => {
    const lat = parseFloat(item.lat);
    const lon = parseFloat(item.lon);
    setQuery(item.display_name.split(",")[0] || item.display_name);
    setShowSuggestions(false);

    onChange({
      latitude: Number(lat.toFixed(6)),
      longitude: Number(lon.toFixed(6)),
    });

    markerRef.current?.setLngLat([lon, lat]);
    mapRef.current?.flyTo({ center: [lon, lat], zoom: 16, essential: true });
  };

  // GPS Locate Current User
  const locateMe = useCallback(() => {
    if (!navigator.geolocation) {
      alert("Trình duyệt của bạn không hỗ trợ Geolocation");
      return;
    }
    setLocating(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLocating(false);
        const { latitude: lat, longitude: lng } = pos.coords;
        onChange({
          latitude: Number(lat.toFixed(6)),
          longitude: Number(lng.toFixed(6)),
        });
        markerRef.current?.setLngLat([lng, lat]);
        mapRef.current?.flyTo({ center: [lng, lat], zoom: 16, essential: true });
      },
      (err) => {
        setLocating(false);
        alert(`Không thể lấy GPS: ${err.message}`);
      },
      { enableHighAccuracy: true, timeout: 8000 }
    );
  }, [onChange]);

  // Reset to SGU / TP.HCM Center
  const resetToCenter = () => {
    mapRef.current?.flyTo({ center: [106.6823, 10.7591], zoom: 15, essential: true });
  };

  return (
    <div style={{ marginTop: "6px", marginBottom: "14px", position: "relative" }}>
      {/* ─── Search Bar with Google Maps Style Autocomplete (NO <form> to prevent submit) ─── */}
      <div style={{ position: "relative", marginBottom: "8px", zIndex: 12 }}>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            background: "#fff",
            border: "1px solid #dcd6cb",
            borderRadius: "7px",
            padding: "8px 12px",
            boxShadow: "0 2px 8px rgba(16,42,69,0.06)",
            gap: "8px",
          }}
        >
          <Search size={15} color="#8c9998" />
          <input
            type="text"
            placeholder="Gõ tìm kiếm địa điểm (VD: Chợ Bến Thành, Dinh Độc Lập, SGU...)"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onFocus={() => {
              if (suggestions.length > 0) setShowSuggestions(true);
            }}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                e.stopPropagation();
                if (suggestions.length > 0) {
                  handleSelectSuggestion(suggestions[0]);
                }
              }
            }}
            style={{
              border: "none",
              outline: "none",
              width: "100%",
              fontSize: "12px",
              background: "transparent",
              color: "#102a43",
            }}
          />
          {searching && <span style={{ fontSize: "11px", color: "#8c9998" }}>Đang tìm...</span>}
          {query && (
            <button
              type="button"
              onClick={() => {
                setQuery("");
                setSuggestions([]);
                setShowSuggestions(false);
              }}
              style={{ padding: "2px", color: "#8c9998", cursor: "pointer" }}
            >
              <X size={14} />
            </button>
          )}
        </div>

        {/* Suggestions Dropdown */}
        {showSuggestions && suggestions.length > 0 && (
          <div
            style={{
              position: "absolute",
              top: "100%",
              left: 0,
              right: 0,
              marginTop: "4px",
              background: "#fff",
              border: "1px solid #e8e3da",
              borderRadius: "8px",
              boxShadow: "0 8px 24px rgba(16,42,69,0.15)",
              maxHeight: "220px",
              overflowY: "auto",
              zIndex: 30,
            }}
          >
            {suggestions.map((item, idx) => (
              <div
                key={item.place_id || idx}
                onClick={() => handleSelectSuggestion(item)}
                style={{
                  padding: "10px 14px",
                  borderBottom: idx < suggestions.length - 1 ? "1px solid #f0ece3" : "none",
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "flex-start",
                  gap: "8px",
                  fontSize: "12px",
                  transition: "background 0.15s",
                }}
                onMouseEnter={(e) => (e.currentTarget.style.background = "#fbfaf7")}
                onMouseLeave={(e) => (e.currentTarget.style.background = "#fff")}
              >
                <MapPin size={14} color="#d76b43" style={{ marginTop: "2px", flexShrink: 0 }} />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <strong style={{ display: "block", color: "#102a43", fontWeight: 600 }}>
                    {item.display_name.split(",")[0]}
                  </strong>
                  <span
                    style={{
                      display: "block",
                      color: "#718385",
                      fontSize: "11px",
                      whiteSpace: "nowrap",
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                    }}
                  >
                    {item.display_name}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ─── MapLibre Map Container with On-Map Floating Toolbar ─── */}
      <div
        style={{
          position: "relative",
          width: "100%",
          height: "290px",
          borderRadius: "8px",
          overflow: "hidden",
          border: "1px solid #dcd6cb",
          boxShadow: "0 2px 10px rgba(16,42,69,0.06)",
        }}
      >
        <div ref={containerRef} style={{ width: "100%", height: "100%" }} />

        {/* On-Map Floating Toolbar (Like Explore Map) */}
        <div
          style={{
            position: "absolute",
            top: "12px",
            left: "12px",
            display: "flex",
            flexDirection: "column",
            gap: "6px",
            zIndex: 10,
          }}
        >
          <button
            type="button"
            className="map-tool-btn"
            title="Định vị vị trí của tôi (GPS)"
            onClick={locateMe}
            disabled={locating}
            style={{ width: "32px", height: "32px" }}
          >
            <LocateFixed size={15} color={locating ? "#d76b43" : "#1e8449"} />
          </button>

          <button
            type="button"
            className="map-tool-btn"
            title={`Chuyển lớp bản đồ: ${styleMode === "osm" ? "Ảnh vệ tinh (ESRI)" : "Bản đồ đường phố"}`}
            onClick={() => setStyleMode((m) => (m === "osm" ? "satellite" : "osm"))}
            style={{ width: "32px", height: "32px" }}
          >
            <Layers size={15} color={styleMode === "satellite" ? "#d76b43" : "#102a43"} />
          </button>

          <button
            type="button"
            className="map-tool-btn"
            title="Về trung tâm TP.HCM / SGU"
            onClick={resetToCenter}
            style={{ width: "32px", height: "32px" }}
          >
            <Compass size={15} color="#102a43" />
          </button>
        </div>

        {/* Coordinates Pill */}
        <div
          style={{
            position: "absolute",
            top: "12px",
            right: "12px",
            zIndex: 10,
            background: "#102a43ee",
            color: "#fff",
            padding: "4px 9px",
            borderRadius: "5px",
            fontSize: "11px",
            fontFamily: "'DM Mono', monospace",
            letterSpacing: "0.5px",
            boxShadow: "0 2px 6px rgba(0,0,0,0.15)",
          }}
        >
          {validLat.toFixed(6)}, {validLng.toFixed(6)}
        </div>

        {/* Bottom Legend Pill */}
        <div
          style={{
            position: "absolute",
            bottom: "10px",
            left: "10px",
            zIndex: 10,
            background: "rgba(255,255,255,0.92)",
            backdropFilter: "blur(4px)",
            padding: "5px 10px",
            borderRadius: "5px",
            fontSize: "11px",
            color: "#102a43",
            display: "flex",
            alignItems: "center",
            gap: "6px",
            boxShadow: "0 2px 6px rgba(0,0,0,0.08)",
            border: "1px solid #e7e2d9",
          }}
        >
          <MapPin size={13} color="#d76b43" />
          <span>
            Click hoặc kéo ghim để chọn toạ độ · Lớp: <b>{styleMode === "satellite" ? "Vệ tinh" : "Đường phố"}</b> · Bán kính: <b>{radius_m}m</b>
          </span>
        </div>
      </div>
    </div>
  );
};
