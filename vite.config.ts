import { resolve } from "node:path";
import { createPyScriptsPlugin } from "./src/ts/pyScriptsPlugin";
import { createInlinePartialsPlugin } from "./src/ts/inlinePartialsPlugin";
import { createPyscriptConfigPlugin } from "./src/ts/pyscriptConfigPlugin";
import { defineConfig } from "vite";

const srcRootPath = resolve(__dirname, "src");

const inlinePartialsPlugin = createInlinePartialsPlugin(srcRootPath);
const pyscriptConfigPlugin = createPyscriptConfigPlugin(resolve(__dirname, "pyscript.json"));
const pyScriptsPlugin = createPyScriptsPlugin(resolve(srcRootPath, "py"));

export default defineConfig({
	plugins: [inlinePartialsPlugin, pyscriptConfigPlugin, pyScriptsPlugin],
	root: "src",

	build: {
		outDir: "../dist",
		emptyOutDir: true,
	},
});
