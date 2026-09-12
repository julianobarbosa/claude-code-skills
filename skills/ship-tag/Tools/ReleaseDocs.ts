// Consumer-facing text for a published release: the README.md shipped inside the
// Universal Package, and the feed's Description field. Both are immutable once a
// version is published, so they are generated from the tagged commit and its
// CHANGELOG section, never typed by hand.

export interface ReleaseInfo {
  pkg: string;
  version: string;
  tag: string;
  commit: string;
  date: string;
  orgUrl: string;
  feed: string;
  feedProject?: string;
  tarball: string;
  sha256: string;
  notes: string;
  compareUrl?: string;
  scripts: string[];
  requiresPython?: string;
  repoBase?: string;
}

/** Body of one TOML table ("project", "project.scripts"), up to the next table header. */
export function tomlTableBody(text: string, table: string): string {
  const esc = table.replace(/\./g, "\\.");
  const re = new RegExp(`^\\[${esc}\\][ \\t]*\\r?\\n([\\s\\S]*?)(?=^\\[|(?![\\s\\S]))`, "m");
  return text.match(re)?.[1] ?? "";
}

/** Console-script names from pyproject.toml's [project.scripts]. */
export function consoleScripts(pyproject: string): string[] {
  return [...tomlTableBody(pyproject, "project.scripts").matchAll(/^([A-Za-z0-9_.-]+)\s*=/gm)].map((m) => m[1]);
}

export function requiresPython(pyproject: string): string {
  return tomlTableBody(pyproject, "project").match(/^requires-python\s*=\s*"([^"]+)"/m)?.[1] ?? "";
}

/** The full download command, for the README. */
export function downloadCommand(r: ReleaseInfo, path: string): string {
  const scope = r.feedProject ? ` --project ${r.feedProject} --scope project` : "";
  return `az artifacts universal download --organization ${r.orgUrl} --feed ${r.feed}${scope} --name ${r.pkg} --version ${r.version} --path ${path}`;
}

/** "Added: a; b. Fixed: c." from a Keep a Changelog section body. */
export function flattenNotes(notes: string): string {
  const parts: string[] = [];
  let cat = "";
  let items: string[] = [];
  const flush = () => {
    if (cat && items.length) parts.push(`${cat}: ${items.join("; ")}.`);
    items = [];
  };
  for (const line of notes.split("\n")) {
    const h = line.match(/^###\s+(.+?)\s*$/);
    if (h) {
      flush();
      cat = h[1];
      continue;
    }
    const e = line.match(/^\s*[-*+]\s+(.*\S)\s*$/);
    if (e) items.push(e[1].replace(/\.$/, ""));
  }
  flush();
  return parts.join(" ");
}

export function renderReadme(r: ReleaseInfo): string {
  const dir = `./${r.pkg}-${r.version}`;
  const use = r.scripts.length
    ? r.scripts.map((s) => `${s} --help`)
    : [`python -c "import importlib.metadata as m; print(m.version('${r.pkg}'))"`];
  return [
    `# ${r.pkg} ${r.version}`,
    "",
    `Released ${r.date} from tag \`${r.tag}\` (commit \`${r.commit.slice(0, 7)}\`)${r.repoBase ? ` of ${r.repoBase}` : ""}.`,
    "",
    "## What's in this package",
    "",
    "| File | What it is |",
    "|---|---|",
    `| \`${r.tarball}\` | Python source distribution. sha256 \`${r.sha256}\` |`,
    "| `README.md` | This file |",
    "",
    "## Install",
    "",
    `You need the Azure CLI with the \`azure-devops\` extension (after \`az login\`), and ${r.requiresPython ? `Python ${r.requiresPython}` : "Python"} with \`uv\` or \`pip\`.`,
    "",
    "```bash",
    downloadCommand(r, dir),
    `cd ${dir}`,
    `echo "${r.sha256}  ${r.tarball}" | sha256sum -c -`,
    `uv pip install ./${r.tarball}        # or: pip install ./${r.tarball}`,
    "```",
    "",
    "For the full source tree instead (scripts, docs, CHANGELOG.md):",
    "",
    "```bash",
    `tar -xzf ${r.tarball}`,
    "```",
    "",
    "## Use it",
    "",
    "```bash",
    ...use,
    "```",
    "",
    `In automation, pin the exact version (\`--version ${r.version}\`) instead of a wildcard, so every run installs the bytes that were verified at release.`,
    "",
    `## What changed in ${r.version}`,
    "",
    r.notes.trim() || "_No CHANGELOG.md entries were found for this version._",
    ...(r.compareUrl ? ["", `Full diff: ${r.compareUrl}`] : []),
    "",
  ].join("\n");
}

/** Shorter form for the feed Description, which is capped: the organization is
 *  implied by the feed page a reader is already on. */
function downloadCommandShort(r: ReleaseInfo): string {
  const scope = r.feedProject ? ` --project ${r.feedProject} --scope project` : "";
  return `az artifacts universal download --feed ${r.feed}${scope} --name ${r.pkg} --version ${r.version} --path .`;
}

/** Plain text for the feed's Description field: what changed and how to get it.
 *
 *  Azure Artifacts rejects a description over 256 characters (artifacttool exits
 *  20: "greater than the allowed maximum of 256 characters"), and a version can
 *  never be republished, so the budget is enforced here: the install line and the
 *  pointer to README.md always survive, and the change summary is trimmed to fit.
 *  Full command, checksum and notes live in the packaged README.md. */
export function renderDescription(r: ReleaseInfo, max = 256): string {
  const head = `${r.pkg} ${r.version} (${r.date}).`;
  const tail = ` Install: ${downloadCommandShort(r)} && uv pip install ./${r.tarball}. Details: README.md in this package.`;
  if (head.length + tail.length > max) return `${r.pkg} ${r.version}. Install: see README.md in this package.`.slice(0, max);
  const changes = flattenNotes(r.notes);
  let body = changes ? ` ${changes}` : "";
  const room = max - head.length - tail.length;
  if (body.length > room) body = room > 12 ? `${body.slice(0, room - 1).trimEnd()}…` : "";
  return head + body + tail;
}
