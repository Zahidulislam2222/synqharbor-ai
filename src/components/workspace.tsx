"use client";

import {
  useEffect,
  useRef,
  useState,
  useSyncExternalStore,
  type FormEvent,
} from "react";
import Link from "next/link";
import {
  AnimatePresence,
  motion,
  MotionConfig,
  useReducedMotion,
} from "motion/react";
import {
  ArrowDownToLine,
  ArrowRight,
  Bell,
  BookOpen,
  Check,
  CheckCheck,
  ChevronDown,
  ChevronRight,
  CircleDot,
  Clock3,
  FileImage,
  FileText,
  Folder,
  LayoutDashboard,
  ListTodo,
  LockKeyhole,
  Menu,
  MessageSquare,
  Moon,
  MoreHorizontal,
  Plus,
  Search,
  Send,
  Settings2,
  ShieldCheck,
  Sparkles,
  Sun,
  Table2,
  Waves,
  X,
} from "lucide-react";
import { demo, site } from "@/content";
import { ui } from "@/config/ui";
import {
  approveTask,
  changeTaskStatus,
  createTask,
  visibleTasks,
  type Task,
  type View,
} from "@/lib/demo-state";
import { Arrow, Dialog, Logo } from "./shared";

const navIcons = {
  overview: LayoutDashboard,
  rooms: MessageSquare,
  board: ListTodo,
  agents: Sparkles,
  approvals: ShieldCheck,
  artifacts: FileText,
  knowledge: BookOpen,
  activity: Clock3,
};

function subscribeHash(listener: () => void) {
  window.addEventListener("hashchange", listener);
  return () => window.removeEventListener("hashchange", listener);
}

function currentHash() {
  const hash = window.location.hash.slice(1);
  return hash in demo.views ? (hash as View) : "overview";
}

function Avatar({ name, large = false }: { name: string; large?: boolean }) {
  const agent = demo.agents.find((item) => item.name === name);
  return (
    <span
      className={`avatar ${agent?.className ?? "human"} ${large ? "avatar-large" : ""}`}
      role="img"
      aria-label={name}
    >
      {agent?.symbol ??
        name
          .split(" ")
          .map((part) => part[0])
          .join("")
          .slice(0, 2)}
    </span>
  );
}

function TaskCard({ task, onOpen }: { task: Task; onOpen: () => void }) {
  return (
    <button className="task-card" onClick={onOpen}>
      <span className="task-card-id">
        {task.id}
        <MoreHorizontal size={16} aria-hidden="true" />
      </span>
      <h3>{task.title}</h3>
      <span className="task-card-tags">
        {task.tags.map((tag) => (
          <span key={tag}>{tag}</span>
        ))}
      </span>
      <span className="task-card-footer">
        <span>
          <Avatar name={task.owner} />
          {task.owner}
        </span>
        <span>
          <MessageSquare size={12} />
          {task.criteria.length}
        </span>
      </span>
    </button>
  );
}

function Board({
  compact = false,
  filtered,
  onNewTask,
  onOpen,
}: {
  compact?: boolean;
  filtered: Task[];
  onNewTask: () => void;
  onOpen: (id: string) => void;
}) {
  return (
    <div className={`work-board ${compact ? "board-compact" : ""}`}>
      {demo.statuses.map((status) => (
        <section
          className="board-column"
          key={status.id}
          aria-label={status.label}
        >
          <div className="board-column-heading">
            <span>
              <span className={`task-dot task-dot-${status.id}`} />
              {status.label}
              <small>
                {filtered.filter((task) => task.status === status.id).length}
              </small>
            </span>
            <button
              onClick={onNewTask}
              className="icon-button"
              aria-label={site.ui.newTask}
            >
              <Plus size={16} />
            </button>
          </div>
          <div className="board-cards">
            {filtered
              .filter((task) => task.status === status.id)
              .map((task) => (
                <TaskCard
                  task={task}
                  key={task.id}
                  onOpen={() => onOpen(task.id)}
                />
              ))}
          </div>
        </section>
      ))}
    </div>
  );
}

function ApprovalSteps({
  task,
  onApprove,
}: {
  task: Task;
  onApprove: (role: "client" | "developer") => void;
}) {
  return (
    <div className="approval-steps">
      <div className={task.clientApproved ? "approved" : ""}>
        <span className="approval-step-icon">
          {task.clientApproved ? <Check size={18} /> : <CircleDot size={18} />}
        </span>
        <div>
          <strong>{demo.labels.clientStep}</strong>
          <small>
            {task.clientApproved
              ? site.ui.approvalComplete
              : site.ui.pendingClient}
          </small>
        </div>
        <button
          className="small-button"
          onClick={() => onApprove("client")}
          aria-label={
            task.clientApproved
              ? site.ui.approvalComplete
              : site.ui.clientApproval
          }
          disabled={task.clientApproved}
        >
          {task.clientApproved ? (
            <CheckCheck size={16} />
          ) : (
            site.ui.clientApproval
          )}
        </button>
      </div>
      <div className={task.developerApproved ? "approved" : ""}>
        <span className="approval-step-icon">
          {task.developerApproved ? (
            <Check size={18} />
          ) : (
            <LockKeyhole size={18} />
          )}
        </span>
        <div>
          <strong>{demo.labels.developerStep}</strong>
          <small>
            {task.developerApproved
              ? site.ui.approvalComplete
              : site.ui.pendingDeveloper}
          </small>
        </div>
        <button
          className="small-button"
          onClick={() => onApprove("developer")}
          aria-label={
            task.developerApproved
              ? site.ui.approvalComplete
              : site.ui.developerApproval
          }
          disabled={!task.clientApproved || task.developerApproved}
        >
          {task.developerApproved ? (
            <CheckCheck size={16} />
          ) : (
            site.ui.developerApproval
          )}
        </button>
      </div>
      <p>
        <ShieldCheck size={13} />
        {demo.labels.notPublished}
      </p>
    </div>
  );
}

