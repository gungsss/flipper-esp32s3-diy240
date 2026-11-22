#!/usr/bin/env python3
"""Add runtime module checks and actionable messages to the ST7735S port."""

from pathlib import Path
import argparse


def replace_once(text, old, new, label):
    if new in text:
        return text
    if text.count(old) != 1:
        raise ValueError(f"{label}: expected one source anchor, found {text.count(old)}")
    return text.replace(old, new, 1)


def patch_file(root, relative, edits):
    path = root / relative
    text = path.read_text(encoding="utf-8")
    for old, new, label in edits:
        text = replace_once(text, old, new, label)
    path.write_text(text, encoding="utf-8")


def replace_function(root, relative, signature, replacement, label):
    path = root / relative
    text = path.read_text(encoding="utf-8")
    start = text.find(signature)
    if start < 0:
        raise ValueError(f"{label}: function signature is missing")
    opening = text.find("{", start + len(signature))
    if opening < 0:
        raise ValueError(f"{label}: function body is missing")
    depth = 0
    end = None
    for index in range(opening, len(text)):
        if text[index] == "{":
            depth += 1
        elif text[index] == "}":
            depth -= 1
            if depth == 0:
                end = index + 1
                break
    if end is None:
        raise ValueError(f"{label}: function body is unterminated")
    path.write_text(text[:start] + replacement + text[end:], encoding="utf-8")


def patch_pairing_layout(root):
    """Give the BLE PIN overlay a native 160x128 drawing surface."""
    patch_file(root, "components/gui/view_port.h", [
        ("void view_port_set_orientation(ViewPort* view_port, ViewPortOrientation orientation);\n",
         "void view_port_set_orientation(ViewPort* view_port, ViewPortOrientation orientation);\n"
         "/* Render this full-screen viewport in physical panel coordinates. */\n"
         "void view_port_set_native_layout(ViewPort* view_port, bool native_layout);\n",
         "native viewport layout API"),
    ])
    patch_file(root, "components/gui/view_port_i.h", [
        ("    ViewPortOrientation orientation;\n",
         "    ViewPortOrientation orientation;\n    bool native_layout;\n",
         "native viewport layout state"),
    ])
    patch_file(root, "components/gui/view_port.c", [
        ("    view_port->orientation = ViewPortOrientationHorizontal;\n",
         "    view_port->orientation = ViewPortOrientationHorizontal;\n"
         "    view_port->native_layout = false;\n",
         "initialize legacy viewport layout"),
        ("        canvas_set_legacy_scale(canvas, true);\n",
         "        canvas_set_legacy_scale(canvas, !view_port->native_layout);\n",
         "respect native viewport layout"),
        ("void view_port_set_orientation(ViewPort* view_port, ViewPortOrientation orientation) {\n"
         "    furi_check(view_port);\n"
         "    furi_check(furi_mutex_acquire(view_port->mutex, FuriWaitForever) == FuriStatusOk);\n"
         "    view_port->orientation = orientation;\n"
         "    furi_check(furi_mutex_release(view_port->mutex) == FuriStatusOk);\n"
         "}\n",
         "void view_port_set_orientation(ViewPort* view_port, ViewPortOrientation orientation) {\n"
         "    furi_check(view_port);\n"
         "    furi_check(furi_mutex_acquire(view_port->mutex, FuriWaitForever) == FuriStatusOk);\n"
         "    view_port->orientation = orientation;\n"
         "    furi_check(furi_mutex_release(view_port->mutex) == FuriStatusOk);\n"
         "}\n\n"
         "void view_port_set_native_layout(ViewPort* view_port, bool native_layout) {\n"
         "    furi_check(view_port);\n"
         "    furi_check(furi_mutex_acquire(view_port->mutex, FuriWaitForever) == FuriStatusOk);\n"
         "    view_port->native_layout = native_layout;\n"
         "    furi_check(furi_mutex_release(view_port->mutex) == FuriStatusOk);\n"
         "}\n",
         "set native viewport layout"),
    ])

    replace_function(
        root,
        "components/btshim/btshim.c",
        "static void bt_pin_code_view_port_draw_callback(Canvas* canvas, void* context)",
        "static void bt_pin_code_view_port_draw_callback(Canvas* canvas, void* context) {\n"
        "    furi_assert(context);\n"
        "    Bt* bt = context;\n"
        "    char pin_code[7];\n"
        "    snprintf(pin_code, sizeof(pin_code), \"%06lu\", (unsigned long)bt->pin_code);\n"
        "\n"
        "    canvas_clear(canvas);\n"
        "    canvas_set_color(canvas, ColorBlack);\n"
        "    canvas_set_font(canvas, FontPrimary);\n"
        "    canvas_draw_icon(canvas, 12, 7, &I_Bluetooth_Idle_5x8);\n"
        "    canvas_draw_str(canvas, 25, 16, \"PAIR DEVICE\");\n"
        "    canvas_draw_line(canvas, 8, 24, 152, 24);\n"
        "\n"
        "    canvas_set_font(canvas, FontSecondary);\n"
        "    canvas_draw_str_aligned(\n"
        "        canvas, 80, 43, AlignCenter, AlignBottom, \"ENTER THIS CODE IN THE APP\");\n"
        "    canvas_draw_rframe(canvas, 13, 49, 134, 45, 4);\n"
        "    canvas_draw_rbox(canvas, 17, 53, 126, 37, 3);\n"
        "    canvas_invert_color(canvas);\n"
        "    canvas_set_font(canvas, FontBigNumbers);\n"
        "    canvas_draw_str_aligned(canvas, 80, 82, AlignCenter, AlignBottom, pin_code);\n"
        "    canvas_invert_color(canvas);\n"
        "\n"
        "    canvas_set_font(canvas, FontSecondary);\n"
        "    canvas_draw_str_aligned(\n"
        "        canvas, 80, 108, AlignCenter, AlignBottom, \"Pair with Flipper mobile app\");\n"
        "    canvas_draw_line(canvas, 8, 114, 152, 114);\n"
        "    canvas_draw_str(canvas, 8, 125, \"BACK: close code\");\n"
        "}",
        "full-screen BLE PIN code layout",
    )
    replace_function(
        root,
        "components/btshim/btshim.c",
        "static void bt_pin_code_view_port_input_callback(InputEvent* event, void* context)",
        "static void bt_pin_code_view_port_input_callback(InputEvent* event, void* context) {\n"
        "    furi_assert(context);\n"
        "    Bt* bt = context;\n"
        "    if(event->type == InputTypeShort && event->key == InputKeyBack) {\n"
        "        view_port_enabled_set(bt->pin_code_view_port, false);\n"
        "    }\n"
        "}",
        "close pairing code only with the physical Back key",
    )
    patch_file(root, "components/btshim/btshim.c", [
        ("    view_port_draw_callback_set(view_port, bt_pin_code_view_port_draw_callback, bt);\n",
         "    view_port_draw_callback_set(view_port, bt_pin_code_view_port_draw_callback, bt);\n"
         "    view_port_set_native_layout(view_port, true);\n",
         "use native 160x128 BLE PIN overlay"),
    ])


