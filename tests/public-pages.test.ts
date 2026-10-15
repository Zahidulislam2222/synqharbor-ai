import { describe, expect, it } from "vitest";
import pages from "../src/content/pages.json";
import navigation from "../src/content/navigation.json";
import site from "../src/content/site.json";

function values(value: unknown): string[] {
  if (typeof value === "string") return [value];
  if (Array.isArray(value)) return value.flatMap(values);
  if (value && typeof value === "object") return Object.values(value).flatMap(values);
  return [];
}

describe("public website contracts", () => {
  it("publishes substantive unique routes and complete navigation targets", () => {
    const routes = new Set(pages.map(page => `/${page.slug}/`));
    expect(routes.size).toBe(pages.length);
    expect(pages.length).toBeGreaterThanOrEqual(20);
    for (const page of pages) {
      expect(page.sections.length, page.slug).toBeGreaterThanOrEqual(3);
      expect(page.description.length, page.slug).toBeGreaterThan(50);
      expect(page.sections.every(section => section.body.length > 80), page.slug).toBe(true);
    }
    for (const { links } of navigation) {
      for (const [, href] of links) if (href.startsWith("/")) expect(routes.has(href), href).toBe(true);
    }
    for (const { href } of site.navigation) expect(routes.has(href), href).toBe(true);
  });
  it("uses professional public language and explicit operating boundaries", () => {
    expect(values([pages, site]).join(" ")).not.toMatch(/\b(?:demo|preview|prototype|synthetic|illustrative)\b/i);
    expect(pages.find(page => page.slug === "docs/api")?.sections[0].body).toContain("no deployed application API");
    expect(pages.find(page => page.slug === "status")?.description).toContain("point-in-time");
    expect(pages.find(page => page.slug === "docs/scalability")?.sections[0].body).toContain("planning assumptions");
  });
});
