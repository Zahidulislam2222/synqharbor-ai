import { demo } from "@/content";
import { ui } from "@/config/ui";

export type Task = (typeof demo.tasks)[number];
export type Status = (typeof demo.statuses)[number]["id"];
export type View = keyof typeof demo.views;

export function createTask(
  title: string,
  project: string,
  priority: string,
  existing: Task[],
): Task {
  const normalized = title.trim();
  if (!normalized || normalized.length > ui.demo.maxTitleLength)
    throw new Error("Invalid task title");
  if (!demo.projects.includes(project) || !demo.priorities.includes(priority))
    throw new Error("Invalid task category");
  const numeric = existing.map((task) => Number(task.id.split("-")[1]));
  const id = `SH-${Math.max(0, ...numeric.filter(Number.isFinite)) + 1}`;
  return {
    id,
    title: normalized,
    project,
    priority,
    status: demo.statuses[0].id,
    owner: demo.workspace.user.split(" ")[0],
    type: demo.labels.taskType,
    description: demo.labels.taskCreatedDescription,
    criteria: [demo.labels.taskCreatedCriteria],
    tags: [demo.labels.taskCreatedTag],
    version: 1,
    clientApproved: false,
    developerApproved: false,
  };
}

export function approveTask(
  task: Task,
  role: "client" | "developer",
  version: number,
): Task {
  if (version !== task.version || task.status !== "review")
    throw new Error("Approval is stale or task is not in review");
  if (role === "developer" && !task.clientApproved)
    throw new Error("Content approval required");
  return {
    ...task,
    clientApproved: role === "client" || task.clientApproved,
    developerApproved: role === "developer" || task.developerApproved,
  };
}

export function changeTaskStatus(task: Task, status: string): Task {
  if (!demo.statuses.some((item) => item.id === status))
    throw new Error("Unknown status");
  if (
    status === "complete" &&
    task.status !== "complete" &&
    !task.developerApproved
  ) {
    throw new Error("Review approvals required");
  }
  if (status === task.status) return task;
  if (status === "complete") return { ...task, status };
  return {
    ...task,
    status,
    version: task.version + 1,
    clientApproved: false,
    developerApproved: false,
  };
}

export function visibleTasks(
  tasks: Task[],
  query: string,
  project: string,
): Task[] {
  const normalized = query.trim().toLocaleLowerCase();
  return tasks.filter(
    (task) =>
      (!project || task.project === project) &&
      [task.id, task.title, task.owner, task.project, ...task.tags]
        .join(" ")
        .toLocaleLowerCase()
        .includes(normalized),
  );
}
