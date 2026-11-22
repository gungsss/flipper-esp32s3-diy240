#include "radio_probe.h"
#include <string.h>
#include "driver/gpio.h"
#include "esp_check.h"

#define CC1101_PARTNUM 0x30
#define CC1101_VERSION 0x31
#define CC1101_READ_STATUS 0xC0
#define NRF_R_REGISTER 0x00
#define NRF_CONFIG 0x00
#define NRF_RF_CH 0x05
#define NRF_SETUP_AW 0x03

static esp_err_t attach(const radio_spi_config_t *cfg, spi_device_handle_t *dev) {
    if (!cfg || !dev || cfg->cs < 0 || cfg->clock_hz <= 0) return ESP_ERR_INVALID_ARG;
    spi_device_interface_config_t dc = {
        .clock_speed_hz = cfg->clock_hz,
        .mode = 0,
        .spics_io_num = cfg->cs,
        .queue_size = 1,
    };
    return spi_bus_add_device(cfg->host, &dc, dev);
}

esp_err_t radio_probe_bus_init(const radio_spi_config_t *cfg) {
    if (!cfg || cfg->sck < 0 || cfg->mosi < 0 || cfg->miso < 0) return ESP_ERR_INVALID_ARG;
    spi_bus_config_t bus = {
        .sclk_io_num = cfg->sck,
        .mosi_io_num = cfg->mosi,
        .miso_io_num = cfg->miso,
        .quadwp_io_num = -1,
        .quadhd_io_num = -1,
        .max_transfer_sz = 32,
    };
    return spi_bus_initialize(cfg->host, &bus, SPI_DMA_DISABLED);
}

static esp_err_t read_register(spi_device_handle_t dev, uint8_t command, uint8_t *value) {
    uint8_t tx[2] = {command, 0};
    uint8_t rx[2] = {0};
    spi_transaction_t tr = {
        .length = 16,
        .tx_buffer = tx,
        .rx_buffer = rx,
    };
    esp_err_t err = spi_device_transmit(dev, &tr);
    if (err == ESP_OK) *value = rx[1];
    return err;
}

esp_err_t radio_probe_cc1101(const radio_spi_config_t *cfg, cc1101_identity_t *out) {
    if (!out) return ESP_ERR_INVALID_ARG;
    memset(out, 0, sizeof(*out));
    spi_device_handle_t dev = NULL;
    esp_err_t err = attach(cfg, &dev);
    if (err != ESP_OK) return err;
    err = read_register(dev, CC1101_PARTNUM | CC1101_READ_STATUS, &out->partnum);
    if (err == ESP_OK) err = read_register(dev, CC1101_VERSION | CC1101_READ_STATUS, &out->version);
    spi_bus_remove_device(dev);
    if (err != ESP_OK) return err;
    /* Floating MISO often reads all zeroes or all ones; not a proof of absence. */
    if ((out->partnum == 0xFF && out->version == 0xFF) ||
        (out->partnum == 0 && out->version == 0)) return ESP_ERR_NOT_FOUND;
    return ESP_OK;
}

esp_err_t radio_probe_nrf24(const radio_spi_config_t *cfg, nrf24_identity_t *out) {
    if (!out) return ESP_ERR_INVALID_ARG;
    memset(out, 0, sizeof(*out));
    spi_device_handle_t dev = NULL;
    esp_err_t err = attach(cfg, &dev);
    if (err != ESP_OK) return err;
    err = read_register(dev, NRF_R_REGISTER | NRF_CONFIG, &out->config);
    if (err == ESP_OK) err = read_register(dev, NRF_R_REGISTER | NRF_RF_CH, &out->rf_ch);
    if (err == ESP_OK) err = read_register(dev, NRF_R_REGISTER | NRF_SETUP_AW, &out->setup_aw);
    spi_bus_remove_device(dev);
    if (err != ESP_OK) return err;
    if (out->setup_aw < 1 || out->setup_aw > 3) return ESP_ERR_NOT_FOUND;
    return ESP_OK;
}
