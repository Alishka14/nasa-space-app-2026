/**
 * EARTH SENSES — deterministic orbital GIF renderer.
 * Created with AI-assisted JavaScript programming (OpenAI ChatGPT).
 * No image/video generation model, third-party images, textures, footage or
 * runtime packages are used for this illustration. The Earth is stylized.
 *
 * Usage: node scripts/build_earth_orbit_loop.mjs --check
 *        node scripts/build_earth_orbit_loop.mjs
 *        node scripts/build_earth_orbit_loop.mjs --output /tmp/earth.gif
 *
 * --check must regenerate the precise tracked GIF bytes without writing files.
 */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';

const W = 480, H = 216, N = 14;
let seed = 20261115;
const rand = () => { seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0; return seed / 4294967296; };
const clamp = v => Math.min(255, Math.max(0, Math.round(v)));
const palette = [];
for (let i = 0; i < 256; i++) {
  let t, r, g, b;
  if (i < 40) { t = i; r = 2 + t * .18; g = 5 + t * .35; b = 17 + t * .65; }
  else if (i < 80) { t = i - 40; r = 4 + t * .6; g = 25 + t * 2.6; b = 50 + t * 4.3; }
  else if (i < 120) { t = i - 80; r = 17 + t * 2.5; g = 40 + t * 3.1; b = 44 + t * 2.3; }
  else if (i < 160) { t = i - 120; r = 21 + t * 3.2; g = 89 + t * 3.9; b = 144 + t * 2.5; }
  else if (i < 184) { t = i - 160; r = 128 + t * 5.2; g = 173 + t * 3.3; b = 190 + t * 2.75; }
  else if (i < 216) { t = i - 184; r = 25 + t * 1.9; g = 24 + t * 1.55; b = 52 + t * 4.6; }
  else { t = i - 216; r = 81 + t * 4; g = 48 + t * 2.9; b = 29 + t * .95; }
  palette.push(clamp(r), clamp(g), clamp(b));
}
const stars = Array.from({length: 80}, () => ({
  x: Math.floor(rand() * W), y: Math.floor(rand() * H),
  phase: rand() * 6, bright: rand() > .8,
}));

function frame(f) {
  const p = new Uint8Array(W * H), theta = f / N * 2 * Math.PI;
  const put = (x, y, c) => {
    x = Math.round(x); y = Math.round(y);
    if (x >= 0 && x < W && y >= 0 && y < H) p[y * W + x] = c;
  };
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
    const dx = (x - 370) / 260, dy = (y - 104) / 160;
    const glow = Math.max(0, 1 - dx * dx - dy * dy);
    p[y * W + x] = clamp(Math.min(39, 7 + 13 * glow + 3 * y / H + 3 * Math.sin(x / 70 + y / 20)));
  }
  for (const s of stars) {
    let a = .5 + .5 * Math.sin(theta + s.phase);
    put(s.x, s.y, s.bright ? Math.floor(166 + 16 * a) : Math.floor(126 + 20 * a));
  }
  for (let k = 0; k < 3; k++) for (let x = 25; x < 230; x++) {
    let t = (x - 25) / 205;
    let y = 60 + k * 42 + Math.sin(t * 18 + theta * .45 + k * 1.4) * 11 + Math.sin(t * 26 + theta * .21) * 3;
    put(x, y, k === 0 ? 130 : k === 1 ? 98 : 150);
  }
  for (let x = 24; x < 232; x++) {
    let y = 190 + Math.sin((x + f * 5) / 19) * 2;
    put(x, y, 150); put(x, y + 1, 103);
  }
  const cx = 365, cy = 108, R = 89;
  for (let j = 0; j < 540; j++) {
    let t = j / 540 * Math.PI * 2, xx = 124 * Math.cos(t), yy = 48 * Math.sin(t), a = -.33;
    put(cx + xx * Math.cos(a) - yy * Math.sin(a), cy + xx * Math.sin(a) + yy * Math.cos(a), j % 4 === 0 ? 145 : 123);
  }
  for (let y = cy - R - 3; y <= cy + R + 3; y++) for (let x = cx - R - 3; x <= cx + R + 3; x++) {
    const nx = (x - cx) / R, ny = (y - cy) / R, r2 = nx * nx + ny * ny;
    if (r2 >= 1 && r2 < 1.12) { put(x, y, Math.floor(120 + (1.12 - r2) / .12 * 23)); continue; }
    if (r2 >= 1) continue;
    const z = Math.sqrt(1 - r2), lon = Math.atan2(nx, z) + theta, lat = Math.asin(-ny);
    const land = Math.sin(2.2 * lon + 1.1 * Math.sin(lat * 3.1)) * Math.cos(lat * .7)
      + .37 * Math.sin(7 * lon + 2 * lat) + .25 * Math.cos(11 * lon - 7 * lat) > .35
      && lat > -.9 && lat < 1.2;
    const light = Math.min(1, Math.max(0, .58 * (-nx) - .25 * ny + .75 * z));
    let index = land ? 80 + Math.floor(light * 38) : 40 + Math.floor(light * 39);
    if (Math.sin(12 * lon + 17 * lat + 2 * Math.sin(4 * lon - 2 * lat)) > .95 && light > .2)
      index = 160 + Math.floor(light * 20);
    if (land && light < .16 && Math.sin(35 * lon + 81 * lat) > .96) index = 224;
    put(x, y, index);
  }
  let t = theta * 1.4 + .4, xx = 124 * Math.cos(t), yy = 48 * Math.sin(t), a = -.33;
  let sx = cx + xx * Math.cos(a) - yy * Math.sin(a), sy = cy + xx * Math.sin(a) + yy * Math.cos(a);
  for (let dy = -3; dy <= 3; dy++) for (let dx = -3; dx <= 3; dx++)
    if (dx * dx + dy * dy <= 9) put(sx + dx, sy + dy, dx * dx + dy * dy < 3 ? 182 : 147);
  return p;
}

