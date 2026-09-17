// SPDX-License-Identifier: MIT
#pragma once
namespace stakia {
constexpr int clamp(int x, int lo, int hi) { return x < lo ? lo : (x > hi ? hi : x); }
constexpr int wrap_rotation(int angle) { return ((angle % 3600) + 3600) % 3600; }
struct EyeGeometry {
    int width, height, iris, pupil, gaze_x, gaze_y, top_cover, bottom_cover;
};
constexpr EyeGeometry geometry(int size, int openness, int gaze_x, int gaze_y) {
    const int s = clamp(size, -100, 100);
    const int w = 96 + s * 8 / 100;
    const int h = 108 + s * 8 / 100;
    const int iris = 54 + s * 4 / 100;
    const int closed = h * (100 - clamp(openness, 0, 100)) / 100;
    return {w, h, iris, iris * 48 / 100,
            clamp(gaze_x, -100, 100) * 12 / 100,
            clamp(gaze_y, -100, 100) * 14 / 100,
            (closed + 1) / 2, closed / 2};
}
}
