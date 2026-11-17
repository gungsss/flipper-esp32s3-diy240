#pragma once

/* Host-side descriptor tests use TinyUSB's real descriptor macros only. */
#define CFG_TUSB_MCU OPT_MCU_NONE
#define CFG_TUSB_OS OPT_OS_NONE
#define CFG_TUD_ENABLED 1
#define CFG_TUD_HID 1
#define CFG_TUD_CDC 1
#define CFG_TUD_MSC 1
#define CFG_TUD_MSC_EP_BUFSIZE 512
#define CFG_TUD_ENDPOINT0_SIZE 64
#define TUP_DCD_ENDPOINT_MAX 6
