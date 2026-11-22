#pragma once
#include <stdbool.h>
#include <stdint.h>
#include "esp_err.h"
#include "driver/spi_master.h"

typedef struct {
    spi_host_device_t host;
    int sck, mosi, miso, cs;
    int clock_hz;
} radio_spi_config_t;

typedef struct {
    uint8_t partnum;
    uint8_t version;
} cc1101_identity_t;

typedef struct {
    uint8_t config;
    uint8_t rf_ch;
    uint8_t setup_aw;
} nrf24_identity_t;

/* Caller must initialize the bus with radio_probe_bus_init, and must not
 * initialize the same SPI host twice. Pins are runtime-configurable. */
esp_err_t radio_probe_bus_init(const radio_spi_config_t *cfg);
esp_err_t radio_probe_cc1101(const radio_spi_config_t *cfg, cc1101_identity_t *out);
esp_err_t radio_probe_nrf24(const radio_spi_config_t *cfg, nrf24_identity_t *out);
