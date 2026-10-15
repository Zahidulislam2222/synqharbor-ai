import Link from "next/link";
import { site } from "@/content";
import { ui } from "@/config/ui";

export default function NotFound() {
  return (
    <main className="not-found">
      <span className="eyebrow">404</span>
      <h1>{site.ui.empty}</h1>
      <p>{site.ui.emptyDescription}</p>
      <Link className="button button-primary" href={ui.routes.home}>
        {site.ui.home}
      </Link>
    </main>
  );
}
