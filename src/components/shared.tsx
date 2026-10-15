"use client";

import Link from "next/link";
import { ArrowUpRight, Waves, X } from "lucide-react";
import { motion, useReducedMotion } from "motion/react";
import { useEffect, useRef, type ReactNode } from "react";
import { site } from "@/content";
import { ui } from "@/config/ui";

export function Logo({ compact = false }: { compact?: boolean }) {
  return (
    <Link href={ui.routes.home} className="logo" aria-label={site.ui.home}>
      <span className="logo-mark">
        <Waves aria-hidden="true" size={25} strokeWidth={1.9} />
      </span>
      {!compact && (
        <span>
          {site.brand}
          <span className="logo-ai">AI</span>
        </span>
      )}
    </Link>
  );
}

export function Arrow({ size = 17 }: { size?: number }) {
  return <ArrowUpRight size={size} aria-hidden="true" />;
}

export function Reveal({
  children,
  className = "",
  delay = 0,
}: {
  children: ReactNode;
  className?: string;
  delay?: number;
}) {
  const reduced = useReducedMotion();
  return (
    <motion.div
      className={className}
      initial={false}
      whileInView={
        reduced ? { opacity: 1, y: 0 } : { opacity: [0.45, 1], y: [24, 0] }
      }
      viewport={{ once: true, amount: 0.12 }}
      transition={{
        duration: reduced ? 0 : ui.motion.reveal,
        delay,
        ease: ui.motion.ease,
      }}
    >
      {children}
    </motion.div>
  );
}

export function Dialog({
  title,
  children,
  onClose,
  wide = false,
}: {
  title: string;
  children: ReactNode;
  onClose: () => void;
  wide?: boolean;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const dialog = ref.current;
    const previous = document.activeElement as HTMLElement | null;
    dialog?.showModal();
    return () => {
      dialog?.close();
      if (previous?.isConnected) previous.focus();
      else document.querySelector<HTMLElement>("main")?.focus();
    };
  }, []);
  return (
    <dialog
      ref={ref}
      className={`dialog ${wide ? "dialog-wide" : ""}`}
      onCancel={(event) => {
        event.preventDefault();
        onClose();
      }}
      aria-labelledby="dialog-title"
    >
      <div className="dialog-header">
        <h2 id="dialog-title">{title}</h2>
        <button
          className="icon-button"
          onClick={onClose}
          aria-label={site.ui.close}
        >
          <X size={20} />
        </button>
      </div>
      {children}
    </dialog>
  );
}
