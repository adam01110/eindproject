from pyscript import when


def sync_placeholder_switch_state():
    placeholder_toggle = get("settings-placeholder-toggle")  # ty:ignore[unresolved-reference]  # noqa: F821
    if not placeholder_toggle:
        return

    placeholder_toggle.ariaChecked = "true" if placeholder_toggle.checked else "false"


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
def on_settings_button_click(event):
    event.preventDefault()

    dialog = get("sidebar-settings-dialog")  # ty:ignore[unresolved-reference]  # noqa: F821
    if not dialog:
        return

    set_dialog_open(not dialog.open)


@when("close", "#sidebar-settings-dialog")
def on_settings_dialog_close(_event):
    trigger = get("sidebar-settings-menu-trigger")  # ty:ignore[unresolved-reference]  # noqa: F821
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


@when("change", "#settings-placeholder-toggle")
def on_placeholder_switch_change(_event):
    sync_placeholder_switch_state()


def start():
    trigger = get("sidebar-settings-menu-trigger")  # ty:ignore[unresolved-reference]  # noqa: F821
    if not trigger:
        return

    trigger.ariaExpanded = "false"
    sync_placeholder_switch_state()


start()
