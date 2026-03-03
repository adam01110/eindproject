import { readdir, readFile } from "node:fs/promises";
import { join, relative } from "node:path";
import type { Plugin } from "vite";

const collectPythonFiles = async (directoryPath: string): Promise<string[]> => {
	const entries = await readdir(directoryPath, { withFileTypes: true });
	const files: string[] = [];

	for (const entry of entries) {
		const entryPath = join(directoryPath, entry.name);

		if (entry.isDirectory()) {
			files.push(...(await collectPythonFiles(entryPath)));
			continue;
		}

		if (entry.isFile() && entry.name.endsWith(".py")) {
			files.push(entryPath);
		}
	}

	return files;
};

export const createPyScriptsPlugin = (pythonRootPath: string): Plugin => ({
	name: "pyscript-sources-plugin",

	async generateBundle() {
		const pythonFiles = await collectPythonFiles(pythonRootPath);

		for (const pythonFilePath of pythonFiles) {
			const source = await readFile(pythonFilePath, "utf8");
			const fileName = relative(pythonRootPath, pythonFilePath)
				.split("\\")
				.join("/");

			this.emitFile({
				type: "asset",
				fileName: `py/${fileName}`,
				source,
			});
		}
	},
});
