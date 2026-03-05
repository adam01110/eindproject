import { spawn } from "node:child_process";
import { readdir, readFile } from "node:fs/promises";
import { join, relative, resolve } from "node:path";
import { normalizePath, type Plugin } from "vite";

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

const minifyPythonFile = async (pythonFilePath: string): Promise<string | null> =>
	new Promise((resolveMinified, rejectMinified) => {
		const child = spawn("pyminify", [pythonFilePath]);
		let stdout = "";
		let stderr = "";
		let settled = false;

		child.stdout.on("data", (chunk: Buffer) => {
			stdout += chunk.toString();
		});

		child.stderr.on("data", (chunk: Buffer) => {
			stderr += chunk.toString();
		});

		child.once("error", (error: NodeJS.ErrnoException) => {
			if (settled) {
				return;
			}

			if (error.code === "ENOENT") {
				settled = true;
				resolveMinified(null);
				return;
			}

			settled = true;
			rejectMinified(error);
		});

		child.once("close", (code) => {
			if (settled) {
				return;
			}

			settled = true;

			if (code === 0) {
				resolveMinified(stdout);
				return;
			}

			rejectMinified(
				new Error(
					`pyminify failed for ${pythonFilePath}: ${stderr.trim() || `exit code ${code}`}`,
				),
			);
		});
	});

export const createPyScriptsPlugin = (pythonRootPath: string): Plugin => ({
	name: "pyscript-sources-plugin",

	handleHotUpdate({ file, server }) {
		const normalizedPythonRootPath = normalizePath(resolve(pythonRootPath));
		const normalizedFilePath = normalizePath(file);

		const isPythonSourceFile = normalizedFilePath.endsWith(".py");
		const isInsidePythonRoot =
			normalizedFilePath === normalizedPythonRootPath ||
			normalizedFilePath.startsWith(`${normalizedPythonRootPath}/`);

		if (!isPythonSourceFile || !isInsidePythonRoot) {
			return;
		}

		server.ws.send({ type: "full-reload" });
		return [];
	},

	async generateBundle() {
		const pythonFiles = await collectPythonFiles(pythonRootPath);
		let hasWarnedMissingPyminify = false;

		for (const pythonFilePath of pythonFiles) {
			const minifiedSource = await minifyPythonFile(pythonFilePath);
			let source = minifiedSource;

			if (source === null) {
				source = await readFile(pythonFilePath, "utf8");

				if (!hasWarnedMissingPyminify) {
					hasWarnedMissingPyminify = true;
					this.warn(
						"pyminify is not available; emitting original Python sources without minification.",
					);
				}
			}

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
