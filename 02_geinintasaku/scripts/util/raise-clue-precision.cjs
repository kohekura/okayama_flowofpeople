const fs = require("fs");
const path = require("path");

const placesPath = path.join(process.cwd(), "public", "data", "places.geojson");
const places = JSON.parse(fs.readFileSync(placesPath, "utf8"));

const updates = {
  p001: {
    catch: "新宿の笑いを読むなら、まずここを起点に",
    sourceStatus: "出典確認済み",
    sourceProgram: "ルミネtheよしもと公式サイト",
    sourceEpisode: "公演スケジュール・劇場情報",
    sourceDate: "公式サイト参照",
    sourceUrl: "https://lumine.yoshimoto.co.jp/",
    talkSummary:
      "吉本興業の劇場として、公演スケジュールと出演者情報が公式に公開されている場所。芸人の私的な行動ではなく、仕事で訪れる起点として扱う。",
    scene:
      "ライブ前後に人の流れができる場所。ここから新宿駅東口、新宿三丁目、思い出横丁方面へ広げて見ると、街の“お笑い濃度”が読みやすい。",
    story:
      "新宿駅直結で、初めてでも立ち寄りやすい劇場。公演前後に周辺の飲食店や書店へ流れる導線まで含めて見ると面白い。",
    sourceMemo: "公式劇場情報・公開スケジュールを確認"
  },
  p005: {
    catch: "寄席の明かりが残す、新宿三丁目のもう一つの起点",
    sourceStatus: "出典確認済み",
    sourceProgram: "新宿末廣亭公式サイト",
    sourceEpisode: "寄席・公演情報",
    sourceDate: "公式サイト参照",
    sourceUrl: "https://suehirotei.com/",
    talkSummary:
      "落語・漫才・講談などの寄席公演が行われる劇場として公式情報が公開されている。若手芸人の行きつけ発言ではなく、笑いの仕事場としての起点。",
    scene:
      "テレビやライブハウスとは違う笑いの時間が流れる場所。新宿三丁目で飲食店の手がかりを探す前に、街の温度を合わせる起点になる。",
    story:
      "建物の存在感も含めて、新宿三丁目を歩く理由になる寄席。夜の街の中に古典芸能の灯りが残っているのがいい。",
    sourceMemo: "公式劇場情報・公開公演情報を確認"
  },
  p101: {
    catch: "渋谷で若手芸人の現在地を追うならここ",
    sourceStatus: "出典確認済み",
    sourceProgram: "ヨシモト∞ホール公式サイト",
    sourceEpisode: "公演スケジュール・劇場情報",
    sourceDate: "公式サイト参照",
    sourceUrl: "https://mugendai.yoshimoto.co.jp/",
    talkSummary:
      "若手芸人のライブが行われる劇場として、公演情報が公式に公開されている。私的な行動ではなく、仕事で訪れる場所として扱う。",
    scene:
      "渋谷の飲食店・トークイベント・劇場をつなぐ時の起点。ここから宇田川町や円山町側へ歩くと、芸人カルチャーの濃い夜の動線が見えてくる。",
    story:
      "渋谷の中心に近く、ライブ後に周辺へ展開しやすい劇場。若手芸人の名前を追い始める入口として使いやすい。",
    sourceMemo: "公式劇場情報・公開スケジュールを確認"
  },
  p201: {
    catch: "神保町の“劇場と本の街”をつなぐ中心点",
    sourceStatus: "出典確認済み",
    sourceProgram: "神保町よしもと漫才劇場公式サイト",
    sourceEpisode: "公演スケジュール・劇場情報",
    sourceDate: "公式サイト参照",
    sourceUrl: "https://jimbocho-manzaigekijyo.yoshimoto.co.jp/",
    talkSummary:
      "若手漫才師の公演が行われる劇場として、公式にスケジュールが公開されている。神保町の古書店・喫茶店へ広げる探索の起点。",
    scene:
      "劇場、古書店、喫茶店が徒歩圏に重なる街。芸人の言葉や本の話が出てきた時に、周辺の手がかりへつなげやすい。",
    story:
      "神保町らしい知的な街並みと、若手漫才の熱が近い距離で重なる場所。観劇前後の寄り道まで含めて楽しめる。",
    sourceMemo: "公式劇場情報・公開スケジュールを確認"
  },
  p901: {
    catch: "番組で芸人が集まる、赤坂の仕事場",
    sourceStatus: "出典確認済み",
    sourceProgram: "TBS公式サイト",
    sourceEpisode: "TBS放送センター所在地・施設情報",
    sourceDate: "公式サイト参照",
    sourceUrl: "https://www.tbs.co.jp/",
    talkSummary:
      "テレビ番組の収録・制作と結びつく放送局。芸人の現在地ではなく、番組発言の背景にある仕事場として見るための起点。",
    scene:
      "グルメ番組やトーク番組の発言をたどる時、赤坂という街そのものが文脈になる。劇場とは別系統の芸人導線として置いておきたい。",
    story:
      "赤坂のランドマーク。番組名から手がかりを探す時の出発点として、地図上にあるだけで文脈が立つ。",
    sourceMemo: "公式施設情報を確認"
  },
  p902: {
    catch: "濱家さんが番組で巡った、裏なんばの記憶",
    name: "裏なんばの串揚げ店（店名要確認）",
    sourceStatus: "出典確認済み",
    sourceProgram: "MBSテレビ「かまいたちの知らんけど」",
    sourceEpisode: "濱家さんが大阪・裏なんばの思い出の店を巡った回",
    sourceDate: "スポニチ記事公開：2023年2月18日",
    sourceUrl: "https://www.sponichi.co.jp/entertainment/news/2023/02/18/kiji/20230218s00041000238000c.html",
    talkSummary:
      "スポニチ記事では、濱家さんが大阪・裏なんばの思い出の店を巡り、1軒目の串揚げ店について、劇場出演後や出演の合間に見取り図リリーさんらと来ていたと紹介されている。",
    scene:
      "“劇場出演後や出演の合間に来ていた”という文脈があるため、ただの人気店ではなく、芸人の大阪時代の導線を想像できる手がかりになる。",
    story:
      "店名は記事本文だけでは特定しきらないため要確認。ただ、裏なんば全体の飲食店密度と劇場文化の近さが伝わる、かなり強い探索ポイント。",
    sourceMemo:
      "スポニチ記事で番組名・エリア・発言文脈を確認。店名は記事本文から特定できないため要確認。"
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
