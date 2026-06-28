const fs = require("fs");
const path = require("path");

const placesPath = path.join(process.cwd(), "public", "data", "places.geojson");
const areasPath = path.join(process.cwd(), "public", "data", "areas.json");
const places = JSON.parse(fs.readFileSync(placesPath, "utf8"));
const areas = JSON.parse(fs.readFileSync(areasPath, "utf8"));

const sourceProgram = "\u0054\u0042\u0053\u30c6\u30ec\u30d3\u300c\u4eba\u751f\u6700\u9ad8\u30ec\u30b9\u30c8\u30e9\u30f3\u300d";
const confirmedStatus = "\u51fa\u5178\u78ba\u8a8d\u6e08\u307f";

const confirmedPlaces = [
  {
    id: "r010",
    name: "\u30e9\u30fc\u30e1\u30f3\u85e4 \u611b\u77e5\u5ddd\u5e97",
    catch: "\u30c0\u30a4\u30a2\u30f32\u4eba\u306e\u7d46\u3092\u6df1\u3081\u305f\u3001\u6ecb\u8cc0\u306e\u601d\u3044\u51fa\u30e9\u30fc\u30e1\u30f3",
    category: "\u30e9\u30fc\u30e1\u30f3",
    area: "\u6ecb\u8cc0\u611b\u8358",
    coordinates: [136.211, 35.171],
    heLevel: 5,
    address: "\u6ecb\u8cc0\u770c\u611b\u77e5\u90e1\u611b\u8358\u753a\u4e2d\u5bbf265-1",
    googleMapsUrl: "https://www.google.com/maps/search/?api=1&query=%E3%83%A9%E3%83%BC%E3%83%A1%E3%83%B3%E8%97%A4%20%E6%84%9B%E7%9F%A5%E5%B7%9D%E5%BA%97",
    tags: ["#\u30c0\u30a4\u30a2\u30f3", "#\u6ecb\u8cc0", "#\u4eba\u751f\u6700\u9ad8\u30ec\u30b9\u30c8\u30e9\u30f3", "#\u30e9\u30fc\u30e1\u30f3"],
    relatedComedians: ["\u30c0\u30a4\u30a2\u30f3", "\u30e6\u30fc\u30b9\u30b1", "\u6d25\u7530\u7be4\u5b8f"],
    sourceEpisode: "2024\u5e743\u67082\u65e5\u653e\u9001 \u3054\u3061\u305d\u3046\u69d8 \u30c0\u30a4\u30a2\u30f3\u3055\u3093",
    sourceDate: "2024\u5e743\u67082\u65e5",
    sourceUrl: "https://www.tbs.co.jp/saikourestaurant/oldv8/202403021/",
    talkSummary: "\u756a\u7d44\u516c\u5f0f\u30a2\u30fc\u30ab\u30a4\u30d6\u3067\u3001\u6ecb\u8cc0\u30fb\u611b\u8358\u753a\u300c2\u4eba\u306e\u7d46\u3092\u6df1\u3081\u305f\uff01\u601d\u3044\u51fa\u306e\u30e9\u30fc\u30e1\u30f3\u300d\u3068\u3057\u3066\u7d39\u4ecb\u3002\u5e97\u8217\u60c5\u5831\u3068\u3057\u3066\u300c\u30e9\u30fc\u30e1\u30f3\u85e4 \u611b\u77e5\u5ddd\u5e97\u300d\u304c\u63b2\u8f09\u3055\u308c\u3066\u3044\u308b\u3002",
    scene: "\u5c0f\u5b66\u751f\u304b\u3089\u9577\u3044\u4ed8\u304d\u5408\u3044\u306e2\u4eba\u304c\u8a9e\u308b\u201c\u601d\u3044\u51fa\u201d\u3068\u3057\u3066\u5f37\u3044\u3002\u6771\u4eac\u306e\u58f2\u308c\u305f\u5f8c\u3067\u306f\u306a\u304f\u3001\u5730\u5143\u306e\u6642\u9593\u306b\u623b\u308c\u308b\u624b\u304c\u304b\u308a\u3002",
    story: "\u6d3e\u624b\u3055\u3088\u308a\u3082\u3001\u30b3\u30f3\u30d3\u306e\u539f\u98a8\u666f\u3068\u3057\u3066\u52b9\u304f\u4e00\u676f\u3002\u5730\u56f3\u3067\u6ecb\u8cc0\u306b\u98db\u3076\u306e\u3082\u9762\u767d\u3044\u3002"
  },
  {
    id: "r011",
    name: "\u3061\u3083\u3093\u307d\u3093\u4ead \u672c\u5e97",
    catch: "\u30c0\u30a4\u30a2\u30f3\u304c2\u4eba\u3067\u901a\u3063\u305f\u3001\u5f66\u6839\u306e\u8fd1\u6c5f\u3061\u3083\u3093\u307d\u3093",
    category: "\u30e9\u30fc\u30e1\u30f3",
    area: "\u5f66\u6839",
    coordinates: [136.263, 35.27],
    heLevel: 5,
    address: "\u6ecb\u8cc0\u770c\u5f66\u6839\u5e02\u5e78\u753a74-1",
    googleMapsUrl: "https://www.google.com/maps/search/?api=1&query=%E3%81%A1%E3%82%83%E3%82%93%E3%81%BD%E3%82%93%E4%BA%AD%20%E6%9C%AC%E5%BA%97",
    tags: ["#\u30c0\u30a4\u30a2\u30f3", "#\u5f66\u6839", "#\u901a\u3063\u305f", "#\u8fd1\u6c5f\u3061\u3083\u3093\u307d\u3093"],
    relatedComedians: ["\u30c0\u30a4\u30a2\u30f3", "\u30e6\u30fc\u30b9\u30b1", "\u6d25\u7530\u7be4\u5b8f"],
    sourceEpisode: "2024\u5e743\u67082\u65e5\u653e\u9001 \u3054\u3061\u305d\u3046\u69d8 \u30c0\u30a4\u30a2\u30f3\u3055\u3093",
    sourceDate: "2024\u5e743\u67082\u65e5",
    sourceUrl: "https://www.tbs.co.jp/saikourestaurant/oldv8/202403021/",
    talkSummary: "\u756a\u7d44\u516c\u5f0f\u30a2\u30fc\u30ab\u30a4\u30d6\u3067\u3001\u6ecb\u8cc0\u30fb\u5f66\u6839\u300c2\u4eba\u3067\u901a\u3063\u305f\uff01\u8fd1\u6c5f\u3061\u3083\u3093\u307d\u3093\u300d\u3068\u3057\u3066\u7d39\u4ecb\u3002\u5e97\u8217\u60c5\u5831\u3068\u3057\u3066\u300c\u3061\u3083\u3093\u307d\u3093\u4ead \u672c\u5e97\u300d\u304c\u63b2\u8f09\u3055\u308c\u3066\u3044\u308b\u3002",
    scene: "\u516c\u5f0f\u898b\u51fa\u3057\u306b\u201c2\u4eba\u3067\u901a\u3063\u305f\u201d\u3068\u6b8b\u3063\u3066\u3044\u308b\u306e\u304c\u5f37\u3044\u3002\u884c\u304d\u3064\u3051\u7cfb\u30ab\u30fc\u30c9\u3068\u3057\u3066\u304b\u306a\u308a\u76f8\u6027\u304c\u3044\u3044\u3002",
    story: "\u30b3\u30f3\u30d3\u306e\u6642\u9593\u304c\u305d\u306e\u307e\u307e\u5e97\u306e\u8a18\u61b6\u306b\u306a\u308b\u30bf\u30a4\u30d7\u3002\u6ecb\u8cc0\u30a8\u30ea\u30a2\u3092\u4f5c\u308b\u4fa1\u5024\u304c\u3042\u308b\u3002"
  },
  {
    id: "r012",
    name: "\u5343\u3068\u305b \u672c\u5e97",
    catch: "\u30c0\u30a4\u30a2\u30f3\u304c\u82b8\u4eba\u306e\u4ef2\u9593\u5165\u308a\u3092\u611f\u3058\u305f\u3001\u306a\u3093\u3070\u306e\u5143\u7956\u5927\u962a\u5473",
    category: "\u3046\u3069\u3093",
    area: "\u96e3\u6ce2",
    coordinates: [135.5037, 34.6655],
    heLevel: 5,
    address: "\u5927\u962a\u5e02\u4e2d\u592e\u533a\u96e3\u6ce2\u5343\u65e5\u524d8-1",
    googleMapsUrl: "https://www.google.com/maps/search/?api=1&query=%E5%8D%83%E3%81%A8%E3%81%9B%20%E6%9C%AC%E5%BA%97%20%E9%9B%A3%E6%B3%A2",
    tags: ["#\u30c0\u30a4\u30a2\u30f3", "#\u96e3\u6ce2", "#\u4eba\u751f\u6700\u9ad8\u306e\u4e00\u54c1", "#\u5927\u962a"],
    relatedComedians: ["\u30c0\u30a4\u30a2\u30f3", "\u30e6\u30fc\u30b9\u30b1", "\u6d25\u7530\u7be4\u5b8f"],
    sourceEpisode: "2024\u5e743\u67082\u65e5\u653e\u9001 \u3054\u3061\u305d\u3046\u69d8 \u30c0\u30a4\u30a2\u30f3\u3055\u3093",
    sourceDate: "2024\u5e743\u67082\u65e5",
    sourceUrl: "https://www.tbs.co.jp/saikourestaurant/oldv8/202403021/",
    talkSummary: "\u756a\u7d44\u516c\u5f0f\u30a2\u30fc\u30ab\u30a4\u30d6\u3067\u3001\u5927\u962a\u30fb\u96e3\u6ce2\u300c\u82b8\u4eba\u306e\u4ef2\u9593\u5165\u308a\u3092\u679c\u305f\u3057\u305f\uff01\u5143\u7956\u30fb\u5927\u962a\u306e\u5473\u300d\u304b\u3064\u4eba\u751f\u6700\u9ad8\u306e\u4e00\u54c1\u3068\u3057\u3066\u7d39\u4ecb\u3002\u5e97\u8217\u60c5\u5831\u3068\u3057\u3066\u300c\u5343\u3068\u305b \u672c\u5e97\u300d\u304c\u63b2\u8f09\u3055\u308c\u3066\u3044\u308b\u3002",
    scene: "\u96e3\u6ce2\u5343\u65e5\u524d\u3068\u3044\u3046\u7acb\u5730\u3068\u201c\u82b8\u4eba\u306e\u4ef2\u9593\u5165\u308a\u201d\u306e\u898b\u51fa\u3057\u304c\u5f37\u3044\u3002\u5287\u5834\u6587\u5316\u3068\u98df\u306e\u8a18\u61b6\u304c\u76f4\u7d50\u3059\u308b\u30ab\u30fc\u30c9\u3002",
    story: "\u5927\u962a\u306e\u304a\u7b11\u3044\u5730\u56f3\u306b\u5165\u308c\u308b\u306a\u3089\u5916\u305b\u306a\u3044\u30bf\u30a4\u30d7\u3002\u82b8\u4eba\u63a2\u7d22MAP\u306e\u6838\u306b\u306a\u308a\u3084\u3059\u3044\u3002"
  }
];

