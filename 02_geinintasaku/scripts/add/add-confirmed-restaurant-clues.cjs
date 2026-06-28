const fs = require("fs");
const path = require("path");

const placesPath = path.join(process.cwd(), "public", "data", "places.geojson");
const areasPath = path.join(process.cwd(), "public", "data", "areas.json");
const places = JSON.parse(fs.readFileSync(placesPath, "utf8"));
const areas = JSON.parse(fs.readFileSync(areasPath, "utf8"));

const confirmedPlaces = [
  {
    id: "r001",
    name: "たこしげ",
    catch: "大悟さんの貧乏時代を支えた、愛情ナポリタン",
    category: "居酒屋",
    area: "大阪日本橋",
    coordinates: [135.5087, 34.6589],
    heLevel: 5,
    address: "大阪府大阪市浪速区日本橋東2-2-14 ナカガワマンション 1F",
    googleMapsUrl: "https://www.google.com/maps/search/?api=1&query=%E3%81%9F%E3%81%93%E3%81%97%E3%81%92%20%E5%A4%A7%E9%98%AA%20%E6%97%A5%E6%9C%AC%E6%A9%8B",
    tags: ["#千鳥", "#大悟", "#人生最高レストラン", "#大阪日本橋"],
    relatedComedians: ["千鳥", "大悟"],
    sourceProgram: "TBSテレビ「人生最高レストラン」",
    sourceEpisode: "2026年5月30日放送 ごちそう様 千鳥 大悟さん",
    sourceDate: "2026年5月30日",
    sourceUrl: "https://www.tbs.co.jp/saikourestaurant/archive/202605301/",
    talkSummary:
      "番組公式アーカイブで、大阪・日本橋「貧乏時代の支え！愛情ナポリタン」として紹介。店舗情報として「たこしげ」が掲載されている。",
    scene:
      "若手時代の食の記憶と店名が公式に残っている。単なる人気店ではなく、芸人の下積みの時間をたどれる強い手がかり。",
    story:
      "大阪日本橋の空気と、腹を満たすごはんの温度が重なる店。カードとしてかなり良い。",
    sourceMemo: "TBS公式アーカイブで番組回・店名・住所を確認"
  },
  {
    id: "r002",
    name: "三と十",
    catch: "大悟さんが笑いの神様と堪能した、麻布十番の焼きそば",
    category: "居酒屋",
    area: "麻布十番",
    coordinates: [139.7335, 35.6546],
    heLevel: 5,
    address: "東京都港区麻布十番2-12-4 第2コーボービル2F",
    googleMapsUrl: "https://www.google.com/maps/search/?api=1&query=%E4%B8%89%E3%81%A8%E5%8D%81%20%E9%BA%BB%E5%B8%83%E5%8D%81%E7%95%AA",
    tags: ["#千鳥", "#大悟", "#志村けん", "#麻布十番"],
    relatedComedians: ["千鳥", "大悟", "志村けん"],
    sourceProgram: "TBSテレビ「人生最高レストラン」",
    sourceEpisode: "2026年5月30日放送 ごちそう様 千鳥 大悟さん",
    sourceDate: "2026年5月30日",
    sourceUrl: "https://www.tbs.co.jp/saikourestaurant/archive/202605301/",
    talkSummary:
      "番組公式アーカイブで、東京・麻布十番「笑いの神様と堪能！肉増し焼きそば」として紹介。店舗情報として「三と十」が掲載されている。",
    scene:
      "大悟さんと志村けんさんの思い出の文脈で出てくる店。芸人同士の縦の関係まで感じられる手がかり。",
    story:
      "麻布十番の落ち着いた夜に、焼きそばの強さがある。地図で見るとかなり味が出る。",
    sourceMemo: "TBS公式アーカイブで番組回・店名・住所を確認"
  },
  {
    id: "r003",
    name: "すし処まさる",
    catch: "大悟さんの“人生最高の一品”として残る寿司店",
    category: "寿司",
    area: "四天王寺前",
    coordinates: [135.5127, 34.6575],
    heLevel: 5,
    address: "大阪府大阪市浪速区下寺2-3-10 梅吉マンション1F",
    googleMapsUrl: "https://www.google.com/maps/search/?api=1&query=%E3%81%99%E3%81%97%E5%87%A6%E3%81%BE%E3%81%95%E3%82%8B%20%E5%A4%A7%E9%98%AA",
    tags: ["#千鳥", "#大悟", "#人生最高の一品", "#寿司"],
    relatedComedians: ["千鳥", "大悟"],
    sourceProgram: "TBSテレビ「人生最高レストラン」",
    sourceEpisode: "2026年5月30日放送 ごちそう様 千鳥 大悟さん",
    sourceDate: "2026年5月30日",
    sourceUrl: "https://www.tbs.co.jp/saikourestaurant/archive/202605301/",
    talkSummary:
      "番組公式アーカイブで、大阪・四天王寺前「両親との思い出が残る高級寿司」かつ人生最高の一品として紹介。店舗情報として「すし処まさる」が掲載されている。",
    scene:
      "行きつけというより、人生の節目と結びついた食の記憶。芸人の物語を深く見せられるカード。",
    story:
      "派手な探索ではなく、記憶の重さで光る店。ストックしたくなるタイプの一軒。",
    sourceMemo: "TBS公式アーカイブで番組回・店名・住所を確認"
  },
  {
    id: "r004",
    name: "三吉うどん",
    catch: "さらば青春の光の下積みを支えた、170円のうどん",
    category: "うどん",
    area: "新世界",
    coordinates: [135.506, 34.6524],
    heLevel: 5,
    address: "大阪府大阪市浪速区恵美須東1-18-6",
    googleMapsUrl: "https://www.google.com/maps/search/?api=1&query=%E4%B8%89%E5%90%89%E3%81%86%E3%81%A9%E3%82%93%20%E6%96%B0%E4%B8%96%E7%95%8C",
    tags: ["#さらば青春の光", "#人生最高レストラン", "#下積み", "#新世界"],
    relatedComedians: ["さらば青春の光", "森田哲矢", "東ブクロ"],
    sourceProgram: "TBSテレビ「人生最高レストラン」",
    sourceEpisode: "2024年7月6日放送 ごちそう様 さらば青春の光",
    sourceDate: "2024年7月6日",
    sourceUrl: "https://www.tbs.co.jp/saikourestaurant/oldv8/202407061/",
    talkSummary:
      "番組公式アーカイブで、大阪・新世界「下積み時代を支えてくれた！170円のうどん」として紹介。店舗情報として「三吉うどん」が掲載されている。",
    scene:
      "下積み時代を支えたという見出しが強い。芸人の売れる前の時間を地図でたどれる、かなり良い手がかり。",
    story:
      "安くて早くて温かい一杯。芸人の物語と相性が良すぎる店。",
    sourceMemo: "TBS公式アーカイブで番組回・店名・住所を確認"
  },
  {
    id: "r005",
    name: "DEN・EN",
    catch: "さらば青春の光が大阪時代に通った老舗レストラン",
    category: "洋食",
    area: "新世界",
    coordinates: [135.5066, 34.6506],
    heLevel: 5,
    address: "大阪市浪速区恵美須東2-3-22",
    googleMapsUrl: "https://www.google.com/maps/search/?api=1&query=DEN%E3%83%BBEN%20%E6%96%B0%E4%B8%96%E7%95%8C",
    tags: ["#さらば青春の光", "#通った", "#新世界", "#洋食"],
    relatedComedians: ["さらば青春の光", "森田哲矢", "東ブクロ"],
    sourceProgram: "TBSテレビ「人生最高レストラン」",
    sourceEpisode: "2024年7月6日放送 ごちそう様 さらば青春の光",
    sourceDate: "2024年7月6日",
    sourceUrl: "https://www.tbs.co.jp/saikourestaurant/oldv8/202407061/",
    talkSummary:
      "番組公式アーカイブで、大阪・新世界「大阪時代に通った！老舗レストラン」として紹介。店舗情報として「DEN・EN」が掲載されている。",
    scene:
      "“通った”という言葉が公式アーカイブに残る、かなり採用しやすい手がかり。新世界エリアの濃さも出る。",
    story:
      "レトロな洋食の気配が、芸人の大阪時代の記憶とよく合う。",
    sourceMemo: "TBS公式アーカイブで番組回・店名・住所を確認"
  },
  {
    id: "r006",
    name: "さらばBAR",
    catch: "さらば青春の光が経営する、五反田の根城",
    category: "バー",
    area: "五反田",
    coordinates: [139.7224, 35.6259],
    heLevel: 5,
    address: "東京都品川区西五反田2-11-11 ヒルトップ五反田ハイツ101",
    googleMapsUrl: "https://www.google.com/maps/search/?api=1&query=%E3%81%95%E3%82%89%E3%81%B0BAR%20%E4%BA%94%E5%8F%8D%E7%94%B0",
    tags: ["#さらば青春の光", "#五反田", "#バー", "#本人経営"],
    relatedComedians: ["さらば青春の光", "森田哲矢", "東ブクロ"],
    sourceProgram: "TBSテレビ「人生最高レストラン」",
    sourceEpisode: "2024年7月6日放送 ごちそう様 さらば青春の光",
    sourceDate: "2024年7月6日",
    sourceUrl: "https://www.tbs.co.jp/saikourestaurant/oldv8/202407061/",
    talkSummary:
      "番組公式アーカイブで、東京・五反田「さらば青春の光が経営するBAR」として紹介。店舗情報として「さらばBAR」が掲載されている。",
    scene:
      "行きつけを超えて、本人たちの活動拠点に近いカード。五反田を芸人探索の街として見せるのに強い。",
    story:
      "店名だけでストーリーが立つ。地図上で見つけた時の引きがかなりある。",
    sourceMemo: "TBS公式アーカイブで番組回・店名・住所を確認"
  },
  {
    id: "r007",
    name: "SO-TEN",
    catch: "さらば青春の光が東京での成功を噛みしめた創作和食",
    category: "和食",
    area: "恵比寿",
    coordinates: [139.7143, 35.6445],
    heLevel: 5,
    address: "東京都渋谷区恵比寿4-27-4",
    googleMapsUrl: "https://www.google.com/maps/search/?api=1&query=SO-TEN%20%E6%81%B5%E6%AF%94%E5%AF%BF",
    tags: ["#さらば青春の光", "#人生最高の一品", "#恵比寿", "#和食"],
    relatedComedians: ["さらば青春の光", "森田哲矢", "東ブクロ"],
    sourceProgram: "TBSテレビ「人生最高レストラン」",
    sourceEpisode: "2024年7月6日放送 ごちそう様 さらば青春の光",
    sourceDate: "2024年7月6日",
    sourceUrl: "https://www.tbs.co.jp/saikourestaurant/oldv8/202407061/",
    talkSummary:
      "番組公式アーカイブで、東京・恵比寿「東京での成功を噛みしめた！創作和食」かつ人生最高の一品として紹介。店舗情報として「SO-TEN」が掲載されている。",
    scene:
      "下積みの新世界から、成功を噛みしめる恵比寿へ。地図上で見ると芸人人生の移動が見える。",
    story:
      "恵比寿らしい大人の店。さらば青春の光のストーリーに奥行きを足せる。",
    sourceMemo: "TBS公式アーカイブで番組回・店名・住所を確認"
  },
  {
    id: "r008",
    name: "中國飯店 六本木店",
    catch: "藤森慎吾さんが“天下統一”を宣言された中国料理",
    category: "中華",
    area: "六本木",
    coordinates: [139.728, 35.6629],
    heLevel: 4,
    address: "東京都港区西麻布 1-1-5 オリエンタルビル 1F",
    googleMapsUrl: "https://www.google.com/maps/search/?api=1&query=%E4%B8%AD%E5%9C%8B%E9%A3%AF%E5%BA%97%20%E5%85%AD%E6%9C%AC%E6%9C%A8%E5%BA%97",
    tags: ["#藤森慎吾", "#オリエンタルラジオ", "#人生最高レストラン", "#六本木"],
    relatedComedians: ["オリエンタルラジオ", "藤森慎吾"],
    sourceProgram: "TBSテレビ「人生最高レストラン」",
    sourceEpisode: "2024年8月10日放送 ごちそう様 オリエンタルラジオ 藤森慎吾さん",
    sourceDate: "2024年8月10日",
    sourceUrl: "https://www.tbs.co.jp/saikourestaurant/oldv8/202408101/",
    talkSummary:
      "番組公式アーカイブで、東京・六本木「天下統一を宣言された！中国料理」として紹介。店舗情報として「中國飯店 六本木店」が掲載されている。",
    scene:
      "行きつけ断定ではなく、番組で語られた食の記憶。六本木の芸能仕事の文脈とも接続しやすい。",
    story:
      "老舗感と華やかさがあり、六本木のカードとして見栄えがいい。",
    sourceMemo: "TBS公式アーカイブで番組回・店名・住所を確認"
  },
  {
    id: "r009",
    name: "ラジャ ヴェッタ 白金高輪店",
    catch: "タカアンドトシの上京生活を支えた、まかないパスタ",
    category: "イタリアン",
    area: "白金高輪",
    coordinates: [139.7356, 35.6378],
    heLevel: 4,
    address: "東京都港区高輪2-16-49 レザミ高輪ビル 1F",
    googleMapsUrl: "https://www.google.com/maps/search/?api=1&query=%E3%83%A9%E3%82%B8%E3%83%A3%20%E3%83%B4%E3%82%A7%E3%83%83%E3%82%BF%20%E7%99%BD%E9%87%91%E9%AB%98%E8%BC%AA%E5%BA%97",
    tags: ["#タカアンドトシ", "#上京生活", "#人生最高レストラン", "#白金高輪"],
    relatedComedians: ["タカアンドトシ", "タカ", "トシ"],
    sourceProgram: "TBSテレビ「人生最高レストラン」",
    sourceEpisode: "2024年8月31日放送 ごちそう様 タカアンドトシさん",
    sourceDate: "2024年8月31日",
    sourceUrl: "https://www.tbs.co.jp/saikourestaurant/oldv8/202408311/",
    talkSummary:
      "番組公式アーカイブで、東京・白金高輪「上京生活を支えた！まかないパスタ」として紹介。店舗情報として「ラジャ ヴェッタ 白金高輪店」が掲載されている。",
    scene:
      "上京生活を支えたという文脈が強い。芸人が東京に根を張っていく時間を感じられるカード。",
    story:
      "白金高輪の落ち着きと、まかないパスタの生活感のギャップが良い。",
    sourceMemo: "TBS公式アーカイブで番組回・店名・住所を確認"
  }
];

