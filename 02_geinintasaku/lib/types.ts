export type Area = {
  id: string;
  name: string;
  center: [number, number];
  zoom: number;
  vibe?: string;
};

export type UserLocation = {
  coordinates: [number, number];
  accuracy?: number;
};

export type SourceStatus = "出典確認済み" | "要確認メモ" | "候補";

export type PlaceProperties = {
  id: string;
  name: string;
  catch: string;
  category: string;
  area: string;
  role?: "anchor" | "clue" | "column";
  importance?: "anchor" | "high" | "medium" | "low";
  heLevel: number;
  address: string;
  googleMapsUrl: string;
  tags: string[];
  relatedComedians: string[];
  scene?: string;
  sourceStatus?: SourceStatus;
  sourceProgram?: string;
  sourceEpisode?: string;
  sourceDate?: string;
  sourceUrl?: string;
  talkSummary?: string;
  story: string;
  sourceMemo: string;
};

export type PlaceFeature = {
  type: "Feature";
  geometry: {
    type: "Point";
    coordinates: [number, number];
  };
  properties: PlaceProperties;
};

export type PlacesGeoJson = {
  type: "FeatureCollection";
  features: PlaceFeature[];
};

export type PolygonGeoJson = {
  type: "FeatureCollection";
  features: Array<{
    type: "Feature";
    geometry: {
      type: "Polygon";
      coordinates: number[][][];
    };
    properties: Record<string, unknown>;
  }>;
};
