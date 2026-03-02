import { resolve } from "node:path";
import { createInlinePartialsPlugin } from "./src/ts/inlinePartialsPlugin";
import { createPyscriptConfigPlugin } from "./src/ts/pyscriptConfigPlugin";
import { defineConfig } from "vite";

const pyscriptConfigPath = resolve(__dirname, "pyscript.json");
const srcRootPath = resolve(__dirname, "src");
const inlinePartialsPlugin = createInlinePartialsPlugin(srcRootPath);
const pyscriptConfigPlugin = createPyscriptConfigPlugin(pyscriptConfigPath);

export default defineConfig({
	plugins: [inlinePartialsPlugin, pyscriptConfigPlugin],
	root: "src",

	build: {
		outDir: "../dist",
		emptyOutDir: true,
	},
});
