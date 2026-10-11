// Eksport bingkai demi bingkai daripada index.html (mod ?export) ke MP4 melalui ffmpeg.
// Guna: node export.mjs [fps=30] [output=bela-bangsa.mp4] [audio.wav]
// Keperluan: Node 18+, playwright (dengan Chromium), ffmpeg dalam PATH.
import { chromium } from "playwright";
import { spawn } from "node:child_process";
import { fileURLToPath, pathToFileURL } from "node:url";
import path from "node:path";

const fps = Number(process.argv[2] || 30);
const out = process.argv[3] || "bela-bangsa.mp4";
const audio = process.argv[4];
const html = path.join(path.dirname(fileURLToPath(import.meta.url)), "index.html");

const browser = await chromium.launch(process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {});
const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
await page.goto(pathToFileURL(html).href + "?export=1");
const dur = await page.evaluate(() => window.DURATION);
const frames = Math.round(dur * fps);

const args = ["-y", "-f", "image2pipe", "-framerate", String(fps), "-i", "-"];
if (audio) args.push("-i", audio);
args.push("-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "medium");
if (audio) args.push("-c:a", "aac", "-b:a", "192k", "-shortest");
args.push("-movflags", "+faststart", out);
const ff = spawn("ffmpeg", args, { stdio: ["pipe", "inherit", "inherit"] });

for (let i = 0; i < frames; i++) {
  await page.evaluate(t => window.renderFrame(t), i / fps);
  const buf = await page.screenshot({ type: "png" });
  if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once("drain", r));
  if (i % fps === 0) process.stdout.write(`\r${(i / fps).toFixed(0)}/${dur}s`);
}
ff.stdin.end();
await new Promise(r => ff.on("close", r));
await browser.close();
console.log(`\nSiap: ${out} (${frames} bingkai @ ${fps} fps)`);