def patch_keyboard(root):
    """Use D-pad geometry semantics and keep text entry lowercase by default."""
    header = root / "components/furi_hal/boards/board_DIY.h"
    if not header.is_file() or "#define BOARD_INPUT_DPAD 1" not in header.read_text(encoding="utf-8"):
        raise ValueError("ST7735S board profile must declare its six-button D-pad")
    keyboard = (root / "components/gui/modules/text_input.c").read_text(encoding="utf-8")
    for token in (
        "bool caps_lock;",
        "model->caps_lock = false;",
        "bool uppercase = model->caps_lock && !symbols_active;",
        "model->caps_lock = !model->caps_lock;",
        "Hold OK: Caps",
        "#if defined(BOARD_INPUT_DPAD) && BOARD_INPUT_DPAD",
    ):
        if token not in keyboard:
            raise ValueError(f"Lowercase/Caps Lock or D-pad keyboard patch missing: {token}")


def patch_subghz(root):
    patch_file(root, "components/furi_hal/furi_hal_subghz.h", [
        ("void furi_hal_subghz_init(void);\n",
         "void furi_hal_subghz_init(void);\n"
         "/* True when the CC1101 answered the boot-time SPI identity probe. */\n"
         "bool furi_hal_subghz_is_connected(void);\n",
         "CC1101 readiness API"),
    ])
    patch_file(root, "components/furi_hal/furi_hal_subghz.c", [
        ("void furi_hal_subghz_init(void) {\n",
         "bool furi_hal_subghz_is_connected(void) {\n"
         "    return furi_hal_subghz.connected;\n"
         "}\n\n"
         "void furi_hal_subghz_init(void) {\n",
         "CC1101 readiness getter"),
    ])


