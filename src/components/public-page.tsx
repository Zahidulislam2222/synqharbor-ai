import Link from "next/link";
import {
  ArrowRight,
  Check,
  CircleDot,
  Layers3,
  ShieldCheck,
  Workflow,
} from "lucide-react";
import pages from "@/content/pages.json";
import { site } from "@/content";
import { ui } from "@/config/ui";
import { SiteHeader, SiteFooter } from "./site-chrome";
import { Arrow, Reveal } from "./shared";
import { ServiceStatus } from "./service-status";

export type PublicPageContent = (typeof pages)[number];
const guides = pages.filter((page) => page.slug.startsWith("docs/"));

function PageVisual({ type }: { type: string }) {
  return (
    <div className={`page-visual visual-${type}`} aria-hidden="true">
      <div className="visual-halo" />
      {type === "flow" ? (
        <div className="visual-flow">
          <span>
            <CircleDot size={24} />
          </span>
          <i />
          <span>
            <Workflow size={28} />
          </span>
          <i />
          <span>
            <ShieldCheck size={24} />
          </span>
        </div>
      ) : type === "grid" ? (
        <div className="visual-grid">
          {[Layers3, Workflow, ShieldCheck, CircleDot].map((Icon, i) => (
            <span key={i}>
              <Icon size={34} strokeWidth={1} />
            </span>
          ))}
        </div>
      ) : (
        <div className="visual-orbits">
          <i />
          <i />
          <i />
          <span>✳</span>
        </div>
      )}
      <div className="visual-caption">
        <span className="status-dot" />
        {site.tagline}
      </div>
    </div>
  );
}

export function PublicPage({ page }: { page: PublicPageContent }) {
  return (
    <div className={`marketing-page layout-${page.layout}`} id="top">
      <a className="skip-link" href="#main">
        {site.ui.skip}
      </a>
      <SiteHeader inner />
      <main id="main" tabIndex={-1}>
        <section className="page-hero">
          <div className="container page-hero-grid">
            <Reveal className="page-intro">
              <div className="page-breadcrumb">
                <Link href="/">{site.brand}</Link>
                <ArrowRight size={12} />
                <span>{page.label}</span>
              </div>
              <p className="eyebrow">
                <span className="status-dot" />
                {page.eyebrow}
              </p>
              <h1>
                {page.title}
                {page.accent && <em>{page.accent}</em>}
              </h1>
              <p className="page-description">{page.description}</p>
              {page.layout === "product" && (
                <div className="page-hero-actions">
                  <Link
                    className="button button-primary"
                    href={ui.routes.workspace}
                  >
                    {site.ui.workspace}
                    <Arrow />
                  </Link>
                  <Link className="page-secondary" href="/docs/">
                    {site.ui.documentation}
                    <Arrow size={15} />
                  </Link>
                </div>
              )}
            </Reveal>
            {page.visual !== "none" && <PageVisual type={page.visual} />}
          </div>
        </section>
        <div className="container page-body-grid">
          <aside className="page-index">
            <span className="tiny-label">{site.ui.onThisPage}</span>
            <nav aria-label={site.ui.onThisPage}>
              {page.sections.map((section, i) => (
                <a href={`#section-${i + 1}`} key={section.title}>
                  <span>{String(i + 1).padStart(2, "0")}</span>
                  {section.title}
                </a>
              ))}
            </nav>
            <Link href="/docs/">
              {site.ui.documentation}
              <Arrow size={14} />
            </Link>
          </aside>
          <div className="page-content">
          {page.slug === "docs" && <div className="contact-actions"><a className="button button-primary" href={ui.links.technicalOverview} download>{site.ui.downloadOverview}<Arrow/></a></div>}
            {page.slug === "status" && <ServiceStatus />}
            {page.slug === "contact" && (
              <div className="contact-actions">
                <a className="button button-primary" href={ui.links.maintainer}>
                  {site.ui.contactMaintainer}
                  <Arrow />
                </a>
                <a className="button button-outline" href={ui.links.issues}>
                  {site.ui.openIssue}
                  <Arrow />
                </a>
              </div>
            )}
            {page.sections.map((section, i) => (
              <Reveal key={section.title}>
                <section className="page-section" id={`section-${i + 1}`}>
                  <div className="page-section-number">
                    {String(i + 1).padStart(2, "0")} /
                  </div>
                  <h2>{section.title}</h2>
                  <p>{section.body}</p>
                  {section.items.length > 0 && (
                    <ul>
                      {section.items.map((item) => (
                        <li key={item}>
                          <Check size={15} />
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                </section>
              </Reveal>
            ))}
            {page.slug === "docs" && (
              <div className="guide-grid">
                {guides.map((guide, i) => (
                  <Link
                    className="guide-card"
                    href={`/${guide.slug}/`}
                    key={guide.slug}
                  >
                    <span className="tiny-label">
                      {String(i + 1).padStart(2, "0")} / {guide.eyebrow}
                    </span>
                    <h2>{guide.label}</h2>
                    <p>{guide.title}</p>
                    <Arrow />
                  </Link>
                ))}
              </div>
            )}
            {page.slug === "self-hosting" && (
              <pre className="install-code">
                <code>{site.ui.installCommands}</code>
              </pre>
            )}
            <div className="page-next">
              <span>{site.ui.nextStep}</span>
              <Link
                href={
                  page.slug.startsWith("docs")
                    ? ui.links.repository
                    : "/roadmap/"
                }
              >
                {page.slug.startsWith("docs")
                  ? site.ui.sourceCode
                  : site.ui.roadmap}
                <Arrow />
              </Link>
            </div>
          </div>
        </div>
        <section className="page-closing">
          <div className="container">
            <span className="eyebrow">{site.closing.eyebrow}</span>
            <h2>
              {site.closing.title}
              <em>{site.closing.italic}</em>
            </h2>
            <Link className="button button-primary" href={ui.routes.workspace}>
              {site.closing.cta}
              <Arrow />
            </Link>
          </div>
        </section>
      </main>
      <SiteFooter />
    </div>
  );
}
