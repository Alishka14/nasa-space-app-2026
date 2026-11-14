# Assets and licences used by the onboarding

## Earth textures

| File in `frontend/src/onboarding/earth/textures/` | Pixels | What it is | Credit |
|---|---|---|---|
| `nasa-blue-marble-ng-200405-2048x1024.jpg` | 2048 × 1024, 312 kB | Blue Marble: Next Generation with topography and bathymetry, May 2004 (Terra MODIS) | NASA Earth Observatory (Reto Stöckli) |
| `nasa-earth-at-night-2012-2048x1024.png` | 2048 × 1024, 1.5 MB | Earth at Night 2012 — land, ocean, ice (Suomi NPP VIIRS day-night band) | NASA Earth Observatory/NOAA NGDC (Robert Simmon; data courtesy Chris Elvidge, NOAA NGDC) |
| `water-mask-natural-earth-50m.png` | 2048 × 1024, 141 kB | Land/water mask for the sun glint, drawn by this project | Made with Natural Earth |

**Where the NASA images come from.** Both are **byte-identical copies** of the files that NASA's own
WorldWind project ships in its repository —
`github.com/NASAWorldWind/WebWorldWind`, folder `images/`, commit `5ffe2dfc54ab4d744fc9e587af9639c9910db228`
(`BMNG_world.topo.bathy.200405.3.2048x1024.jpg` for its Blue Marble layer,
`dnb_land_ocean_ice_2012.png` for its atmosphere/night layer). WorldWind is developed by NASA Ames Research
Center, and its site `worldwind.arc.nasa.gov` names that GitHub organisation as the project's official home.
`scripts/build_earth_textures.py` refuses a file whose SHA-256 differs from the pinned value, and
`backend/tests/test_10_earth_textures.py` checks every shipped texture against
[`SOURCES.json`](../../frontend/src/onboarding/earth/textures/SOURCES.json).

**What was not possible here.** NASA's own image servers (`visibleearth.nasa.gov`, `eoimages.gsfc.nasa.gov`)
are blocked by this build environment's network policy, so the files were not downloaded from Visible Earth
directly and could not be compared with Visible Earth's copies byte for byte. They are NASA images distributed
by a NASA project, not images found in a third-party package; the earlier, unverified textures from the npm
package `three-globe` have been removed.

**Terms.** NASA Visible Earth: most images are freely available for re-publication or re-use, including
commercial purposes, except where copyright is indicated; please use the credit given with each image; the
only mandatory credit is **NASA** (visibleearth.nasa.gov/image-use-policy). For Blue Marble: Next Generation
the Earth Observatory asks for the credit "NASA Earth Observatory". NASA does not endorse this project, and no
NASA logo or insignia is used.

**Credit line used in the app and the films:** *Earth imagery: NASA Earth Observatory (Blue Marble: Next
Generation; Earth at Night 2012, with NOAA NGDC). Coastlines and water mask: Natural Earth.*

## Data drawn on the globe

| Data | Licence | Use |
|---|---|---|
| Natural Earth 1:110m land, via `world-atlas@2` (`countries-110m.json`) | Public domain (Natural Earth); package ISC | Coastline overlay, 2D fallback land dots |
| Natural Earth 1:50m land, via `world-atlas@2` (`land-50m.json`) | Public domain (Natural Earth); package ISC | Water mask (drawn once by `scripts/build_earth_textures.py`) |
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