def patch_rfid(root):
    patch_file(root, "components/furi_hal/furi_hal_rfid.h", [
        ("void furi_hal_rfid_init(void);\n",
         "void furi_hal_rfid_init(void);\n"
         "/* True after at least one valid tag packet from a read-only UART reader. */\n"
         "bool furi_hal_rfid_has_seen_tag(void);\n",
         "RDM6300 presence API"),
    ])
    path = root / "components/furi_hal/furi_hal_rfid.c"
    text = path.read_text(encoding="utf-8")
    edits = [
        ("static FuriThread* s_reader_thread = NULL;\n",
         "static FuriThread* s_reader_thread = NULL;\n"
         "static atomic_uint s_valid_tag_packets = ATOMIC_VAR_INIT(0);\n",
         "RDM6300 packet counter"),
        ("        ESP_LOGI(TAG, \"RDM6300 tag: %02X%02X%02X%02X%02X\",\n"
         "                 card_data[0], card_data[1], card_data[2], card_data[3], card_data[4]);\n",
         "        atomic_fetch_add_explicit(&s_valid_tag_packets, 1, memory_order_relaxed);\n"
         "        ESP_LOGI(TAG, \"RDM6300 tag: %02X%02X%02X%02X%02X\",\n"
         "                 card_data[0], card_data[1], card_data[2], card_data[3], card_data[4]);\n",
         "record valid RDM6300 packet"),
    ]
    for old, new, label in edits:
        text = replace_once(text, old, new, label)
    no_reader_marker = "#else /* !BOARD_HAS_RFID */\n"
    if no_reader_marker not in text:
        raise ValueError("RFID HAL no-module branch anchor is missing")
    before, after = text.split(no_reader_marker, 1)
    before = replace_once(
        before,
        "void furi_hal_rfid_init(void) {\n",
        "bool furi_hal_rfid_has_seen_tag(void) {\n"
        "    return atomic_load_explicit(&s_valid_tag_packets, memory_order_relaxed) != 0;\n"
        "}\n\n"
        "void furi_hal_rfid_init(void) {\n",
        "RDM6300 packet query",
    )
    if "bool furi_hal_rfid_has_seen_tag(void)" not in after:
        after = replace_once(
            after,
            "void furi_hal_rfid_init(void) {\n",
            "bool furi_hal_rfid_has_seen_tag(void) { return false; }\n\n"
            "void furi_hal_rfid_init(void) {\n",
            "RDM6300 status stub when the profile has no reader pins",
        )
    path.write_text(before + no_reader_marker + after, encoding="utf-8")


