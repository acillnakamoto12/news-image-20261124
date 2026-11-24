// News-image entry — Tuesday 24 November 2026.
//
// The entry image is entry.png next to this file. It was drawn by
// generate.py (Python + Pillow) from news.json, the day's verified
// stories. This program adds nothing creative: it only carries that
// finished image into the output directory, byte for byte, every run.
//
// Before copying, the PNG is checked — signature bytes, IHDR chunk,
// width, height and colour type must all be right. Anything else is
// refused, so a broken or wrong-sized image can never slip through.
//
// Outside the grader's container, MAKEFUN_OUTPUT_DIR stands in for
// /output:
//   mkdir -p out && MAKEFUN_OUTPUT_DIR=out node main.ts

import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

const PNG_SIGNATURE = Buffer.from([
  0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a,
]);
const EXPECTED_WIDTH = 1024;
const EXPECTED_HEIGHT = 1024;
// IHDR colour types we accept: 2 = truecolour (RGB), 6 = RGB + alpha.
const ACCEPTED_COLOURS = [2, 6];

interface PngSize {
  width: number;
  height: number;
  colour: number;
}

function readEntry(): Buffer {
  const location = new URL('./entry.png', import.meta.url);
  if (!existsSync(location)) {
    throw new Error('entry.png is missing beside main.ts — cannot produce the entry image');
  }
  return readFileSync(location);
}

function checkPng(bytes: Buffer): PngSize {
  if (bytes.length < 33) {
    throw new Error('entry.png is too small to be a PNG file');
  }
  if (Buffer.compare(bytes.subarray(0, 8), PNG_SIGNATURE) !== 0) {
    throw new Error('entry.png does not start with the PNG signature');
  }
  if (bytes.readUInt32BE(8) !== 13 || bytes.toString('latin1', 12, 16) !== 'IHDR') {
    throw new Error('entry.png has no IHDR chunk where one belongs');
  }
  return {
    width: bytes.readUInt32BE(16),
    height: bytes.readUInt32BE(20),
    colour: bytes[25],
  };
}

function fail(message: string): never {
  console.error(`error: ${message}`);
  process.exit(1);
}

function main(): void {
  let bytes: Buffer;
  let size: PngSize;
  try {
    bytes = readEntry();
    size = checkPng(bytes);
  } catch (error) {
    fail(error instanceof Error ? error.message : String(error));
  }

  if (size.width !== EXPECTED_WIDTH || size.height !== EXPECTED_HEIGHT) {
    fail(
      `entry.png is not a valid ${EXPECTED_WIDTH}x${EXPECTED_HEIGHT} PNG ` +
        `(got ${size.width}x${size.height}) — refusing to copy a broken entry image`,
    );
  }
  if (!ACCEPTED_COLOURS.includes(size.colour)) {
    fail(
      `entry.png has an unexpected PNG colour type (${size.colour}) — ` +
        'refusing to copy a broken entry image',
    );
  }

  // An empty MAKEFUN_OUTPUT_DIR is the same as an unset one.
  const outDir = process.env.MAKEFUN_OUTPUT_DIR || '/output';
  mkdirSync(outDir, { recursive: true });
  const target = join(outDir, 'entry.png');
  writeFileSync(target, bytes);
  // Read the copy back: the entry must arrive byte for byte, or fail.
  const written = readFileSync(target);
  if (!written.equals(bytes)) {
    fail(`failed to copy entry.png to ${target} intact`);
  }
  console.log(`wrote ${target} (${bytes.length} bytes)`);
}

main();
