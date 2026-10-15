import siteData from "./site.json";
import demoData from "./demo.json";

export const site = siteData;
export const demo = demoData;

if (
  !site.brand ||
  !site.hero.title.length ||
  !demo.tasks.length ||
  !demo.statuses.length
) {
  throw new Error("Required presentation content is missing");
}
if (new Set(demo.tasks.map((task) => task.id)).size !== demo.tasks.length) {
  throw new Error("Duplicate preview task identifiers");
}
if (
  demo.tasks.some(
    (task) => !demo.statuses.some((status) => status.id === task.status),
  )
) {
  throw new Error("Unknown preview task status");
}