const areasToAdd = [
  { id: "shiga-aisho", name: "\u6ecb\u8cc0\u611b\u8358", center: [136.211, 35.171], zoom: 14, vibe: "\u30c0\u30a4\u30a2\u30f3\u306e\u5730\u5143\u8a18\u61b6\u3092\u305f\u3069\u308c\u308b\u3001\u30b3\u30f3\u30d3\u306e\u539f\u98a8\u666f\u306b\u8fd1\u3044\u63a2\u7d22\u30a8\u30ea\u30a2\u3002" },
  { id: "hikone", name: "\u5f66\u6839", center: [136.263, 35.27], zoom: 14, vibe: "\u30c0\u30a4\u30a2\u30f3\u304c2\u4eba\u3067\u901a\u3063\u305f\u98df\u306e\u8a18\u61b6\u3092\u8ffd\u3048\u308b\u6ecb\u8cc0\u306e\u8857\u3002" },
  { id: "namba", name: "\u96e3\u6ce2", center: [135.5037, 34.6655], zoom: 15, vibe: "\u5927\u962a\u82b8\u4eba\u306e\u5287\u5834\u6587\u5316\u3068\u98df\u306e\u8a18\u61b6\u304c\u3082\u3063\u3068\u3082\u91cd\u306a\u308a\u3084\u3059\u3044\u4e2d\u5fc3\u5730\u3002" }
];

