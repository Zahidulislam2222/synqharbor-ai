import type { MetadataRoute } from "next";
import { publicSettings } from "@/config/ui";
export const dynamic = "force-static";
export default function robots(): MetadataRoute.Robots {
  const { origin } = publicSettings();
  return {
    rules: { userAgent: "*", allow: "/", disallow: "/workspace/" },
    sitemap: origin ? `${origin}/sitemap.xml` : undefined,
  };
}
