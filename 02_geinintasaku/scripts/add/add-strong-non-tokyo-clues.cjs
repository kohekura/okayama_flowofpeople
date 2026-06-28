const fs = require("fs");
const path = require("path");

const placesPath = path.join(process.cwd(), "public", "data", "places.geojson");
const areasPath = path.join(process.cwd(), "public", "data", "areas.json");
const places = JSON.parse(fs.readFileSync(placesPath, "utf8"));
const areas = JSON.parse(fs.readFileSync(areasPath, "utf8"));

const sourceProgram = "TBSテレビ「人生最高レストラン」";
const sourceStatus = "出典確認済み";
const sourceMemo = "TBS公式アーカイブで番組回・店名・住所を確認";

const clues = [
  {
    id: "r029",
    name: "谷九 ふる里",
    catch: "今田耕司さんが40年通う、谷町九丁目の老舗うどんと寿司",
    category: "和食",
    area: "谷町九丁目",
    coordinates: [135.5155, 34.6674],
    heLevel: 5,
    address: "大阪府大阪市天王寺区生玉寺町1-32",
    googleMapsUrl: "https://www.google.com/maps/search/?api=1&query=%E8%B0%B7%E4%B9%9D%20%E3%81%B5%E3%82%8B%E9%87%8C",
    tags: ["#今田耕司", "#40年通う", "#谷町九丁目", "#行きつけ系"],
    relatedComedians: ["今田耕司"],
    sourceEpisode: "2023年2月25日放送 ごちそう様 今田耕司さん",
    sourceDate: "2023年2月25日",
    sourceUrl: "https://www.tbs.co.jp/saikourestaurant/oldv8/202302251/",
    talkSummary: "番組公式アーカイブで、大阪・谷町九丁目「40年通う！老舗のうどんとお寿司」として紹介。店舗情報として「谷九 ふる里」が掲載されている。",
    scene: "公式見出しに“40年通う”とある、かなり強い行きつけ系カード。芸人の長い時間がそのまま店に残っている。",
    story: "うどんと寿司という日常の強さがある。大阪の芸人地図に厚みを足す一軒。"
  },
  {
    id: "r030",
    name: "ともちゃん",
    catch: "博多大吉さんの芸人人生の原点、天神の屋台めし",
    category: "屋台",
    area: "福岡天神",
    coordinates: [130.4017, 33.5914],
    heLevel: 5,
    address: "福岡県福岡市中央区天神1-14",
    googleMapsUrl: "https://www.google.com/maps/search/?api=1&query=%E3%81%A8%E3%82%82%E3%81%A1%E3%82%83%E3%82%93%20%E5%B1%8B%E5%8F%B0%20%E5%A4%A9%E7%A5%9E",
    tags: ["#博多大吉", "#芸人人生の原点", "#福岡", "#屋台"],
    relatedComedians: ["博多大吉", "博多華丸・大吉"],
    sourceEpisode: "2023年9月23日放送 博多大吉さん",
    sourceDate: "2023年9月23日",
    sourceUrl: "https://www.tbs.co.jp/saikourestaurant/oldv8/202309231/",
    talkSummary: "番組公式アーカイブで、福岡・天神「芸人人生の原点の味！屋台めし」かつ人生最高の一品として紹介。店舗情報として「ともちゃん」が掲載されている。",
    scene: "“芸人人生の原点”という見出しが強い。会えるというより、芸人の原点を地図でたどるカード。",
    story: "福岡の屋台文化と芸人の記憶が重なる。遠征したくなるタイプの一軒。"
  },
  {
    id: "r031",
    name: "Genji",
    catch: "ハイヒール・モモコさんが30年以上愛する、帝塚山のウニのババロア",
    category: "洋食",
    area: "帝塚山",
    coordinates: [135.4935, 34.6247],
    heLevel: 5,
    address: "大阪府大阪市西成区玉出東2-14-4 GRACE帝塚山1F",
    googleMapsUrl: "https://www.google.com/maps/search/?api=1&query=Genji%20%E5%B8%9D%E5%A1%9A%E5%B1%B1",
    tags: ["#ハイヒールモモコ", "#30年以上", "#大阪", "#行きつけ系"],
    relatedComedians: ["ハイヒール・モモコ", "ハイヒール"],
    sourceEpisode: "2024年9月28日放送 ごちそう様 ハイヒール・モモコさん",
    sourceDate: "2024年9月28日",
    sourceUrl: "https://www.tbs.co.jp/saikourestaurant/oldv8/202409281/",
    talkSummary: "番組公式アーカイブで、大阪・帝塚山「30年以上愛してやまない！ウニのババロア」かつ人生最高の一品として紹介。店舗情報として「Genji」が掲載されている。",
    scene: "“30年以上愛してやまない”は行きつけに近い強い文脈。長く愛されている店として説得力がある。",
    story: "料理名のインパクトも強く、カードとして読ませる力がある。"
  }
];

const areaAdds = [
  { id: "tanimachi9", name: "谷町九丁目", center: [135.5155, 34.6674], zoom: 15, vibe: "大阪芸人が長く通う食の記憶を拾える、落ち着いた探索エリア。" },
  { id: "fukuoka-tenjin", name: "福岡天神", center: [130.4017, 33.5914], zoom: 15, vibe: "博多芸人の原点や屋台文化をたどれるエリア。" },
  { id: "tezukayama", name: "帝塚山", center: [135.4935, 34.6247], zoom: 15, vibe: "大阪のベテラン芸人が長く愛する店の記憶が残る街。" }
];

const existing = new Set(places.features.map((feature) => feature.properties.id));
for (const clue of clues) {
  if (existing.has(clue.id)) continue;
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
      sourceStatus: sourceStatus,
      sourceProgram: sourceProgram,
      sourceEpisode: clue.sourceEpisode,
      sourceDate: clue.sourceDate,
      sourceUrl: clue.sourceUrl,
      talkSummary: clue.talkSummary,
      story: clue.story,
      sourceMemo: sourceMemo
    }
  });
}

const existingAreaIds = new Set(areas.map((area) => area.id));
for (const area of areaAdds) {
  if (!existingAreaIds.has(area.id)) areas.push(area);
}

fs.writeFileSync(placesPath, `${JSON.stringify(places, null, 2)}\n`, "utf8");
fs.writeFileSync(areasPath, `${JSON.stringify(areas, null, 2)}\n`, "utf8");
