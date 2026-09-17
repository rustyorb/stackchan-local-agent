#include "stakia_geometry.h"
#include <cassert>
int main() {
    using namespace stakia;
    const auto normal = geometry(0, 100, 0, 0);
    assert(normal.width == 96 && normal.height == 108);
    assert(normal.top_cover == 0 && normal.bottom_cover == 0);
    const auto blink = geometry(0, 0, 0, 0);
    assert(blink.top_cover + blink.bottom_cover == blink.height);
    for (int size = -100; size <= 100; size += 5)
      for (int openness = 0; openness <= 100; openness += 5)
        for (int gaze = -100; gaze <= 100; gaze += 5) {
          auto g = geometry(size, openness, gaze, -gaze);
          assert(g.width <= 104 && g.height <= 116);
          assert(g.iris / 2 + g.gaze_x <= g.width / 2);
          assert(g.iris / 2 - g.gaze_x <= g.width / 2);
          assert(g.iris / 2 + g.gaze_y <= g.height / 2);
          assert(g.iris / 2 - g.gaze_y <= g.height / 2);
          assert(g.top_cover + g.bottom_cover <= g.height);
        }
    assert(wrap_rotation(-450) == 3150);
    assert(wrap_rotation(3600) == 0);
}