def patch_lfrfid_view(root):
    path = root / "applications/main/lfrfid/lfrfid_i.h"
    text = path.read_text(encoding="utf-8")
    if "    uint8_t module_probe_seconds;" not in text:
        text = replace_once(
            text,
            "    LFRFIDWorkerReadType read_type;\n",
            "    LFRFIDWorkerReadType read_type;\n"
            "    uint8_t module_probe_seconds;\n"
            "    bool module_probe_hint_shown;\n"
            "    bool module_probe_tag_seen;\n",
            "LF reader probe state",
        )
        path.write_text(text, encoding="utf-8")

    patch_file(root, "applications/main/lfrfid/views/lfrfid_view_read.h", [
        ("void lfrfid_view_read_set_read_mode(LfRfidReadView* read_view, LfRfidReadViewMode mode);\n",
         "void lfrfid_view_read_set_read_mode(LfRfidReadView* read_view, LfRfidReadViewMode mode);\n"
         "void lfrfid_view_read_set_module_hint(LfRfidReadView* read_view, bool visible);\n",
         "LF reader diagnostic view API"),
    ])
    patch_file(root, "applications/main/lfrfid/views/lfrfid_view_read.c", [
        ("    LfRfidReadViewMode read_mode;\n",
         "    LfRfidReadViewMode read_mode;\n"
         "    bool module_hint_visible;\n",
         "LF reader diagnostic view model"),
        ("            model->icon = icon_animation_alloc(&A_Round_loader_8x8);\n",
         "            model->icon = icon_animation_alloc(&A_Round_loader_8x8);\n"
         "            model->module_hint_visible = false;\n",
         "initialize LF reader diagnostic state"),
        ("    canvas_set_font(canvas, FontSecondary);\n"
         "    canvas_draw_str(canvas, 61, 56, \"Don't move card\");\n",
         "    canvas_set_font(canvas, FontSecondary);\n"
         "    if(model->module_hint_visible) {\n"
         "        canvas_draw_str(canvas, 28, 48, \"No tag data\");\n"
         "        canvas_draw_str(canvas, 8, 59, \"Check RDM6300 / EM4100\");\n"
         "    } else {\n"
         "        canvas_draw_str(canvas, 61, 56, \"Don't move card\");\n"
         "    }\n",
         "LF reader no-response hint"),
    ])
    patch_file(root, "applications/main/lfrfid/views/lfrfid_view_read.c", [
        ("void lfrfid_view_read_set_read_mode(LfRfidReadView* read_view, LfRfidReadViewMode mode) {\n",
         "void lfrfid_view_read_set_module_hint(LfRfidReadView* read_view, bool visible) {\n"
         "    with_view_model(\n"
         "        read_view->view,\n"
         "        LfRfidReadViewModel * model,\n"
         "        { model->module_hint_visible = visible; },\n"
         "        true);\n"
         "}\n\n"
         "void lfrfid_view_read_set_read_mode(LfRfidReadView* read_view, LfRfidReadViewMode mode) {\n",
         "LF reader diagnostic view setter"),
    ])

    patch_file(root, "applications/main/lfrfid/lfrfid.c", [
        ("static LfRfid* lfrfid_alloc(void) {\n",
         "static void lfrfid_tick_event_callback(void* context) {\n"
         "    LfRfid* app = context;\n"
         "    scene_manager_handle_tick_event(app->scene_manager);\n"
         "}\n\n"
         "static LfRfid* lfrfid_alloc(void) {\n",
         "LF reader probe tick callback"),
        ("    view_dispatcher_set_navigation_event_callback(\n"
         "        lfrfid->view_dispatcher, lfrfid_debug_back_event_callback);\n",
         "    view_dispatcher_set_navigation_event_callback(\n"
         "        lfrfid->view_dispatcher, lfrfid_debug_back_event_callback);\n"
         "    view_dispatcher_set_tick_event_callback(\n"
         "        lfrfid->view_dispatcher, lfrfid_tick_event_callback, 1000);\n",
         "LF reader probe tick setup"),
    ])

    patch_file(root, "applications/main/lfrfid/scenes/lfrfid_scene_read.c", [
        ("    if(app->read_type == LFRFIDWorkerReadTypePSKOnly) {\n",
         "    app->module_probe_seconds = 0;\n"
         "    app->module_probe_hint_shown = false;\n"
         "    app->module_probe_tag_seen = false;\n"
         "    lfrfid_view_read_set_module_hint(app->read_view, false);\n\n"
         "    if(app->read_type == LFRFIDWorkerReadTypePSKOnly) {\n",
         "reset LF module probe on scan start"),
        ("        } else if(event.event == LfRfidEventReadSenseCardStart) {\n"
         "            notification_message(app->notifications, &sequence_blink_set_green);\n",
         "        } else if(event.event == LfRfidEventReadSenseCardStart) {\n"
         "            app->module_probe_tag_seen = true;\n"
         "            app->module_probe_hint_shown = false;\n"
         "            lfrfid_view_read_set_module_hint(app->read_view, false);\n"
         "            notification_message(app->notifications, &sequence_blink_set_green);\n",
         "clear LF hint after card response"),
        ("    }\n\n    return consumed;\n}\n\nvoid lfrfid_scene_read_on_exit(void* context) {\n",
         "    } else if(event.type == SceneManagerEventTypeTick) {\n"
         "        if(!app->module_probe_tag_seen && !app->module_probe_hint_shown) {\n"
         "            if(app->module_probe_seconds < 30) app->module_probe_seconds++;\n"
         "            if(app->module_probe_seconds >= 6) {\n"
         "                app->module_probe_hint_shown = true;\n"
         "                lfrfid_view_read_set_module_hint(app->read_view, true);\n"
         "            }\n"
         "        }\n"
         "        consumed = true;\n"
         "    }\n\n    return consumed;\n}\n\nvoid lfrfid_scene_read_on_exit(void* context) {\n",
         "show actionable LF no-response hint"),
    ])


