import type { Metadata } from "next";
import "@fontsource-variable/manrope";
import "@fontsource/instrument-serif/400.css";
import "@fontsource/instrument-serif/400-italic.css";
import "./globals.css";
import { site } from "@/content";
import { publicSettings } from "@/config/ui";

const { origin } = publicSettings();

export const metadata: Metadata = {
  title: {
    default: `${site.product} — ${site.tagline}`,
    template: `%s · ${site.product}`,
  },
  description: site.description,
  metadataBase: origin ? new URL(origin) : undefined,
  openGraph: {
    title: site.product,
    description: site.description,
    type: "website",
    images: ["/media/harbor.webp"],
  },
  twitter: {
    card: "summary_large_image",
    title: site.product,
    description: site.description,
  },
  robots: { index: true, follow: true },
  icons: { icon: "/icon.svg" },
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
