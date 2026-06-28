const fs = require("fs");
const path = require("path");

const placesPath = path.join(process.cwd(), "public", "data", "places.geojson");
const places = JSON.parse(fs.readFileSync(placesPath, "utf8"));

const confirmedStatus = "\u51fa\u5178\u78ba\u8a8d\u6e08\u307f";
const sourceProgram = "\u0054\u0042\u0053\u30c6\u30ec\u30d3\u300c\u4eba\u751f\u6700\u9ad8\u30ec\u30b9\u30c8\u30e9\u30f3\u300d";
const sourceMemo = "\u0054\u0042\u0053\u516c\u5f0f\u30a2\u30fc\u30ab\u30a4\u30d6\u3067\u756a\u7d44\u56de\u30fb\u5e97\u540d\u30fb\u4f4f\u6240\u3092\u78ba\u8a8d";

const clues = [
  {
    id: "r020",
    name: "\u6e0b\u8c37\u3063\u5b50\u5c45\u9152\u5c4b \u3068\u3068\u3068\u308a\u3068\u3093",
    catch: "\u30cb\u30e5\u30fc\u30e8\u30fc\u30af\u304c\u82b8\u4eba\u4ef2\u9593\u3068\u8a9e\u308a\u5408\u3063\u305f\u3001\u9053\u7384\u5742\u306e\u5c45\u9152\u5c4b\u3081\u3057",
    category: "\u5c45\u9152\u5c4b",
    area: "\u6e0b\u8c37",
    coordinates: [139.6992, 35.6589],
    heLevel: 5,
    address: "\u6771\u4eac\u90fd\u6e0b\u8c37\u533a\u9053\u7384\u57422-7-3 \u4e09\u559c\u30d3\u30eb 3F",
    googleMapsUrl: "https://www.google.com/maps/search/?api=1&query=%E6%B8%8B%E8%B0%B7%E3%81%A3%E5%AD%90%E5%B1%85%E9%85%92%E5%B1%8B%20%E3%81%A8%E3%81%A8%E3%81%A8%E3%82%8A%E3%81%A8%E3%82%93",
    tags: ["#\u30cb\u30e5\u30fc\u30e8\u30fc\u30af", "#\u6e0b\u8c37", "#\u82b8\u4eba\u4ef2\u9593", "#\u5c45\u9152\u5c4b", "#\u884c\u304d\u3064\u3051\u7cfb"],
    relatedComedians: ["\u30cb\u30e5\u30fc\u30e8\u30fc\u30af", "\u5d8b\u4f50\u548c\u4e5f", "\u5c4b\u6577\u88d5\u653f"],
    sourceEpisode: "2023\u5e7412\u670816\u65e5\u653e\u9001 \u3054\u3061\u305d\u3046\u69d8 \u30cb\u30e5\u30fc\u30e8\u30fc\u30af",
    sourceDate: "2023\u5e7412\u670816\u65e5",
    sourceUrl: "https://www.tbs.co.jp/saikourestaurant/oldv8/202312161/",
    talkSummary: "\u756a\u7d44\u516c\u5f0f\u30a2\u30fc\u30ab\u30a4\u30d6\u3067\u3001\u6771\u4eac\u30fb\u6e0b\u8c37\u300c\u82b8\u4eba\u4ef2\u9593\u3068\u8a9e\u308a\u5408\u3063\u305f\uff01\u5c45\u9152\u5c4b\u3081\u3057\u300d\u3068\u3057\u3066\u7d39\u4ecb\u3002\u5e97\u8217\u60c5\u5831\u3068\u3057\u3066\u300c\u6e0b\u8c37\u3063\u5b50\u5c45\u9152\u5c4b \u3068\u3068\u3068\u308a\u3068\u3093\u300d\u304c\u63b2\u8f09\u3055\u308c\u3066\u3044\u308b\u3002",
    scene: "\u201c\u82b8\u4eba\u4ef2\u9593\u3068\u8a9e\u308a\u5408\u3063\u305f\u201d\u3068\u3044\u3046\u516c\u5f0f\u898b\u51fa\u3057\u304c\u5f37\u3044\u3002\u5287\u5834\u306b\u9650\u3089\u306a\u3044\u3001\u6e0b\u8c37\u306e\u82b8\u4eba\u5c0e\u7dda\u3092\u611f\u3058\u3089\u308c\u308b\u30ab\u30fc\u30c9\u3002",
    story: "\u9053\u7384\u5742\u306e\u99c5\u8fd1\u5c45\u9152\u5c4b\u3002\u30cb\u30e5\u30fc\u30e8\u30fc\u30af\u306e\u58f2\u308c\u308b\u524d\u5f8c\u306e\u8a18\u61b6\u3068\u6e0b\u8c37\u306e\u591c\u304c\u3064\u306a\u304c\u308b\u3002"
  }
];

const existingPlaceIds = new Set(places.features.map((feature) => feature.properties.id));

for (const clue of clues) {
  if (existingPlaceIds.has(clue.id)) continue;

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
      importance: "high",
      heLevel: clue.heLevel,
      address: clue.address,
      googleMapsUrl: clue.googleMapsUrl,
      tags: clue.tags,
      relatedComedians: clue.relatedComedians,
      scene: clue.scene,
      sourceStatus: confirmedStatus,
      sourceProgram,
      sourceEpisode: clue.sourceEpisode,
      sourceDate: clue.sourceDate,
      sourceUrl: clue.sourceUrl,
      talkSummary: clue.talkSummary,
      story: clue.story,
      sourceMemo
    }
  });
}

fs.writeFileSync(placesPath, `${JSON.stringify(places, null, 2)}\n`, "utf8");