function encode(px) {
  const out = []; let bits = 0, buf = 0;
  const emit = code => {
    buf |= code << bits; bits += 9;
    while (bits >= 8) { out.push(buf & 255); buf >>>= 8; bits -= 8; }
  };
  emit(256);
  for (let i = 0; i < px.length; i++) {
    if (i > 0 && i % 180 === 0) emit(256);
    emit(px[i]);
  }
  emit(257);
  if (bits) out.push(buf & 255);
  const blocks = [];
  for (let i = 0; i < out.length; i += 255) {
    blocks.push(Math.min(255, out.length - i));
    for (let j = i; j < Math.min(i + 255, out.length); j++) blocks.push(out[j]);
  }
  blocks.push(0);
  return blocks;
}
function build() {
  const data = [71, 73, 70, 56, 57, 97];
  const u16 = n => { data.push(n & 255, (n >> 8) & 255); };
  u16(W); u16(H); data.push(0xF7, 0, 0, ...palette);
  data.push(33, 255, 11, ...[...'NETSCAPE2.0'].map(x => x.charCodeAt(0)), 3, 1, 0, 0, 0);
  for (let i = 0; i < N; i++) {
    data.push(33, 249, 4, 8, 12, 0, 0, 0, 44);
    u16(0); u16(0); u16(W); u16(H);
    data.push(0, 8);
    const b = encode(frame(i));
    for (let j = 0; j < b.length; j += 12000) data.push(...b.slice(j, j + 12000));
  }
  data.push(59);
  return Buffer.from(data);
}
const here = path.dirname(fileURLToPath(import.meta.url));
const defaultFile = path.resolve(here, '../docs/brand/earth-senses-orbit-loop.gif');
const args = process.argv.slice(2);
let out = defaultFile, check = args.includes('--check');
let outputFlag = args.indexOf('--output');
if (outputFlag >= 0) {
  if (!args[outputFlag + 1]) throw new Error('--output requires a path');
  out = path.resolve(args[outputFlag + 1]);
}
const bytes = build();
const sha256 = crypto.createHash('sha256').update(bytes).digest('hex');
const gitSha = crypto.createHash('sha1').update('blob ' + bytes.length + '\0').update(bytes).digest('hex');
if (check) {
  if (!fs.existsSync(out)) throw new Error('Missing tracked GIF: ' + out);
  const actual = fs.readFileSync(out);
  if (!actual.equals(bytes)) {
    const actualSha = crypto.createHash('sha1').update('blob ' + actual.length + '\0').update(actual).digest('hex');
    throw new Error('GIF mismatch; expected Git blob ' + gitSha + ', actual ' + actualSha);
  }
  console.log('PASS exact reproduction: ' + W + 'x' + H + ', ' + N + ' frames, '
    + bytes.length + ' bytes, SHA-256 ' + sha256 + ', Git blob ' + gitSha);
} else {
  fs.mkdirSync(path.dirname(out), {recursive: true});
  fs.writeFileSync(out, bytes);
  console.log('Wrote ' + out + ' (' + bytes.length + ' bytes, SHA-256 ' + sha256 + ', Git blob ' + gitSha + ')');
}
