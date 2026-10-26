import React, { useEffect, useRef, useState } from "react";
import * as maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { Compass, LocateFixed, Layers } from "lucide-react";
import type { Poi } from "../samplePois";

interface MapLibreViewProps {
  pois: Poi[];
  selected: Poi | null;
  onSelectPoi: (poi: Poi) => void;
  userCoords?: { latitude: number; longitude: number } | null;
  onLocateUser?: () => void;
}

// OpenStreetMap & CARTO tile styles (no API key required)
const MAP_STYLES = {
  satellite: {
    label: "Ảnh vệ tinh (ESRI)",
    style: {
      version: 8 as const,
      sources: {
        "esri-satellite": {
          type: "raster" as const,
          tiles: [
            "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
          ],
          tileSize: 256,
          attribution: '&copy; <a href="https://www.esri.com/">Esri</a> &copy; USGS',
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
  osm: {
    label: "OpenStreetMap",
    style: {
      version: 8 as const,
      sources: {
        "osm-tiles": {
          type: "raster" as const,
          tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
          tileSize: 256,
          attribution:
            '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
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
};

export const MapLibreView: React.FC<MapLibreViewProps> = ({
  pois,
  selected,
  onSelectPoi,
  userCoords,
  onLocateUser,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const markersRef = useRef<maplibregl.Marker[]>([]);
  const userMarkerRef = useRef<maplibregl.Marker | null>(null);
  const activePopupRef = useRef<maplibregl.Popup | null>(null);
  const [styleMode, setStyleMode] = useState<"osm" | "satellite">("osm");
  const [mapLoaded, setMapLoaded] = useState(false);

  // Initialize MapLibre
  useEffect(() => {
    if (!containerRef.current) return;

    try {
      const map = new maplibregl.Map({
        container: containerRef.current,
        style: MAP_STYLES[styleMode].style,
        center: [106.6823, 10.7591], // SGU Main Campus
        zoom: 14,
        attributionControl: false,
      });

      // Add navigation controls (zoom in/out, rotate/pitch compass)
      map.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), "top-right");
      map.addControl(
        new maplibregl.AttributionControl({ compact: true, customAttribution: "CityEcho SGU" }),
        "bottom-right"
      );
      map.addControl(new maplibregl.ScaleControl({ unit: "metric" }), "bottom-left");

      map.on("load", () => {
        setMapLoaded(true);
      });

      mapRef.current = map;

      return () => {
        map.remove();
        mapRef.current = null;
        setMapLoaded(false);
      };
    } catch (err) {
      console.warn("MapLibre GL could not initialize, falling back:", err);
    }
  }, []);

  // Update style when toggled
  useEffect(() => {
    if (!mapRef.current || !mapLoaded) return;
    mapRef.current.setStyle(MAP_STYLES[styleMode].style);
  }, [styleMode, mapLoaded]);

  // Update POI markers
  useEffect(() => {
    if (!mapRef.current || !mapLoaded) return;

    // Remove existing markers
    markersRef.current.forEach((m) => m.remove());
    markersRef.current = [];

    pois.forEach((poi, index) => {
      const isChosen = selected?.id === poi.id;

      // Custom HTML Marker element
      const el = document.createElement("button");
      el.className = `maplibre-marker ${isChosen ? "is-selected" : ""}`;
      el.setAttribute("aria-label", poi.translation.name);
      el.title = poi.translation.name;

      el.innerHTML = `
        <div class="marker-pin ${isChosen ? "chosen" : ""}">
          <span>${index + 1}</span>
        </div>
      `;

      el.addEventListener("click", (e) => {
        e.stopPropagation();
        onSelectPoi(poi);

        // Open popup
        if (activePopupRef.current) activePopupRef.current.remove();
        const popup = new maplibregl.Popup({ offset: 25, closeButton: false })
          .setLngLat([poi.longitude, poi.latitude])
          .setHTML(`
            <div class="map-popup-card">
              <span class="popup-tag">${poi.category}</span>
              <strong>${poi.translation.name}</strong>
              <small>Bán kính: ${poi.radius_m}m · Độ ưu tiên: ${poi.priority}</small>
            </div>
          `)
          .addTo(mapRef.current!);
        activePopupRef.current = popup;
      });

      const marker = new maplibregl.Marker({ element: el, anchor: "bottom" })
        .setLngLat([poi.longitude, poi.latitude])
        .addTo(mapRef.current!);

      markersRef.current.push(marker);
    });
  }, [pois, selected, mapLoaded, onSelectPoi]);

  // Update user location marker & fly to user location
  // User location marker & centering
  useEffect(() => {
    if (!mapRef.current || !mapLoaded) return;

    if (userCoords) {
      if (!userMarkerRef.current) {
        const userEl = document.createElement("div");
        userEl.className = "user-location-pulse";
        userEl.title = "Vị trí của bạn";
        userEl.innerHTML = `<div class="pulse-dot"></div><div class="pulse-ring"></div>`;

        userMarkerRef.current = new maplibregl.Marker({ element: userEl })
          .setLngLat([userCoords.longitude, userCoords.latitude])
          .addTo(mapRef.current!);
      } else {
        userMarkerRef.current.setLngLat([userCoords.longitude, userCoords.latitude]);
      }

      // If user has nearby POIs with distance, fit bounds to show both user and closest POIs!
      const poisWithDist = pois.filter((p) => p.distance_m !== undefined);
      if (poisWithDist.length > 0) {
        const bounds = new maplibregl.LngLatBounds();
        bounds.extend([userCoords.longitude, userCoords.latitude]);
        poisWithDist.slice(0, 2).forEach((p) => bounds.extend([p.longitude, p.latitude]));
        mapRef.current.fitBounds(bounds, { padding: 80, maxZoom: 15.5, duration: 1200 });
      } else {
        mapRef.current.flyTo({
          center: [userCoords.longitude, userCoords.latitude],
          zoom: 15,
          essential: true,
        });
      }
    } else if (userMarkerRef.current) {
      userMarkerRef.current.remove();
      userMarkerRef.current = null;
    }
  }, [userCoords, mapLoaded]);

  // Fly to selected POI
  useEffect(() => {
    if (!mapRef.current || !mapLoaded || !selected) return;

    mapRef.current.flyTo({
      center: [selected.longitude, selected.latitude],
      zoom: 15.5,
      essential: true,
      duration: 1200,
    });
  }, [selected, mapLoaded]);

  const handleLocateClick = () => {
    if (userCoords && mapRef.current) {
      mapRef.current.flyTo({
        center: [userCoords.longitude, userCoords.latitude],
        zoom: 16.5,
        essential: true,
      });
    } else if (onLocateUser) {
      onLocateUser();
    }
  };

  const handleResetToSgu = () => {
    if (!mapRef.current) return;
    mapRef.current.flyTo({
      center: [106.6823, 10.7591],
      zoom: 14.5,
      essential: true,
    });
  };

  const handleFitAll = () => {
    if (!mapRef.current || pois.length === 0) return;
    const bounds = new maplibregl.LngLatBounds();
    pois.forEach((p) => bounds.extend([p.longitude, p.latitude]));
    if (userCoords) bounds.extend([userCoords.longitude, userCoords.latitude]);
    mapRef.current.fitBounds(bounds, { padding: 50, maxZoom: 16 });
  };

  return (
    <div className="maplibre-container-wrapper">
      <div ref={containerRef} className="maplibre-container" />

      {/* Floating map toolbar */}
      <div className="maplibre-toolbar">
        {onLocateUser && (
          <button
            type="button"
            className="map-tool-btn"
            title="Định vị của tôi"
            onClick={handleLocateClick}
          >
            <LocateFixed size={16} />
          </button>
        )}
        <button
          type="button"
          className="map-tool-btn"
          title="Về Trường ĐH Sài Gòn (SGU)"
          onClick={handleResetToSgu}
        >
          <Compass size={16} />
        </button>
        <button
          type="button"
          className="map-tool-btn"
          title="Xem bao quát tất cả POI"
          onClick={handleFitAll}
        >
          <span>⤢</span>
        </button>
        <button
          type="button"
          className="map-tool-btn"
          title={`Đổi lớp bản đồ: ${styleMode === "osm" ? "Ảnh vệ tinh (ESRI)" : "Bản đồ đường phố (OSM)"}`}
          onClick={() => setStyleMode((m) => (m === "osm" ? "satellite" : "osm"))}
        >
          <Layers size={16} />
        </button>
      </div>

      {/* Bottom map legend */}
      <div className="map-legend">
        <span className="legend-dot" />
        <span>Bản đồ MapLibre GL · {pois.length} điểm tham quan</span>
      </div>
    </div>
  );
};
