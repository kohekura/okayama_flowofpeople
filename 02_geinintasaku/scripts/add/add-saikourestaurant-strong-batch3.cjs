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
    id: "r022",
    name: "満州王",
    catch: "今田耕司さんが松本人志さんと通った、東高円寺の町中華",
    category: "中華",
    area: "東高円寺",
    coordinates: [139.6587, 35.6977],
    heLevel: 5,
    address: "東京都杉並区高円寺南1-11-1",
    googleMapsUrl: "https://www.google.com/maps/search/?api=1&query=%E6%BA%80%E5%B7%9E%E7%8E%8B%20%E6%9D%B1%E9%AB%98%E5%86%86%E5%AF%BA",
    tags: ["#今田耕司", "#松本人志", "#通った", "#東高円寺", "#行きつけ系"],
    relatedComedians: ["今田耕司", "松本人志"],
    sourceEpisode: "2023年2月25日放送 ごちそう様 今田耕司さん",
    sourceDate: "2023年2月25日",
    sourceUrl: "https://www.tbs.co.jp/saikourestaurant/oldv8/202302251/",
    talkSummary: "番組公式アーカイブで、東京・東高円寺「松本人志と通った！思い出の町中華」として紹介。店舗情報として「満州王」が掲載されている。",
    scene: "公式見出しに“通った”と残る強い手がかり。芸人同士の関係と若い頃の時間が、東高円寺の町中華に重なる。",
    story: "派手な店ではなく、町中華という生活感が良い。都内の劇場外エリアに強い芯を作れるカード。"
  },
  {
    id: "r023",
    name: "みはら庵",
    catch: "バイきんぐの下積み時代を支えた、千川のカツ丼",
    category: "和食",
    area: "千川",
    coordinates: [139.6892, 35.7383],
    heLevel: 5,
    address: "東京都豊島区要町3-9-13 2F",
    googleMapsUrl: "https://www.google.com/maps/search/?api=1&query=%E3%81%BF%E3%81%AF%E3%82%89%E5%BA%B5%20%E5%8D%83%E5%B7%9D",
    tags: ["#バイきんぐ", "#下積み", "#千川", "#カツ丼", "#行きつけ系"],
    relatedComedians: ["バイきんぐ", "小峠英二", "西村瑞樹"],
    sourceEpisode: "2023年3月18日放送 ごちそう様 バイきんぐ 小峠英二さん・西村瑞樹さん",
    sourceDate: "2023年3月18日",
    sourceUrl: "https://www.tbs.co.jp/saikourestaurant/oldv8/202303181/",
    talkSummary: "番組公式アーカイブで、東京・千川「下積み時代を支えた！カツ丼」かつ人生最高の一品として紹介。店舗情報として「みはら庵」が掲載されている。",
    scene: "“下積み時代を支えた”という文脈が、会える場所MAPにかなり合う。東京の売れる前の生活導線を想像できる。",
    story: "千川という少し外したエリアも良い。芸人の地図が新宿・渋谷だけではないことを見せられる。"
  },
  {
    id: "r024",
    name: "鍋屋横丁 やきとん なべ屋",
    catch: "ヒコロヒーさんの下積み時代を支えた、中野のボリュームめし",
    category: "居酒屋",
    area: "中野",
    coordinates: [139.6715, 35.6975],
    heLevel: 5,
    address: "東京都中野区中央4-2-3 日興マンション 1F",
    googleMapsUrl: "https://www.google.com/maps/search/?api=1&query=%E9%8D%8B%E5%B1%8B%E6%A8%AA%E4%B8%81%20%E3%82%84%E3%81%8D%E3%81%A8%E3%82%93%20%E3%81%AA%E3%81%B9%E5%B1%8B",
    tags: ["#ヒコロヒー", "#下積み", "#中野", "#やきとん", "#行きつけ系"],
    relatedComedians: ["ヒコロヒー"],
    sourceEpisode: "2023年6月24日放送 ごちそう様 ヒコロヒーさん",
    sourceDate: "2023年6月24日",
    sourceUrl: "https://www.tbs.co.jp/saikourestaurant/oldv8/202306241/",
    talkSummary: "番組公式アーカイブで「下積み時代を支えた！ボリュームめし」として紹介。店舗情報として「鍋屋横丁 やきとん なべ屋」が掲載されている。",
    scene: "中野エリアの強い手がかり。芸人の下積みと、街の飲み屋文化が自然につながる。",
    story: "ボリュームめしという言葉が良い。食べに行く理由がすぐ伝わるカード。"
  },
  {
    id: "r025",
    name: "鶏々舎",
    catch: "ウエストランドがM-1王者になるまでお世話になった、代田橋の焼き鳥",
    category: "居酒屋",
    area: "代田橋",
    coordinates: [139.6588, 35.6717],
    heLevel: 5,
    address: "東京都世田谷区大原2-18-3 コーポはなみずき1F",
    googleMapsUrl: "https://www.google.com/maps/search/?api=1&query=%E9%B6%8F%E3%80%85%E8%88%8E%20%E4%BB%A3%E7%94%B0%E6%A9%8B",
    tags: ["#ウエストランド", "#M1", "#代田橋", "#焼き鳥", "#行きつけ系"],
    relatedComedians: ["ウエストランド", "井口浩之", "河本太"],
    sourceEpisode: "2023年8月5日放送 ウエストランド 井口浩之さん・河本太さん",
    sourceDate: "2023年8月5日",
    sourceUrl: "https://www.tbs.co.jp/saikourestaurant/oldv8/202308051/",
    talkSummary: "番組公式アーカイブで、東京・代田橋「M-1チャンピオンになるまでお世話になった！涙の焼き鳥」として紹介。店舗情報として「鶏々舎」が掲載されている。",
    scene: "“お世話になった”の文脈が強い。芸人の売れる前後を支えた店として、かなりコンセプトに近い。",
    story: "代田橋の焼き鳥店という渋さが良い。都内の探索範囲を自然に広げてくれる。"
  },
  {
    id: "r026",
    name: "松月庵",
    catch: "東京03角田さんの下積み時代の思い出、東高円寺のカツカレー",
    category: "和食",
    area: "東高円寺",
    coordinates: [139.6585, 35.6976],
    heLevel: 5,
    address: "東京都杉並区高円寺南1-11-3",
    googleMapsUrl: "https://www.google.com/maps/search/?api=1&query=%E6%9D%BE%E6%9C%88%E5%BA%B5%20%E6%9D%B1%E9%AB%98%E5%86%86%E5%AF%BA",
    tags: ["#東京03", "#角田晃広", "#下積み", "#東高円寺", "#行きつけ系"],
    relatedComedians: ["東京03", "角田晃広"],
    sourceEpisode: "2023年11月4日放送 東京03角田晃広さん",
    sourceDate: "2023年11月4日",
    sourceUrl: "https://www.tbs.co.jp/saikourestaurant/oldv8/202311041/",
    talkSummary: "番組公式アーカイブで、東京・東高円寺「下積み時代の思い出！カツカレー」として紹介。店舗情報として「松月庵」が掲載されている。",
    scene: "東高円寺に芸人の下積みカードが複数立つことで、街としての説得力が出る。劇場近くではない都内芸人マップの良い核。",
    story: "カツカレーという日常食が、下積みの記憶とよく合う。"
  },
  {
    id: "r027",
    name: "KO-LA 池尻店",
    catch: "東京03角田さんの芸人人生を変えた、池尻大橋の焼肉",
    category: "焼肉",
    area: "池尻大橋",
    coordinates: [139.6816, 35.6504],
    heLevel: 5,
    address: "東京都世田谷区池尻3-16-2",
    googleMapsUrl: "https://www.google.com/maps/search/?api=1&query=KO-LA%20%E6%B1%A0%E5%B0%BB%E5%BA%97",
    tags: ["#東京03", "#角田晃広", "#池尻大橋", "#焼肉"],
    relatedComedians: ["東京03", "角田晃広"],
    sourceEpisode: "2023年11月4日放送 東京03角田晃広さん",
    sourceDate: "2023年11月4日",
    sourceUrl: "https://www.tbs.co.jp/saikourestaurant/oldv8/202311041/",
    talkSummary: "番組公式アーカイブで、東京・池尻大橋「芸人人生を変えた！焼き肉」かつ人生最高の一品として紹介。店舗情報として「KO‐LA 池尻店」が掲載されている。",
    scene: "行きつけ断定ではないが、“芸人人生を変えた”という見出しが強い。池尻大橋にも芸人の食の記憶を置ける。",
    story: "都心から少し外れた焼肉店。芸人の節目を感じるカードとして使える。"
  },
  {
    id: "r028",
    name: "居酒屋たこしげ",
    catch: "サバンナ高橋さんの下積み時代の思い出が詰まった、千日前の居酒屋めし",
    category: "居酒屋",
    area: "千日前",
    coordinates: [135.5061, 34.6687],
    heLevel: 5,
    address: "大阪府大阪市中央区千日前1-4-1",
    googleMapsUrl: "https://www.google.com/maps/search/?api=1&query=%E5%B1%85%E9%85%92%E5%B1%8B%E3%81%9F%E3%81%93%E3%81%97%E3%81%92%20%E5%8D%83%E6%97%A5%E5%89%8D",
    tags: ["#サバンナ", "#高橋茂雄", "#下積み", "#千日前", "#行きつけ系"],
    relatedComedians: ["サバンナ", "高橋茂雄"],
    sourceEpisode: "2023年2月11日放送 ごちそう様 高橋茂雄さん（サバンナ）",
    sourceDate: "2023年2月11日",
    sourceUrl: "https://www.tbs.co.jp/saikourestaurant/oldv8/202302111/",
    talkSummary: "番組公式アーカイブで、大阪・千日前「下積み時代の思い出が詰まった！居酒屋メシ」として紹介。店舗情報として「居酒屋たこしげ」が掲載されている。",
    scene: "千日前と芸人の下積みが直結する強いカード。大阪の芸人探索を厚くできる。",
    story: "大阪芸人の記憶が残る居酒屋として、地図に置いた時の説得力がある。"
  }
];

const areaAdds = [
  { id: "higashi-koenji", name: "東高円寺", center: [139.6587, 35.6977], zoom: 15, vibe: "今田耕司さんや東京03角田さんの下積みの食の記憶が重なる、都内の濃い探索エリア。" },
  { id: "senkawa", name: "千川", center: [139.6892, 35.7383], zoom: 15, vibe: "バイきんぐの下積み時代の記憶が残る、劇場外の強い手がかりエリア。" },
  { id: "daitabashi", name: "代田橋", center: [139.6588, 35.6717], zoom: 15, vibe: "ウエストランドのM-1前後の物語を感じられる、静かな都内探索エリア。" },
  { id: "ikejiri", name: "池尻大橋", center: [139.6816, 35.6504], zoom: 15, vibe: "芸人の節目の食事や大人の店の記憶が拾える街。" },
  { id: "sennichimae", name: "千日前", center: [135.5061, 34.6687], zoom: 15, vibe: "大阪芸人の劇場文化と下積みの食の記憶が集まる探索エリア。" }
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
