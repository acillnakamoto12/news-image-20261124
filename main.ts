// main.ts — validate entry.png and deliver a byte-identical copy to the
// make.fun output directory.
//
// Reads entry.png next to this file, checks the PNG signature and the
// IHDR chunk (it must declare a 1024x1024 image), then copies it
// unchanged to $MAKEFUN_OUTPUT_DIR/entry.png (default /output/entry.png).

import { copyFile, mkdir, readFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const PNG_SIGNATURE = Buffer.from([
  0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a,
]);
const EXPECTED_WIDTH = 1024;
const EXPECTED_HEIGHT = 1024;

const here = dirname(fileURLToPath(import.meta.url));
const sourcePath = join(here, "entry.png");
const outputDir = process.env.MAKEFUN_OUTPUT_DIR || "/output";
const destPath = join(outputDir, "entry.png");

const bytes = await readFile(sourcePath);
if (bytes.length < 33) {
  throw new Error(
    `entry.png is too small (${bytes.length} bytes) to be a PNG`,
  );
}
if (!bytes.subarray(0, 8).equals(PNG_SIGNATURE)) {
  throw new Error("entry.png does not start with the PNG signature");
}
if (bytes.toString("ascii", 12, 16) !== "IHDR") {
  throw new Error("entry.png has no IHDR chunk where one is expected");
}
const width = bytes.readUInt32BE(16);
const height = bytes.readUInt32BE(20);
if (width !== EXPECTED_WIDTH || height !== EXPECTED_HEIGHT) {
  throw new Error(
    `entry.png is ${width}x${height}, expected ` +
      `${EXPECTED_WIDTH}x${EXPECTED_HEIGHT}`,
  );
}

await mkdir(outputDir, { recursive: true });
await copyFile(sourcePath, destPath);

// Read the copy back and prove it is byte-identical to the source.
const copied = await readFile(destPath);
if (!copied.equals(bytes)) {
  throw new Error("copied entry.png differs from the source");
}
console.log(
  `entry.png: ${width}x${height}, ${bytes.length} bytes -> ${destPath}`,
);
console.log(`verified: copy is byte-identical (${copied.length} bytes)`);
