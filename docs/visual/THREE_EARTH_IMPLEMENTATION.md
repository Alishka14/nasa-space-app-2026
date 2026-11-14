# The 3D Earth — implementation

A real WebGL globe built with **three.js 0.187** directly (no react-three-fiber, no game
engine). It is the background of the splash, the language screen and the intro.

## Files

| File | Role |
|---|---|
| `frontend/src/onboarding/earth/EarthScene.ts` | The WebGL globe: scene graph, shaders, overlays, marker, stars, camera tweens, texture loading |
| `frontend/src/onboarding/earth/shaders.ts` | GLSL: day/night globe shader and atmosphere shader |
| `frontend/src/onboarding/earth/geo.ts` | Lat/lon ↔ sphere mapping, camera angles, Natural Earth coastlines, tween and seeded random helpers |
| `frontend/src/onboarding/earth/FlatGlobe.ts` | 2D canvas fallback when WebGL is unavailable (labelled as 2D) |
| `frontend/src/onboarding/earth/EarthCanvas.tsx` | React wrapper: picks WebGL or the fallback, hands the controller to the screens |
| `frontend/src/onboarding/earth/types.ts` | The `EarthController` interface both implementations satisfy |
| `frontend/src/onboarding/earth/textures/` | Three textures (see *Assets*) |

## Scene graph

```
Scene
├── stars (2 Points layers, 2,540 seeded points, fixed in space)
└── root            ← horizontal / vertical shift (layout: globe beside a panel, rising Earth on the splash)
    ├── atmosphere  ← back-faced sphere r = 1.075, additive Fresnel glow, lit by the fixed sun
    └── tilt        ← rotation.x = latitude of the point of interest
        └── spin    ← rotation.y = longitude (+ slow spin)
            ├── globe (SphereGeometry 128 × 96, ShaderMaterial)
            ├── coastlines (LineSegments, Natural Earth 1:110m, r = 1.0025)
            ├── graticule  (LineSegments, every 30°, r = 1.0015)
            └── marker group (core dot, ring, pulse ring, beam) at the grid cell
```

Bringing a point to the centre of the screen is two rotations: spin by
`−atan2(−cos φ, sin φ)` (φ = longitude + 180°) and tilt by the latitude
(`geo.ts: yawFor`). The spin always takes the shortest way round (`nearestAngle`).

## Shading

- **Globe** (`globeFragment`): day texture lit by `max(N·L, 0)`; night texture where
  `N·L` is negative, with the warm bright pixels kept as city lights; a soft terminator
  (`smoothstep(−0.10, 0.28, N·L)`); a narrow ocean sun glint from the water mask; a blue
  Fresnel rim; an optional analytical tint. Textures are sampled in linear space and
  converted back with `<colorspace_fragment>`.
- **Atmosphere**: back faces of a slightly larger sphere, intensity
  `pow(0.78 − N·V, 3.2)`, brighter on the day side, additive blending.
- **Sun** is fixed in world space at (−0.82, 0.30, 0.48): light from the left, night on
  the right, so most framings show a terminator.

## Camera and timing

All animated values (`lat`, `yaw`, `dist`, `x`, `y`, overlay opacities, tint) are
`Tween`s evaluated against one clock. `setView({lat, lon, dist, x, y, spin}, seconds)`
and `setOverlays({coast, graticule, marker, tint}, seconds)` start new tweens from the
current value. `setManualTime(t)` freezes the clock at `t`, which is how the intro is
captured frame by frame; texture fade-in uses wall-clock time, because loading is not
part of the script.

## Performance

- Three textures, 0.85 MB in total (day 3072 × 1536 JPEG 590 KB, night 2048 × 1024 JPEG
  131 KB, water mask 1024 × 512 PNG 108 KB); anisotropy ≤ 8.
- Pixel ratio capped at 2; one draw call each for globe, atmosphere, coastlines,
  graticule, two star layers and four marker meshes.
- The onboarding is a separate lazily loaded chunk: three.js and the textures are
  fetched only when the onboarding is shown. Bundle sizes after the change:
  main `index.js` 2,596,887 B (was 2,588,028 B on `main`, +8.9 KB for the gate and the
  Kazakh table); `Onboarding.js` 605,480 B (158 KB gzip).
- Returning visitors who have seen the intro do not download the onboarding chunk or
  the textures at all.
- The animation loop stops when the onboarding unmounts (`dispose` releases geometries,
  materials, textures and the renderer).

## Loading and failure

- A 1 × 1 dark texture is bound until the real ones arrive; the globe fades from a dark
  placeholder sphere (with rim glow) to the textured one in 1.4 s.
- Progress is reported to the splash ("Loading Earth imagery · 67 %").
- If a texture fails, the placeholder sphere, coastlines, atmosphere and marker remain,
  and the flow continues.
- **No WebGL** (or `?earth=2d` to test it): `FlatGlobe` draws Natural Earth land as dots
  in an orthographic projection on a 2D canvas, with the same camera API, and the screen
  says so: "WebGL is unavailable — showing a 2D view, not the 3D globe". It is not
  presented as 3D.

## Region focus

`setMarker(lat, lon)` moves the marker; `setView({lat, lon, dist})` flies the camera to
it; `markerScreen()` returns its screen position and whether it faces the camera, which
the intro uses to pin the place label and the variable chips to the globe. The app's
own region selection still uses the existing MapLibre map; linking the two is a possible
next step, not done.

## Assets

See `ASSETS_AND_LICENSES.md`.

## Preview

See `PREVIEW_NOTES.md` and `docs/visual/screenshots/` — real captures of the running
application in headless Chrome (SwiftShader WebGL).
