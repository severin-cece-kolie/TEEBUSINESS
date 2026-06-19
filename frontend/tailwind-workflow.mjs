import { spawn } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const root = path.resolve(import.meta.dirname, "..");
const input = path.join(root, "frontend", "tailwind.css");
const compatibilityOutput = path.join(
  root,
  "static",
  "css",
  "tailwind.generated.css",
);
const standaloneOutput = path.join(
  root,
  "static",
  "css",
  "tailwind.standalone.css",
);
const rawOutput = path.join(os.tmpdir(), `teebusiness-tailwind-${process.pid}.css`);
const cli = path.join(
  root,
  "node_modules",
  ".bin",
  process.platform === "win32" ? "tailwindcss.cmd" : "tailwindcss",
);

const watch = process.argv.includes("--watch");
const minify = process.argv.includes("--minify");
const propertyPattern = /@property\s+--[\w-]+\s*\{[^{}]*\}/g;
const individualTransformPattern = /\b(?:translate|scale|rotate)\s*:[^;{}]+;?/g;

function writeBuildOutputs() {
  if (!fs.existsSync(rawOutput)) return;

  const raw = fs.readFileSync(rawOutput, "utf8");
  const registrations = raw.match(propertyPattern) ?? [];
  const individualTransforms = raw.match(individualTransformPattern) ?? [];
  const compatible = raw
    .replace(propertyPattern, "")
    .replace(individualTransformPattern, "");
  const banner = minify
    ? "/*! Tailwind v4 candidate; typed properties and individual transforms removed while CDN v3 remains active. */"
    : [
        "/*",
        " * Tailwind v4 candidate.",
        " *",
        " * Compatibility note: CSS @property registrations and individual",
        " * transform properties are removed while Tailwind's v3 CDN runtime",
        " * remains active. Otherwise gradients and transforms conflict.",
        " * Remove this compatibility step together with the CDN.",
        " */",
        "",
      ].join("\n");

  const standaloneBanner = minify
    ? "/*! Native standalone Tailwind v4 build; generated file. */"
    : [
        "/*",
        " * Native standalone Tailwind v4 build.",
        " * Generated from frontend/tailwind.css without coexistence filtering.",
        " */",
        "",
      ].join("\n");

  fs.writeFileSync(compatibilityOutput, `${banner}${compatible}`);
  fs.writeFileSync(standaloneOutput, `${standaloneBanner}${raw}`);
  console.log(
    `Prepared ${path.relative(root, compatibilityOutput)} (${registrations.length} @property registrations and ${individualTransforms.length} individual transforms removed for CDN compatibility).`,
  );
  console.log(
    `Prepared ${path.relative(root, standaloneOutput)} (native Tailwind v4 output).`,
  );
}

function cleanup() {
  fs.rmSync(rawOutput, { force: true });
}

const args = ["-i", input, "-o", rawOutput];
if (watch) args.push("--watch");
if (minify) args.push("--minify");

const child = spawn(cli, args, {
  cwd: root,
  stdio: "inherit",
});

if (watch) {
  let lastModified = 0;
  const timer = setInterval(() => {
    if (!fs.existsSync(rawOutput)) return;
    const modified = fs.statSync(rawOutput).mtimeMs;
    if (modified !== lastModified) {
      lastModified = modified;
      writeBuildOutputs();
    }
  }, 150);

  const stop = (signal) => {
    clearInterval(timer);
    child.kill(signal);
    cleanup();
  };
  process.on("SIGINT", () => stop("SIGINT"));
  process.on("SIGTERM", () => stop("SIGTERM"));

  child.on("exit", (code) => {
    clearInterval(timer);
    cleanup();
    process.exit(code ?? 0);
  });
} else {
  child.on("exit", (code) => {
    if (code === 0) writeBuildOutputs();
    cleanup();
    process.exit(code ?? 1);
  });
}
