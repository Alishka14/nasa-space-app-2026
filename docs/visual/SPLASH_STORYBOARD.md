# Splash storyboard

Component: `frontend/src/onboarding/Splash.tsx` (camera in `Onboarding.tsx`, styles in
`onboarding.css`). Screenshot: `screenshots/01_splash_en.jpg`.

## Layout

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│      NASA SPACE APPS CHALLENGE 2026 · BE AN EARTH SYSTEM …   │  kicker, cyan, tracked caps
│                 E A R T H   S E N S E S                      │  wordmark, 800, glow
│   We don't just visualize Earth's changes. We investigate    │  tagline
│                    their relationships.                      │
│              AI proposes. Evidence decides.                  │  motto, muted
│                                                              │
│                  ╭───────────────────────╮                   │
│              ╭───╯    rising Earth       ╰───╮               │  globe centred low (y = −0.47)
│   Press any key or click to continue      Skip intro →       │  footer
└──────────────────────────────────────────────────────────────┘
```

## Timeline (normal motion)

| Time | Picture | Text |
|---|---|---|
| 0.0 s | Black space, stars. Earth far and low (distance 4.4, lowered 62 % of the screen); dark placeholder sphere with rim glow while textures load | Loading line: "Loading Earth imagery · n %" |
| 0.0–7.0 s | Camera pushes in to distance 2.75 and the planet rises to 47 % below centre, turning slowly (4°/s); Europe and Asia come into view; textures fade in over 1.4 s once loaded | — |
| 0.25–0.85 s | — | Wordmark letters resolve from blur, 50 ms apart |
| 1.3 s | — | Tagline rises in |
| 2.0 s | — | Kicker fades in |
| 2.6 s | — | Motto fades in |
| loaded | — | Loading line replaced by "Press any key or click to continue" (slow pulse) |
| ≥ 5.2 s and loaded | Automatic transition to the language screen | — |

## Loading behaviour

- The splash never waits on the network for longer than **12 s**: after that it moves on
  even if textures have not arrived (the globe stays the placeholder sphere with
  coastlines and glow).
- Progress shown is real (`THREE.LoadingManager`), not a timer.
- The onboarding chunk itself is loaded lazily; while it downloads, a plain dark screen
  is shown so the app never flashes underneath.

## Skip behaviour

| Input | Effect |
|---|---|
| Any key or click after 0.8 s | Continue to the language screen |
| `Esc` or "Skip intro →" | Close the onboarding and open the app; the intro is marked as seen |

## Exit

The splash text unmounts; the same globe (one WebGL canvas for the whole onboarding)
glides to the language-screen framing: latitude 36°, longitude 72°, distance 3.05,
shifted right by 23 % of the width, coastlines at 55 %, marker on. There is no cut and
no reload of the globe.

## Reduced motion

`prefers-reduced-motion: reduce` shows all text at once without animation, stops the
spin, shortens camera moves to 0.4 s and continues after 2.5 s.
