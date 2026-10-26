import React, { useEffect, useRef, useState } from "react";
import * as maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { LocateFixed, MapPin, Search } from "lucide-react";

interface LocationPickerProps {
  latitude: number;
  longitude: number;
  radius_m?: number;
  onChange: (coords: { latitude: number; longitude: number }) => void;
}

const CARTO_VOYAGER_STYLE = {
  version: 8 as const,
  sources: {
    "carto-voyager": {
      type: "raster" as const,
      tiles: [
        "https://a.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png",
        "https://b.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png",
        "https://c.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png",
      ],
      tileSize: 256,
      attribution: '&copy; <a href="https://carto.com/">CARTO</a> &copy; OpenStreetMap',
    },
  },
  layers: [
    {
      id: "carto-voyager-layer",
      type: "raster" as const,
      source: "carto-voyager",
      minzoom: 0,
      maxzoom: 19,
    },
  ],
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
  const [searchQuery, setSearchQuery] = useState("");
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
        style: CARTO_VOYAGER_STYLE,
        center: [validLng, validLat],
        zoom: 15,
        attributionControl: false,
      });

      map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");

      // Custom Draggable Pin Marker
      const pinEl = document.createElement("div");
      pinEl.style.width = "36px";
      pinEl.style.height = "36px";
      pinEl.style.borderRadius = "50% 50% 50% 0";
      pinEl.style.transform = "rotate(-45deg)";
      pinEl.style.background = "#d76b43";
      pinEl.style.border = "3px solid #ffffff";
      pinEl.style.boxShadow = "0 4px 14px rgba(215, 107, 67, 0.5)";
      pinEl.style.cursor = "grab";
      pinEl.style.display = "grid";
      pinEl.style.placeItems = "center";
      pinEl.innerHTML = `<span style="transform: rotate(45deg); color: #fff; font-size: 14px; font-weight: bold;">📍</span>`;

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

      // Click on map to place pin
      map.on("click", (e) => {
        marker.setLngLat(e.lngLat);
        onChange({
          latitude: Number(e.lngLat.lat.toFixed(6)),
          longitude: Number(e.lngLat.lng.toFixed(6)),
        });
      });

      mapRef.current = map;
      markerRef.current = marker;

      return () => {
        map.remove();
        mapRef.current = null;
        markerRef.current = null;
      };
    } catch (err) {
      console.warn("LocationPickerMap init error:", err);
    }
  }, []);

  // Update marker position when props change from external edits
  useEffect(() => {
    if (!markerRef.current) return;
    const current = markerRef.current.getLngLat();
    if (Math.abs(current.lat - validLat) > 0.00001 || Math.abs(current.lng - validLng) > 0.00001) {
      markerRef.current.setLngLat([validLng, validLat]);
      mapRef.current?.panTo([validLng, validLat], { duration: 400 });
    }
  }, [validLat, validLng]);

  // GPS Locate Current User
  const locateMe = () => {
    if (!navigator.geolocation) {
      alert("Trình duyệt không hỗ trợ Geolocation");
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
        mapRef.current?.flyTo({ center: [lng, lat], zoom: 16 });
      },
      (err) => {
        setLocating(false);
        alert(`Không thể lấy vị trí GPS: ${err.message}`);
      },
      { enableHighAccuracy: true, timeout: 8000 }
    );
  };

  // Search Address / Place in Vietnam
  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim() || searching) return;
    setSearching(true);
    try {
      const q = encodeURIComponent(`${searchQuery}, TP. Hồ Chí Minh`);
      const res = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${q}&countrycodes=vn&limit=1`);
      const data = await res.json();
      if (data && data.length > 0) {
        const lat = parseFloat(data[0].lat);
        const lon = parseFloat(data[0].lon);
        onChange({
          latitude: Number(lat.toFixed(6)),
          longitude: Number(lon.toFixed(6)),
        });
        markerRef.current?.setLngLat([lon, lat]);
        mapRef.current?.flyTo({ center: [lon, lat], zoom: 16 });
      } else {
        alert("Không tìm thấy địa điểm này. Bạn hãy click trực tiếp trên bản đồ nhé!");
      }
    } catch {
      alert("Lỗi khi tìm kiếm địa chỉ. Vui lòng click chọn trực tiếp trên bản đồ.");
    } finally {
      setSearching(false);
    }
  };

  return (
    <div style={{ marginTop: "8px", marginBottom: "16px", display: "flex", flexDirection: "column", gap: "8px" }}>
      {/* Search and Helper Toolbar */}
      <div style={{ display: "flex", gap: "8px", alignItems: "center", flexWrap: "wrap" }}>
        <form onSubmit={handleSearch} style={{ display: "flex", gap: "6px", flex: 1, minWidth: "220px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "6px", background: "#fbfaf7", border: "1px solid #dedbd3", borderRadius: "6px", padding: "6px 10px", width: "100%" }}>
            <Search size={14} color="#8c9998" />
            <input
              type="text"
              placeholder="Tìm tên địa điểm (VD: Chợ Bến Thành, Dinh Độc Lập...)"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{ border: "none", outline: "none", background: "transparent", fontSize: "12px", width: "100%" }}
            />
          </div>
          <button type="submit" disabled={searching} style={{ background: "#102a43", color: "#fff", padding: "6px 12px", borderRadius: "6px", fontSize: "11px", fontWeight: "600", whiteSpace: "nowrap" }}>
            {searching ? "Đang tìm..." : "Tìm"}
          </button>
        </form>

        <button
          type="button"
          onClick={locateMe}
          disabled={locating}
          style={{ display: "inline-flex", alignItems: "center", gap: "5px", background: "#e8f8f5", color: "#1e8449", border: "1px solid #a3e4d7", padding: "6px 12px", borderRadius: "6px", fontSize: "11px", fontWeight: "600", cursor: "pointer", whiteSpace: "nowrap" }}
        >
          <LocateFixed size={13} />
          {locating ? "Đang định vị..." : "Lấy vị trí của tôi"}
        </button>
      </div>

      {/* Map Container */}
      <div style={{ position: "relative", width: "100%", height: "260px", borderRadius: "8px", overflow: "hidden", border: "1px solid #dcd6cb", boxShadow: "0 2px 8px rgba(16,42,69,0.06)" }}>
        <div ref={containerRef} style={{ width: "100%", height: "100%" }} />

        {/* Floating guidance badge */}
        <div style={{ position: "absolute", bottom: "10px", left: "10px", zIndex: 2, background: "rgba(255,255,255,0.92)", backdropFilter: "blur(4px)", padding: "5px 9px", borderRadius: "5px", fontSize: "11px", color: "#102a43", display: "flex", alignItems: "center", gap: "6px", boxShadow: "0 2px 6px rgba(0,0,0,0.1)", border: "1px solid #e7e2d9" }}>
          <MapPin size={13} color="#d76b43" />
          <span>Click hoặc kéo ghim cam để chọn vị trí (bán kính: <b>{radius_m}m</b>)</span>
        </div>

        {/* Coordinates status badge */}
        <div style={{ position: "absolute", top: "10px", left: "10px", zIndex: 2, background: "#102a43ee", color: "#fff", padding: "4px 8px", borderRadius: "4px", fontSize: "10px", fontFamily: "'DM Mono', monospace", letterSpacing: "0.5px" }}>
          {validLat.toFixed(6)}, {validLng.toFixed(6)}
        </div>
      </div>
    </div>
  );
};
