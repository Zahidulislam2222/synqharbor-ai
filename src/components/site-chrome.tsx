"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { Menu, X } from "lucide-react";
import { site } from "@/content";
import { Arrow, Logo } from "./shared";
import { ui } from "@/config/ui";
import navigation from "@/content/navigation.json";

export const footerGroups = navigation.map((group) => ({
  ...group,
  links: group.links.map(([label, href]) => [
    label,
    Object.hasOwn(ui.links, href)
      ? ui.links[href as keyof typeof ui.links]
      : href,
  ]),
}));

export function SiteHeader({ inner = false }: { inner?: boolean }) {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const button = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    if (!open) return;
    const handle = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setOpen(false);
        button.current?.focus();
      }
    };
    document.addEventListener("keydown", handle);
    return () => document.removeEventListener("keydown", handle);
  }, [open]);
  return (
    <header className={`site-header ${inner ? "inner-header" : ""}`}>
      <div className="nav-shell">
        <Logo />
        <nav className="desktop-nav" aria-label={site.ui.mainNavigation}>
          {site.navigation.map((item) => (
            <Link
              href={item.href}
              key={item.href}
              aria-current={pathname === item.href ? "page" : undefined}
            >
              {item.label}
            </Link>
          ))}
        </nav>
        <Link className="nav-cta" href={ui.routes.workspace}>
          {site.ui.workspace}
          <Arrow size={16} />
        </Link>
        <button
          ref={button}
          className="mobile-menu-button icon-button"
          aria-label={open ? site.ui.closeMenu : site.ui.menu}
          aria-expanded={open}
          aria-controls="mobile-navigation"
          onClick={() => setOpen(!open)}
        >
          {open ? <X /> : <Menu />}
        </button>
      </div>
      <nav
        id="mobile-navigation"
        className="mobile-navigation complete-navigation"
        aria-label={site.ui.mobileNavigation}
        hidden={!open}
      >
        {footerGroups
          .slice(0, 3)
          .flatMap((group) => group.links)
          .filter(([, href]) => href.startsWith("/"))
          .map(([label, href]) => (
            <Link
              key={href}
              href={href}
              onClick={() => setOpen(false)}
              aria-current={pathname === href ? "page" : undefined}
            >
              {label}
              <Arrow size={15} />
            </Link>
          ))}
      </nav>
    </header>
  );
}

export function SiteFooter() {
  return (
    <footer className="site-footer complete-footer">
      <div className="container footer-directory">
        <div className="footer-brand">
          <Logo />
          <p>{site.footer.note}</p>
          <a href={ui.links.maintainer}>
            {site.footer.maintainer}
            <Arrow size={13} />
          </a>
        </div>
        {footerGroups.map((group) => (
          <nav key={group.title} aria-label={group.title}>
            <h2>{group.title}</h2>
            {group.links.map(([label, href]) => (
              <Link href={href} key={href}>
                {label}
              </Link>
            ))}
          </nav>
        ))}
      </div>
      <div className="container footer-bottom">
        <span>{site.footer.copyright}</span>
        <span>{site.footer.status}</span>
        <a href="#top">
          {site.footer.back}
          <Arrow size={13} />
        </a>
      </div>
    </footer>
  );
}
