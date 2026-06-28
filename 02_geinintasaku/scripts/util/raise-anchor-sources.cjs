const fs = require("fs");
const path = require("path");

const placesPath = path.join(process.cwd(), "public", "data", "places.geojson");
const places = JSON.parse(fs.readFileSync(placesPath, "utf8"));

const updates = {
  p102: {
    catch: "渋谷で“素の話”がこぼれやすいトークの箱",
    sourceStatus: "出典確認済み",
    sourceProgram: "LOFT9 Shibuya公式サイト",
    sourceEpisode: "イベントスケジュール・会場情報",
    sourceDate: "公式サイト参照",
    sourceUrl: "https://www.loft-prj.co.jp/loft9/",
    talkSummary:
      "トークイベントや配信イベントが行われる会場として、公式にイベント情報が公開されている。芸人の番組外の言葉を追う時に候補へ入れたい場所。",
    scene:
      "劇場より少し近い距離で話を聞けるタイプの箱。芸人の“好きなもの”“最近の話”がイベントタイトルに出てくることがあり、次の手がかりを拾いやすい。",
    story:
      "円山町寄りの渋谷で、トークとカルチャーの温度がある場所。夜の探索に混ぜると、地図が一気に番組外の空気になる。",
    sourceMemo: "公式イベント情報・会場情報を確認"
  },
  p103: {
    catch: "芸人が映画を語る夜に、名前が出てきそうなミニシアター",
    sourceStatus: "出典確認済み",
    sourceProgram: "ユーロスペース公式サイト",
    sourceEpisode: "劇場情報・上映情報",
    sourceDate: "公式サイト参照",
    sourceUrl: "https://www.eurospace.co.jp/",
    talkSummary:
      "渋谷のミニシアターとして上映情報が公式に公開されている。特定芸人の発言確認済みではなく、映画好き芸人の文脈を拾うコラム寄りスポット。",
    scene:
      "映画、単独ライブ、ラジオの話題はつながりやすい。芸人が映画を語った時に、渋谷の文化圏として置いておくと見え方が広がる。",
    story:
      "大きすぎない劇場で、作品選びにも色がある。映画好きの発言を追う時、街の文脈として効く場所。",
    sourceMemo: "公式劇場情報・上映情報を確認"
  },
  p202: {
    catch: "芸人の本棚を想像しながら寄りたい神保町の大型書店",
    sourceStatus: "出典確認済み",
    sourceProgram: "三省堂書店公式サイト",
    sourceEpisode: "店舗情報",
    sourceDate: "公式サイト参照",
    sourceUrl: "https://www.books-sanseido.co.jp/",
    talkSummary:
      "神保町の書店として公式に店舗情報が公開されている。芸人個人の行きつけ断定ではなく、劇場前後に本や言葉の手がかりへ広げる場所。",
    scene:
      "神保町よしもと漫才劇場と本の街が近いこと自体が面白い。ネタ作り、エッセイ、ラジオ本の話が出た時に寄り道先として自然に浮かぶ。",
    story:
      "本を探すだけでなく、街の気分を切り替える場所。神保町の探索に厚みを出してくれる。",
    sourceMemo: "公式店舗情報を確認"
  },
  p401: {
    catch: "下北沢の舞台カルチャーを読むための大きな起点",
    sourceStatus: "出典確認済み",
    sourceProgram: "本多劇場グループ公式サイト",
    sourceEpisode: "本多劇場・公演情報",
    sourceDate: "公式サイト参照",
    sourceUrl: "https://www.honda-geki.com/honda/",
    talkSummary:
      "演劇公演が行われる劇場として、公式に公演情報が公開されている。コント師や俳優仕事をする芸人の文脈を追う起点。",
    scene:
      "テレビの芸人像とは違う、舞台側の顔が見えやすい場所。下北沢で“芸人と演劇”の線を引くならここから始めたい。",
    story:
      "街の中心に近く、観劇前後の飲食や古着屋めぐりにも流れやすい。下北沢らしい余白がある劇場。",
    sourceMemo: "公式劇場情報・公演情報を確認"
  },
  p402: {
    catch: "小劇場の距離感で、コントの気配を拾う場所",
    sourceStatus: "出典確認済み",
    sourceProgram: "本多劇場グループ公式サイト",
    sourceEpisode: "駅前劇場・公演情報",
    sourceDate: "公式サイト参照",
    sourceUrl: "https://www.honda-geki.com/ekimae/",
    talkSummary:
      "駅前劇場の公演情報は公式サイトで公開されている。特定の目撃情報ではなく、舞台出演・小劇場文化の起点として扱う。",
    scene:
      "客席との距離が近い劇場は、芸人の芝居・コント・単独ライブの温度を想像しやすい。下北沢の手がかりとして強い。",
    story:
      "駅から近く、ふらっと街歩きにも組み込みやすい。劇場が街の日常に溶けている感じがいい。",
    sourceMemo: "公式劇場情報・公演情報を確認"
  }
};

for (const feature of places.features) {
  const update = updates[feature.properties.id];
  if (!update) continue;

  feature.properties = {
    ...feature.properties,
    ...update
  };
}

fs.writeFileSync(placesPath, `${JSON.stringify(places, null, 2)}\n`, "utf8");