function subscribeViewport(listener: () => void) {
  const query = window.matchMedia(
    `(max-width: ${ui.preview.navigationBreakpoint}px)`,
  );
  query.addEventListener("change", listener);
  return () => query.removeEventListener("change", listener);
}
function mobileSnapshot() {
  return window.matchMedia(`(max-width: ${ui.preview.navigationBreakpoint}px)`)
    .matches;
}

export function Workspace() {
  const prefersReducedMotion = useReducedMotion();
  const isMobile = useSyncExternalStore(
    subscribeViewport,
    mobileSnapshot,
    () => false,
  );
  const sidebarRef = useRef<HTMLElement>(null);
  const menuButtonRef = useRef<HTMLButtonElement>(null);
  const view = useSyncExternalStore(
    subscribeHash,
    currentHash,
    () => "overview" as View,
  );
  const [tasks, setTasks] = useState<Task[]>(() => structuredClone(demo.tasks));
  const [query, setQuery] = useState("");
  const [project, setProject] = useState("");
  const [newTaskOpen, setNewTaskOpen] = useState(false);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [sourceId, setSourceId] = useState<number | null>(null);
  const [mobileNav, setMobileNav] = useState(false);
  const [toast, setToast] = useState("");
  const [title, setTitle] = useState("");
  const [taskProject, setTaskProject] = useState(demo.projects[0]);
  const [priority, setPriority] = useState(demo.priorities[0]);
  const [error, setError] = useState("");
  const [messages, setMessages] = useState(demo.messages);
  const [message, setMessage] = useState("");
  const [theme, setTheme] = useState("midnight");
  const [calm, setCalm] = useState(false);
  const [notifications, setNotifications] = useState(true);
  const [timezone, setTimezone] = useState(demo.timezones[0]);
  const [reviewedArtifacts, setReviewedArtifacts] = useState<string[]>([]);
  const searchRef = useRef<HTMLInputElement>(null);
  const toastTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const selected = tasks.find((task) => task.id === taskId);
  const filtered = visibleTasks(tasks, query, project);
  const waiting = tasks.filter(
    (task) => task.status === "review" && !task.developerApproved,
  );
  const activeTasks = tasks.filter((task) => task.status === "progress");
  const completeTasks = tasks.filter((task) => task.status === "complete");
  const spotlight =
    tasks.find((task) => task.id === demo.tasks[0].id) ?? tasks[0];
  const currentView = demo.views[view];

  useEffect(() => {
    const handle = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        searchRef.current?.focus();
      }
    };
    window.addEventListener("keydown", handle);
    return () => {
      window.removeEventListener("keydown", handle);
      if (toastTimer.current) clearTimeout(toastTimer.current);
    };
  }, []);

  useEffect(() => {
    if (!mobileNav || !isMobile) return;
    const previous = document.activeElement as HTMLElement | null;
    const panel = sidebarRef.current;
    const menuButton = menuButtonRef.current;
    const getControls = () =>
      Array.from(
        panel?.querySelectorAll<HTMLElement>(
          "a[href], button:not([disabled]), input, select",
        ) ?? [],
      ).filter((element) => element.getClientRects().length > 0);
    getControls()[0]?.focus();
    const handle = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        setMobileNav(false);
        return;
      }
      if (event.key !== "Tab") return;
      const controls = getControls();
      const first = controls[0],
        last = controls.at(-1);
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last?.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first?.focus();
      }
    };
    document.addEventListener("keydown", handle);
    return () => {
      document.removeEventListener("keydown", handle);
      if (previous?.isConnected && previous.getClientRects().length)
        previous.focus();
      else if (menuButton?.getClientRects().length) menuButton.focus();
    };
  }, [mobileNav, isMobile]);

  function navigate(target: View) {
    window.history.pushState(null, "", `#${target}`);
    window.dispatchEvent(new HashChangeEvent("hashchange"));
    setMobileNav(false);
    setQuery("");
  }
  function notify(text: string) {
    if (!notifications) return;
    setToast(text);
    if (toastTimer.current) clearTimeout(toastTimer.current);
    toastTimer.current = setTimeout(() => setToast(""), ui.demo.toastDuration);
  }
  function submitTask(event: FormEvent) {
    event.preventDefault();
    try {
      const task = createTask(title, taskProject, priority, tasks);
      setTasks([...tasks, task]);
      setTitle("");
      setError("");
      setNewTaskOpen(false);
      navigate("board");
      notify(site.ui.created);
    } catch {
      setError(site.ui.required);
    }
  }
  function setStatus(task: Task, status: string) {
    try {
      setTasks(
        tasks.map((item) =>
          item.id === task.id ? changeTaskStatus(item, status) : item,
        ),
      );
      notify(site.ui.updated);
    } catch {
      notify(demo.labels.statusCompleteRequiresApproval);
    }
  }
  function approve(task: Task, role: "client" | "developer") {
    try {
      const next = approveTask(task, role, task.version);
      setTasks(tasks.map((item) => (item.id === task.id ? next : item)));
      notify(
        role === "client" ? site.ui.approvedClient : site.ui.approvedDeveloper,
      );
    } catch {
      notify(site.ui.reviewFirst);
    }
  }
  function sendMessage(event: FormEvent) {
    event.preventDefault();
    if (!message.trim() || message.length > ui.demo.maxMessageLength) return;
    setMessages([
      ...messages,
      {
        name: demo.workspace.user,
        initials: demo.workspace.userInitials,
        role: demo.workspace.userRole,
        time: new Date().toLocaleTimeString("en-GB", {
          timeZone: timezone,
          hour: "2-digit",
          minute: "2-digit",
        }),
        text: message.trim(),
        type: "human",
      },
    ]);
    setMessage("");
    notify(site.ui.messageSent);
  }
  function downloadReport(task: Task) {
    const text = [
      site.ui.sampleReportTitle,
      site.ui.sampleReportNote,
      "",
      task.id,
      task.title,
      `${site.ui.project}: ${task.project}`,
      `${site.ui.version}: ${task.version}`,
      `${site.ui.status}: ${task.status}`,
      "",
      site.ui.acceptance,
      ...task.criteria.map((item) => `- ${item}`),
    ].join("\n");
    const url = URL.createObjectURL(
      new Blob([text], { type: "text/plain;charset=utf-8" }),
    );
    const link = document.createElement("a");
    link.href = url;
    link.download = demo.labels.reportFile;
    link.click();
    requestAnimationFrame(() => URL.revokeObjectURL(url));
    notify(site.ui.downloaded);
  }

  return (
    <MotionConfig reducedMotion={calm ? "always" : "user"}>
      <div className="workspace-app" data-theme={theme} data-calm={calm}>
        <a className="skip-link" href="#workspace-main">
          {site.ui.skip}
        </a>
        {mobileNav && (
          <button
            className="sidebar-scrim"
            aria-label={site.ui.closeMenu}
            onClick={() => setMobileNav(false)}
          />
        )}
        <aside
          ref={sidebarRef}
          inert={isMobile && !mobileNav}
          aria-hidden={isMobile && !mobileNav ? true : undefined}
          className={`app-sidebar ${mobileNav ? "sidebar-open" : ""}`}
        >
          <div className="app-brand">
            <Logo />
            <button
              className="sidebar-close icon-button"
              onClick={() => setMobileNav(false)}
              aria-label={site.ui.closeMenu}
            >
              <X size={20} />
            </button>
          </div>
          <button
            className="workspace-switcher"
            onClick={() => navigate("settings")}
          >
            <span className="workspace-letter">{demo.workspace.initials}</span>
            <span>
              <strong>{demo.workspace.name}</strong>
              <small>{site.ui.preview}</small>
            </span>
            <ChevronDown size={15} />
          </button>
          <nav
            className="app-navigation"
            aria-label={site.ui.workspaceNavigation}
          >
            {demo.navigation.map((item) => {
              const Icon = navIcons[item.id as keyof typeof navIcons];
              return (
                <a
                  key={item.id}
                  href={`#${item.id}`}
                  onClick={() => {
                    setMobileNav(false);
                    setQuery("");
                  }}
                  className={view === item.id ? "active" : ""}
                  aria-current={view === item.id ? "page" : undefined}
                >
                  <Icon size={18} strokeWidth={1.65} />
                  <span>{item.label}</span>
                  {item.id === "approvals" && waiting.length > 0 && (
                    <small>{waiting.length}</small>
                  )}
                </a>
              );
            })}
          </nav>
          <div className="sidebar-projects">
            <span className="tiny-label">{site.ui.project}</span>
            {demo.projects.map((name, index) => (
              <button
                key={name}
                onClick={() => {
                  navigate("board");
                  setProject(name);
                }}
              >
                <span className={`project-square project-square-${index}`} />
                {name}
                <ChevronRight size={13} />
              </button>
            ))}
          </div>
          <div className="sidebar-bottom">
            <div className="sidebar-invitation">
              <Waves size={28} strokeWidth={1.5} />
              <p>{demo.workspace.plan}</p>
              <Link href={ui.routes.home}>
                {site.ui.return}
                <Arrow size={14} />
              </Link>
            </div>
            <button
              className={
                view === "settings"
                  ? "sidebar-settings active"
                  : "sidebar-settings"
              }
              onClick={() => navigate("settings")}
            >
              <Settings2 size={17} />
              {site.ui.settings}
            </button>
            <div className="app-user">
              <Avatar name={demo.workspace.user} />
              <div>
                <strong>{demo.workspace.user}</strong>
                <small>{demo.workspace.userRole}</small>
              </div>
              <span className="status-dot" />
            </div>
          </div>
        </aside>

        <div className="app-body" inert={mobileNav && isMobile}>
          <header className="app-header">
            <div className="app-breadcrumb">
              <button
                ref={menuButtonRef}
                className="app-mobile-menu icon-button"
                aria-label={site.ui.mobileNav}
                onClick={() => setMobileNav(true)}
              >
                <Menu size={20} />
              </button>
              <span className="breadcrumb-workspace">
                {demo.workspace.name}
              </span>
              <ChevronRight className="breadcrumb-divider" size={14} />
              <span>
                {demo.navigation.find((item) => item.id === view)?.label ??
                  site.ui.settings}
              </span>
            </div>
            <div className="app-header-right">
              <label className="app-search">
                <Search size={16} />
                <input
                  ref={searchRef}
                  type="search"
                  value={query}
                  onChange={(event) => {
                    setQuery(event.target.value);
                    if (!["overview", "board"].includes(view))
                      window.location.hash = "board";
                  }}
                  placeholder={site.ui.searchPlaceholder}
                  aria-label={site.ui.search}
                />
                <kbd>⌘ K</kbd>
              </label>
              <button
                className="icon-button notification-button"
                aria-label={site.ui.activity}
                onClick={() => navigate("activity")}
              >
                <Bell size={19} />
                <i />
              </button>
              <Avatar name={demo.workspace.user} />
            </div>
          </header>

          <main className="app-main" id="workspace-main" tabIndex={-1}>
            <div className="app-page-heading">
              <div>
                <span className="app-eyebrow">
                  <span className="status-dot" />
                  {site.ui.preview} <span>·</span> {site.ui.sample}
                </span>
                <h1>{currentView.title}</h1>
                <p>{currentView.description}</p>
              </div>
              <button
                className="button button-primary app-new-task"
                onClick={() => setNewTaskOpen(true)}
              >
                <Plus size={17} />
                {site.ui.newTask}
              </button>
            </div>
            <motion.div
              key={view}
              initial={
                calm || prefersReducedMotion ? false : { opacity: 0, y: 8 }
              }
              animate={{ opacity: 1, y: 0 }}
              transition={{
                duration: calm || prefersReducedMotion ? 0 : ui.motion.hover,
              }}
            >
              {view === "overview" && (
                <>
                  <div className="overview-top">
                    <div className="workspace-spotlight">
                      <span className="tiny-label">{demo.labels.focus}</span>
                      <h2>{demo.labels.focusTitle}</h2>
                      <p>{demo.labels.focusDescription}</p>
                      <button
                        className="button button-primary"
                        onClick={() => setTaskId(spotlight.id)}
                      >
                        {demo.labels.reviewCta}
                        <Arrow />
                      </button>
                      <div className="spotlight-art" aria-hidden="true">
                        <span />
                        <span />
                        <span />
                      </div>
                      <div className="spotlight-footer">
                        <span className="avatar builder">✳</span>
                        <span className="avatar reviewer">◎</span>
                        <span>{demo.workspace.projectName}</span>
                        <span className="spotlight-label">
                          <CircleDot size={12} />
                          {site.ui.review}
                        </span>
                      </div>
                    </div>
                    <div className="overview-stats">
                      <button
                        onClick={() => {
                          navigate("board");
                          setProject("");
                        }}
                      >
                        <span className="stat-icon">
                          <Sparkles size={20} />
                        </span>
                        <strong>
                          {activeTasks.length.toString().padStart(2, "0")}
                        </strong>
                        <span>
                          {demo.labels.moving}
                          <ArrowRight size={15} />
                        </span>
                      </button>
                      <button onClick={() => navigate("approvals")}>
                        <span className="stat-icon">
                          <ShieldCheck size={20} />
                        </span>
                        <strong>
                          {waiting.length.toString().padStart(2, "0")}
                        </strong>
                        <span>
                          {demo.labels.needsYou}
                          <ArrowRight size={15} />
                        </span>
                      </button>
                      <button onClick={() => navigate("board")}>
                        <span className="stat-icon">
                          <CheckCheck size={20} />
                        </span>
                        <strong>
                          {completeTasks.length.toString().padStart(2, "0")}
                        </strong>
                        <span>
                          {demo.labels.completed}
                          <ArrowRight size={15} />
                        </span>
                      </button>
                    </div>
                  </div>
                  <div className="app-section-heading">
                    <h2>{site.ui.viewBoard}</h2>
                    <button
                      className="text-link"
                      onClick={() => navigate("board")}
                    >
                      {site.ui.viewAll}
                      <Arrow size={15} />
                    </button>
                  </div>
                  <Board
                    compact
                    filtered={filtered}
                    onNewTask={() => setNewTaskOpen(true)}
                    onOpen={setTaskId}
                  />
                  <div className="overview-bottom">
                    <section className="app-panel">
                      <div className="app-section-heading">
                        <h2>{site.ui.activity}</h2>
                        <button
                          className="icon-button"
                          onClick={() => navigate("activity")}
                          aria-label={site.ui.activity}
                        >
                          <ArrowRight size={17} />
                        </button>
                      </div>
                      <ActivityList compact />
                    </section>
                    <section className="app-panel">
                      <div className="app-section-heading">
                        <h2>{demo.labels.sources}</h2>
                        <button
                          className="icon-button"
                          onClick={() => navigate("knowledge")}
                          aria-label={demo.labels.sources}
                        >
                          <ArrowRight size={17} />
                        </button>
                      </div>
                      {demo.sources.slice(0, 2).map((source, index) => (
                        <button
                          className="source-compact"
                          onClick={() => setSourceId(index)}
                          key={source.title}
                        >
                          <span>
                            <FileText size={17} />
                          </span>
                          <div>
                            <strong>{source.title}</strong>
                            <small>{source.type}</small>
                          </div>
                          <Arrow size={14} />
                        </button>
                      ))}
                    </section>
                  </div>
                </>
              )}

              {view === "board" && (
                <>
                  <div className="board-toolbar">
                    <div className="toolbar-pill">
                      <ListTodo size={15} />
                      {site.ui.all}
                      <span>{filtered.length}</span>
                    </div>
                    <label className="project-filter">
                      <Folder size={15} />
                      <select
                        value={project}
                        onChange={(event) => setProject(event.target.value)}
                        aria-label={site.ui.filter}
                      >
                        <option value="">{site.ui.all}</option>
                        {demo.projects.map((name) => (
                          <option key={name}>{name}</option>
                        ))}
                      </select>
                    </label>
                  </div>
                  {filtered.length ? (
                    <Board
                      filtered={filtered}
                      onNewTask={() => setNewTaskOpen(true)}
                      onOpen={setTaskId}
                    />
                  ) : (
                    <Empty />
                  )}
                </>
              )}

              {view === "rooms" && (
                <div className="room-layout">
                  <section className="room-chat app-panel">
                    <header className="room-heading">
                      <span className="room-hash">#</span>
                      <div>
                        <h2>{demo.workspace.room}</h2>
                        <p>{demo.labels.people}</p>
                      </div>
                      <span className="room-member-avatars">
                        {demo.workspace.participants.map((name) => (
                          <Avatar key={name} name={name} />
                        ))}
                      </span>
                    </header>
                    <div className="room-date">
                      <span>{demo.workspace.date}</span>
                    </div>
                    <div className="message-list">
                      {messages.map((item, index) => (
                        <div className="message" key={`${item.name}-${index}`}>
                          <Avatar
                            name={item.type === "human" ? item.name : item.name}
                          />
                          <div>
                            <header>
                              <strong>{item.name}</strong>
                              <span>{item.role}</span>
                              <time>{item.time}</time>
                            </header>
                            <p>{item.text}</p>
                            {index === 3 && (
                              <button
                                className="message-artifact"
                                onClick={() => setTaskId(demo.tasks[0].id)}
                              >
                                <span>
                                  <FileImage size={20} />
                                </span>
                                <div>
                                  <strong>{demo.artifacts[0].name}</strong>
                                  <small>
                                    {demo.artifacts[0].type} ·{" "}
                                    {`v${tasks.find((task) => task.id === demo.artifacts[0].task)?.version ?? ""}`}
                                  </small>
                                </div>
                                <Arrow />
                              </button>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                    <form className="message-composer" onSubmit={sendMessage}>
                      <label className="sr-only" htmlFor="room-message">
                        {site.ui.messagePlaceholder}
                      </label>
                      <textarea
                        id="room-message"
                        value={message}
                        onChange={(event) => setMessage(event.target.value)}
                        maxLength={ui.demo.maxMessageLength}
                        placeholder={site.ui.messagePlaceholder}
                        rows={2}
                      />
                      <div>
                        <small>{site.ui.demoNote}</small>
                        <button
                          className="send-button"
                          disabled={!message.trim()}
                          aria-label={site.ui.send}
                        >
                          <Send size={17} />
                        </button>
                      </div>
                    </form>
                  </section>
                  <aside className="room-context">
                    <span className="tiny-label">{demo.labels.context}</span>
                    <h3>{demo.workspace.projectName}</h3>
                    <p>{demo.sources[0].description}</p>
                    <div className="room-context-divider" />
                    <span className="tiny-label">{site.ui.evidence}</span>
                    {demo.artifacts.slice(0, 2).map((artifact) => (
                      <button
                        className="context-file"
                        key={artifact.name}
                        onClick={() => setTaskId(artifact.task)}
                      >
                        <FileText size={17} />
                        <span>
                          {artifact.name}
                          <small>{`v${tasks.find((task) => task.id === artifact.task)?.version ?? ""}`}</small>
                        </span>
                        <Arrow size={13} />
                      </button>
                    ))}
                    <div className="room-context-divider" />
                    <span className="tiny-label">{demo.labels.team}</span>
                    {[
                      demo.workspace.user,
                      "Maya Chen",
                      ...demo.agents.map((agent) => agent.name),
                    ].map((name) => (
                      <div className="room-person" key={name}>
                        <Avatar name={name} />
                        <span>{name}</span>
                        <span className="status-dot" />
                      </div>
                    ))}
                  </aside>
                </div>
              )}

              {view === "agents" && (
                <div className="workspace-agent-grid">
                  {demo.agents.map((agent, index) => (
                    <article
                      className="workspace-agent app-panel"
                      key={agent.name}
                    >
                      <div className="workspace-agent-visual">
                        <span className={`agent-symbol ${agent.className}`}>
                          {agent.symbol}
                        </span>
                        <span className="agent-orbit" />
                      </div>
                      <div className="workspace-agent-info">
                        <span className="tiny-label">{site.ui.role}</span>
                        <h2>{agent.name}</h2>
                        <p>{agent.role}</p>
                        <span className="agent-status">
                          <span className="status-dot" />
                          {agent.status}
                        </span>
                        <span className="tiny-label capabilities-label">
                          {demo.labels.capabilities}
                        </span>
                        <ul>
                          {agent.capabilities.map((capability) => (
                            <li key={capability}>
                              <Check size={15} />
                              {capability}
                            </li>
                          ))}
                        </ul>
                        <div className="agent-boundary">
                          <ShieldCheck size={17} />
                          <div>
                            <span className="tiny-label">
                              {demo.labels.boundary}
                            </span>
                            <p>{agent.boundary}</p>
                          </div>
                        </div>
                        <span className="tiny-label">
                          {demo.labels.assignment}
                        </span>
                        <button
                          className="assignment-button"
                          onClick={() =>
                            setTaskId(
                              index === 0 ? demo.tasks[0].id : demo.tasks[3].id,
                            )
                          }
                        >
                          {agent.assignment}
                          <Arrow size={16} />
                        </button>
                      </div>
                    </article>
                  ))}
                </div>
              )}

              {view === "approvals" && (
                <div className="approvals-layout">
                  {tasks.filter((task) => task.status === "review").length ? (
                    tasks
                      .filter((task) => task.status === "review")
                      .map((task) => (
                        <article
                          className="approval-card app-panel"
                          key={task.id}
                        >
                          <div className="approval-card-top">
                            <span className="review-badge">
                              <CircleDot size={13} />
                              {task.developerApproved
                                ? site.ui.approvalComplete
                                : task.clientApproved
                                  ? site.ui.pendingDeveloper
                                  : site.ui.pendingClient}
                            </span>
                            <span>
                              {task.id} · v{task.version}
                            </span>
                          </div>
                          <h2>{task.title}</h2>
                          <p>{task.description}</p>
                          <button
                            className="approval-artifact"
                            onClick={() => setTaskId(task.id)}
                          >
                            <FileImage size={25} />
                            <div>
                              <strong>
                                {demo.artifacts.find(
                                  (artifact) => artifact.task === task.id,
                                )?.name ?? task.title}
                              </strong>
                              <small>
                                {site.ui.version} {task.version} ·{" "}
                                {demo.labels.sampleEvidence}
                              </small>
                            </div>
                            <Arrow />
                          </button>
                          <ApprovalSteps
                            task={task}
                            onApprove={(role) => approve(task, role)}
                          />
                        </article>
                      ))
                  ) : (
                    <Empty />
                  )}
                  <aside className="approval-note">
                    <ShieldCheck size={29} strokeWidth={1.4} />
                    <h3>{site.control.items[2].title}</h3>
                    <p>{site.control.items[2].description}</p>
                    <p className="subtle-note">{site.ui.demoNote}</p>
                  </aside>
                </div>
              )}

              {view === "artifacts" && (
                <div className="artifact-grid">
                  {demo.artifacts.map((artifact, index) => (
                    <article
                      className="artifact-card app-panel"
                      key={artifact.name}
                    >
                      <button
                        className={`artifact-cover artifact-cover-${index}`}
                        onClick={() => setTaskId(artifact.task)}
                        aria-label={`${site.ui.inspect}: ${artifact.name}`}
                      >
                        {index === 0 ? (
                          <div className="artifact-mini-site">
                            <div />
                            <span>Northstar.</span>
                            <i />
                            <i />
                          </div>
                        ) : index === 1 ? (
                          <div className="artifact-mini-doc">
                            <FileText size={28} />
                            <i />
                            <i />
                            <i />
                            <span>
                              <CheckCheck size={17} />
                            </span>
                          </div>
                        ) : (
                          <div className="artifact-mini-table">
                            <Table2 size={30} />
                            <i />
                            <i />
                            <i />
                          </div>
                        )}
                        <span className="artifact-version">{`v${tasks.find((task) => task.id === artifact.task)?.version ?? ""}`}</span>
                      </button>
                      <div className="artifact-card-body">
                        <span className="tiny-label">{artifact.type}</span>
                        <h2>{artifact.name}</h2>
                        <p>{artifact.description}</p>
                        <div className="artifact-card-actions">
                          <button
                            className="text-link"
                            onClick={() => {
                              setReviewedArtifacts([
                                ...reviewedArtifacts,
                                `${artifact.task}:${tasks.find((task) => task.id === artifact.task)?.version}:${artifact.name}`,
                              ]);
                              notify(site.ui.reviewed);
                            }}
                            disabled={reviewedArtifacts.includes(
                              `${artifact.task}:${tasks.find((task) => task.id === artifact.task)?.version}:${artifact.name}`,
                            )}
                          >
                            {reviewedArtifacts.includes(
                              `${artifact.task}:${tasks.find((task) => task.id === artifact.task)?.version}:${artifact.name}`,
                            ) ? (
                              <Check size={16} />
                            ) : (
                              <ShieldCheck size={16} />
                            )}
                            {reviewedArtifacts.includes(
                              `${artifact.task}:${tasks.find((task) => task.id === artifact.task)?.version}:${artifact.name}`,
                            )
                              ? site.ui.review
                              : site.ui.markReviewed}
                          </button>
                          <button
                            className="icon-button"
                            aria-label={site.ui.download}
                            onClick={() =>
                              downloadReport(
                                tasks.find(
                                  (task) => task.id === artifact.task,
                                ) ?? tasks[0],
                              )
                            }
                          >
                            <ArrowDownToLine size={18} />
                          </button>
                        </div>
                      </div>
                    </article>
                  ))}
                </div>
              )}

              {view === "knowledge" && (
                <div className="knowledge-grid">
                  {demo.sources.map((source, index) => (
                    <button
                      className="knowledge-card app-panel"
                      key={source.title}
                      onClick={() => setSourceId(index)}
                    >
                      <div>
                        <span className="knowledge-icon">
                          <BookOpen size={23} strokeWidth={1.5} />
                        </span>
                        <span className="scope-badge">
                          <LockKeyhole size={11} />
                          {source.scope}
                        </span>
                      </div>
                      <span className="tiny-label">{source.type}</span>
                      <h2>{source.title}</h2>
                      <p>{source.description}</p>
                      <footer>
                        <span>{demo.labels.sourceFooter}</span>
                        <Arrow size={17} />
                      </footer>
                    </button>
                  ))}
                </div>
              )}

              {view === "activity" && (
                <section className="activity-full app-panel">
                  <ActivityList />
                </section>
              )}

              {view === "settings" && (
                <section className="settings-panel app-panel">
                  <span className="tiny-label">{demo.labels.preferences}</span>
                  <div className="setting-row">
                    <div>
                      <h2>{site.ui.theme}</h2>
                      <p>{site.ui.themeDescription}</p>
                    </div>
                    <div className="theme-options">
                      <button
                        className={theme === "midnight" ? "selected" : ""}
                        aria-pressed={theme === "midnight"}
                        onClick={() => setTheme("midnight")}
                      >
                        <Moon size={16} />
                        {site.ui.dark}
                      </button>
                      <button
                        className={theme === "daylight" ? "selected" : ""}
                        aria-pressed={theme === "daylight"}
                        onClick={() => setTheme("daylight")}
                      >
                        <Sun size={16} />
                        {site.ui.light}
                      </button>
                    </div>
                  </div>
                  <div className="setting-row">
                    <div>
                      <h2>{site.ui.reducedMotion}</h2>
                      <p>{site.ui.reducedMotionDescription}</p>
                    </div>
                    <button
                      className={`switch ${calm ? "switch-on" : ""}`}
                      role="switch"
                      aria-checked={calm}
                      aria-label={site.ui.reducedMotion}
                      onClick={() => setCalm(!calm)}
                    >
                      <span />
                    </button>
                  </div>
                  <div className="setting-row">
                    <div>
                      <h2>{site.ui.notifications}</h2>
                      <p>{site.ui.notificationsDescription}</p>
                    </div>
                    <button
                      className={`switch ${notifications ? "switch-on" : ""}`}
                      role="switch"
                      aria-checked={notifications}
                      aria-label={site.ui.notifications}
                      onClick={() => setNotifications(!notifications)}
                    >
                      <span />
                    </button>
                  </div>
                  <div className="setting-row">
                    <label htmlFor="timezone">
                      <h2>{site.ui.timezone}</h2>
                      <p>{demo.labels.previewOnly}</p>
                    </label>
                    <select
                      id="timezone"
                      value={timezone}
                      onChange={(event) => setTimezone(event.target.value)}
                    >
                      {demo.timezones.map((zone) => (
                        <option key={zone}>{zone}</option>
                      ))}
                    </select>
                  </div>
                  <div className="settings-footer">
                    <p>{demo.labels.previewOnly}</p>
                    <button
                      className="button button-primary"
                      onClick={() => notify(site.ui.saved)}
                    >
                      {site.ui.save}
                      <Check size={16} />
                    </button>
                  </div>
                  <div className="reset-row">
                    <div>
                      <h2>{site.ui.reset}</h2>
                      <p>{demo.labels.resetDescription}</p>
                    </div>
                    <button
                      className="small-button"
                      onClick={() => {
                        setTasks(structuredClone(demo.tasks));
                        setMessages(demo.messages);
                        setReviewedArtifacts([]);
                        setProject("");
                        setQuery("");
                        notify(site.ui.resetDone);
                      }}
                    >
                      {site.ui.reset}
                    </button>
                  </div>
                </section>
              )}
            </motion.div>
            <div className="app-preview-footer">
              <span className="status-dot" />
              {site.ui.demoNote}
              <Link href={ui.routes.home}>
                {site.ui.return}
                <Arrow size={13} />
              </Link>
            </div>
          </main>
        </div>

        {newTaskOpen && (
          <Dialog
            title={site.ui.newTask}
            onClose={() => {
              setNewTaskOpen(false);
              setError("");
            }}
          >
            <p className="dialog-description">{site.ui.newTaskDescription}</p>
            <form onSubmit={submitTask} className="task-form">
              <label htmlFor="task-title">{site.ui.taskTitle}</label>
              <input
                id="task-title"
                value={title}
                onChange={(event) => {
                  setTitle(event.target.value);
                  setError("");
                }}
                maxLength={ui.demo.maxTitleLength}
                placeholder={site.ui.taskTitlePlaceholder}
                aria-invalid={!!error}
                aria-describedby={error ? "task-error" : undefined}
              />
              {error && (
                <p role="alert" id="task-error" className="form-error">
                  {error}
                </p>
              )}
              <div className="form-row">
                <div>
                  <label htmlFor="task-project">{site.ui.project}</label>
                  <select
                    id="task-project"
                    value={taskProject}
                    onChange={(event) => setTaskProject(event.target.value)}
                  >
                    {demo.projects.map((name) => (
                      <option key={name}>{name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label htmlFor="task-priority">{site.ui.priority}</label>
                  <select
                    id="task-priority"
                    value={priority}
                    onChange={(event) => setPriority(event.target.value)}
                  >
                    {demo.priorities.map((name) => (
                      <option key={name}>{name}</option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="dialog-actions">
                <button
                  type="button"
                  className="small-button"
                  onClick={() => setNewTaskOpen(false)}
                >
                  {site.ui.cancel}
                </button>
                <button className="button button-primary" type="submit">
                  {site.ui.create}
                  <Plus size={16} />
                </button>
              </div>
            </form>
          </Dialog>
        )}

        {selected && (
          <Dialog
            title={site.ui.taskDetails}
            wide
            onClose={() => setTaskId(null)}
          >
            <div className="task-detail-meta">
              <span>{selected.id}</span>
              <span>{selected.project}</span>
              <span>v{selected.version}</span>
            </div>
            <h3 className="task-detail-title">{selected.title}</h3>
            <p className="dialog-description">{selected.description}</p>
            <div className="task-detail-fields">
              <label>
                {site.ui.status}
                <select
                  value={selected.status}
                  onChange={(event) => setStatus(selected, event.target.value)}
                >
                  {demo.statuses.map((status) => (
                    <option value={status.id} key={status.id}>
                      {status.label}
                    </option>
                  ))}
                </select>
              </label>
              <div>
                <span>{site.ui.owner}</span>
                <strong>
                  <Avatar name={selected.owner} />
                  {selected.owner}
                </strong>
              </div>
            </div>
            <div className="detail-section">
              <h4>{site.ui.acceptance}</h4>
              <ul>
                {selected.criteria.map((item) => (
                  <li key={item}>
                    <Check size={15} />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
            <div className="detail-section">
              <h4>{site.ui.evidence}</h4>
              <button
                className="detail-evidence"
                onClick={() => downloadReport(selected)}
              >
                <FileText size={20} />
                <span>
                  {demo.labels.reportEvidence}
                  <small>
                    {site.ui.version} {selected.version} · {site.ui.sample}
                  </small>
                </span>
                <ArrowDownToLine size={17} />
              </button>
            </div>
            {selected.status === "review" && (
              <ApprovalSteps
                task={selected}
                onApprove={(role) => approve(selected, role)}
              />
            )}
            <p className="dialog-preview-note">{site.ui.demoNote}</p>
          </Dialog>
        )}

        {sourceId !== null && (
          <Dialog
            title={demo.sources[sourceId].title}
            onClose={() => setSourceId(null)}
          >
            <div className="source-dialog-meta">
              <span className="tiny-label">{demo.sources[sourceId].type}</span>
              <span className="scope-badge">
                <LockKeyhole size={12} />
                {demo.sources[sourceId].scope}
              </span>
            </div>
            <p className="source-dialog-content">
              {demo.sources[sourceId].details}
            </p>
            <p className="dialog-preview-note">{demo.labels.sourceFooter}</p>
          </Dialog>
        )}
        <div className="toast-region" role="status" aria-live="polite">
          <AnimatePresence>
            {toast && (
              <motion.div
                className="toast"
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 8 }}
              >
                <span>
                  <Check size={16} />
                </span>
                {toast}
                <button aria-label={site.ui.close} onClick={() => setToast("")}>
                  <X size={15} />
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </MotionConfig>
  );
}

function Empty() {
  return (
    <div className="empty-state">
      <span>
        <Waves size={33} strokeWidth={1.3} />
      </span>
      <h2>{site.ui.empty}</h2>
      <p>{site.ui.emptyDescription}</p>
    </div>
  );
}

function ActivityList({ compact = false }: { compact?: boolean }) {
  return (
    <div className={`activity-list ${compact ? "activity-compact" : ""}`}>
      {demo.activity.slice(0, compact ? 3 : undefined).map((item) => (
        <div className="activity-item" key={item.text}>
          <Avatar name={item.actor} />
          <div>
            <p>
              <strong>{item.actor}</strong> {item.text}
            </p>
            <small>{item.time}</small>
          </div>
          <span className="activity-item-dot" />
        </div>
      ))}
    </div>
  );
}
