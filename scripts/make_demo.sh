#!/usr/bin/env bash
# English demo for the NASA submission form, 30 seconds or less, 1920×1080, silent with English captions.
#   bash scripts/make_demo.sh                       # without a team line
#   TEAM="Team Name · Ann, Bob" bash scripts/make_demo.sh
# Built only from real material: screenshots of the running app (docs/video/demo_stills/, made by
# capturing http://localhost:8000 at 1920×1080) and the app's own Short intro (docs/video/renders/teaser_en.mp4).
set -euo pipefail
cd "$(dirname "$0")/.."
S=docs/video/demo_stills
T=${TEASER:-docs/video/renders/teaser_en.mp4}
OUT=${OUT:-docs/video/renders/demo_en.mp4}
FONT=${FONT:-/usr/share/fonts/opentype/inter/Inter-SemiBold.otf}
[ -f "$FONT" ] || FONT=$(fc-match -f '%{file}' 'sans:semibold')
W=$(mktemp -d)
printf '%s' "In the app: choose a place, variables and years — NASA POWER data" > "$W/c1.txt"
printf '%s' "Raw −0.28, seasons removed +0.59 — and not detected in winter" > "$W/c2.txt"
printf '%s' "Every result keeps its evidence, counter-evidence and NASA source file" > "$W/c3.txt"
printf '%s' "${TEAM:-}" > "$W/team.txt"

cap() {  # drawtext for a caption file, bottom centre
  echo "drawtext=fontfile=$FONT:textfile=$1:fontsize=44:fontcolor=white:box=1:boxcolor=black@0.86:boxborderw=22:x=(w-text_w)/2:y=h-150"
}
still() {  # $1 image, $2 seconds, $3 extra filter (may be empty)
  local f="scale=7680:4320:flags=lanczos,zoompan=z='1+0.00035*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1920x1080:fps=24,setsar=1"
  [ -n "${3:-}" ] && f="$f,$3"
  echo "$f,fade=t=in:st=0:d=0.3,fade=t=out:st=$(echo "$2 - 0.3" | bc):d=0.3,format=yuv420p"
}
TEAMF=""
[ -n "${TEAM:-}" ] && TEAMF="drawtext=fontfile=$FONT:textfile=$W/team.txt:fontsize=40:fontcolor=white:x=(w-text_w)/2:y=96"

ffmpeg -y -loglevel error \
  -loop 1 -framerate 24 -t 3.0 -i "$S/demo_01_splash.jpg" \
  -i "$T" \
  -loop 1 -framerate 24 -t 3.0 -i "$S/demo_02_results.jpg" \
  -loop 1 -framerate 24 -t 3.4 -i "$S/demo_03_card.jpg" \
  -loop 1 -framerate 24 -t 3.4 -i "$S/demo_04_evidence.jpg" \
  -filter_complex "\
[0:v]$(still x 3.0 "$TEAMF")[a];\
[1:v]scale=1920:1080,setsar=1,format=yuv420p[b];\
[2:v]$(still x 3.0 "$(cap "$W/c1.txt")")[c];\
[3:v]$(still x 3.4 "$(cap "$W/c2.txt")")[d];\
[4:v]$(still x 3.4 "$(cap "$W/c3.txt")")[e];\
[a][b][c][d][e]concat=n=5:v=1:a=0[v]" \
  -map "[v]" -r 24 -c:v libx264 -preset veryfast -crf 20 -pix_fmt yuv420p -movflags +faststart \
  -metadata title="EARTH SENSES — demo (NASA Space Apps Challenge 2026)" \
  -metadata comment="Screen recording and screenshots of the running EARTH SENSES app; not generated footage. App code and texts were written with AI assistance (Claude, Anthropic). Earth imagery: NASA Earth Observatory. Data: NASA POWER (MERRA-2)." \
  "$OUT"
rm -rf "$W"
ffprobe -v error -show_entries format=duration,size -of default=nw=1 "$OUT"
