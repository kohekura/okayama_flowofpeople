const fs = require("fs");
const path = require("path");

const placesPath = path.join(process.cwd(), "public", "data", "places.geojson");
const places = JSON.parse(fs.readFileSync(placesPath, "utf8"));

const candidates = [
  {
    id: "c001",
    name: "新宿三丁目の芸人飲み候補（店名確認中）",
    catch: "番組・ラジオで出がちな“新宿で飲むなら”枠",
    category: "居酒屋",
    area: "新宿",
    coordinates: [139.7061, 35.6905],
    heLevel: 3,
    tags: ["#発言候補", "#新宿三丁目", "#居酒屋", "#要確認"],
    relatedComedians: ["千鳥", "かまいたち", "ニューヨーク"],
    sourceProgram: "調査候補：テレビ番組・ラジオ・YouTubeの飲みトーク",
    sourceEpisode: "「新宿でよく行く」「劇場帰りに飲む」系の発言確認待ち",
    talkSummary:
      "現時点では店名・番組回を未確定。新宿三丁目は劇場導線と飲食店密度が高いため、発言ありカード化の優先調査枠として置いておく。",
    scene:
      "ルミネtheよしもと、新宿末廣亭、歌舞伎町に近く、芸人のライブ後トークと結びつきやすいエリア。番組名と店名が揃えば強いカードになる。",
    story:
      "古い酒場から深夜営業の店まで選択肢が多く、街としての説得力がある。候補段階でも探索の導線としてはかなり面白い。",
    address: "東京都新宿区新宿3丁目周辺",
    googleMapsUrl: "https://www.google.com/maps/search/?api=1&query=%E6%96%B0%E5%AE%BF%E4%B8%89%E4%B8%81%E7%9B%AE%20%E5%B1%85%E9%85%92%E5%B1%8B",
    sourceMemo: "番組名・店名・発言内容・出典URLの確認待ち"
  },
  {
    id: "c002",
    name: "歌舞伎町の深夜メシ候補（店名確認中）",
    catch: "収録後・ライブ後の“もう一軒”を探す枠",
    category: "ラーメン",
    area: "新宿",
    coordinates: [139.7039, 35.6946],
    heLevel: 3,
    tags: ["#発言候補", "#歌舞伎町", "#深夜メシ", "#要確認"],
    relatedComedians: ["さらば青春の光", "鬼越トマホーク", "ニューヨーク"],
    sourceProgram: "調査候補：深夜番組・YouTube・ラジオの食事トーク",
    sourceEpisode: "「深夜に行く」「仕事終わりに寄る」系の発言確認待ち",
    talkSummary:
      "歌舞伎町の具体店名は未確定。芸人の深夜メシ発言が拾えたら、店名確定後に発言ありカードへ昇格させる。",
    scene:
      "新宿の夜の文脈が強く、劇場・テレビ・飲食の話が接続しやすい。軽く見えるが、出典が取れるとかなり強い手がかりになる。",
    story:
      "地図上で光らせると、探索感が出るエリア。断定せず候補として持っておく価値がある。",
    address: "東京都新宿区歌舞伎町周辺",
    googleMapsUrl: "https://www.google.com/maps/search/?api=1&query=%E6%AD%8C%E8%88%9E%E4%BC%8E%E7%94%BA%20%E3%83%A9%E3%83%BC%E3%83%A1%E3%83%B3",
    sourceMemo: "番組名・店名・発言内容・出典URLの確認待ち"
  },
  {
    id: "c003",
    name: "渋谷・宇田川町のトーク後ごはん候補",
    catch: "若手芸人のライブ後トークに出てきそうな渋谷の夜",
    category: "居酒屋",
    area: "渋谷",
    coordinates: [139.6977, 35.6621],
    heLevel: 3,
    tags: ["#発言候補", "#渋谷", "#宇田川町", "#要確認"],
    relatedComedians: ["令和ロマン", "男性ブランコ", "ニューヨーク"],
    sourceProgram: "調査候補：劇場ライブ後のラジオ・YouTube・インタビュー",
    sourceEpisode: "ヨシモト∞ホール周辺の食事・飲み発言確認待ち",
    talkSummary:
      "若手芸人の渋谷周辺発言を集めるための候補ピン。出典が取れるまでは店名を断定しない。",
    scene:
      "ヨシモト∞ホールやLOFT9 Shibuyaから動きやすい。発言の断片が拾えれば、街の導線としてかなり使いやすい。",
    story:
      "渋谷の中心部で、ライブ・トーク・食事が近い距離でつながる。候補棚として置いておくと調査が進めやすい。",
    address: "東京都渋谷区宇田川町周辺",
    googleMapsUrl: "https://www.google.com/maps/search/?api=1&query=%E6%B8%8B%E8%B0%B7%20%E5%AE%87%E7%94%B0%E5%B7%9D%E7%94%BA%20%E5%B1%85%E9%85%92%E5%B1%8B",
    sourceMemo: "番組名・店名・発言内容・出典URLの確認待ち"
  },
  {
    id: "c004",
    name: "神保町の喫茶店トーク候補（店名確認中）",
    catch: "漫才師の本・ネタ作り話と相性がいい喫茶枠",
    category: "カフェ",
    area: "神保町",
    coordinates: [139.7584, 35.6957],
    heLevel: 3,
    tags: ["#発言候補", "#神保町", "#喫茶店", "#要確認"],
    relatedComedians: ["オズワルド", "令和ロマン", "ナイチンゲールダンス"],
    sourceProgram: "調査候補：神保町芸人のラジオ・インタビュー・劇場配信",
    sourceEpisode: "劇場前後に使う喫茶店・作業場所の発言確認待ち",
    talkSummary:
      "神保町の喫茶店は候補が多いため、店名を急いで断定しない。発言元が取れたものから個別ピンへ分ける。",
    scene:
      "劇場、本屋、喫茶店が近く、漫才師の言葉やネタ作りの話と相性がいい。発言あり化するとかなり味のあるカードになる。",
    story:
      "神保町らしい静かな時間があり、派手さよりも“考えている芸人”の気配が出せる。",
    address: "東京都千代田区神田神保町周辺",
    googleMapsUrl: "https://www.google.com/maps/search/?api=1&query=%E7%A5%9E%E4%BF%9D%E7%94%BA%20%E5%96%AB%E8%8C%B6%E5%BA%97",
    sourceMemo: "番組名・店名・発言内容・出典URLの確認待ち"
  },
  {
    id: "c005",
    name: "中野ブロードウェイ周辺の趣味トーク候補",
    catch: "芸人の収集癖・漫画・ゲーム話を拾う枠",
    category: "街",
    area: "中野",
    coordinates: [139.6655, 35.7064],
    heLevel: 3,
    tags: ["#発言候補", "#中野", "#趣味", "#要確認"],
    relatedComedians: ["バカリズム", "ケンドーコバヤシ", "空気階段"],
    sourceProgram: "調査候補：趣味系番組・ラジオ・エッセイ",
    sourceEpisode: "漫画・フィギュア・ゲーム関連の発言確認待ち",
    talkSummary:
      "中野ブロードウェイ周辺は趣味トークの受け皿として強い。具体店名や番組回が取れたらカードを分割する。",
    scene:
      "趣味の深掘りをする芸人ほど、街の濃度と相性がいい。食事よりも“何を好きか”が見える手がかりとして使える。",
    story:
      "歩くだけで情報量が多く、ストックしておくと後から掘りやすいエリア。",
    address: "東京都中野区中野5丁目周辺",
    googleMapsUrl: "https://www.google.com/maps/search/?api=1&query=%E4%B8%AD%E9%87%8E%E3%83%96%E3%83%AD%E3%83%BC%E3%83%89%E3%82%A6%E3%82%A7%E3%82%A4",
    sourceMemo: "番組名・店名・発言内容・出典URLの確認待ち"
  },
  {
    id: "c006",
    name: "下北沢のライブ後カレー候補（店名確認中）",
    catch: "小劇場帰りの食事トークを拾いたい枠",
    category: "カフェ",
    area: "下北沢",
    coordinates: [139.6682, 35.662],
    heLevel: 3,
    tags: ["#発言候補", "#下北沢", "#カレー", "#要確認"],
    relatedComedians: ["シソンヌ", "空気階段", "男性ブランコ"],
    sourceProgram: "調査候補：舞台・コント・単独ライブ後の食事トーク",
    sourceEpisode: "下北沢のカレー店・喫茶店に関する発言確認待ち",
    talkSummary:
      "下北沢はカレー店が多く、芸人の舞台後トークと結びつく可能性が高い。店名と発言元が揃うまで候補扱い。",
    scene:
      "本多劇場や駅前劇場から近く、舞台の余韻と食事の導線が作りやすい。確定すると使いやすい発言カードになる。",
    story:
      "街全体に舞台と食の距離が近い。下北沢らしいカードを増やすための調査ポイント。",
    address: "東京都世田谷区北沢周辺",
    googleMapsUrl: "https://www.google.com/maps/search/?api=1&query=%E4%B8%8B%E5%8C%97%E6%B2%A2%20%E3%82%AB%E3%83%AC%E3%83%BC",
    sourceMemo: "番組名・店名・発言内容・出典URLの確認待ち"
  }
];

const existingIds = new Set(places.features.map((feature) => feature.properties.id));

for (const candidate of candidates) {
  if (existingIds.has(candidate.id)) {
    continue;
  }

  places.features.push({
    type: "Feature",
    geometry: {
      type: "Point",
      coordinates: candidate.coordinates
    },
    properties: {
      id: candidate.id,
      name: candidate.name,
      catch: candidate.catch,
      category: candidate.category,
      area: candidate.area,
      role: "clue",
      importance: "medium",
      heLevel: candidate.heLevel,
      address: candidate.address,
      googleMapsUrl: candidate.googleMapsUrl,
      tags: candidate.tags,
      relatedComedians: candidate.relatedComedians,
      scene: candidate.scene,
      sourceStatus: "要確認メモ",
      sourceProgram: candidate.sourceProgram,
      sourceEpisode: candidate.sourceEpisode,
      talkSummary: candidate.talkSummary,
      story: candidate.story,
      sourceMemo: candidate.sourceMemo
    }
  });
}

fs.writeFileSync(placesPath, `${JSON.stringify(places, null, 2)}\n`, "utf8");