const existingPlaceIds = new Set(places.features.map((feature) => feature.properties.id));

for (const place of confirmedPlaces) {
  if (existingPlaceIds.has(place.id)) continue;

  places.features.push({
    type: "Feature",
    geometry: { type: "Point", coordinates: place.coordinates },
    properties: {
      id: place.id,
      name: place.name,
      catch: place.catch,
      category: place.category,
      area: place.area,
      role: "clue",
      importance: "high",
      heLevel: place.heLevel,
      address: place.address,
      googleMapsUrl: place.googleMapsUrl,
      tags: place.tags,
      relatedComedians: place.relatedComedians,
      scene: place.scene,
      sourceStatus: confirmedStatus,
      sourceProgram,
      sourceEpisode: place.sourceEpisode,
      sourceDate: place.sourceDate,
      sourceUrl: place.sourceUrl,
      talkSummary: place.talkSummary,
      story: place.story,
      sourceMemo: "\u0054\u0042\u0053\u516c\u5f0f\u30a2\u30fc\u30ab\u30a4\u30d6\u3067\u756a\u7d44\u56de\u30fb\u5e97\u540d\u30fb\u4f4f\u6240\u3092\u78ba\u8a8d"
    }
  });
}

const existingAreaIds = new Set(areas.map((area) => area.id));
for (const area of areasToAdd) {
  if (!existingAreaIds.has(area.id)) areas.push(area);
}

fs.writeFileSync(placesPath, `${JSON.stringify(places, null, 2)}\n`, "utf8");
fs.writeFileSync(areasPath, `${JSON.stringify(areas, null, 2)}\n`, "utf8");
