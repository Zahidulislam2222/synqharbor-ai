import type { MetadataRoute } from "next";
import pages from "@/content/pages.json";
import { publicSettings } from "@/config/ui";
export const dynamic = "force-static";
export default function sitemap(): MetadataRoute.Sitemap {
  const { origin } = publicSettings();
  if (!origin) return [];
  return ["", ...pages.map((page) => page.slug + "/")].map((path) => ({
    url: `${origin}/${path}`,
  }));
}
