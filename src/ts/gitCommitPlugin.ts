import { execSync } from "node:child_process";
import type { Plugin } from "vite";

const UNKNOWN_HASH = "unknown";

const readShortGitHash = (): string => {
	try {
		return (
			execSync("git rev-parse --short HEAD", {
			encoding: "utf8",
			}).trim() || UNKNOWN_HASH
		);
	} catch {
		return UNKNOWN_HASH;
	}
};

export const createGitCommitPlugin = (
	placeholder = "__GIT_COMMIT_HASH__",
): Plugin => {
	const shortGitHash = readShortGitHash();

	return {
		name: "git-commit-html-plugin",
		transformIndexHtml(html) {
			return html.split(placeholder).join(shortGitHash);
		},
	};
};
