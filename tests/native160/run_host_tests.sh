#!/usr/bin/env bash
# Source-level checks only. This does not build or flash ESP32 firmware.
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source_root="${1:?Usage: run_host_tests.sh <prepared-source-tree>}"
source_root="$(cd -- "$source_root" && pwd)"
ui="$source_root/components/gui/native160"
output_dir="$(mktemp -d)"
trap 'rm -rf -- "$output_dir"' EXIT
flags=(-std=c11 -Wall -Wextra -Werror -g -fsanitize=address,undefined -fno-omit-frame-pointer)
python3 "$here/test_original_frames.py" "$source_root" "$output_dir/frames"
gcc "${flags[@]}" -I "$ui" "$ui/graphics160.c" "$ui/menu160.c" "$here/test_menu160.c" -o "$output_dir/menu"
gcc "${flags[@]}" -I "$ui" "$ui/graphics160.c" "$ui/home160.c" "$here/test_home160.c" -o "$output_dir/home"
gcc "${flags[@]}" -I "$ui" "$ui/graphics160.c" "$ui/list160.c" "$here/test_list160.c" -o "$output_dir/list"
gcc "${flags[@]}" -I "$ui" "$ui/graphics160.c" "$ui/home160.c" "$ui/menu160.c" "$ui/list160.c" "$ui/present160.c" "$here/test_present160.c" -o "$output_dir/present"
gcc "${flags[@]}" -I "$ui" "$ui/graphics160.c" "$ui/home160.c" "$ui/menu160.c" "$ui/list160.c" "$ui/present160.c" "$ui/frame160.c" "$here/test_frame160.c" -o "$output_dir/frame"
gcc "${flags[@]}" -I "$here/stubs" -I "$source_root/components/gui" -I "$ui" "$ui/graphics160.c" "$ui/home160.c" "$ui/menu160.c" "$ui/list160.c" "$ui/present160.c" "$ui/frame160.c" "$ui/native160_canvas.c" "$here/test_canvas_bridge160.c" -o "$output_dir/bridge"
gcc -std=gnu11 -Wall -Wextra -Werror -g -fsanitize=address,undefined -fno-omit-frame-pointer \
    -ffunction-sections -fdata-sections -Wl,--gc-sections -I "$here/model_stubs" \
    -I "$source_root/components/input" -I "$source_root/components/gui" \
    -I "$source_root/components/gui/modules" -I "$source_root/components/mlib" \
    "$here/test_actual_list_models.c" -o "$output_dir/models"
for geometry in 160 240; do
    if [[ "$geometry" == 160 ]]; then height=128; margin=0; else height=240; margin=4; fi
    gcc "${flags[@]}" -I "$source_root/components/furi_hal" -DBOARD_LCD_H_RES="$geometry" -DBOARD_LCD_V_RES="$height" -DBOARD_LCD_SIDE_MARGIN="$margin" "$here/test_display_geometry.c" -o "$output_dir/geometry$geometry"
done
export ASAN_OPTIONS=detect_leaks=0
"$output_dir/menu" "$output_dir/menu.ppm"
"$output_dir/list"
"$output_dir/models"
"$output_dir/home" "$output_dir/frames/frame-0.raw" "$output_dir/home.ppm"
"$output_dir/present" "$output_dir/frames/frame-0.raw"
"$output_dir/frame"
"$output_dir/bridge"
"$output_dir/geometry160"
"$output_dir/geometry240"
