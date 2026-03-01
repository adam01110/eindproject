import { defineConfig } from "vite";
import { tablerWoff2Only } from "./build/tablerWoff2Only";

export default defineConfig({
	root: "src",
	plugins: [tablerWoff2Only()],
	build: {
		outDir: "../dist",
		emptyOutDir: true,
	},
});
