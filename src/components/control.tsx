"use client";

import { Fragment, useCallback, useEffect, useRef, useState, type FormEvent } from "react";
import Link from "next/link";
import { control } from "@/config/control";
import copy from "@/content/control.json";
import { ApiError, request, type Person, type WorkspaceRecord, type WorkspaceState,
  type RunRecord, type Receipt, type Capabilities, type ControlTask, type RepositoryScope, type SourceRecord } from "@/lib/control-api";
import styles from "./control.module.css";

export function Control() {
  const csrf = useRef("");
  const identity = useRef<string | null>(null);
  const workspaceScope = useRef("");
  const pending = useRef(false);
  const generation = useRef(0);
  const keys = useRef(new Map<string, string>());
  const [user, setUser] = useState<Person | null>(null);
  const [initialized, setInitialized] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [registration, setRegistration] = useState(false);
  const [workspaces, setWorkspaces] = useState<WorkspaceRecord[]>([]);
  const [wid, setWid] = useState("");
  const [state, setState] = useState<WorkspaceState | null>(null);
  const [runs, setRuns] = useState<RunRecord[]>([]);
  const [receipts, setReceipts] = useState<Receipt[]>([]);
  const [capabilities, setCapabilities] = useState<Capabilities | null>(null);
  const [fixture, setFixture] = useState("");
  const [repositories, setRepositories] = useState<RepositoryScope[]>([]);
  const [repository, setRepository] = useState("");
  const [sources, setSources] = useState<SourceRecord[]>([]);
  const [selectedSources, setSelectedSources] = useState<string[]>([]);
  const [stopped, setStopped] = useState(false);
  const [invitation, setInvitation] = useState("");
  const [artifact, setArtifact] = useState<{ id: string; text: string } | null>(null);
  const [readArtifacts, setReadArtifacts] = useState<string[]>([]);
  const navigateWorkspace = useCallback((next: string) => {
    generation.current++;
    workspaceScope.current = next;
    keys.current.clear();
    setWid(next); setState(null); setRuns([]); setReceipts([]);
    setArtifact(null); setInvitation(""); setReadArtifacts([]);
    setRepositories([]); setRepository(""); setSources([]); setSelectedSources([]); setStopped(false); setFixture("");
  }, []);
  const clearPrivateState = useCallback(() => {
    navigateWorkspace("");
    csrf.current = "";
    setWorkspaces([]); setCapabilities(null);
  }, [navigateWorkspace]);

  const failure = useCallback((reason: unknown) => {
    const code = reason instanceof ApiError ? reason.code : "error";
    setError(code === "unavailable" ? copy.unavailable : copy.errors[code as keyof typeof copy.errors] ?? copy.error);
    if (reason instanceof ApiError && reason.status === 401) {
      clearPrivateState(); identity.current = null; setUser(null);
    } else if (code === "not_found") {
      clearPrivateState();
    }
  }, [clearPrivateState]);

  const verifySession = useCallback(async (epoch: number) => {
    const session = await request<{ user: Person | null; csrf: string }>(control.endpoints.session, "");
    if (epoch !== generation.current) return false;
    if ((session.user?.id ?? null) !== identity.current) {
      clearPrivateState(); identity.current = session.user?.id ?? null;
      csrf.current = session.csrf; setUser(session.user);
      return false;
    }
    csrf.current = session.csrf;
    return true;
  }, [clearPrivateState]);

  const refresh = useCallback(async () => {
    if (!user || wid !== workspaceScope.current) return;
    const epoch = generation.current;
    try {
    if (!await verifySession(epoch)) return;
    const [spaces, caps] = await Promise.all([
      request<WorkspaceRecord[]>(control.endpoints.workspaces, csrf.current),
      request<Capabilities>(control.endpoints.capabilities, csrf.current),
    ]);
    if (!await verifySession(epoch)) return;
    setWorkspaces(spaces); setCapabilities(caps);
    if (!wid && spaces.length) {
      // A refresh started before submission must not supersede create/join navigation.
      if (!pending.current) navigateWorkspace(spaces[0].id);
      return;
    }
    if (!wid) return;
    const base = `${control.endpoints.workspaces}/${wid}`;
    const [next, jobs, deliveries, targets, documents, execution] = await Promise.all([
      request<WorkspaceState>(base + "/state", csrf.current),
      request<RunRecord[]>(base + "/runs", csrf.current),
      request<Receipt[]>(base + "/deliveries", csrf.current),
      request<RepositoryScope[]>(base + "/repositories", csrf.current),
      request<SourceRecord[]>(base + "/sources", csrf.current),
      request<{ stopped: boolean }>(base + "/execution", csrf.current),
    ]);
    if (!await verifySession(epoch)) return;
    setState(next); setRuns(jobs); setReceipts(deliveries);
    setRepositories(targets); setSources(documents); setStopped(execution.stopped);
    setSelectedSources((ids) => ids.filter((id) => documents.some((source) => source.id === id)));
    } catch (reason) { if (epoch === generation.current) throw reason; }
  }, [user, wid, verifySession, navigateWorkspace]);

  useEffect(() => {
    let cancelled = false;
    const epoch = generation.current;
    request<{ user: Person | null; csrf: string }>(control.endpoints.session, "")
      .then((session) => { if (!cancelled && epoch === generation.current) { identity.current = session.user?.id ?? null; csrf.current = session.csrf; setUser(session.user); } })
      .catch((reason: unknown) => { if (!cancelled && epoch === generation.current) failure(reason); })
      .finally(() => { if (!cancelled && epoch === generation.current) setInitialized(true); });
    return () => { cancelled = true; };
  }, [failure]);

  useEffect(() => {
    const activate = () => {
      if (document.visibilityState !== "visible") return;
      // Shared cookies may have changed in another tab. Hide private state
      // before waiting for the current identity, and fence delayed responses.
      clearPrivateState(); identity.current = null; setUser(null); setInitialized(false);
      const epoch = generation.current;
      void request<{ user: Person | null; csrf: string }>(control.endpoints.session, "")
        .then((session) => {
          if (epoch !== generation.current) return;
          identity.current = session.user?.id ?? null; csrf.current = session.csrf; setUser(session.user);
        }).catch((reason: unknown) => { if (epoch === generation.current) failure(reason); })
        .finally(() => { if (epoch === generation.current) setInitialized(true); });
    };
    window.addEventListener("focus", activate);
    document.addEventListener("visibilitychange", activate);
    return () => { window.removeEventListener("focus", activate); document.removeEventListener("visibilitychange", activate); };
  }, [clearPrivateState, failure]);

  useEffect(() => {
    if (!user) return;
    let active = true;
    let running = false;
    const poll = async () => {
      if (!active || running || pending.current) return;
      running = true;
      try { await refresh(); } catch (reason) { if (active) failure(reason); }
      finally { running = false; }
    };
    void poll();
    const timer = setInterval(() => { void poll(); }, control.pollMilliseconds);
    return () => { active = false; clearInterval(timer); };
  }, [refresh, user, failure]);

  async function action(operation: () => Promise<void>) {
    if (pending.current) return;
    pending.current = true; setBusy(true); setError(""); setNotice("");
    const epoch = generation.current;
    try { if (await verifySession(epoch)) { await operation(); if (epoch === generation.current) setNotice(copy.saved); } }
    catch (reason) { if (epoch === generation.current) failure(reason); }
    finally { pending.current = false; setBusy(false); }
  }

  function requestKey(operation: string) {
    if (!keys.current.has(operation)) keys.current.set(operation, crypto.randomUUID());
    return keys.current.get(operation)!;
  }

  async function authenticate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    await action(async () => {
      const session = await request<{ csrf: string }>(control.endpoints.session, "");
      csrf.current = session.csrf;
      const result = await request<{ user: Person; csrf: string }>(registration ? control.endpoints.register : control.endpoints.login,
        csrf.current, { email: form.get("email"), password: form.get("password"), ...(registration ? { name: form.get("name") } : {}) });
      clearPrivateState(); identity.current = result.user.id; csrf.current = result.csrf; setUser(result.user);
    });
  }

  function submitForm(event: FormEvent<HTMLFormElement>, operation: (form: FormData) => Promise<void>, refreshAfter = true) {
    event.preventDefault();
    const element = event.currentTarget;
    const form = new FormData(element);
    void action(async () => { await operation(form); element.reset(); if (refreshAfter) await refresh(); });
  }

  const base = `${control.endpoints.workspaces}/${wid}`;
  const selectedState = state?.workspace.id === wid ? state : null;
  const canBuild = selectedState?.workspace.role === "owner" || selectedState?.workspace.role === "developer";
  const canClientApprove = selectedState?.workspace.role === "owner" || selectedState?.workspace.role === "client";
  const canCreateTask = canBuild || selectedState?.workspace.role === "client";

  async function runTask(task: ControlTask, mode: "draft" | "code") {
    await action(async () => {
      const chosen = repositories.find((item) => `${item.target}:${item.profile}` === repository);
      const key = `run:${task.id}:${task.revision}:${mode}:${fixture}:${repository}:${selectedSources.join(",")}`;
      await request(base + `/tasks/${task.id}/runs`, csrf.current,
        { revision: task.revision, request_key: requestKey(key), mode,
          ...(mode === "code" ? chosen ? { repository: chosen.target, profile: chosen.profile } : { fixture }
            : { source_ids: selectedSources }) });
      keys.current.delete(key); await refresh();
    });
  }

  async function approve(task: ControlTask, kind: "client" | "developer") {
    await action(async () => {
      await request(base + `/tasks/${task.id}/approvals`, csrf.current,
        { revision: task.revision, version: task.version, content_hash: task.content_hash, kind });
      await refresh();
    });
  }

  async function readArtifact(task: ControlTask) {
    if (!task.artifact_id) return;
    await action(async () => {
      const epoch = generation.current;
      const response = await fetch(control.apiPrefix + base + `/artifacts/${task.artifact_id}`, {
        credentials: "same-origin", cache: "no-store", signal: AbortSignal.timeout(control.requestTimeoutMilliseconds),
      });
      if (!response.ok) throw new ApiError(response.status === 401 ? "authentication_required" : "error", response.status);
      const text = await response.text();
      if (!await verifySession(epoch)) return;
      setArtifact({ id: task.artifact_id!, text });
      setReadArtifacts((ids) => [...ids, task.artifact_id!]);
    });
  }

  return <main className={styles.root}>
    <header className={styles.header}><div><p>{copy.product}</p><h1>{copy.title}</h1><p>{copy.intro}</p></div>
      <nav aria-label={copy.title}><Link href="/">{copy.website}</Link><Link href="/workspace/">{copy.demo}</Link></nav></header>
    {error && <p role="alert" className={styles.error}>{error}</p>}
    <p role="status" aria-live="polite">{busy ? copy.working : notice}</p>
    {!initialized ? <p>{copy.loading}</p> : !user ? <section className={styles.panel}>
      <h2>{registration ? copy.register : copy.signIn}</h2>
      <form onSubmit={(event) => { void authenticate(event); }}>
        {registration && <label>{copy.name}<input name="name" autoComplete="name" required maxLength={control.limits.name} /></label>}
        <label>{copy.email}<input name="email" type="email" autoComplete="username" required /></label>
        <label>{copy.password}<input name="password" type="password" autoComplete={registration ? "new-password" : "current-password"}
          minLength={control.limits.passwordMin} maxLength={control.limits.passwordMax} required /></label>
        <button disabled={busy}>{registration ? copy.register : copy.signIn}</button>
      </form>
      <button type="button" onClick={() => setRegistration(!registration)}>{registration ? copy.signIn : copy.register}</button>
    </section> : <Fragment key={user.id}>
      <div className={styles.row}><p>{user.name} · {user.email}</p><button disabled={busy} onClick={() => { void action(async () => {
        await request(control.endpoints.logout, csrf.current, {}, "POST");
        clearPrivateState(); identity.current = null; setUser(null);
      }); }}>{copy.signOut}</button><button disabled={busy} onClick={() => { void action(refresh); }}>{copy.refresh}</button>
        <button disabled={busy} onClick={() => { void action(async () => {
          await request("/auth/revoke-sessions", csrf.current, {}); clearPrivateState(); identity.current = null; setUser(null);
        }); }}>{copy.revokeSessions}</button></div>
      <section className={styles.grid}>
        <div className={styles.panel}><label>{copy.workspace}<select value={wid} onChange={(event) => {
          navigateWorkspace(event.target.value);
        }}><option value="">—</option>{workspaces.map((space) => <option key={space.id} value={space.id}>{space.name} · {space.role}</option>)}</select></label>
          <form onSubmit={(event) => submitForm(event, async (form) => {
            const epoch = generation.current;
            const space = await request<WorkspaceRecord>(control.endpoints.workspaces, csrf.current, { name: form.get("workspace") });
            if (await verifySession(epoch)) navigateWorkspace(space.id);
          }, false)}><label>{copy.workspaceName}<input name="workspace" required maxLength={control.limits.name} /></label><button disabled={busy}>{copy.createWorkspace}</button></form>
        </div>
        <div className={styles.panel}><form onSubmit={(event) => submitForm(event, async (form) => {
          const epoch = generation.current;
          const joined = await request<{ workspace_id: string }>(control.endpoints.acceptInvitation, csrf.current, { token: form.get("invitation") });
            if (await verifySession(epoch)) navigateWorkspace(joined.workspace_id);
          }, false)}><label>{copy.invitation}<input name="invitation" required autoComplete="off" /></label><button disabled={busy}>{copy.join}</button></form>
          {selectedState?.workspace.role === "owner" && <form onSubmit={(event) => submitForm(event, async (form) => {
            const epoch = generation.current;
            const result = await request<{ token: string }>(base + "/invitations", csrf.current, { role: form.get("role") });
            if (await verifySession(epoch)) setInvitation(result.token);
          })}><label htmlFor="control-invitation-role">{copy.role}</label><select id="control-invitation-role" name="role">{copy.roles.map((role) => <option key={role}>{role}</option>)}</select><button disabled={busy}>{copy.invite}</button></form>}
          {invitation && <div><p>{copy.inviteHelp}</p><output className={styles.digest}>{invitation}</output></div>}
        </div>
      </section>
      {state && selectedState && <>
        <section className={styles.panel}><h2>{state.workspace.name}</h2>
          <p>{capabilities?.inference_configured ? copy.inferenceReady : copy.inferenceMissing}</p>
          <p>{capabilities?.runner_configured ? copy.runnerReady : copy.runnerMissing}</p>
          <p role="status">{stopped ? copy.executionStopped : copy.executionEnabled}</p>
          {state.workspace.role === "owner" && <button disabled={busy} onClick={() => { void action(async () => {
            await request(base + "/execution", csrf.current, { stopped: !stopped }, "PUT"); await refresh();
          }); }}>{stopped ? copy.resumeExecution : copy.stopExecution}</button>}
          <label>{copy.repository}<select value={repository} onChange={(event) => { setRepository(event.target.value); setFixture(""); }}>
            <option value="">{copy.noRepository}</option>{repositories.map((item) => <option key={`${item.target}:${item.profile}`} value={`${item.target}:${item.profile}`}>{item.target} · {item.name}</option>)}
          </select></label>
          {repositories.filter((item) => `${item.target}:${item.profile}` === repository).map((item) => <div key={item.profile}><p>{item.specification}</p><p>{item.files.join(", ")}</p></div>)}
          <label>{copy.fixture}<select value={fixture} onChange={(event) => { setFixture(event.target.value); setRepository(""); }}>
            <option value="">—</option>{capabilities?.fixtures.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
          </select></label><p>{capabilities?.fixtures.find((item) => item.id === fixture)?.specification}</p><p>{copy.fixtureHelp}</p>
        </section>
        <section className={styles.panel}><h2>{copy.sources}</h2><p>{copy.sourceHelp}</p>
          {sources.map((source) => <div key={source.id}>
            <label><input type="checkbox" checked={selectedSources.includes(source.id)} onChange={(event) => {
              setSelectedSources((ids) => event.target.checked ? [...ids, source.id] : ids.filter((id) => id !== source.id));
            }} />{source.name}</label><details><summary>{copy.readSource}</summary><pre>{source.text}</pre></details>
            {canBuild && <button disabled={busy} onClick={() => { void action(async () => {
              await request(base + `/sources/${source.id}`, csrf.current, {}, "DELETE"); await refresh();
            }); }}>{copy.revokeSource}</button>}
          </div>)}
          {canCreateTask && <form onSubmit={(event) => submitForm(event, async (form) => {
            const file = form.get("sourceFile");
            if (file instanceof File && file.size > control.limits.sourceBytes) throw new ApiError("source_context_limit", 422);
            const text = file instanceof File && file.size ? await file.text() : String(form.get("sourceText"));
            await request(base + "/sources", csrf.current, { name: form.get("sourceName"), text });
          })}>
            <label>{copy.sourceName}<input name="sourceName" required maxLength={control.limits.name} /></label>
            <label>{copy.sourceText}<textarea name="sourceText" maxLength={control.limits.text} /></label>
            <label>{copy.sourceFile}<input name="sourceFile" type="file" accept=".txt,.md,text/plain,text/markdown" /></label>
            <button disabled={busy}>{copy.addSource}</button>
          </form>}
        </section>
        <section className={styles.panel}><h2>{copy.members}</h2>{state.members.map((person) => <div key={person.id}>
          <p>{person.name} · {person.role}</p>{state.workspace.role === "owner" && person.role !== "owner" && <button disabled={busy} onClick={() => { void action(async () => {
            await request(base + `/members/${person.id}`, csrf.current, {}, "DELETE"); await refresh();
          }); }}>{copy.removeMember}</button>}
        </div>)}</section>
        {canCreateTask && <section className={styles.panel}><h2>{copy.createTask}</h2>
          <form onSubmit={(event) => submitForm(event, async (form) => { await request(base + "/tasks", csrf.current,
            { title: form.get("title"), description: form.get("description"), project: form.get("project"),
              criteria: String(form.get("criteria")).split("\n").map((item) => item.trim()).filter(Boolean) }); })}>
            <label>{copy.taskTitle}<input name="title" required maxLength={control.limits.title} /></label>
            <label>{copy.project}<input name="project" required maxLength={control.limits.name} /></label>
            <label>{copy.description}<textarea name="description" maxLength={control.limits.text} /></label>
            <label>{copy.criteria}<textarea name="criteria" required maxLength={control.limits.text} /></label>
            <button disabled={busy}>{copy.createTask}</button>
          </form></section>}
        <section><h2>{copy.tasks}</h2>{!state.tasks.length && <p>{copy.empty}</p>}
          <div className={styles.grid}>{state.tasks.map((task) => {
            const active = runs.some((run) => run.task_id === task.id && ["queued", "running"].includes(run.status));
            const read = !!task.artifact_id && readArtifacts.includes(task.artifact_id);
            return <article key={task.id} className={styles.panel}><h3>{task.title}</h3><p>{task.description}</p>
              <p>{task.status} · {copy.version} {task.version} · {copy.revision} {task.revision}</p>
              <ul>{task.criteria.map((criterion, index) => <li key={index}>{criterion}</li>)}</ul>
              <p>{copy.client}: {task.clientApproved ? copy.approved : copy.pending} · {copy.developer}: {task.developerApproved ? copy.approved : copy.pending}</p>
              {task.content_hash && <code className={styles.digest}>{task.content_hash}</code>}
              <div className={styles.row}>
                {canBuild && <><button disabled={busy || active || stopped || !capabilities?.inference_configured} onClick={() => { void runTask(task, "draft"); }}>{copy.draft}</button>
                  <button disabled={busy || active || stopped || !capabilities?.inference_configured || !capabilities?.runner_configured || (!fixture && !repository)} onClick={() => { void runTask(task, "code"); }}>{copy.code}</button></>}
                {task.artifact_id && <><button disabled={busy} onClick={() => { void readArtifact(task); }}>{copy.artifact}</button>
                  <a href={control.apiPrefix + base + `/artifacts/${task.artifact_id}`} download>{copy.export}</a></>}
              </div>
              {task.status === "review" && <><p>{copy.approvalHelp}</p><div className={styles.row}>
                {canClientApprove && <button disabled={busy || !read || task.clientApproved} onClick={() => { void approve(task, "client"); }}>{copy.clientApproval}</button>}
                {canBuild && <button disabled={busy || !read || !task.clientApproved || task.developerApproved} onClick={() => { void approve(task, "developer"); }}>{copy.developerApproval}</button>}
                {canBuild && <button disabled={busy || stopped || !task.clientApproved || !task.developerApproved} onClick={() => { void action(async () => {
                  const key = `deliver:${task.id}:${task.version}`;
                  await request(base + `/tasks/${task.id}/deliveries`, csrf.current, { revision: task.revision, version: task.version,
                    content_hash: task.content_hash, request_key: requestKey(key) }); keys.current.delete(key); await refresh();
                }); }}>{copy.deliver}</button>}
              </div><p>{copy.deliveryHelp}</p></>}
            </article>;
          })}</div>
        </section>
        {artifact && <section className={styles.panel}><h2>{copy.artifactRead}</h2><button onClick={() => setArtifact(null)}>{copy.close}</button><pre>{artifact.text}</pre></section>}
        <section><h2>{copy.runs}</h2>{!runs.length && <p>{copy.noRuns}</p>}
          {runs.map((run) => <article className={styles.panel} key={run.id}><h3>{state.tasks.find((task) => task.id === run.task_id)?.title ?? run.task_id}</h3>
            <p>{run.mode} · {run.status} · {run.error_code}</p><ol>{run.events.map((item) => <li key={item.sequence}>{item.action}</li>)}</ol>
            <pre>{JSON.stringify(run.evidence, null, 2)}</pre>
            {canBuild && ["queued", "running"].includes(run.status) && <button disabled={busy} onClick={() => { void action(async () => {
              await request(base + `/runs/${run.id}/cancel`, csrf.current, {}); await refresh();
            }); }}>{copy.cancel}</button>}
          </article>)}
        </section>
        <section className={styles.panel}><h2>{copy.messages}</h2>
          {state.messages.map((message) => <p key={message.id}><strong>{message.name}</strong>: {message.text}</p>)}
          {canCreateTask && <form onSubmit={(event) => submitForm(event, async (form) => { await request(base + "/messages", csrf.current, { text: form.get("message") }); })}>
            <label>{copy.message}<textarea name="message" required maxLength={control.limits.text} /></label><button disabled={busy}>{copy.send}</button>
          </form>}
        </section>
        <section className={styles.panel}><h2>{copy.receipts}</h2>{!receipts.length && <p>{copy.noReceipts}</p>}
          {receipts.map((item) => <div key={item.id}><pre>{JSON.stringify(item, null, 2)}</pre>
            <a href={control.apiPrefix + base + `/deliveries/${item.id}/report`} download>{copy.deliveryReport}</a>
            {canBuild && item.release?.status === "uncertain" && <button disabled={busy} onClick={() => { void action(async () => {
              await request(base + `/deliveries/${item.id}/reconcile`, csrf.current, {}); await refresh();
            }); }}>{copy.reconcile}</button>}
          </div>)}
          <h2>{copy.activity}</h2><ul>{state.activity.map((item) => <li key={item.id}>{item.actor} · {item.action}</li>)}</ul>
        </section>
      </>}
    </Fragment>}
  </main>;
}
