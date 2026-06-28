const fs = require("fs");
const path = require("path");

const placesPath = path.join(process.cwd(), "public", "data", "places.geojson");
const areasPath = path.join(process.cwd(), "public", "data", "areas.json");
const places = JSON.parse(fs.readFileSync(placesPath, "utf8"));
const areas = JSON.parse(fs.readFileSync(areasPath, "utf8"));

const clue = {
  id: "r021",
  name: "\u3082\u3093\u3058\u3083 \u5927\u6c5f\u6238\u5742\u4e95",
  catch: "\u6d77\u539f\u3084\u3059\u3088 \u3068\u3082\u3053\u56de\u306b\u51fa\u305f\u3001\u6708\u5cf6\u306e\u7121\u9650\u30eb\u30fc\u30d7\u3082\u3093\u3058\u3083",
  category: "\u3082\u3093\u3058\u3083",
  area: "\u6708\u5cf6",
  coordinates: [139.784, 35.6646],
  heLevel: 4,
  address: "\u6771\u4eac\u90fd\u4e2d\u592e\u533a\u6708\u5cf61-8-1 \u30a2\u30a4\u30de\u30fc\u30af\u30bf\u30ef\u30fc102",
  googleMapsUrl: "https://www.google.com/maps/search/?api=1&query=%E3%82%82%E3%82%93%E3%81%98%E3%82%83%20%E5%A4%A7%E6%B1%9F%E6%88%B8%E5%9D%82%E4%BA%95",
  tags: ["#\u6d77\u539f\u3084\u3059\u3088\u3068\u3082\u3053", "#\u6708\u5cf6", "#\u4eba\u751f\u6700\u9ad8\u30ec\u30b9\u30c8\u30e9\u30f3", "#\u3082\u3093\u3058\u3083"],
  relatedComedians: ["\u6d77\u539f\u3084\u3059\u3088 \u3068\u3082\u3053"],
  sourceProgram: "\u0054\u0042\u0053\u30c6\u30ec\u30d3\u300c\u4eba\u751f\u6700\u9ad8\u30ec\u30b9\u30c8\u30e9\u30f3\u300d",
  sourceEpisode: "2025\u5e745\u670831\u65e5\u653e\u9001 \u3054\u3061\u305d\u3046\u69d8 \u6d77\u539f\u3084\u3059\u3088 \u3068\u3082\u3053",
  sourceDate: "2025\u5e745\u670831\u65e5",
  sourceUrl: "https://www.tbs.co.jp/saikourestaurant/archive/202505311/",
  talkSummary: "\u756a\u7d44\u516c\u5f0f\u30a2\u30fc\u30ab\u30a4\u30d6\u3067\u3001\u6771\u4eac\u30fb\u6708\u5cf6\u300c\u7121\u9650\u30eb\u30fc\u30d7\u98df\u3044\uff01\u6708\u5cf6\u3082\u3093\u3058\u3083\u300d\u3068\u3057\u3066\u7d39\u4ecb\u3002\u5e97\u8217\u60c5\u5831\u3068\u3057\u3066\u300c\u3082\u3093\u3058\u3083 \u5927\u6c5f\u6238\u5742\u4e95\u300d\u304c\u63b2\u8f09\u3055\u308c\u3066\u3044\u308b\u3002",
  scene: "\u884c\u304d\u3064\u3051\u65ad\u5b9a\u3067\u306f\u306a\u3044\u304c\u3001\u59c9\u59b9\u6f2b\u624d\u30b3\u30f3\u30d3\u306e\u756a\u7d44\u56de\u306b\u6b8b\u308b\u6771\u4eac\u306e\u98df\u306e\u8a18\u61b6\u3002\u5287\u5834\u5468\u8fba\u306b\u504f\u3089\u306a\u3044\u5730\u56f3\u306e\u5e83\u304c\u308a\u306b\u52b9\u304f\u3002",
  story: "\u6708\u5cf6\u306e\u3082\u3093\u3058\u3083\u306f\u8857\u305d\u306e\u3082\u306e\u304c\u30b3\u30f3\u30c6\u30f3\u30c4\u3002\u5927\u962a\u6f2b\u624d\u5e2b\u3068\u6771\u4eac\u306e\u4e0b\u753a\u30b0\u30eb\u30e1\u304c\u91cd\u306a\u308b\u306e\u304c\u9762\u767d\u3044\u3002",
  sourceMemo: "\u0054\u0042\u0053\u516c\u5f0f\u30a2\u30fc\u30ab\u30a4\u30d6\u3067\u756a\u7d44\u56de\u30fb\u5e97\u540d\u30fb\u4f4f\u6240\u3092\u78ba\u8a8d"
};

const existingPlaceIds = new Set(places.features.map((feature) => feature.properties.id));
if (!existingPlaceIds.has(clue.id)) {
  places.features.push({
    type: "Feature",
    geometry: { type: "Point", coordinates: clue.coordinates },
    properties: {
      id: clue.id,
      name: clue.name,
      catch: clue.catch,
      category: clue.category,
      area: clue.area,
      role: "clue",
      importance: "medium",
      heLevel: clue.heLevel,
      address: clue.address,
      googleMapsUrl: clue.googleMapsUrl,
      tags: clue.tags,
      relatedComedians: clue.relatedComedians,
      scene: clue.scene,
      sourceStatus: "\u51fa\u5178\u78ba\u8a8d\u6e08\u307f",
      sourceProgram: clue.sourceProgram,
      sourceEpisode: clue.sourceEpisode,
      sourceDate: clue.sourceDate,
      sourceUrl: clue.sourceUrl,
      talkSummary: clue.talkSummary,
      story: clue.story,
      sourceMemo: clue.sourceMemo
    }
  });
}

if (!areas.some((area) => area.id === "tsukishima")) {
  areas.push({
    id: "tsukishima",
    name: "\u6708\u5cf6",
    center: [139.784, 35.6646],
    zoom: 15,
    vibe: "\u5287\u5834\u3068\u306f\u5225\u306e\u3001\u6771\u4eac\u306e\u4e0b\u753a\u30b0\u30eb\u30e1\u6587\u8108\u3092\u62fe\u3048\u308b\u8857\u3002"
  });
}

fs.writeFileSync(placesPath, `${JSON.stringify(places, null, 2)}\n`, "utf8");
fs.writeFileSync(areasPath, `${JSON.stringify(areas, null, 2)}\n`, "utf8");
