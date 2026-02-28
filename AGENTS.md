# AGENTS.md
This file is for coding agents working in this repository.
Follow these repo-specific rules in addition to system-level instructions.

## 1) Project Snapshot
- Stack: Vite + Tailwind CSS v4 + Basecoat + PyScript.
- Entry point: `src/index.html`.
- Python client logic: `src/py/navigation.py`.
- Tailwind aggregation file: `src/styles.css`.
- Theme tokens: `src/theme.css`.
- Vite config: `vite.config.ts`.
- PostCSS config: `postcss.config.ts`.
- Package manager: Bun is preferred (`bun.lock` is committed).

## 2) Rule Files Audit (Cursor/Copilot)
Checked paths:
- `.cursor/rules/` -> not present
- `.cursorrules` -> not present
- `.github/copilot-instructions.md` -> not present
Implication:
- There are currently no repo-local Cursor/Copilot instruction files.
- Treat this `AGENTS.md` as the canonical local agent guide.

## 3) Build / Lint / Test Commands
### Setup
```bash
bun install
```
### Development
```bash
bun run dev
```
### Production Build
```bash
bun run build
```
### Preview Built Output
```bash
bun run preview
```

### Lint / Format Status
Current status:
- No dedicated `lint` script exists in `package.json`.
- Canonical lint/format command is Nix-based (`nix fmt`).

Lint/format command for this repo:
```bash
# Run repository linting/formatting via treefmt
nix fmt
```

Notes:
- `nix fmt` is configured through `parts/treefmt.nix`.
- Current treefmt programs include `alejandra`, `nixf-diagnose`,
  `deadnix`, `statix`, and `biome`.
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
- Keep app page structure in HTML (`src/index.html`).
- Keep behavior logic in Python (`src/py/*.py`) via PyScript.
- Do not add custom JavaScript business logic unless explicitly requested.
- Keep Tailwind/Basecoat/theme wiring in CSS config files.
- Keep Vite config minimal and TypeScript-based.

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
- IDs for routed sections: stable, descriptive, hash-friendly (`page-1`).
- CSS custom properties: existing token naming (`--color-*`, `--sidebar-*`).

### HTML / Tailwind / Basecoat
- Prefer Basecoat component classes for component structure.
- Use Tailwind utilities for spacing/layout tweaks.
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

### Error Handling
- Fail soft for UI state mismatches (fallback to defaults).
- Prefer safe defaults (`page-1`) over raising exceptions.
- Normalize external inputs (URL hash, dataset values) before use.
- For invalid state, no-op gracefully rather than crashing render flow.

## 6) Editing and Change Scope Rules
- Make focused changes; avoid unrelated refactors.
- Preserve the POC marker comments in `src/index.html` unless asked to remove.
- When adding components, keep them clearly removable.
- Keep paths rooted under `src/` for app code.
- Do not reintroduce legacy root `index.html` or root `py/` app logic.

## 7) Validation Checklist Before Commit
Run, at minimum:
```bash
nix fmt
python -m json.tool package.json >/dev/null
python -m py_compile src/py/navigation.py
bun run build
```
Then verify:
- `bun run dev` starts without config errors.
- Hash navigation updates sidebar state and visible section.
- Theme tokens still apply (light/dark variables intact).
