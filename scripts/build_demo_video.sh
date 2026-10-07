#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "$0")/.." && pwd)"
media_dir="$repo_dir/submission/media"
screen_recording="${1:-$media_dir/hearound-screen-recording.mp4}"
output_video="${2:-$media_dir/hearound-demo-final.mp4}"
voiceover="$media_dir/hearound-demo-voiceover-en.mp3"
captions="$repo_dir/submission/DEMO_CAPTIONS_EN.srt"

if [[ ! -f "$screen_recording" ]]; then
  echo "Missing screen recording: $screen_recording" >&2
  echo "Record the 2:42 walkthrough and save it there, or pass its path as argument 1." >&2
  exit 1
fi

ffmpeg -y \
  -i "$screen_recording" \
  -i "$voiceover" \
  -filter_complex "[0:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1,subtitles='${captions//:/\\:}':force_style='FontName=Arial,FontSize=22,PrimaryColour=&H00FFFFFF,OutlineColour=&H0010171D,BorderStyle=1,Outline=2,Shadow=0,MarginV=38'[v]" \
  -map "[v]" -map 1:a:0 \
  -c:v libx264 -preset medium -crf 20 -pix_fmt yuv420p \
  -c:a aac -b:a 192k \
  -shortest -movflags +faststart \
  "$output_video"

echo "Created: $output_video"