def patch_app_guards(root):
    patch_file(root, "applications/main/subghz/subghz.c", [
        ("#include \"subghz_i.h\"\n",
         "#include \"subghz_i.h\"\n"
         "#include \"../m4145_module_guard.h\"\n",
         "Sub-GHz guard include"),
        ("    FURI_LOG_D(\n        TAG,\n        \"heap before alloc: internal=%zu spiram=%zu\",\n",
         "    if(!furi_hal_subghz_is_connected()) {\n"
         "        m4145_show_module_notice(\n"
         "            \"CC1101 not detected\",\n"
         "            \"CC1101 wiring required:\\nSCK 9, MOSI 10, MISO 21,\\nCSN TX/GPIO43, GDO0 13.\",\n"
         "            NULL,\n"
         "            \"OK\");\n"
         "        return -1;\n"
         "    }\n\n"
         "    FURI_LOG_D(\n        TAG,\n        \"heap before alloc: internal=%zu spiram=%zu\",\n",
         "Sub-GHz runtime module guard"),
    ])

    patch_file(root, "applications/main/nfc/nfc_app.c", [
        ("        // No connection to the chip, show an error screen\n",
         "        // No connection to the module, show the exact required hardware and wiring.\n",
         "NFC missing-module comment"),
        ("        dialog_message_set_header(message, \"Error: NFC Chip Failed\", 64, 0, AlignCenter, AlignTop);\n"
         "        dialog_message_set_text(\n"
         "            message, \"Send error photo via\\nsupport.flipper.net\", 0, 63, AlignLeft, AlignBottom);\n",
         "        dialog_message_set_header(message, \"PN532 not detected\", 64, 0, AlignCenter, AlignTop);\n"
         "        dialog_message_set_text(\n"
         "            message,\n"
         "            \"Needs PN532 V3 in I2C mode.\\nSDA GPIO41, SCL GPIO42.\\nCheck 3V3 and GND.\",\n"
         "            2, 20, AlignLeft, AlignTop);\n",
         "NFC exact module notice"),
    ])

    patch_file(root, "applications/main/nrf24/nrf24_app.c", [
        ("#include \"nrf24_app.h\"\n",
         "#include \"nrf24_app.h\"\n"
         "#include \"nrf24_hw.h\"\n"
         "#include \"../m4145_module_guard.h\"\n",
         "nRF24 guard includes"),
        ("    Nrf24App* app = nrf24_app_alloc();\n",
         "    nrf24_hw_init();\n"
         "    nrf24_hw_acquire();\n"
         "    bool module_detected = nrf24_hw_probe();\n"
         "    nrf24_hw_power_down();\n"
         "    nrf24_hw_release();\n"
         "    nrf24_hw_deinit();\n"
         "    if(!module_detected) {\n"
        "        furi_hal_shared_pins_release(&owner);\n"
         "        m4145_show_module_notice(\n"
         "            \"nRF24L01+ not detected\",\n"
         "            \"Needs nRF24L01+ module.\\nSCK 41, MOSI 42, MISO 47,\\nCSN 1, CE 2; use 3.3V.\",\n"
         "            NULL,\n"
         "            \"OK\");\n"
         "        return -1;\n"
         "    }\n\n"
         "    Nrf24App* app = nrf24_app_alloc();\n",
         "nRF24 runtime SPI probe"),
    ])
    fam = root / "applications/main/nrf24/application.fam"
    fam_text = fam.read_text(encoding="utf-8")
    fam_text = replace_once(
        fam_text,
        "    entry_point=\"nrf24_app\",\n",
        "    entry_point=\"nrf24_app\",\n"
        "    requires=[\"gui\", \"dialogs\"],\n",
        "nRF24 dialog dependency",
    )
    fam.write_text(fam_text, encoding="utf-8")

    patch_file(root, "applications/main/infrared/infrared_app.c", [
        ("#include \"infrared_app_i.h\"\n",
         "#include \"infrared_app_i.h\"\n"
         "#include \"../m4145_module_guard.h\"\n",
         "Infrared guard include"),
        ("int32_t infrared_app(void* p) {\n"
         "    InfraredApp* infrared = infrared_alloc();\n",
         "int32_t infrared_app(void* p) {\n"
         "    if(m4145_show_module_notice(\n"
         "           \"IR hardware check\",\n"
         "           \"IR has no module ID pin.\\nNeeds an IR LED + driver on TX GPIO1\\nand a 38kHz receiver on RX GPIO2.\",\n"
         "           \"Back\",\n"
         "           \"Continue\") != DialogMessageButtonRight) {\n"
         "        return -1;\n"
         "    }\n"
         "    InfraredApp* infrared = infrared_alloc();\n",
         "Infrared physical module confirmation"),
    ])

    patch_file(root, "applications/main/lfrfid/lfrfid.c", [
        ("#include \"lfrfid_i.h\"\n",
         "#include \"lfrfid_i.h\"\n"
         "#include \"../m4145_module_guard.h\"\n",
         "LF RFID guard include"),
        ("int32_t lfrfid_app(void* p) {\n"
         "    LfRfid* app = lfrfid_alloc();\n",
         "int32_t lfrfid_app(void* p) {\n"
         "    if(m4145_show_module_notice(\n"
         "           \"LF RFID reader check\",\n"
         "           \"Read module: RDM6300 125kHz.\\nUse an EM4100 card to confirm it.\\nThis reader cannot write or emulate.\",\n"
         "           \"Back\",\n"
         "           \"Continue\") != DialogMessageButtonRight) {\n"
         "        return -1;\n"
         "    }\n"
         "    LfRfid* app = lfrfid_alloc();\n",
         "LF RFID exact module confirmation"),
    ])

    patch_file(root, "applications/main/lfrfid/scenes/lfrfid_scene_saved_key_menu.c", [
        ("#include \"../lfrfid_i.h\"\n",
         "#include \"../lfrfid_i.h\"\n"
         "#include \"../../m4145_module_guard.h\"\n",
         "LF saved menu guard include"),
        ("        if(event.event == SubmenuIndexEmulate) {\n"
         "            scene_manager_next_scene(app->scene_manager, LfRfidSceneEmulate);\n"
         "            dolphin_deed(DolphinDeedRfidEmulate);\n"
         "            consumed = true;\n"
         "        } else if(event.event == SubmenuIndexWrite) {\n"
         "            scene_manager_next_scene(app->scene_manager, LfRfidSceneWrite);\n"
         "            consumed = true;\n",
         "        if(event.event == SubmenuIndexEmulate) {\n"
         "            m4145_show_module_notice(\n"
         "                \"LF emulation unavailable\",\n"
         "                \"RDM6300 is read-only.\\nNeeds a 125kHz transmit coil/front-end\\nand a matching ESP32 driver.\",\n"
         "                NULL,\n"
         "                \"OK\");\n"
         "            consumed = true;\n"
         "        } else if(event.event == SubmenuIndexWrite) {\n"
         "            m4145_show_module_notice(\n"
         "                \"LF writing unavailable\",\n"
         "                \"RDM6300 cannot write.\\nNeeds a compatible 125kHz writer,\\nrewritable tag, and ESP32 driver.\",\n"
         "                NULL,\n"
         "                \"OK\");\n"
         "            consumed = true;\n",
         "block unsupported LF write and emulate"),
        ("        } else if(event.event == SubmenuIndexWriteAndSetPass) {\n"
         "            scene_manager_set_scene_state(\n"
         "                app->scene_manager, LfRfidSceneEnterPassword, LfRfidSceneWriteAndSetPass);\n"
         "            scene_manager_next_scene(app->scene_manager, LfRfidSceneEnterPassword);\n"
         "            consumed = true;\n",
         "        } else if(event.event == SubmenuIndexWriteAndSetPass) {\n"
         "            m4145_show_module_notice(\n"
         "                \"LF writing unavailable\",\n"
         "                \"Password writing needs a compatible\\n125kHz writer and ESP32 driver.\\nRDM6300 is read-only.\",\n"
         "                NULL,\n"
         "                \"OK\");\n"
         "            consumed = true;\n",
         "block unsupported LF password write"),
    ])

    patch_file(root, "applications/main/lfrfid/scenes/lfrfid_scene_extra_actions.c", [
        ("#include \"../lfrfid_i.h\"\n",
         "#include \"../lfrfid_i.h\"\n"
         "#include \"../../m4145_module_guard.h\"\n",
         "LF extra actions guard include"),
        ("        } else if(event.event == SubmenuIndexClearT5577) {\n"
         "            scene_manager_set_scene_state(\n"
         "                app->scene_manager, LfRfidSceneEnterPassword, LfRfidSceneClearT5577Confirm);\n"
         "            scene_manager_next_scene(app->scene_manager, LfRfidSceneEnterPassword);\n"
         "            consumed = true;\n",
         "        } else if(event.event == SubmenuIndexClearT5577) {\n"
         "            m4145_show_module_notice(\n"
         "                \"T5577 writer unavailable\",\n"
         "                \"This build has no LF writer.\\nNeeds a compatible T5577 writer\\nand its ESP32 driver.\",\n"
         "                NULL,\n"
         "                \"OK\");\n"
         "            consumed = true;\n",
         "block unsupported T5577 write"),
        ("        } else if(event.event == SubmenuIndexRAWEmulate) {\n"
         "            scene_manager_next_scene(app->scene_manager, LfRfidSceneSelectRawKey);\n"
         "            consumed = true;\n",
         "        } else if(event.event == SubmenuIndexRAWEmulate) {\n"
         "            m4145_show_module_notice(\n"
         "                \"RAW emulation unavailable\",\n"
         "                \"Needs a 125kHz transmit coil/front-end\\nand an ESP32 emulation driver.\",\n"
         "                NULL,\n"
         "                \"OK\");\n"
         "            consumed = true;\n",
         "block unsupported raw emulation"),
    ])


