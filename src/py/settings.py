from pyscript import when

PENDING_THEME = None
PENDING_SIDEBAR_EDGE_HOVER = True


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


def normalize_sidebar_edge_hover(value):
    if isinstance(value, bool):
        return value

    return True


def set_sidebar_edge_hover_switch_value(is_enabled):
    sidebar_edge_hover_switch = get("settings-sidebar-edge-hover-switch")  # ty:ignore[unresolved-reference]  # noqa: F821
    if not sidebar_edge_hover_switch:
        return

    normalized_value = normalize_sidebar_edge_hover(is_enabled)
    sidebar_edge_hover_switch.checked = normalized_value
    sidebar_edge_hover_switch.ariaChecked = "true" if normalized_value else "false"


async def sync_theme_select_state():
    global PENDING_THEME

    current_theme = await read_saved_theme()  # ty:ignore[unresolved-reference]  # noqa: F821
    PENDING_THEME = normalize_theme(current_theme)
    set_theme_select_value(PENDING_THEME)


async def sync_sidebar_edge_hover_switch_state():
    global PENDING_SIDEBAR_EDGE_HOVER

    current_value = await read_sidebar_edge_hover_enabled()  # ty:ignore[unresolved-reference]  # noqa: F821
    PENDING_SIDEBAR_EDGE_HOVER = normalize_sidebar_edge_hover(current_value)
    set_sidebar_edge_hover_switch_value(PENDING_SIDEBAR_EDGE_HOVER)


async def sync_settings_state():
    await sync_theme_select_state()
    await sync_sidebar_edge_hover_switch_state()


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
    global PENDING_THEME, PENDING_SIDEBAR_EDGE_HOVER

    trigger = get("sidebar-settings-menu-trigger")  # ty:ignore[unresolved-reference]  # noqa: F821
    dialog = get("sidebar-settings-dialog")  # ty:ignore[unresolved-reference]  # noqa: F821

    if dialog and dialog.returnValue == "save" and PENDING_THEME is not None:
        await set_theme(PENDING_THEME)  # ty:ignore[unresolved-reference]  # noqa: F821
        normalized_edge_hover = normalize_sidebar_edge_hover(PENDING_SIDEBAR_EDGE_HOVER)
        set_sidebar_edge_hover_enabled(normalized_edge_hover)  # ty:ignore[unresolved-reference]  # noqa: F821
        await set_setting("sidebar_edge_hover", normalized_edge_hover)  # ty:ignore[unresolved-reference]  # noqa: F821

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


@when("change", "#settings-sidebar-edge-hover-switch")
def on_sidebar_edge_hover_change(event):
    global PENDING_SIDEBAR_EDGE_HOVER

    is_enabled = bool(event.target and event.target.checked)
    PENDING_SIDEBAR_EDGE_HOVER = normalize_sidebar_edge_hover(is_enabled)
    set_sidebar_edge_hover_switch_value(PENDING_SIDEBAR_EDGE_HOVER)


def start():
    trigger = get("sidebar-settings-menu-trigger")  # ty:ignore[unresolved-reference]  # noqa: F821
    if not trigger:
        return

    trigger.ariaExpanded = "false"


start()
