import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import { defineConfig, type Plugin } from "vite";

const pyscriptConfigPath = resolve(__dirname, "pyscript.json");
const readPyscriptConfig = () => readFile(pyscriptConfigPath, "utf8");

const pyscriptConfigPlugin: Plugin = {
	name: "pyscript-config-plugin",

	configureServer(server) {
		server.middlewares.use(
			"/pyscript.json",
			async (_request, response, next) => {
				try {
					const source = await readPyscriptConfig();
					response.setHeader("Content-Type", "application/json; charset=utf-8");
					response.end(source);
				} catch (error) {
					next(error);
				}
			},
		);
	},

	async generateBundle() {
		const source = await readPyscriptConfig();
		this.emitFile({
			type: "asset",
			fileName: "pyscript.json",
			source,
		});
	},
};

export default defineConfig({
	plugins: [pyscriptConfigPlugin],
	root: "src",

	build: {
		outDir: "../dist",
		emptyOutDir: true,
	},
});
