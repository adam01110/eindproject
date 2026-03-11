# AGENTS.md
This file is for coding agents working in this repository.
Follow these repo-specific rules in addition to system-level instructions.

## 1) Project Snapshot
- Stack: Vite + Tailwind CSS v4 + Basecoat + PyScript.
- Package manager: Bun is preferred (`bun.lock` is committed).
- Vite root: `src/`; entry document: `src/index.html`; app bootstrap: `src/index.ts`.
- Page content is split into partials under `src/pages/*.html` and inlined at build/dev time.
- PyScript client logic lives under `src/py/*.py`.
- Build-time Vite plugins live under `src/ts/*.ts`.
- Tailwind aggregation file: `src/index.css`.
- Theme tokens: `src/theme.css`.
- PyScript config source: `pyscript.json`.
- Vite config: `vite.config.ts`.
- PostCSS config: `postcss.config.ts`.
- Nix flake entrypoint: `flake.nix`; Nix modules live under `src/nix/*.nix`.
- Icons: Iconify Tailwind plugin with Tabler icon set (`@iconify/tailwind4` + `@iconify-json/tabler`).

## 2) MCP / Docs Tooling Rules
- Always use Context7 for library/framework work in this repo,
  especially for:
  - PyScript
  - Basecoat
  - Tailwind CSS
  - Vite/PostCSS config patterns when relevant
- Treat Context7 as the primary docs source for implementation decisions;
  use generic web search only as a secondary fallback.
- Always use the Nix MCP for Nix-related work (flake files, Nix packages,
  options, channels, Home Manager, nix-darwin concerns).

## 3) Build / Lint / Test Commands
For setup/development/build/preview commands, read `package.json`
scripts directly and use them as the source of truth.

### Lint / Format
Lint/format command for this repo:
```bash
# Run repository linting/formatting via treefmt
nix fmt
```

Notes:
- `nix fmt` is configured through `src/nix/treefmt.nix`.
- Current treefmt programs include `alejandra`, `nixf-diagnose`,
  `deadnix`, `statix`, `ruff-format`, and `biome`.
- There is no dedicated single-file lint command documented for the
  current setup; use `nix fmt` for authoritative lint/format checks.

Additional lightweight validation commands used in this repo:
```bash
# Validate Python syntax for all PyScript files
find src/py -name "*.py" -print0 | xargs -0 -n1 python -m py_compile

# Validate a single Python file (single-test equivalent)
python -m py_compile src/py/navigation.py

# Validate package JSON syntax
python -m json.tool package.json >/dev/null
```

### Test Status
Current status:
- No JS/TS unit test framework is configured.
- No `test` script exists in `package.json`.
Single-test guidance in current state:
- Use `python -m py_compile src/py/navigation.py` as the smallest deterministic check.
If a test framework is later added:
- Add a `test` script and document single-test invocation here.
- Prefer deterministic single-file or single-test-name execution.

## 4) Architecture and Responsibility Boundaries
- Keep app shell and routed section placeholders in `src/index.html`.
- Keep page markup in `src/pages/*.html`.
- Keep browser behavior logic in PyScript modules under `src/py/*.py`.
- Use TypeScript under `src/ts/*.ts` for Vite/build tooling only unless the user explicitly requests browser-side JS/TS logic.
- Keep Tailwind/Basecoat/theme wiring in CSS and config files.
- Keep Vite config minimal and TypeScript-based.
- Preserve the current build pipeline:
  - `inlinePartialsPlugin` inlines `data-page-partial` sections.
  - `pyscriptConfigPlugin` serves/emits `pyscript.json`.
  - `pyScriptsPlugin` emits `src/py` files into the build output and reloads on Python edits.
  - `gitCommitPlugin` replaces `__GIT_COMMIT_HASH__` in HTML.

## 5) Code Style Guidelines
### Imports
- TypeScript config files: use ESM imports.
- Python: group imports as stdlib -> third-party -> local.
- Remove unused imports immediately.

### Formatting
- Preserve existing file-local formatting style.
- Do not mass-reformat unrelated files.
- Keep Markdown concise and task-oriented.
- Keep HTML readable with stable indentation.

### Types and Typing Discipline
- In TypeScript config files, keep types explicit when complexity grows.
- Avoid `any` in new TS files unless unavoidable and documented.
- In Python, use clear function names and predictable return behavior.

### Naming Conventions
- Python functions/variables: `snake_case`.
- Python constants: `UPPER_SNAKE_CASE`.
- HTML data attributes: `kebab-case` (e.g. `data-page-id`).
- IDs for routed sections: stable, descriptive, and hash-based (`home`, `lineaire-vergelijking-oplosser`).
- CSS custom properties: existing token naming (`--color-*`, `--sidebar-*`).

### HTML / Tailwind / Basecoat
- Prefer Basecoat component classes for component structure.
- Use Tailwind utilities for spacing/layout tweaks.
- Use Iconify Tabler classes for icons: `icon-[tabler--icon-name]`.
- Do not use legacy Tabler webfont classes (`ti ti-*`) or `@tabler/icons-webfont`.
- Do not inline SVG icons unless explicitly requested.
- Keep theme tokens in `src/theme.css`.
- Do not inline `<style>` blocks for new feature work.
- Do not hardcode one-off colors when token-based alternatives exist.
- Preserve accessibility attributes:
  - `aria-current` for active nav links.
  - semantic headings and sectioning.

### PyScript / Python Logic
- DOM selection must be defensive:
  - check `None` before property access.
  - return early on missing elements.
- Keep hash-routing normalization explicit and deterministic.
- Keep event listener registration centralized near startup.
- Avoid hidden side effects at import time beyond startup wiring.
- Prefer shared helper access through the existing PyScript globals established by `src/py/lib.py`.
- When changing settings/state flows, preserve the async local-storage pattern already used by `src/py/theme.py`, `src/py/sidebar.py`, and `src/py/settings.py`.

### Vite / TypeScript Tooling
- Use ESM imports in TS files.
- Keep plugin factories pure and focused.
- Preserve the current `src`-rooted build output assumptions (`build.outDir = ../dist`, emitted assets under `py/`, emitted `pyscript.json`).
- Do not add runtime framework code when the existing HTML + PyScript approach is sufficient.

### Error Handling
- Fail soft for UI state mismatches (fallback to defaults).
- Prefer safe defaults (`home`) over raising exceptions.
- Normalize external inputs (URL hash, dataset values) before use.
- For invalid state, no-op gracefully rather than crashing render flow.

## 6) Editing and Change Scope Rules
- Make focused changes; avoid unrelated refactors.
- When adding components, keep them clearly removable.
- Keep paths rooted under `src/` for app code.
- Do not reintroduce legacy root `index.html` or root `py/` app logic.

## 7) Validation Checklist Before Commit
Run, at minimum:
```bash
nix fmt
python -m json.tool package.json >/dev/null
find src/py -name "*.py" -print0 | xargs -0 -n1 python -m py_compile
bun run build
```
Then verify:
- `bun run dev` starts without config errors.
- Hash navigation updates sidebar state and visible section.
- Theme and settings changes still persist and apply correctly.
- Page partials render in dev/build output and PyScript assets are emitted as expected.
