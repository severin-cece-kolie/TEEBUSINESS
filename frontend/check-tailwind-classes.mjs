import fs from "node:fs";
import path from "node:path";

const root = path.resolve(import.meta.dirname, "..");
const cssPath = path.join(root, "static", "css", "tailwind.standalone.css");
const safelistPath = path.join(root, "frontend", "safelist.txt");
const templateRoots = [
  path.join(root, "templates"),
  path.join(root, "accounts", "templates"),
  path.join(root, "cart", "templates"),
  path.join(root, "communication", "templates"),
  path.join(root, "pages", "templates"),
  path.join(root, "shop", "templates"),
];

function walk(directory) {
  if (!fs.existsSync(directory)) return [];

  return fs.readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const target = path.join(directory, entry.name);
    if (entry.isDirectory()) {
      if (target === path.join(root, "templates", "admin")) return [];
      return walk(target);
    }
    return entry.isFile() && entry.name.endsWith(".html") ? [target] : [];
  });
}

function escapeClassName(value) {
  return value.replace(/[^a-zA-Z0-9_-]/g, (character) => `\\${character}`);
}

function quotedUtilities(expression) {
  const utilities = [];
  for (const match of expression.matchAll(/(['"])(.*?)\1/g)) {
    utilities.push(
      ...match[2]
        .split(/\s+/)
        .filter(Boolean)
        .filter(
          (value) =>
            value === "hidden" ||
            value.startsWith("-") ||
            /[-:[\]/]/.test(value),
        ),
    );
  }
  return utilities;
}

const candidates = new Set();
for (const file of templateRoots.flatMap(walk)) {
  const source = fs.readFileSync(file, "utf8");

  for (const match of source.matchAll(
    /(?:x-bind:class|:class)\s*=\s*"([^"]*)"/g,
  )) {
    quotedUtilities(match[1]).forEach((utility) => candidates.add(utility));
  }

  for (const match of source.matchAll(
    /classList\.(?:add|remove|toggle)\(([^)]*)\)/g,
  )) {
    quotedUtilities(match[1]).forEach((utility) => candidates.add(utility));
  }
}

for (const line of fs.readFileSync(safelistPath, "utf8").split(/\r?\n/)) {
  const utility = line.trim();
  if (utility && !utility.startsWith("#")) candidates.add(utility);
}

const css = fs.readFileSync(cssPath, "utf8");
const missing = [...candidates]
  .filter((utility) => !css.includes(`.${escapeClassName(utility)}`))
  .sort();

if (missing.length) {
  console.error("Missing dynamic Tailwind classes:");
  for (const utility of missing) console.error(`- ${utility}`);
  process.exit(1);
}

console.log(
  `Verified ${candidates.size} dynamic/safelisted classes in ${path.relative(root, cssPath)}.`,
);
