#include "fw_ota_profile.h"
#include <assert.h>
#include <stdint.h>
#include <string.h>

int main(void) {
    const FwOtaBoardProfile* expected = &fw_ota_board_profile;
    assert(expected->schema == 1);
#if defined(BOARD_OTA_PROFILE_ST7789) && BOARD_OTA_PROFILE_ST7789
    assert(expected->display_controller == 7789);
#else
    assert(expected->display_controller == 7735);
#endif
    assert(expected->pins[0] == 11 && expected->pins[1] == 12);
    assert(expected->pins[4] == UINT16_MAX && expected->pins[8] == 38);
    assert(expected->pins[14] == 8 && expected->pins[15] == 18);
    uint8_t candidate[sizeof(*expected) + 1];
    memcpy(candidate + 1, expected, sizeof(*expected));
    assert(fw_ota_profile_matches(candidate + 1, sizeof(*expected)));
    assert(!fw_ota_profile_matches(candidate + 1, sizeof(*expected) - 1));
    assert(!fw_ota_profile_matches(NULL, sizeof(*expected)));
    for(size_t index = 0; index < sizeof(*expected); ++index) {
        candidate[index + 1] ^= 1;
        assert(!fw_ota_profile_matches(candidate + 1, sizeof(*expected)));
        candidate[index + 1] ^= 1;
    }
    return 0;
}
