import type { Metadata } from "next";
import { Workspace } from "@/components/workspace";
import { site } from "@/content";

export const metadata: Metadata = {
  title: site.ui.preview,
  robots: { index: false, follow: false },
};

export default function WorkspacePage() {
  return <Workspace />;
}
