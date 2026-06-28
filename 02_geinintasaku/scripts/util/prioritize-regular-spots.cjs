const fs = require("fs");
const path = require("path");

const placesPath = path.join(process.cwd(), "public", "data", "places.geojson");
const places = JSON.parse(fs.readFileSync(placesPath, "utf8"));

for (const feature of places.features) {
  const props = feature.properties;
  const sourceText = [
    props.sourceProgram,
    props.sourceEpisode,
    props.talkSummary,
    props.scene,
    props.story
  ].join(" ");

  if (props.sourceProgram === "TBSテレビ「ベスコングルメ」") {
    props.role = "column";
    props.importance = "medium";
    props.heLevel = Math.min(props.heLevel ?? 3, 4);
    props.tags = Array.from(new Set([...(props.tags ?? []), "#番組訪問"]));
    props.sourceMemo = `${props.sourceMemo} / 行きつけではなく番組訪問として扱う`;
    continue;
  }

  if (
    sourceText.includes("行きつけ") ||
    sourceText.includes("通った") ||
    sourceText.includes("来ていた") ||
    sourceText.includes("下積み時代を支えて")
  ) {
    props.role = "clue";
    props.importance = "high";
    props.heLevel = Math.max(props.heLevel ?? 4, 5);
    props.tags = Array.from(new Set([...(props.tags ?? []), "#行きつけ系"]));
  }
}

fs.writeFileSync(placesPath, `${JSON.stringify(places, null, 2)}\n`, "utf8");
