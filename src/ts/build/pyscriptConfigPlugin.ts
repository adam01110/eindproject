import { readFile } from "node:fs/promises";
import type { Plugin } from "vite";

export const createPyscriptConfigPlugin = (
	pyscriptConfigPath: string,
): Plugin => {
	const readPyscriptConfig = () => readFile(pyscriptConfigPath, "utf8");

	return {
		name: "pyscript-config-plugin",

		configureServer(server) {
			server.middlewares.use(
				"/pyscript.json",
				async (_request, response, next) => {
					try {
						const source = await readPyscriptConfig();
						response.setHeader(
							"Content-Type",
							"application/json; charset=utf-8",
						);
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
};
