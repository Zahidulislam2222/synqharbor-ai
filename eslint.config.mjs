import { defineConfig, globalIgnores } from "eslint/config";
import js from "@eslint/js";
import tseslint from "typescript-eslint";
import hooks from "eslint-plugin-react-hooks";
import a11y from "eslint-plugin-jsx-a11y";

export default defineConfig([
  js.configs.recommended,
  ...tseslint.configs.recommended,
  hooks.configs.flat.recommended,
  a11y.flatConfigs.recommended,
  globalIgnores([
    ".next/**",
    "out/**",
    "node_modules/**",
    ".tools/**",
    "memory/**",
    "next-env.d.ts",
  ]),
]);
