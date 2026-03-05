import { resolve } from "node:path";
import { defineConfig } from "vite";
import { createGitCommitPlugin } from "./src/ts/gitCommitPlugin";
import { createInlinePartialsPlugin } from "./src/ts/inlinePartialsPlugin";
import { createPyScriptsPlugin } from "./src/ts/pyScriptsPlugin";
import { createPyscriptConfigPlugin } from "./src/ts/pyscriptConfigPlugin";

const srcRootPath = resolve(__dirname, "src");

const inlinePartialsPlugin = createInlinePartialsPlugin(srcRootPath);
const pyscriptConfigPlugin = createPyscriptConfigPlugin(
	resolve(__dirname, "pyscript.json"),
);
const pyScriptsPlugin = createPyScriptsPlugin(resolve(srcRootPath, "py"));
const gitCommitPlugin = createGitCommitPlugin();

export default defineConfig({
	plugins: [
		inlinePartialsPlugin,
		pyscriptConfigPlugin,
		pyScriptsPlugin,
		gitCommitPlugin,
	],
	root: "src",

	build: {
		outDir: "../dist",
		emptyOutDir: true,
	},
});
