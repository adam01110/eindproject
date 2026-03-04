from pyscript import document, when
from pyscript.ffi import create_proxy

KEYDOWN_PROXY = None


def set_menu_open(is_open):
    trigger = get("sidebar-settings-menu-trigger")  # ty:ignore[unresolved-reference]  # noqa: F821
    popover = get("sidebar-settings-menu-popover")  # ty:ignore[unresolved-reference]  # noqa: F821

    if not trigger or not popover:
        return

    trigger.ariaExpanded = "true" if is_open else "false"
    popover.ariaHidden = "false" if is_open else "true"


@when("click", "#sidebar-settings-menu-trigger")
def on_settings_button_click(event):
    event.preventDefault()
    event.stopPropagation()

    trigger = get("sidebar-settings-menu-trigger")  # ty:ignore[unresolved-reference]  # noqa: F821
    if not trigger:
        return

    should_open = trigger.ariaExpanded != "true"
    set_menu_open(should_open)


@when("click", "body")
def on_body_click(event):
    menu_root = get("sidebar-settings-menu")  # ty:ignore[unresolved-reference]  # noqa: F821
    if not menu_root:
        return

    target = event.target
    if target and menu_root.contains(target):
        return

    set_menu_open(False)


def on_keydown(event):
    if event.key == "Escape":
        set_menu_open(False)


def start():
    global KEYDOWN_PROXY

    KEYDOWN_PROXY = create_proxy(on_keydown)
    document.addEventListener("keydown", KEYDOWN_PROXY)
    set_menu_open(False)


start()
