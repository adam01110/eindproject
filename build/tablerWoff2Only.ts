import type { Plugin } from "vite";

export function tablerWoff2Only(): Plugin {
	return {
		name: "tabler-woff2-only",
		apply: "build",
		generateBundle(_, bundle) {
			for (const chunk of Object.values(bundle)) {
				if (chunk.type !== "asset" || !chunk.fileName.endsWith(".css")) {
					continue;
				}

				if (typeof chunk.source !== "string") {
					continue;
				}

				chunk.source = chunk.source.replace(
					/,\s*url\([^)]*tabler-icons-[^)]*\.woff[^)]*\)\s*format\(["']woff["']\)\s*,\s*url\([^)]*tabler-icons-[^)]*\.ttf[^)]*\)\s*format\(["']truetype["']\)/g,
					"",
				);
			}

			for (const [fileName, chunk] of Object.entries(bundle)) {
				if (chunk.type !== "asset") {
					continue;
				}

				if (/tabler-icons-.*\.(woff|ttf)$/.test(chunk.fileName)) {
					delete bundle[fileName];
				}
			}
		},
	};
}
