import asyncio

from pyscript import when

PENDING_THEME = None


def normalize_theme(theme_value):
    return theme_value if theme_value in {"light", "dark"} else "dark"


def set_theme_select_value(theme_value):
    theme_select = get("settings-theme-select")  # ty:ignore[unresolved-reference]  # noqa: F821
    if not theme_select:
        return

    normalized_theme = normalize_theme(theme_value)

    if hasattr(theme_select, "select"):
        theme_select.select(normalized_theme)
        return

    if hasattr(theme_select, "value"):
        theme_select.value = normalized_theme


async def sync_theme_select_state():
    global PENDING_THEME

    current_theme = await read_saved_theme()  # ty:ignore[unresolved-reference]  # noqa: F821
    PENDING_THEME = normalize_theme(current_theme)
    set_theme_select_value(PENDING_THEME)


def set_dialog_open(is_open):
    trigger = get("sidebar-settings-menu-trigger")  # ty:ignore[unresolved-reference]  # noqa: F821
    dialog = get("sidebar-settings-dialog")  # ty:ignore[unresolved-reference]  # noqa: F821

    if not trigger or not dialog:
        return

    if is_open:
        dialog.showModal()
    else:
        dialog.close()

    trigger.ariaExpanded = "true" if is_open else "false"


@when("click", "#sidebar-settings-menu-trigger")
async def on_settings_button_click(event):
    event.preventDefault()

    dialog = get("sidebar-settings-dialog")  # ty:ignore[unresolved-reference]  # noqa: F821
    if not dialog:
        return

    if not dialog.open:
        await sync_theme_select_state()

    set_dialog_open(not dialog.open)


@when("close", "#sidebar-settings-dialog")
async def on_settings_dialog_close(_event):
    global PENDING_THEME

    trigger = get("sidebar-settings-menu-trigger")  # ty:ignore[unresolved-reference]  # noqa: F821
    dialog = get("sidebar-settings-dialog")  # ty:ignore[unresolved-reference]  # noqa: F821

    if dialog and dialog.returnValue == "save" and PENDING_THEME is not None:
        await set_theme(PENDING_THEME)  # ty:ignore[unresolved-reference]  # noqa: F821

    if not trigger:
        return

    trigger.ariaExpanded = "false"


@when("click", "#sidebar-settings-dialog")
def on_settings_dialog_click(event):
    dialog = get("sidebar-settings-dialog")  # ty:ignore[unresolved-reference]  # noqa: F821
    if not dialog:
        return

    if event.target == dialog:
        dialog.close()


@when("change", "#settings-theme-select")
def on_theme_select_change(event):
    global PENDING_THEME

    selected_value = None
    detail = getattr(event, "detail", None)

    if detail and hasattr(detail, "value"):
        selected_value = detail.value
    elif event.target and hasattr(event.target, "value"):
        selected_value = event.target.value

    PENDING_THEME = normalize_theme(selected_value)
    set_theme_select_value(PENDING_THEME)


def start():
    trigger = get("sidebar-settings-menu-trigger")  # ty:ignore[unresolved-reference]  # noqa: F821
    if not trigger:
        return

    trigger.ariaExpanded = "false"
    asyncio.create_task(sync_theme_select_state())


start()
