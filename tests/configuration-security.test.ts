import { describe, expect, it } from "vitest";
import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";

function sourceFiles(root: string): string[] {
  return readdirSync(root, { withFileTypes: true }).flatMap((entry) => {
    const path = join(root, entry.name);
    return entry.isDirectory()
      ? sourceFiles(path)
      : /\.tsx?$/.test(path)
        ? [path]
        : [];
  });
}

describe("frontend configuration and secret regression boundary", () => {
  it("keeps provider URLs, model IDs, and secret material out of feature modules", () => {
    const files = [...sourceFiles("src/components"), ...sourceFiles("src/lib")];
    for (const file of files) {
      const source = readFileSync(file, "utf8");
      expect(source, file).not.toMatch(/https?:\/\//);
      expect(source, file).not.toMatch(
        /(?:bytedance|openai|anthropic)\/[\w.-]+/i,
      );
      expect(source, file).not.toMatch(
        /BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY/,
      );
      expect(source, file).not.toMatch(/(?:sk-|Bearer )[A-Za-z0-9_-]{20,}/);
    }
  });
  it("has a static export without server actions or runtime integrations", () => {
    expect(readFileSync("next.config.ts", "utf8")).toMatch(
      /output:\s*["']export["']/,
    );
    expect(
      sourceFiles("src")
        .map((file) => readFileSync(file, "utf8"))
        .join("\n"),
    ).not.toContain("'use server'");
  });
  it("keeps runtime public variables documented without a paid provider key", () => {
    const example = readFileSync(".env.example", "utf8");
    expect(example).toContain("NEXT_PUBLIC_SITE_URL=");
    expect(example).not.toContain("API_KEY=");
  });
});
