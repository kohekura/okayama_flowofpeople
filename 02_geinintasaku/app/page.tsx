"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import AreaTabs from "@/components/AreaTabs";
import CurrentLocationButton from "@/components/CurrentLocationButton";
import MapView from "@/components/MapView";
import PinCard from "@/components/PinCard";
import SearchBar from "@/components/SearchBar";
import SpotRail from "@/components/SpotRail";
import TodayCard from "@/components/TodayCard";
import type { Area, PlaceFeature, PlacesGeoJson, PolygonGeoJson, UserLocation } from "@/lib/types";

const STOCK_STORAGE_KEY = "geinin-map-stocked-place-ids";

function includesQuery(place: PlaceFeature, query: string) {
  const normalizedQuery = query.trim().toLowerCase();

  if (!normalizedQuery) {
    return true;
  }

  const searchableText = [
    place.properties.name,
    place.properties.area,
    place.properties.story,
    place.properties.scene,
    place.properties.sourceProgram,
    place.properties.sourceEpisode,
    place.properties.talkSummary,
    ...place.properties.relatedComedians,
    ...place.properties.tags
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();

  return searchableText.includes(normalizedQuery);
}

export default function Home() {
  const [places, setPlaces] = useState<PlaceFeature[]>([]);
  const [areas, setAreas] = useState<Area[]>([]);
  const [heat, setHeat] = useState<PolygonGeoJson | null>(null);
  const [query, setQuery] = useState("");
  const [activeAreaId, setActiveAreaId] = useState("shinjuku");
  const [selectedPlace, setSelectedPlace] = useState<PlaceFeature | null>(null);
  const [userLocation, setUserLocation] = useState<UserLocation | null>(null);
  const [isLocating, setIsLocating] = useState(false);
  const [locationMessage, setLocationMessage] = useState("");
  const [stockedIds, setStockedIds] = useState<string[]>([]);
  const [showStockedOnly, setShowStockedOnly] = useState(false);
  const [hasLoadedStocks, setHasLoadedStocks] = useState(false);

  useEffect(() => {
    async function loadData() {
      const [placesResponse, areasResponse, heatResponse] = await Promise.all([
        fetch("/data/places.geojson"),
        fetch("/data/areas.json"),
        fetch("/data/heat.geojson")
      ]);

      const placesData = (await placesResponse.json()) as PlacesGeoJson;
      const areasData = (await areasResponse.json()) as Area[];
      const heatData = (await heatResponse.json()) as PolygonGeoJson;

      setPlaces(placesData.features);
      setAreas(areasData);
      setHeat(heatData);
    }

    loadData().catch(() => {
      setPlaces([]);
      setAreas([]);
      setHeat(null);
    });
  }, []);

  useEffect(() => {
    try {
      const storedValue = window.localStorage.getItem(STOCK_STORAGE_KEY);
      const parsedValue = storedValue ? (JSON.parse(storedValue) as unknown) : [];

      if (Array.isArray(parsedValue)) {
        setStockedIds(parsedValue.filter((id): id is string => typeof id === "string"));
      }
    } catch {
      setStockedIds([]);
    } finally {
      setHasLoadedStocks(true);
    }
  }, []);

  useEffect(() => {
    if (!hasLoadedStocks) {
      return;
    }

    window.localStorage.setItem(STOCK_STORAGE_KEY, JSON.stringify(stockedIds));
  }, [hasLoadedStocks, stockedIds]);

  const activeArea = areas.find((area) => area.id === activeAreaId) ?? areas[0] ?? null;
  const activeAreaName = activeArea?.name ?? "新宿";

  const filteredPlaces = useMemo(
    () => places.filter((place) => includesQuery(place, query)),
    [places, query]
  );

  const visiblePlaces = useMemo(() => {
    const areaPlaces = query.trim()
      ? filteredPlaces
      : filteredPlaces.filter((place) => place.properties.area === activeAreaName);

    if (!showStockedOnly) {
      return areaPlaces;
    }

    return areaPlaces.filter((place) => stockedIds.includes(place.properties.id));
  }, [activeAreaName, filteredPlaces, query, showStockedOnly, stockedIds]);

  const hasAreaSpots = useMemo(
    () => places.some((place) => place.properties.area === activeAreaName),
    [activeAreaName, places]
  );

  const selectedPlaceIsStocked = selectedPlace
    ? stockedIds.includes(selectedPlace.properties.id)
    : false;

  const handleAreaSelect = useCallback((area: Area) => {
    setActiveAreaId(area.id);
    setSelectedPlace(null);
  }, []);

  const handleSearchChange = useCallback((value: string) => {
    setQuery(value);
    setSelectedPlace(null);
  }, []);

  const toggleStock = useCallback((placeId: string) => {
    setStockedIds((currentIds) =>
      currentIds.includes(placeId)
        ? currentIds.filter((id) => id !== placeId)
        : [...currentIds, placeId]
    );
  }, []);

  const handleStockFilter = useCallback(() => {
    setShowStockedOnly((currentValue) => !currentValue);
    setSelectedPlace(null);
  }, []);

  const handleLocate = useCallback(() => {
    if (!navigator.geolocation) {
      setLocationMessage("このブラウザでは現在地を使えません");
      return;
    }

    setIsLocating(true);
    setLocationMessage("");
    setSelectedPlace(null);

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setUserLocation({
          coordinates: [position.coords.longitude, position.coords.latitude],
          accuracy: position.coords.accuracy
        });
        setIsLocating(false);
        setLocationMessage("現在地を表示しました");
      },
      () => {
        setIsLocating(false);
        setLocationMessage("現在地の許可が必要です");
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 60000
      }
    );
  }, []);

  useEffect(() => {
    if (!locationMessage) {
      return;
    }

    const timeoutId = window.setTimeout(() => {
      setLocationMessage("");
    }, 2600);

    return () => window.clearTimeout(timeoutId);
  }, [locationMessage]);

  return (
    <main className="relative h-dvh w-full overflow-hidden bg-slate-950">
      <MapView
        places={visiblePlaces}
        selectedPlace={selectedPlace}
        selectedPlaceId={selectedPlace?.properties.id}
        activeArea={activeArea}
        heat={heat}
        isCardOpen={Boolean(selectedPlace)}
        userLocation={userLocation}
        onSelectPlace={setSelectedPlace}
      />

      <div className="pointer-events-none fixed inset-x-0 top-0 z-20 mx-auto max-w-xl bg-gradient-to-b from-slate-950/92 via-slate-950/44 to-transparent px-3 pb-5 pt-[calc(10px+env(safe-area-inset-top))]">
        <div className="mb-2 flex items-end justify-between gap-3 px-1">
          <div className="min-w-0">
            <p className="case-eyebrow">geinin field notes</p>
            <h1 className="mt-1 text-xl font-black leading-none text-cyan-50">芸人探索MAP</h1>
            <p className="mt-1 text-[11px] font-semibold text-slate-400">公開発言から街を読む</p>
          </div>
          <button
            type="button"
            onClick={handleStockFilter}
            className={`pointer-events-auto rounded-full border px-3 py-1.5 text-[10px] font-black tracking-[0.12em] transition active:scale-[0.96] ${
              showStockedOnly
                ? "border-amber-200/45 bg-amber-300/20 text-amber-100 shadow-[0_0_18px_rgba(252,211,77,0.2)]"
                : "border-cyan-100/15 bg-cyan-300/10 text-cyan-200"
            }`}
            aria-pressed={showStockedOnly}
          >
            STOCK {stockedIds.length}
          </button>
        </div>
        <div className="pointer-events-auto">
          <SearchBar value={query} onChange={handleSearchChange} />
        </div>
        <div className="pointer-events-auto mt-3">
          <AreaTabs areas={areas} activeAreaId={activeAreaId} onSelect={handleAreaSelect} />
        </div>
      </div>

      <div className="pointer-events-none fixed left-3 top-[174px] z-10">
        <TodayCard areaName={activeAreaName} vibe={activeArea?.vibe} isPreparing={!hasAreaSpots} />
      </div>

      <div className={`fixed right-4 z-20 transition-[bottom] ${selectedPlace ? "bottom-[calc(72dvh+12px)]" : "bottom-[154px]"}`}>
        <CurrentLocationButton
          onClick={handleLocate}
          isLoading={isLocating}
          hasLocation={Boolean(userLocation)}
        />
      </div>

      {locationMessage ? (
        <div className="case-panel fixed right-4 top-[174px] z-20 max-w-[180px] rounded-2xl px-3 py-2 text-xs font-bold text-cyan-100">
          {locationMessage}
        </div>
      ) : null}

      {!selectedPlace ? (
        <div className="pointer-events-none fixed inset-x-0 bottom-0 z-20 mx-auto max-w-xl px-3">
          <SpotRail
            places={visiblePlaces}
            stockedIds={stockedIds}
            userLocation={userLocation}
            onSelectPlace={setSelectedPlace}
            onToggleStock={toggleStock}
          />
        </div>
      ) : null}

      {visiblePlaces.length === 0 ? (
        <div className="fixed left-1/2 top-[220px] z-20 w-[min(300px,calc(100vw-40px))] -translate-x-1/2 rounded-2xl border border-cyan-100/15 bg-slate-950/92 px-4 py-3 text-center text-sm font-semibold text-cyan-100 shadow-[0_12px_30px_rgba(0,0,0,0.46)] backdrop-blur">
          {showStockedOnly
            ? "ストックはまだありません。気になる手がかりを保存しておけます。"
            : "見つかりませんでした。別の芸人名や番組名で探してみてください。"}
        </div>
      ) : null}

      <PinCard
        place={selectedPlace}
        isStocked={selectedPlaceIsStocked}
        onToggleStock={toggleStock}
        onClose={() => setSelectedPlace(null)}
      />
    </main>
  );
}