def patch_about(root):
    patch_file(root, "applications/settings/about/about.c", [
        ("#include <furi_hal_info.h>\n",
         "#include <furi_hal_info.h>\n"
         "#include <furi_hal_subghz.h>\n",
         "module status HAL includes"),
        ("static DialogMessageButton fw_version_screen(DialogsApp* dialogs, DialogMessage* message) {\n",
         "static DialogMessageButton module_status_screen(DialogsApp* dialogs, DialogMessage* message) {\n"
         "    const bool cc1101 = furi_hal_subghz_is_connected();\n"
         "    FuriString* text = furi_string_alloc_printf(\n"
         "        \"CC1101: %s\\nnRF24: open app to test\\n\"\n"
         "        \"PN532 / IR / LF RFID: not in this test build\\n\"\n"
         "        \"iButton: not supported\",\n"
         "        cc1101 ? \"detected\" : \"not detected\");\n"
         "    dialog_message_set_header(message, \"Module status\", 0, 0, AlignLeft, AlignTop);\n"
         "    dialog_message_set_text(message, furi_string_get_cstr(text), 0, 13, AlignLeft, AlignTop);\n"
         "    DialogMessageButton result = dialog_message_show(dialogs, message);\n"
         "    dialog_message_set_header(message, NULL, 0, 0, AlignLeft, AlignTop);\n"
         "    dialog_message_set_text(message, NULL, 0, 0, AlignLeft, AlignTop);\n"
         "    furi_string_free(text);\n"
         "    return result;\n"
         "}\n\n"
         "static DialogMessageButton fw_version_screen(DialogsApp* dialogs, DialogMessage* message) {\n",
         "module runtime status page"),
        ("    fw_version_screen};\n",
         "    fw_version_screen,\n"
         "    module_status_screen};\n",
         "append module status page"),
    ])


