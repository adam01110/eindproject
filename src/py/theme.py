import asyncio

from lib import (
    add_proxy_listener,
    first,
    get,
    get_delegated_target,
    get_setting,
    set_setting,
)
from pyscript import document, window

DEFAULT_THEME = "dark"
THEME_SETUP_FLAG = "__eindproject_theme_setup__"
THEME_CLICK_PROXY = None


def read_active_theme():
    root = document.documentElement
    if not root:
        return DEFAULT_THEME

    class_name = str(root.getAttribute("class") or "")
    return "dark" if "dark" in class_name.split() else "light"


def normalize_theme(theme_value):
    return theme_value if theme_value in {"light", "dark"} else DEFAULT_THEME


def apply_theme(theme_value):
    root = document.documentElement
    if not root:
        return

    if normalize_theme(theme_value) == "dark":
        root.classList.add("dark")
    else:
        root.classList.remove("dark")


def dispatch_theme_change(theme_value):
    event = document.createEvent("Event")
    event.initEvent("app:themechange", True, True)
    event.theme = normalize_theme(theme_value)
    window.dispatchEvent(event)


async def read_saved_theme():
    saved_theme = await get_setting("theme", DEFAULT_THEME)
    return normalize_theme(saved_theme)


def update_theme_toggle(theme_value):
    toggle_node = first("[data-theme-toggle]")
    if not toggle_node:
        return

    if normalize_theme(theme_value) == "dark":
        toggle_node.setAttribute("aria-pressed", "true")
        toggle_node.setAttribute("aria-label", "Switch to light mode")
        toggle_node.dataset.tooltip = "Switch to light mode"
    else:
        toggle_node.setAttribute("aria-pressed", "false")
        toggle_node.setAttribute("aria-label", "Switch to dark mode")
        toggle_node.dataset.tooltip = "Switch to dark mode"


def update_theme_select(theme_value):
    theme_select = get("settings-theme-select")
    if not theme_select:
        return

    theme_select.value = normalize_theme(theme_value)


async def set_theme(theme_value, persist=True):
    normalized_theme = normalize_theme(theme_value)
    apply_theme(normalized_theme)
    update_theme_toggle(normalized_theme)
    update_theme_select(normalized_theme)
    dispatch_theme_change(normalized_theme)

    if persist:
        await set_setting("theme", normalized_theme)


async def toggle_theme():
    next_theme = "light" if read_active_theme() == "dark" else "dark"
    await set_theme(next_theme)


def on_document_click(event):
    if not get_delegated_target(event, "[data-theme-toggle]"):
        return

    asyncio.create_task(toggle_theme())


async def sync_saved_theme():
    saved_theme = await read_saved_theme()
    await set_theme(saved_theme, persist=False)


def start():
    global THEME_CLICK_PROXY

    if bool(getattr(window, THEME_SETUP_FLAG, False)):
        return

    setattr(window, THEME_SETUP_FLAG, True)
    THEME_CLICK_PROXY = add_proxy_listener(document, "click", on_document_click)
    asyncio.create_task(sync_saved_theme())


start()
