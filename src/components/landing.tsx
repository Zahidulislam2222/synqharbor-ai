"use client";

import Link from "next/link";
import Image from "next/image";
import { useEffect, useRef, useState } from "react";
import {
  AnimatePresence,
  motion,
  MotionConfig,
  useReducedMotion,
  useScroll,
  useTransform,
} from "motion/react";
import Lenis from "lenis";
import {
  ArrowDown,
  ArrowRight,
  Check,
  CheckCheck,
  ChevronDown,
  Circle,
  CircleDot,
  FileText,
  Layers3,
  LayoutDashboard,
  LockKeyhole,
  MessageSquare,
  Pause,
  Play,
  Plus,
  ShieldCheck,
  Sparkles,
  Workflow,
} from "lucide-react";
import { site, demo } from "@/content";
import { ui } from "@/config/ui";
import { Arrow, Reveal } from "./shared";
import { SiteHeader, SiteFooter } from "./site-chrome";

const iconMap = {
  message: MessageSquare,
  sparkles: Sparkles,
  check: CheckCheck,
  lock: LockKeyhole,
  layers: Layers3,
  shield: ShieldCheck,
};

function WorkspaceSnapshot({ tab }: { tab: number }) {
  const reduced = useReducedMotion();
  return (
    <div className="snapshot">
      <div className="snapshot-chrome">
        <div className="window-dots">
          <i />
          <i />
          <i />
        </div>
        <span>
          {site.brand} <span>/</span> {demo.workspace.name}
        </span>
        <span className="snapshot-sample">
          <span className="status-dot" />
          {site.ui.sample}
        </span>
      </div>
      <div className="snapshot-inner">
        <aside className="snapshot-sidebar">
          <div className="snapshot-workspace">
            <span className="workspace-letter">A</span>
            <div>
              <strong>{demo.workspace.name}</strong>
              <small>{site.ui.preview}</small>
            </div>
            <ChevronDown size={14} />
          </div>
          <div className="mini-nav">
            {demo.navigation.slice(0, 6).map((item, i) => {
              const Icon = [
                LayoutDashboard,
                MessageSquare,
                Workflow,
                Sparkles,
                ShieldCheck,
                FileText,
              ][i];
              return (
                <div
                  className={i === (tab === 2 ? 3 : 0) ? "active" : ""}
                  key={item.id}
                >
                  <Icon size={15} />
                  <span>{item.label}</span>
                  {i === 4 && <small>1</small>}
                </div>
              );
            })}
          </div>
          <div className="mini-sidebar-label">{demo.labels.team}</div>
          <div className="mini-person">
            <span className="avatar human">AM</span>
            {demo.workspace.user}
            <span className="status-dot" />
          </div>
          <div className="mini-person">
            <span className="avatar builder">✳</span>
            {demo.agents[0].name}
            <span className="status-dot" />
          </div>
          <div className="mini-person">
            <span className="avatar reviewer">◎</span>
            {demo.agents[1].name}
            <span className="status-dot" />
          </div>
          <div className="mini-sidebar-bottom">
            <span className="tiny-orbit">◎</span>
            <p>{demo.workspace.plan}</p>
          </div>
        </aside>
        <div className="snapshot-main">
          <div className="snapshot-title">
            <div>
              <span className="tiny-label">{site.ui.preview}</span>
              <h3>{demo.views[tab === 2 ? "agents" : "overview"].title}</h3>
              <p>{demo.views[tab === 2 ? "agents" : "overview"].description}</p>
            </div>
            <Link className="mini-action" href={ui.routes.workspace}>
              <Plus size={14} />
              {site.ui.newTask}
            </Link>
          </div>
          <AnimatePresence mode="wait">
            <motion.div
              key={tab}
              className="snapshot-tab-content"
              initial={reduced ? false : { opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -5 }}
              transition={{ duration: reduced ? 0 : ui.motion.hover }}
            >
              {tab === 0 && (
                <>
                  <div className="mini-focus">
                    <div>
                      <span className="tiny-label">{demo.labels.focus}</span>
                      <h4>{demo.labels.focusTitle}</h4>
                      <p>{demo.labels.focusDescription}</p>
                      <span className="mini-pill">
                        <span className="status-dot" />
                        {site.ui.pendingClient}
                      </span>
                    </div>
                    <div className="focus-sculpture" aria-hidden="true">
                      <div />
                      <div />
                      <div />
                    </div>
                  </div>
                  <div className="mini-bottom">
                    <div className="mini-work">
                      <div className="mini-section-title">
                        {demo.labels.moving}
                        <ArrowRight size={14} />
                      </div>
                      {demo.tasks.slice(0, 3).map((task, index) => (
                        <div className="mini-task" key={task.id}>
                          <span
                            className={`task-dot task-dot-${task.status}`}
                          />
                          <span>{task.title}</span>
                          <span
                            className={`avatar ${index === 0 ? "builder" : "reviewer"}`}
                          >
                            {index === 0 ? "✳" : "◎"}
                          </span>
                        </div>
                      ))}
                    </div>
                    <div className="mini-activity">
                      <div className="mini-section-title">
                        {site.ui.activity}
                      </div>
                      {demo.activity.slice(0, 2).map((item) => (
                        <div key={item.text}>
                          <span className={`avatar ${item.icon}`}>
                            {item.icon === "builder" ? "✳" : "◎"}
                          </span>
                          <p>
                            <strong>{item.actor}</strong> {item.text}
                            <small>{item.time}</small>
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                </>
              )}
              {tab === 1 && (
                <div className="mini-workflow">
                  {site.workflow.steps.map((step, i) => (
                    <div key={step.number}>
                      <span className="mini-workflow-number">
                        {step.number}
                      </span>
                      <div>
                        <h4>{step.title}</h4>
                        <p>{step.description}</p>
                      </div>
                      <span
                        className={i === 2 ? "pending-symbol" : "done-symbol"}
                      >
                        {i === 2 ? <Circle size={20} /> : <Check size={20} />}
                      </span>
                    </div>
                  ))}
                </div>
              )}
              {tab === 2 && (
                <div className="mini-agent-grid">
                  {demo.agents.map((agent) => (
                    <div key={agent.name}>
                      <span className={`agent-symbol ${agent.className}`}>
                        {agent.symbol}
                      </span>
                      <h4>{agent.name}</h4>
                      <p>{agent.role}</p>
                      <span className="mini-pill">{agent.status}</span>
                      <small>{agent.boundary}</small>
                    </div>
                  ))}
                </div>
              )}
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}

export function Landing() {
  const [tab, setTab] = useState(0);
  const [workflow, setWorkflow] = useState(0);
  const [faq, setFaq] = useState<number | null>(0);
  const [paused, setPaused] = useState(false);
  const reduced = useReducedMotion();
  const heroRef = useRef<HTMLElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const { scrollYProgress } = useScroll({
    target: heroRef,
    offset: ["start start", "end start"],
  });
  const heroY = useTransform(
    scrollYProgress,
    [0, 1],
    [0, ui.motion.heroParallax],
  );
  const currentFlow = site.workflows.items[workflow];

  useEffect(() => {
    if (reduced) return;
    const lenis = new Lenis({
      autoRaf: true,
      duration: ui.motion.lenisDuration,
      anchors: true,
      syncTouch: false,
    });
    return () => lenis.destroy();
  }, [reduced]);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;
    const update = () => {
      if (reduced !== false || paused || document.hidden) video.pause();
      else void video.play().catch(() => undefined);
    };
    update();
    document.addEventListener("visibilitychange", update);
    return () => document.removeEventListener("visibilitychange", update);
  }, [paused, reduced]);

  return (
    <MotionConfig reducedMotion="user">
      <div className="landing" id="top">
        <a className="skip-link" href="#main">
          {site.ui.skip}
        </a>
        <SiteHeader />

        <main id="main">
          <section className="hero" ref={heroRef} aria-labelledby="hero-title">
            <motion.div
              className="hero-visual"
              style={{ y: reduced ? 0 : heroY }}
            >
              <picture>
                <source
                  media="(max-width: 600px)"
                  srcSet={ui.media.heroMobile}
                />
                <Image
                  src={ui.media.hero}
                  alt={site.hero.imageAlt}
                  width={1672}
                  height={941}
                  priority
                />
              </picture>
              <video
                ref={videoRef}
                src={reduced ? undefined : ui.media.video}
                muted
                loop
                playsInline
                preload="none"
                poster={ui.media.hero}
                aria-hidden="true"
              />
            </motion.div>
            <div className="hero-shade" />
            <div className="hero-grain" aria-hidden="true" />
            <div className="hero-content container">
              <motion.div
                initial={reduced ? false : { opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{
                  duration: ui.motion.reveal,
                  ease: ui.motion.ease,
                }}
              >
                <span className="eyebrow hero-eyebrow">
                  <span className="status-dot" />
                  {site.hero.eyebrow}
                </span>
                <h1 id="hero-title">
                  {site.hero.title[0]}
                  <br />
                  <em>{site.hero.title[1]}</em>
                  <span className="hero-spark" aria-hidden="true">
                    ✳
                  </span>
                </h1>
                <p className="hero-description">{site.hero.description}</p>
                <div className="hero-actions">
                  <Link
                    className="button button-primary"
                    href={ui.routes.workspace}
                  >
                    {site.hero.primary}
                    <Arrow />
                  </Link>
                  <a className="button button-ghost" href="#how-it-works">
                    <span className="play-circle">
                      <Play size={11} fill="currentColor" />
                    </span>
                    {site.hero.secondary}
                  </a>
                </div>
                <p className="hero-note">
                  <span className="mini-avatar">AM</span>
                  <span className="mini-avatar mini-avatar-agent">✳</span>
                  <span className="mini-avatar mini-avatar-reviewer">◎</span>
                  {site.hero.note}
                </p>
              </motion.div>
            </div>
            <motion.div
              className="hero-floating"
              initial={reduced ? false : { opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{
                delay: ui.motion.reveal,
                duration: ui.motion.reveal,
              }}
            >
              <span className="floating-icon">
                <Workflow size={19} />
              </span>
              <div>
                <span>{site.hero.floating}</span>
                <small>{site.tagline}</small>
              </div>
              <span className="status-dot" />
            </motion.div>
            <div className="hero-bottom container">
              <span>{site.hero.index}</span>
              <span className="hero-bottom-caption">{site.hero.caption}</span>
              <div>
                <button
                  className="motion-toggle"
                  disabled={!!reduced}
                  onClick={() => setPaused(!paused)}
                  aria-label={paused ? site.ui.play : site.ui.pause}
                  aria-pressed={paused}
                >
                  {paused ? <Play size={14} /> : <Pause size={14} />}
                </button>
                <a
                  className="scroll-cue"
                  href="#platform"
                  aria-label={site.hero.secondary}
                >
                  <ArrowDown size={18} />
                </a>
              </div>
            </div>
          </section>

          <div className="principles-strip">
            <div className="container">
              {site.principles.map((principle, i) => {
                const Icon = [Sparkles, MessageSquare, ShieldCheck, Layers3][i];
                return (
                  <span key={principle}>
                    <Icon size={17} strokeWidth={1.6} />
                    {principle}
                  </span>
                );
              })}
            </div>
          </div>

          <section
            id="platform"
            className="platform section-light section-space"
          >
            <div className="container">
              <Reveal className="section-heading centered">
                <span className="eyebrow">{site.platform.eyebrow}</span>
                <h2>
                  {site.platform.title}
                  <br />
                  <em>{site.platform.italic}</em>
                </h2>
                <p>{site.platform.description}</p>
              </Reveal>
              <Reveal>
                <div
                  className="preview-tabs"
                  role="group"
                  aria-label={site.platform.previewLabel}
                >
                  {site.platform.tabs.map((label, index) => (
                    <button
                      key={label}
                      type="button"
                      aria-pressed={tab === index}
                      className={tab === index ? "selected" : ""}
                      onClick={() => setTab(index)}
                    >
                      {label}
                    </button>
                  ))}
                </div>
                <WorkspaceSnapshot tab={tab} />
              </Reveal>
              <div className="section-link">
                <Link href={ui.routes.workspace}>
                  {site.platform.link}
                  <Arrow />
                </Link>
                <span>{site.ui.demoNote}</span>
              </div>
            </div>
          </section>

          <section
            id="how-it-works"
            className="workflow-section section-light section-space"
          >
            <div className="container">
              <Reveal className="section-heading split-heading">
                <div>
                  <span className="eyebrow">{site.workflow.eyebrow}</span>
                  <h2>{site.workflow.title}</h2>
                </div>
                <p>{site.workflow.description}</p>
              </Reveal>
              <div className="story-grid">
                {site.workflow.steps.map((step, index) => {
                  const Icon = iconMap[step.icon as keyof typeof iconMap];
                  return (
                    <Reveal
                      key={step.number}
                      delay={index * ui.motion.stagger}
                      className={`story-card story-card-${index}`}
                    >
                      <div className="story-card-top">
                        <span>{step.number}</span>
                        <Icon size={24} strokeWidth={1.5} />
                      </div>
                      <div
                        className={`story-illustration story-illustration-${index}`}
                        aria-hidden="true"
                      >
                        {index === 0 ? (
                          <>
                            <div className="illustration-message">
                              <span className="avatar human">AM</span>
                              <div>
                                <i />
                                <i />
                              </div>
                            </div>
                            <div className="illustration-message illustration-reply">
                              <span className="avatar builder">✳</span>
                              <div>
                                <i />
                                <i />
                              </div>
                            </div>
                          </>
                        ) : index === 1 ? (
                          <>
                            <div className="orbit orbit-one" />
                            <div className="orbit orbit-two" />
                            <span className="orbit-center">✳</span>
                            <span className="orbit-node">◎</span>
                            <span className="orbit-node orbit-node-two">
                              AM
                            </span>
                          </>
                        ) : (
                          <>
                            <div className="illustration-approval">
                              <span className="approval-circle">
                                <CheckCheck size={30} />
                              </span>
                              <i />
                              <span className="illustration-chip">
                                <Check size={12} />
                                {site.ui.clientLabel}
                              </span>
                              <span className="illustration-chip">
                                <Check size={12} />
                                {site.ui.developerLabel}
                              </span>
                            </div>
                          </>
                        )}
                      </div>
                      <span className="tiny-label">{step.label}</span>
                      <h3>{step.title}</h3>
                      <p>{step.description}</p>
                    </Reveal>
                  );
                })}
              </div>
            </div>
          </section>

          <section className="agents-section section-space">
            <div className="container agents-layout">
              <Reveal className="section-heading">
                <span className="eyebrow">{site.agents.eyebrow}</span>
                <h2>
                  {site.agents.title}
                  <br />
                  <em>{site.agents.italic}</em>
                </h2>
                <p>{site.agents.description}</p>
                <Link
                  className="button button-outline-light"
                  href={`${ui.routes.workspace}#agents`}
                >
                  {site.ui.workspace}
                  <Arrow />
                </Link>
                <div className="agent-note">
                  <span className="connecting-line" />
                  {site.agents.note}
                </div>
              </Reveal>
              <div className="agent-profile-stack">
                {site.agents.cards.map((agent, i) => (
                  <Reveal
                    key={agent.name}
                    delay={i * ui.motion.stagger}
                    className={`landing-agent-card ${agent.className}`}
                  >
                    <div className="landing-agent-top">
                      <span className={`agent-symbol ${agent.className}`}>
                        {agent.symbol}
                      </span>
                      <span className="agent-role-label">{agent.role}</span>
                      <Arrow size={19} />
                    </div>
                    <h3>
                      {agent.name}
                      <span className="status-dot" />
                    </h3>
                    <p>{agent.description}</p>
                    <div className="agent-card-bottom">
                      <span className="agent-small-orbit">◎</span>
                      <span>{demo.agents[i].boundary}</span>
                    </div>
                  </Reveal>
                ))}
              </div>
            </div>
          </section>

          <section
            id="workflows"
            className="usecase-section section-space section-light"
          >
            <div className="container">
              <Reveal className="section-heading centered">
                <span className="eyebrow">{site.workflows.eyebrow}</span>
                <h2>
                  {site.workflows.title} <em>{site.workflows.italic}</em>
                </h2>
              </Reveal>
              <Reveal className="usecase-layout">
                <div
                  className="usecase-nav"
                  role="group"
                  aria-label={site.workflows.eyebrow}
                >
                  {site.workflows.items.map((item, index) => (
                    <button
                      aria-pressed={workflow === index}
                      onClick={() => setWorkflow(index)}
                      className={workflow === index ? "active" : ""}
                      key={item.id}
                    >
                      <span>0{index + 1}</span>
                      {item.label}
                      <Arrow />
                    </button>
                  ))}
                </div>
                <AnimatePresence mode="wait">
                  <motion.div
                    className="usecase-panel"
                    key={currentFlow.id}
                    initial={reduced ? false : { opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -8 }}
                    transition={{ duration: reduced ? 0 : ui.motion.hover }}
                  >
                    <div className="usecase-top">
                      <span className="tiny-label">{currentFlow.tag}</span>
                      <span className="usecase-symbol" aria-hidden="true">
                        {workflow === 0 ? "↗" : workflow === 1 ? "◎" : "✳"}
                      </span>
                    </div>
                    <h3>{currentFlow.title}</h3>
                    <p>{currentFlow.description}</p>
                    <div className="usecase-flow">
                      {currentFlow.steps.map((step, index) => (
                        <div key={step}>
                          <span>
                            {index === 3 ? (
                              <Check size={15} />
                            ) : (
                              <CircleDot size={15} />
                            )}
                          </span>
                          <small>{step}</small>
                          {index < 3 && (
                            <ArrowRight className="flow-arrow" size={14} />
                          )}
                        </div>
                      ))}
                    </div>
                    <Link
                      href={`${ui.routes.workspace}#${workflow === 0 ? "board" : workflow === 1 ? "knowledge" : "rooms"}`}
                      className="text-link"
                    >
                      {site.platform.link}
                      <Arrow />
                    </Link>
                  </motion.div>
                </AnimatePresence>
              </Reveal>
            </div>
          </section>

          <section className="control-section section-light section-space">
            <div className="container control-layout">
              <Reveal className="section-heading">
                <span className="eyebrow">{site.control.eyebrow}</span>
                <h2>{site.control.title}</h2>
                <p>{site.control.description}</p>
                <div className="control-stamp">
                  <ShieldCheck size={20} />
                  <span>{site.tagline}</span>
                </div>
              </Reveal>
              <div>
                {site.control.items.map((item, index) => {
                  const Icon = iconMap[item.icon as keyof typeof iconMap];
                  return (
                    <Reveal
                      key={item.title}
                      delay={index * ui.motion.stagger}
                      className="control-row"
                    >
                      <span className="control-icon">
                        <Icon size={23} strokeWidth={1.5} />
                      </span>
                      <div>
                        <h3>{item.title}</h3>
                        <p>{item.description}</p>
                      </div>
                    </Reveal>
                  );
                })}
              </div>
            </div>
          </section>

          <section className="faq-section section-light section-space">
            <div className="container faq-container">
              <Reveal className="section-heading">
                <span className="eyebrow">{site.faq.eyebrow}</span>
                <h2>{site.faq.title}</h2>
              </Reveal>
              <div className="faq-list">
                {site.faq.items.map((item, index) => (
                  <Reveal
                    className={`faq-item ${faq === index ? "open" : ""}`}
                    key={item.question}
                  >
                    <button
                      onClick={() => setFaq(faq === index ? null : index)}
                      aria-expanded={faq === index}
                      aria-controls={`answer-${index}`}
                    >
                      <span>{item.question}</span>
                      <Plus size={19} />
                    </button>
                    <div
                      id={`answer-${index}`}
                      className="faq-answer"
                      hidden={faq !== index}
                    >
                      <p>{item.answer}</p>
                    </div>
                  </Reveal>
                ))}
              </div>
            </div>
          </section>

          <section className="closing-section section-space">
            <div className="closing-orbit" aria-hidden="true" />
            <Reveal className="container section-heading centered">
              <span className="eyebrow">{site.closing.eyebrow}</span>
              <h2>
                {site.closing.title}
                <br />
                <em>{site.closing.italic}</em>
              </h2>
              <p>{site.closing.description}</p>
              <Link
                className="button button-primary"
                href={ui.routes.workspace}
              >
                {site.closing.cta}
                <Arrow />
              </Link>
            </Reveal>
            <div className="closing-wordmark" aria-hidden="true">
              {site.brand}
            </div>
          </section>
        </main>

        <SiteFooter />
      </div>
    </MotionConfig>
  );
}
