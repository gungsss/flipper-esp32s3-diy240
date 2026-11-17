#include <assert.h>
#include <stddef.h>
#include <stdint.h>
#include "furi_hal_usb_hid_output_report.h"

int main(void) {
    uint8_t led = 0xa5;
    const uint8_t control[] = {0x02};
    const uint8_t interrupt[] = {FURI_HAL_USB_HID_KEYBOARD_REPORT_ID, 0x05};
    const uint8_t other[] = {2, 0xff};

    assert(furi_hal_usb_hid_keyboard_led_report(1, control, 1, &led));
    assert(led == 0x02);
    assert(furi_hal_usb_hid_keyboard_led_report(0, interrupt, 2, &led));
    assert(led == 0x05);
    assert(!furi_hal_usb_hid_keyboard_led_report(0, interrupt, 1, &led));
    assert(!furi_hal_usb_hid_keyboard_led_report(0, other, 2, &led));
    assert(!furi_hal_usb_hid_keyboard_led_report(2, control, 1, &led));
    assert(!furi_hal_usb_hid_keyboard_led_report(1, NULL, 1, &led));
    assert(!furi_hal_usb_hid_keyboard_led_report(1, control, 1, NULL));
    assert(led == 0x05);
    return 0;
}
