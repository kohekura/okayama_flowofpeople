const fs = require("fs");

const filePath = "public/data/places.geojson";
const data = JSON.parse(fs.readFileSync(filePath, "utf8"));

const anchorIds = new Set(["p001", "p005", "p101", "p201", "p401", "p402", "p901"]);
const highClueIds = new Set(["p902", "p002", "p003", "p004", "p102", "p203", "p304"]);

data.features = data.features.map((feature) => {
  const { id, category, sourceStatus, heLevel } = feature.properties;
  let role = "column";
  let importance = "low";

  if (anchorIds.has(id) || category === "劇場" || category === "テレビ局") {
    role = "anchor";
    importance = "anchor";
  } else if (highClueIds.has(id) || sourceStatus === "出典確認済み" || heLevel >= 4) {
    role = "clue";
    importance = "high";
  }

  return {
    ...feature,
    properties: {
      ...feature.properties,
      role,
      importance
    }
  };
});

fs.writeFileSync(filePath, `${JSON.stringify(data, null, 2)}\n`, "utf8");
