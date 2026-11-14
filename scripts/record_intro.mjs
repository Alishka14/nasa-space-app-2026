// Frame-exact screen capture of the in-app intro (not generated footage).
// Needs: the app running (EARTH_SENSES_OFFLINE=1 uvicorn ... --port 8000), Chrome or Chromium,
// puppeteer-core (npm i puppeteer-core) and ffmpeg on PATH.
//   node scripts/record_intro.mjs <teaser|explainer|hero> <en|ru|kk> [fps=24] [width=1280] [height=720]
// Writes docs/video/renders/<variant>_<lang>.mp4
import { spawn } from 'node:child_process'
import { mkdirSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import puppeteer from 'puppeteer-core'

const [variant = 'teaser', lang = 'en', fpsArg = '24', wArg = '1280', hArg = '720'] = process.argv.slice(2)
const fps = Number(fpsArg), width = Number(wArg), height = Number(hArg)
const root = resolve(dirname(fileURLToPath(import.meta.url)), '..')
const outDir = process.env.OUT_DIR ? resolve(process.env.OUT_DIR) : resolve(root, 'docs/video/renders')
mkdirSync(outDir, { recursive: true })
const out = resolve(outDir, `${variant}_${lang}.mp4`)
const chrome = process.env.CHROME_PATH || '/usr/bin/google-chrome'
const base = process.env.APP_URL || 'http://127.0.0.1:8000/'

const browser = await puppeteer.launch({ executablePath: chrome, headless: 'new',
  args: ['--no-sandbox', '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--hide-scrollbars'] })
const page = await browser.newPage()
await page.setViewport({ width, height, deviceScaleFactor: 1 })
await page.goto(`${base}?capture&variant=${variant}&lang=${lang}`, { waitUntil: 'load', timeout: 60000 })
await page.waitForFunction(() => window.__esIntro?.ready, { timeout: 30000 })
await new Promise(r => setTimeout(r, 3000))      // textures arrive and fade in (wall-clock)
const duration = await page.evaluate(() => window.__esIntro.duration)
const frames = Math.round(duration * fps)

const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-i', '-',
  '-c:v', 'libx264', '-preset', 'veryfast', '-crf', process.env.CRF || '22', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out],
  { stdio: ['pipe', 'inherit', 'inherit'] })
const t0 = Date.now()
for (let i = 0; i < frames; i++) {
  await page.evaluate(t => window.__esIntro.seek(t), i / fps)
  await page.evaluate(() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r))))
  const buf = await page.screenshot({ type: 'jpeg', quality: 92 })
  if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r))
  if (i % (fps * 5) === 0) console.log(`${variant}/${lang}: ${(i / fps).toFixed(0)} / ${duration.toFixed(1)} s`)
}
ff.stdin.end()
await new Promise(r => ff.on('close', r))
await browser.close()
console.log(`wrote ${out} — ${frames} frames, ${((Date.now() - t0) / 1000).toFixed(0)} s`)
