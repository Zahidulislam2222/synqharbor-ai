import { describe, expect, it } from "vitest";
import { demo } from "@/content";
import { ui } from "@/config/ui";
import {
  approveTask,
  changeTaskStatus,
  createTask,
  visibleTasks,
} from "@/lib/demo-state";

const task = () => structuredClone(demo.tasks[0]);

describe("bounded preview task creation", () => {
  it("normalizes a title and allocates an unused identifier", () => {
    const result = createTask(
      "  A new idea  ",
      demo.projects[0],
      demo.priorities[0],
      demo.tasks,
    );
    expect(result.title).toBe("A new idea");
    expect(demo.tasks.some((item) => item.id === result.id)).toBe(false);
    expect(result.clientApproved).toBe(false);
    expect(result.developerApproved).toBe(false);
  });
  it("supports an empty board without an invalid identifier", () => {
    expect(
      createTask("First task", demo.projects[0], demo.priorities[0], []).id,
    ).toMatch(/^SH-\d+$/);
  });
  it.each(["", "   ", "x".repeat(ui.demo.maxTitleLength + 1)])(
    "rejects invalid task title %j",
    (title) => {
      expect(() =>
        createTask(title, demo.projects[0], demo.priorities[0], demo.tasks),
      ).toThrow();
    },
  );
  it("rejects a project or priority outside the configured preview", () => {
    expect(() =>
      createTask(
        "A task",
        "unconfigured-project",
        demo.priorities[0],
        demo.tasks,
      ),
    ).toThrow();
    expect(() =>
      createTask(
        "A task",
        demo.projects[0],
        "unconfigured-priority",
        demo.tasks,
      ),
    ).toThrow();
  });
});

describe("versioned preview approval flow", () => {
  it("rejects developer release before client content approval", () => {
    const item = task();
    expect(() => approveTask(item, "developer", item.version)).toThrow();
  });
  it("rejects approval bound to a stale artifact version", () => {
    const item = task();
    expect(() => approveTask(item, "client", item.version - 1)).toThrow();
  });
  it("does not approve work outside review", () => {
    const item = { ...task(), status: "planned" };
    expect(() => approveTask(item, "client", item.version)).toThrow();
  });
  it("keeps client acceptance separate from release authorization", () => {
    const item = task();
    const content = approveTask(item, "client", item.version);
    expect(content.clientApproved).toBe(true);
    expect(content.developerApproved).toBe(false);
    const release = approveTask(content, "developer", item.version);
    expect(release.developerApproved).toBe(true);
    expect(item.clientApproved).toBe(false);
  });
  it("invalidates old approvals after a revision/status change", () => {
    const item = task();
    const content = approveTask(item, "client", item.version);
    const changed = changeTaskStatus(content, "progress");
    expect(changed.version).toBeGreaterThan(content.version);
    expect(changed.clientApproved).toBe(false);
    expect(() => approveTask(changed, "developer", content.version)).toThrow();
  });
  it("cannot mark an unapproved review or planned task complete", () => {
    expect(() => changeTaskStatus(task(), "complete")).toThrow();
    expect(() => changeTaskStatus(demo.tasks[2], "complete")).toThrow();
  });
  it("completes an approved version without erasing its approval evidence", () => {
    const item = task();
    const approved = approveTask(
      approveTask(item, "client", item.version),
      "developer",
      item.version,
    );
    const completed = changeTaskStatus(approved, "complete");
    expect(completed.status).toBe("complete");
    expect(completed.version).toBe(item.version);
    expect(completed.clientApproved && completed.developerApproved).toBe(true);
  });
  it("rejects unknown status values", () => {
    expect(() => changeTaskStatus(task(), "published-to-production")).toThrow();
  });
});

describe("workspace search boundaries", () => {
  it("matches titles, identifiers, owners, and project names case-insensitively", () => {
    expect(visibleTasks(demo.tasks, "SH-104", "")[0].id).toBe("SH-104");
    expect(
      visibleTasks(demo.tasks, "BUILDER", "").every(
        (item) => item.owner === "Builder",
      ),
    ).toBe(true);
    expect(visibleTasks(demo.tasks, "northstar", "").length).toBe(2);
  });
  it("combines project filters with search and returns a genuine empty result", () => {
    expect(visibleTasks(demo.tasks, "homepage", demo.projects[1])).toEqual([]);
    expect(visibleTasks(demo.tasks, "nothing-matches-this-query", "")).toEqual(
      [],
    );
  });
});
