from pyscript import when

PENDING_THEME = None
PENDING_SIDEBAR_EDGE_HOVER = True


def normalize_theme(theme_value):
    return theme_value if theme_value in {"light", "dark"} else "dark"


def normalize_sidebar_edge_hover(value):
    return value if isinstance(value, bool) else True


def set_theme_select_value(theme_value):
    theme_select = get("settings-theme-select")  # ty:ignore[unresolved-reference]  # noqa: F821
    if not theme_select:
        return
    normalized = normalize_theme(theme_value)
    if hasattr(theme_select, "select"):
        theme_select.select(normalized)
    elif hasattr(theme_select, "value"):
        theme_select.value = normalized


def set_sidebar_edge_hover_switch_value(is_enabled):
    toggle = get("settings-sidebar-edge-hover-switch")  # ty:ignore[unresolved-reference]  # noqa: F821
    if not toggle:
        return
    enabled = normalize_sidebar_edge_hover(is_enabled)
    toggle.checked = enabled
    toggle.ariaChecked = "true" if enabled else "false"


async def sync_settings_state():
    global PENDING_THEME, PENDING_SIDEBAR_EDGE_HOVER
    PENDING_THEME = normalize_theme(await read_saved_theme())  # ty:ignore[unresolved-reference]  # noqa: F821
    PENDING_SIDEBAR_EDGE_HOVER = normalize_sidebar_edge_hover(
        await read_sidebar_edge_hover_enabled()  # ty:ignore[unresolved-reference]  # noqa: F821
    )
    set_theme_select_value(PENDING_THEME)
    set_sidebar_edge_hover_switch_value(PENDING_SIDEBAR_EDGE_HOVER)


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
        await sync_settings_state()
    set_dialog_open(not dialog.open)


@when("close", "#sidebar-settings-dialog")
async def on_settings_dialog_close(_event):
    trigger = get("sidebar-settings-menu-trigger")  # ty:ignore[unresolved-reference]  # noqa: F821
    dialog = get("sidebar-settings-dialog")  # ty:ignore[unresolved-reference]  # noqa: F821
    if dialog and dialog.returnValue == "save" and PENDING_THEME is not None:
        enabled = normalize_sidebar_edge_hover(PENDING_SIDEBAR_EDGE_HOVER)
        await set_theme(PENDING_THEME)  # ty:ignore[unresolved-reference]  # noqa: F821
        set_sidebar_edge_hover_enabled(enabled)  # ty:ignore[unresolved-reference]  # noqa: F821
        await set_setting("sidebar_edge_hover", enabled)  # ty:ignore[unresolved-reference]  # noqa: F821
    if trigger:
        trigger.ariaExpanded = "false"


@when("click", "#sidebar-settings-dialog")
def on_settings_dialog_click(event):
    dialog = get("sidebar-settings-dialog")  # ty:ignore[unresolved-reference]  # noqa: F821
    if dialog and event.target == dialog:
        dialog.close()


@when("change", "#settings-theme-select")
def on_theme_select_change(event):
    global PENDING_THEME
    detail = getattr(event, "detail", None)
    selected = detail.value if detail and hasattr(detail, "value") else None
    if selected is None and event.target and hasattr(event.target, "value"):
        selected = event.target.value
    PENDING_THEME = normalize_theme(selected)
    set_theme_select_value(PENDING_THEME)


@when("change", "#settings-sidebar-edge-hover-switch")
def on_sidebar_edge_hover_change(event):
    global PENDING_SIDEBAR_EDGE_HOVER
    PENDING_SIDEBAR_EDGE_HOVER = normalize_sidebar_edge_hover(
        bool(event.target and event.target.checked)
    )
    set_sidebar_edge_hover_switch_value(PENDING_SIDEBAR_EDGE_HOVER)


def start():
    trigger = get("sidebar-settings-menu-trigger")  # ty:ignore[unresolved-reference]  # noqa: F821
    if trigger:
        trigger.ariaExpanded = "false"


start()