const additionalAreas = [
  { id: "osaka-nihonbashi", name: "大阪日本橋", center: [135.5087, 34.6589], zoom: 15, vibe: "大悟さんの若手時代や、なんば周辺の劇場文化とつながる大阪の探索エリア。" },
  { id: "azabujuban", name: "麻布十番", center: [139.7335, 35.6546], zoom: 15, vibe: "芸人同士の食事や、大人の店の記憶が残りやすい東京の夜の街。" },
  { id: "shitennoji", name: "四天王寺前", center: [135.5127, 34.6575], zoom: 15, vibe: "大阪の思い出深い食の記憶を追うための静かな探索エリア。" },
  { id: "shinsekai", name: "新世界", center: [135.5063, 34.6514], zoom: 15, vibe: "さらば青春の光の下積み時代の食の記憶が濃く残る、大阪らしい探索エリア。" },
  { id: "gotanda", name: "五反田", center: [139.7224, 35.6259], zoom: 15, vibe: "さらば青春の光の拠点感があり、東京芸人の少し生々しい導線が見える街。" },
  { id: "ebisu", name: "恵比寿", center: [139.7143, 35.6445], zoom: 15, vibe: "成功後の食の記憶や、大人の芸人カルチャーを拾いやすい街。" },
  { id: "roppongi", name: "六本木", center: [139.728, 35.6629], zoom: 15, vibe: "テレビ、芸能、食事の文脈が交わる、華やかな探索エリア。" },
  { id: "shirokane", name: "白金高輪", center: [139.7356, 35.6378], zoom: 15, vibe: "上京生活や仕事の節目と結びつく、落ち着いた食の記憶を拾う街。" }
];

const existingPlaceIds = new Set(places.features.map((feature) => feature.properties.id));

for (const place of confirmedPlaces) {
  if (existingPlaceIds.has(place.id)) {
    continue;
  }

  places.features.push({
    type: "Feature",
    geometry: {
      type: "Point",
      coordinates: place.coordinates
    },
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
      sourceStatus: "出典確認済み",
      sourceProgram: place.sourceProgram,
      sourceEpisode: place.sourceEpisode,
      sourceDate: place.sourceDate,
      sourceUrl: place.sourceUrl,
      talkSummary: place.talkSummary,
      story: place.story,
      sourceMemo: place.sourceMemo
    }
  });
}

const existingAreaIds = new Set(areas.map((area) => area.id));
for (const area of additionalAreas) {
  if (!existingAreaIds.has(area.id)) {
    areas.push(area);
  }
}

fs.writeFileSync(placesPath, `${JSON.stringify(places, null, 2)}\n`, "utf8");
fs.writeFileSync(areasPath, `${JSON.stringify(areas, null, 2)}\n`, "utf8");
