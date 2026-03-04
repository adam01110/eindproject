import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import type { Plugin } from "vite";

const partialSectionPattern =
	/(<section\b[^>]*\bdata-page-partial="([^"]+)"[^>]*>)([\s\S]*?)(<\/section>)/g;

export const createInlinePartialsPlugin = (srcRootPath: string): Plugin => ({
	name: "inline-page-partials-plugin",

	async transformIndexHtml(html) {
		const matches = [...html.matchAll(partialSectionPattern)];
		if (matches.length === 0) {
			return html;
		}

		let transformedHtml = html;

		for (const match of matches) {
			const [fullMatch, openingTag, partialPath, _innerContent, closingTag] = match;
			if (!partialPath) {
				continue;
			}

			const resolvedPath = resolve(srcRootPath, partialPath.trim());
			let partialHtml: string;

			try {
				partialHtml = await readFile(resolvedPath, "utf8");
			} catch {
				continue;
			}

			const nextSection = `${openingTag}\n${partialHtml.trim()}\n${closingTag}`;

			transformedHtml = transformedHtml.replace(fullMatch, nextSection);
		}

		return transformedHtml;
	},
});