def patch_nrf24_passive_test_menu(root):
    """Keep the bring-up menu to chip detection and passive channel survey."""
    path = root / "applications/main/nrf24/scenes/scene_menu.c"
    text = path.read_text(encoding="utf-8")
    if "Passive 2.4 GHz Survey" in text:
        return
    replacement = '''#include "../nrf24_app.h"

enum SubmenuIndex {
    SubmenuIndexPassiveSurvey,
};

static void nrf24_scene_menu_submenu_callback(void* context, uint32_t index) {
    Nrf24App* app = context;
    view_dispatcher_send_custom_event(app->view_dispatcher, index);
}

void nrf24_app_scene_menu_on_enter(void* context) {
    Nrf24App* app = context;
    submenu_add_item(
        app->submenu,
        "Passive 2.4 GHz Survey",
        SubmenuIndexPassiveSurvey,
        nrf24_scene_menu_submenu_callback,
        app);
    view_dispatcher_switch_to_view(app->view_dispatcher, Nrf24ViewSubmenu);
}

bool nrf24_app_scene_menu_on_event(void* context, SceneManagerEvent event) {
    Nrf24App* app = context;
    if(event.type == SceneManagerEventTypeCustom && event.event == SubmenuIndexPassiveSurvey) {
        scene_manager_next_scene(app->scene_manager, Nrf24AppSceneSpectrum);
        return true;
    }
    return false;
}

void nrf24_app_scene_menu_on_exit(void* context) {
    Nrf24App* app = context;
    submenu_reset(app->submenu);
}
'''
    if "SubmenuIndexMouseJacker" not in text or "SubmenuIndexJammer" not in text:
        raise ValueError("nRF24 test menu source differs from the expected upstream menu")
    path.write_text(replacement, encoding="utf-8")


