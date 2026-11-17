#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#include "driver/spi_master.h"
#include "esp_check.h"
#include "esp_heap_caps.h"
#include "esp_lcd_panel_io.h"
#include "esp_lcd_panel_ops.h"
#include "esp_lcd_panel_vendor.h"
#include "esp_lcd_st7735.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"
#include "freertos/task.h"

// Matches the DIY240 firmware wiring. This test does not drive BLK, the SD
// card, or any buttons. The display is a write-only SPI device without CS.
enum {
    TFT_SCLK = 12, TFT_MOSI = 11, TFT_RESET = 16, TFT_DC = 15,
    WIDTH = 128, HEIGHT = 160, STRIPE = 10,
};

static const char *TAG = "TFT_TEST";

static bool color_transfer_done(esp_lcd_panel_io_handle_t io,
                                esp_lcd_panel_io_event_data_t *event,
                                void *user_ctx)
{
    (void)io;
    (void)event;
    BaseType_t woken = pdFALSE;
    xSemaphoreGiveFromISR((SemaphoreHandle_t)user_ctx, &woken);
    return woken == pdTRUE;
}

static void fill_screen(esp_lcd_panel_handle_t panel, SemaphoreHandle_t done,
                        uint16_t *stripe, uint16_t rgb565)
{
    // The ST7789 expects the high byte of RGB565 first on SPI.
    uint16_t wire_color = __builtin_bswap16(rgb565);
    for (int i = 0; i < WIDTH * STRIPE; ++i) stripe[i] = wire_color;
    for (int y = 0; y < HEIGHT; y += STRIPE) {
        ESP_ERROR_CHECK(esp_lcd_panel_draw_bitmap(panel, 0, y, WIDTH, y + STRIPE, stripe));
        if (xSemaphoreTake(done, pdMS_TO_TICKS(3000)) != pdTRUE) {
            ESP_LOGE(TAG, "Timeout waiting for SPI transfer");
            abort();
        }
    }
}

void app_main(void)
{
    ESP_LOGI(TAG, "ST7735S test: SCLK=12 MOSI=11 RST=16 DC=15; CS grounded, BLK not driven");
    SemaphoreHandle_t done = xSemaphoreCreateBinary();
    assert(done);
    uint16_t *stripe = heap_caps_malloc(WIDTH * STRIPE * sizeof(uint16_t),
                                       MALLOC_CAP_DMA | MALLOC_CAP_INTERNAL);
    assert(stripe);

    const spi_bus_config_t bus = {
        .sclk_io_num = TFT_SCLK,
        .mosi_io_num = TFT_MOSI,
        .miso_io_num = -1,
        .quadwp_io_num = -1,
        .quadhd_io_num = -1,
        .max_transfer_sz = WIDTH * STRIPE * sizeof(uint16_t),
    };
    ESP_ERROR_CHECK(spi_bus_initialize(SPI2_HOST, &bus, SPI_DMA_CH_AUTO));

    const esp_lcd_panel_io_spi_config_t io_config = {
        .dc_gpio_num = TFT_DC,
        .cs_gpio_num = -1,
        .pclk_hz = 5 * 1000 * 1000,
        .lcd_cmd_bits = 8,
        .lcd_param_bits = 8,
        .spi_mode = 0,
        .trans_queue_depth = 1,
        .on_color_trans_done = color_transfer_done,
        .user_ctx = done,
    };
    esp_lcd_panel_io_handle_t io = NULL;
    ESP_ERROR_CHECK(esp_lcd_new_panel_io_spi((esp_lcd_spi_bus_handle_t)SPI2_HOST, &io_config, &io));
    const esp_lcd_panel_dev_config_t panel_config = {
        .reset_gpio_num = TFT_RESET,
        .rgb_ele_order = LCD_RGB_ELEMENT_ORDER_RGB,
        .bits_per_pixel = 16,
    };
    esp_lcd_panel_handle_t panel = NULL;
    ESP_ERROR_CHECK(esp_lcd_new_panel_st7735(io, &panel_config, &panel));
    ESP_ERROR_CHECK(esp_lcd_panel_reset(panel));
    ESP_ERROR_CHECK(esp_lcd_panel_init(panel));
    ESP_ERROR_CHECK(esp_lcd_panel_invert_color(panel, false));
    ESP_ERROR_CHECK(esp_lcd_panel_mirror(panel, true, true));
    ESP_ERROR_CHECK(esp_lcd_panel_disp_on_off(panel, true));

    const struct { const char *name; uint16_t color; } colors[] = {
        {"MERAH", 0xf800}, {"HIJAU", 0x07e0}, {"BIRU", 0x001f},
        {"PUTIH", 0xffff}, {"HITAM", 0x0000},
    };
    const int offsets[][2] = {{0, 0}, {2, 1}};
    while (true) {
        for (size_t i = 0; i < sizeof(offsets) / sizeof(offsets[0]); ++i) {
            ESP_ERROR_CHECK(esp_lcd_panel_set_gap(panel, offsets[i][0], offsets[i][1]));
            for (size_t j = 0; j < sizeof(colors) / sizeof(colors[0]); ++j) {
                ESP_LOGI(TAG, "offset_x=%d offset_y=%d warna=%s", offsets[i][0], offsets[i][1], colors[j].name);
                fill_screen(panel, done, stripe, colors[j].color);
                vTaskDelay(pdMS_TO_TICKS(2000));
            }
        }
    }
}
