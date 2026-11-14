# Assets and licences used by the onboarding

## Earth textures — provenance to verify before public release

| File in `frontend/src/onboarding/earth/textures/` | Size | Made from | Source file SHA-256 |
|---|---|---|---|
| `earth-day.jpg` | 3072 × 1536, 590 KB | `three-globe@2.45.6/example/img/earth-blue-marble.jpg` (4096 × 2048), resized | `228deba2e4b600146bdcb6cfa359b8ead6aacc2b1c13550a29cd82824cfa1c01` |
| `earth-night.jpg` | 2048 × 1024, 131 KB | `three-globe@2.45.6/example/img/earth-night.jpg` (4096 × 2048), resized | `355ab23dd1323315b393d7b91dd2d7ee223a1cbaaba2b48dc72ba90d371ced24` |
| `earth-water.png` | 1024 × 512, 108 KB | `three-globe@2.45.6/example/img/earth-water.png` (1600 × 800), resized, greyscale | `3a8132db56aac4e64e7fcbf2928ee970c075ac6a96b38798d0bb8be82836a4d3` |

**What is known.** The files were taken from the npm package `three-globe` 2.45.6
(MIT licence, © Vasco Asturiano), which ships them as example images. The package does
not state where the images come from. The day image matches the appearance of NASA's
Blue Marble composites and the night image NASA's "Earth at Night" city-lights
composites, but that was **not verified** in this build: the build environment could not
reach NASA's image servers.

**What NASA says about its imagery** (if they are NASA images): Visible Earth images are
freely available for re-use, the only mandatory credit is "NASA", and NASA branding must
not imply endorsement.

**To do before public release (5 minutes):** download the day and night images directly
from NASA Visible Earth (Blue Marble Next Generation; Earth at Night / Black Marble),
resize them to the sizes above, replace the three files and record the source URLs here.
The code does not depend on the exact images.

## Data drawn on the globe

| Data | Licence | Use |
|---|---|---|
| Natural Earth 1:110m land, via `world-atlas@2` (`countries-110m.json`) | Public domain (Natural Earth); package ISC | Coastline overlay, 2D fallback land dots |
| `facts.json`, `series.json` | Computed by this project from NASA POWER (MERRA-2) data | Numbers and curves in the intro |

## Libraries

| Library | Version | Licence |
|---|---|---|
| three | 0.187.0 | MIT |
| @types/three (dev) | 0.187.0 | MIT |
| topojson-client | 3.1.0 | ISC |
| React | 19 | MIT |

## Not used

No fonts are downloaded, no audio files exist, no generated (AI) images or video are
included, no NASA logo or insignia is used.
