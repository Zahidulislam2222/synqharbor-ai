"use client";
import { useState } from "react";
import { CheckCircle2, RefreshCw, AlertCircle } from "lucide-react";
import { site } from "@/content";
import { ui } from "@/config/ui";

export function ServiceStatus() {
  const [state, setState] = useState<
    "idle" | "checking" | "available" | "unreachable"
  >("idle");
  const [checked, setChecked] = useState("");
  async function check() {
    setState("checking");
    try {
      const response = await fetch(ui.routes.home, {
        method: "HEAD",
        cache: "no-store",
        signal: AbortSignal.timeout(ui.status.timeout),
      });
      setState(response.ok ? "available" : "unreachable");
    } catch {
      setState("unreachable");
    }
    setChecked(new Date().toLocaleString());
  }
  return (
    <div className="service-check">
      <div aria-live="polite">
        <span className={`service-indicator ${state}`}>
          {state === "available" ? (
            <CheckCircle2 />
          ) : state === "unreachable" ? (
            <AlertCircle />
          ) : (
            <RefreshCw />
          )}
        </span>
        <h2>{site.status[state]}</h2>
        <p>
          {checked ? `${site.status.checked} ${checked}` : site.status.note}
        </p>
      </div>
      <button
        className="button button-primary"
        onClick={() => void check()}
        disabled={state === "checking"}
      >
        {site.status.button}
        <RefreshCw size={15} />
      </button>
    </div>
  );
}