def patch_radio_bringup_profile(root):
    """Keep the hardware test image to passive radio checks and surveys."""
    patch_file(root, "fam_config.py", [
        ("EXTRA_EXT_APPS = []\n",
         "EXTRA_EXT_APPS = []\n\n"
         "# M4145 hardware bring-up profile: omit active Wi-Fi/BLE disruption apps.\n"
         "APPS = [app for app in APPS if app not in (\"wlan\", \"ble_spam\")]\n",
         "passive-only bring-up app filter"),
    ])

    cmake_path = root / "CMakeLists.txt"
    cmake = cmake_path.read_text(encoding="utf-8")
    start_marker = (
        "# ---------------------------------------------------------------------------\n"
        "# Patch libnet80211.a to allow raw TX of deauth/disassoc management frames."
    )
    end_marker = (
        "# ---------------------------------------------------------------------------\n"
        "# App-Descriptor-Version"
    )
    if start_marker in cmake:
        start = cmake.index(start_marker)
        end = cmake.find(end_marker, start)
        if end < 0:
            raise ValueError("Wi-Fi raw-TX patch block has no ending anchor")
        cmake = (
            cmake[:start]
            + "# M4145 ST7735S bring-up keeps the ESP-IDF Wi-Fi raw-TX guard intact.\n"
            + cmake[end:]
        )
    elif "M4145 ST7735S bring-up keeps the ESP-IDF Wi-Fi raw-TX guard intact." not in cmake:
        raise ValueError("Wi-Fi raw-TX patch block or safe-profile marker is missing")

    cmake = replace_once(
        cmake,
        "include(cmake/wifite_sdk_adapter.cmake)\n",
        "# WPS PIN attack adapter is omitted from the M4145 hardware bring-up image.\n",
        "disable WPS attack adapter",
    )
    cmake_path.write_text(cmake, encoding="utf-8")

    # Wifite is an attack stack (including WPS/Pixie Dust workflows), not a
    # prerequisite for ordinary Wi-Fi scanning or connection. Removing the
    # app alone leaves its SDK bridge symbols in the Wi-Fi component, so omit
    # the attack sources from the firmware image as well. The port's exported
    # FAP API still names the Wifite functions, so retain inert stubs only.
    stubs = root / "components/wifi/m4145_safe_profile_stubs.c"
    stubs_source = '''/* Safe bring-up stubs for unused attack-only firmware API entries. */
#include <stddef.h>
#include "wlan_hal.h"
#include "wifite.h"

WifiteJob* wifite_start(WifiteMode mode, const WfTarget* target, const char* pin) {
    (void)mode;
    (void)target;
    (void)pin;
    return NULL;
}

bool wifite_poll(WifiteJob* job, WifiteEvent* event) {
    (void)job;
    (void)event;
    return false;
}

void wifite_cancel(WifiteJob* job) {
    (void)job;
}

bool wifite_finished(WifiteJob* job) {
    (void)job;
    return true;
}

void wifite_free(WifiteJob* job) {
    (void)job;
}

bool wlan_hal_evil_portal_is_running(void) {
    return false;
}
'''
    if not stubs.exists():
        stubs.write_text(stubs_source, encoding="utf-8")
    elif stubs.read_text(encoding="utf-8") != stubs_source:
        raise ValueError("safe bring-up stub file exists with unexpected contents")

    patch_file(root, "components/wifi/CMakeLists.txt", [
        ('        "wifite/core.c"\n'
         '        "wifite/pixie.c"\n'
         '        "wifite/radio.c"\n'
         '        "wifite/link.c"\n',
         '        "m4145_safe_profile_stubs.c"\n',
         "exclude Wifite/WPS attack stack from Wi-Fi component"),
    ])

    # Streaming reuses only the generic LAN list view from the Wi-Fi app.
    # Compile that view directly so its UI stays available without including
    # the Wi-Fi attack app and its scenes.
    patch_file(root, "applications/main/streaming/application.fam", [
        ('    entry_point="streaming_app",\n',
         '    entry_point="streaming_app",\n'
         '    sources=["*.c*", "../wlan_app/views/wlan_lan_view.c",\n'
         '             "../wlan_app/views/wlan_view_common.c"],\n',
         "bundle generic LAN view with Streaming"),
    ])


def patch(root):
    header = root / "applications/main/m4145_module_guard.h"
    if not header.exists():
        header.write_text(
            """#pragma once

#include <furi.h>
#include <dialogs/dialogs.h>
static inline DialogMessageButton m4145_show_module_notice(
    const char* title,
    const char* details,
    const char* left_button,
    const char* right_button) {
    DialogsApp* dialogs = furi_record_open(RECORD_DIALOGS);
    DialogMessage* message = dialog_message_alloc();
    dialog_message_set_header(message, title, 64, 2, AlignCenter, AlignTop);
    dialog_message_set_text(message, details, 2, 15, AlignLeft, AlignTop);
    dialog_message_set_buttons(message, left_button, NULL, right_button);
    const DialogMessageButton result = dialog_message_show(dialogs, message);
    dialog_message_free(message);
    furi_record_close(RECORD_DIALOGS);
    return result;
}
""",
            encoding="utf-8",
        )
    helper_text = header.read_text(encoding="utf-8")
    helper_text = helper_text.replace("#include <dialogs/dialog_message.h>\n", "")
    header.write_text(helper_text, encoding="utf-8")
    patch_pairing_layout(root)
    patch_keyboard(root)
    patch_subghz(root)
    patch_rfid(root)
    patch_lfrfid_view(root)
    patch_app_guards(root)
    patch_about(root)
    patch_nrf24_passive_test_menu(root)
    patch_radio_bringup_profile(root)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    args = parser.parse_args()
    patch(args.source)


if __name__ == "__main__":
    main()
