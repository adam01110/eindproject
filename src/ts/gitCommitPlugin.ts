import { execSync } from "node:child_process";
import type { Plugin } from "vite";

const read_short_git_hash = (): string => {
	try {
		const value = execSync("git rev-parse --short HEAD", {
			encoding: "utf8",
		}).trim();

		return value || "unknown";
	} catch {
		return "unknown";
	}
};

export const createGitCommitPlugin = (
	placeholder = "__GIT_COMMIT_HASH__",
): Plugin => {
	const shortGitHash = read_short_git_hash();

	return {
		name: "git-commit-html-plugin",

		transformIndexHtml(html) {
			return html.split(placeholder).join(shortGitHash);
		},
	};
};
