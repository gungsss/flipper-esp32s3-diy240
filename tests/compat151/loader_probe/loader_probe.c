#include <furi.h>
#include <loader/loader.h>

/* Build/import probe only; the CI does not execute this application. */
int32_t loader_api_probe(void* context) {
    Loader* loader = furi_record_open(RECORD_LOADER);
    FuriString* path = furi_string_alloc();
    FuriString* name = furi_string_alloc();
    bool available = loader_get_application_name(loader, name);
    available |= loader_get_application_launch_path(loader, path);
    if(context) {
        available |= loader_signal(loader, 0, context);
        loader_enqueue_launch(loader, "test", NULL, LoaderDeferredLaunchFlagNone);
        loader_clear_launch_queue(loader);
    }
    furi_string_free(name);
    furi_string_free(path);
    furi_record_close(RECORD_LOADER);
    return available ? 0 : 1;
}
