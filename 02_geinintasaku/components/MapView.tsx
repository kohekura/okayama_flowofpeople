"use client";

import { useEffect, useRef } from "react";
import maplibregl, { type GeoJSONSource, type Map, type Marker } from "maplibre-gl";
import type { Area, PlaceFeature, PolygonGeoJson, UserLocation } from "@/lib/types";

type MapViewProps = {
  places: PlaceFeature[];
  selectedPlace: PlaceFeature | null;
  selectedPlaceId?: string;
  activeArea: Area | null;
  heat: PolygonGeoJson | null;
  isCardOpen: boolean;
  userLocation: UserLocation | null;
  onSelectPlace: (place: PlaceFeature) => void;
};

export default function MapView({
  places,
  selectedPlace,
  selectedPlaceId,
  activeArea,
  heat,
  isCardOpen,
  userLocation,
  onSelectPlace
}: MapViewProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<Map | null>(null);
  const markerRefs = useRef<Marker[]>([]);
  const userMarkerRef = useRef<Marker | null>(null);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) {
      return;
    }

    const map = new maplibregl.Map({
      container: containerRef.current,
      center: [139.7005, 35.6909],
      zoom: 14,
      pitch: 0,
      attributionControl: false,
      cooperativeGestures: false,
      style: {
        version: 8,
        sources: {
          darkMatter: {
            type: "raster",
            tiles: [
              "https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png",
              "https://b.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png",
              "https://c.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png",
              "https://d.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png"
            ],
            tileSize: 256,
            attribution: "© OpenStreetMap contributors © CARTO"
          }
        },
        layers: [
          {
            id: "darkMatter",
            type: "raster",
            source: "darkMatter",
            paint: {
              "raster-brightness-min": 0.06,
              "raster-brightness-max": 0.9,
              "raster-saturation": -0.25,
              "raster-contrast": 0.12
            }
          }
        ]
      }
    });

    map.addControl(
      new maplibregl.AttributionControl({
        compact: true
      }),
      "bottom-right"
    );

    mapRef.current = map;

    return () => {
      markerRefs.current.forEach((marker) => marker.remove());
      userMarkerRef.current?.remove();
      map.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !activeArea) {
      return;
    }

    map.flyTo({
      center: activeArea.center,
      zoom: activeArea.zoom,
      duration: 700,
      essential: true
    });
  }, [activeArea]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) {
      return;
    }

    map.easeTo({
      padding: {
        top: 172,
        right: 18,
        bottom: isCardOpen ? 330 : 156,
        left: 18
      },
      duration: 300
    });
  }, [isCardOpen]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !selectedPlace) {
      return;
    }

    map.flyTo({
      center: selectedPlace.geometry.coordinates,
      zoom: Math.max(map.getZoom(), 15.3),
      duration: 500,
      essential: true
    });
  }, [selectedPlace]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) {
      return;
    }

    if (!userLocation) {
      userMarkerRef.current?.remove();
      userMarkerRef.current = null;
      return;
    }

    if (!userMarkerRef.current) {
      const markerElement = document.createElement("div");
      markerElement.className = "user-location-marker";
      markerElement.setAttribute("aria-label", "あなたの現在地");

      userMarkerRef.current = new maplibregl.Marker({
        element: markerElement,
        anchor: "center"
      }).addTo(map);
    }

    userMarkerRef.current.setLngLat(userLocation.coordinates);

    map.flyTo({
      center: userLocation.coordinates,
      zoom: Math.max(map.getZoom(), 15.4),
      duration: 700,
      essential: true
    });
  }, [userLocation]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !heat) {
      return;
    }

    const addOrUpdateHeat = () => {
      if (map.getSource("meet-area")) {
        const source = map.getSource("meet-area") as GeoJSONSource;
        source.setData(heat);
        return;
      }

      map.addSource("meet-area", {
        type: "geojson",
        data: heat
      });

      map.addLayer({
        id: "meet-area-fill",
        type: "fill",
        source: "meet-area",
        paint: {
          "fill-color": "#22d3ee",
          "fill-opacity": 0.13
        }
      });

      map.addLayer({
        id: "meet-area-line",
        type: "line",
        source: "meet-area",
        paint: {
          "line-color": "#67e8f9",
          "line-opacity": 0.38,
          "line-width": 2
        }
      });
    };

    if (map.isStyleLoaded()) {
      addOrUpdateHeat();
    } else {
      map.once("load", addOrUpdateHeat);
    }
  }, [heat]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) {
      return;
    }

    markerRefs.current.forEach((marker) => marker.remove());
    markerRefs.current = places.map((place) => {
      const markerElement = document.createElement("button");
      markerElement.type = "button";
      const importance = place.properties.importance ?? "medium";
      const role = place.properties.role ?? "clue";
      markerElement.className = `geinin-marker is-${role} is-${importance} ${
        place.properties.id === selectedPlaceId ? "is-selected" : ""
      }`;
      markerElement.innerHTML = `<span class="geinin-marker-core"></span>`;
      markerElement.setAttribute("aria-label", place.properties.name);
      markerElement.addEventListener("click", () => {
        onSelectPlace(place);
        map.flyTo({
          center: place.geometry.coordinates,
          zoom: Math.max(map.getZoom(), 15.3),
          duration: 500,
          essential: true
        });
      });

      return new maplibregl.Marker({
        element: markerElement,
        anchor: "bottom"
      })
        .setLngLat(place.geometry.coordinates)
        .addTo(map);
    });
  }, [onSelectPlace, places, selectedPlaceId]);

  return <div ref={containerRef} className="map-shell h-full w-full" aria-label="芸人ゆかりスポットの地図" />;
}
