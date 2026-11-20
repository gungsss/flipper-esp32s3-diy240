/* Flipper Zero 1.5.1 hotel-card parser, adapted for the ESP32 backport. */
#include "nfc_supported_card_plugin.h"

#include <flipper_application/flipper_application.h>
#include <bit_lib/bit_lib.h>
#include <nfc/nfc_device.h>
#include <nfc/protocols/mf_classic/mf_classic_poller_sync.h>

static const uint64_t saflok_sector1_keya = 0x2A2C13CC242A;
static const uint64_t vingcard_sector2_keyb = 0x0000014B5C31;
static const uint64_t onity_sector1_keya = 0x8A19D40CF2B5;

static bool hotels_parse(const NfcDevice* device, FuriString* parsed_data) {
    furi_assert(device);
    furi_assert(parsed_data);

    const MfClassicData* data = nfc_device_get_data(device, NfcProtocolMfClassic);
    if(!data) return false;

    const MfClassicSectorTrailer* sector1 =
        mf_classic_get_sector_trailer_by_sector(data, 1);
    const MfClassicSectorTrailer* sector2 =
        mf_classic_get_sector_trailer_by_sector(data, 2);
    if(!sector1 || !sector2) return false;

    const uint64_t key_a = bit_lib_bytes_to_num_be(sector1->key_a.data, 6);
    const uint64_t key_b = bit_lib_bytes_to_num_be(sector2->key_b.data, 6);
    const char* hotel = NULL;

    if(key_a == saflok_sector1_keya) {
        hotel = "Saflok";
    } else if(key_a == onity_sector1_keya) {
        hotel = "Onity";
    } else if(key_b == vingcard_sector2_keyb) {
        hotel = "VingCard";
    }

    if(!hotel) return false;
    furi_string_printf(parsed_data, "\e#Hotel\n%s", hotel);
    return true;
}

static const NfcSupportedCardsPlugin hotels_plugin = {
    .protocol = NfcProtocolMfClassic,
    .verify = NULL,
    .read = NULL,
    .parse = hotels_parse,
};

static const FlipperAppPluginDescriptor hotels_plugin_descriptor = {
    .appid = NFC_SUPPORTED_CARD_PLUGIN_APP_ID,
    .ep_api_version = NFC_SUPPORTED_CARD_PLUGIN_API_VERSION,
    .entry_point = &hotels_plugin,
};

const FlipperAppPluginDescriptor* hotels_plugin_ep(void) {
    return &hotels_plugin_descriptor;
}
