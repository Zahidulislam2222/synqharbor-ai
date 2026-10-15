export const ui = {
  motion: {
    reveal: 0.72,
    hover: 0.24,
    dialog: 0.22,
    stagger: 0.075,
    ease: [0.22, 1, 0.36, 1] as [number, number, number, number],
    lenisDuration: 1.1,
    heroParallax: 70,
  },
  media: {
    hero: "/media/harbor.webp",
    heroMobile: "/media/harbor-mobile.webp",
    video: "/media/harbor-loop.mp4",
  },
  routes: { home: "/", workspace: "/workspace/" },
  links: {
    repository: "https://github.com/Zahidulislam2222/synqharbor-ai",
    maintainer: "https://github.com/Zahidulislam2222",
    issues: "https://github.com/Zahidulislam2222/synqharbor-ai/issues",
    technicalOverview: "/documents/SynqHarbor-AI-Technical-Overview.pdf",
  },
  status: { timeout: 8000 },
  demo: { maxTitleLength: 100, maxMessageLength: 500, toastDuration: 4200 },
  preview: { navigationBreakpoint: 980 },
} as const;

export function publicSettings() {
  const origin = process.env.NEXT_PUBLIC_SITE_URL;
  if (!origin) return { origin: undefined };
  const parsed = new URL(origin);
  if (!["http:", "https:"].includes(parsed.protocol))
    throw new Error("Invalid public origin");
  return { origin: parsed.origin };
}
