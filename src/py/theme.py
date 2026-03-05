import asyncio

from pyscript import when

DEFAULT_THEME = "dark"


def normalize_theme(theme_value):
    return theme_value if theme_value in {"light", "dark"} else DEFAULT_THEME


def apply_theme(theme_value):
    root = first("html")  # ty:ignore[unresolved-reference]  # noqa: F821
    if not root:
        return

    if normalize_theme(theme_value) == "dark":
        root.classList.add("dark")
    else:
        root.classList.remove("dark")


async def read_saved_theme():
    saved_theme = await get_setting("theme", DEFAULT_THEME)  # ty:ignore[unresolved-reference]  # noqa: F821
    return normalize_theme(saved_theme)


def update_theme_toggle(theme_value):
    toggle_node = first("[data-theme-toggle]")  # ty:ignore[unresolved-reference]  # noqa: F821
    if not toggle_node:
        return

    if normalize_theme(theme_value) == "dark":
        toggle_node.ariaPressed = "true"
        toggle_node.ariaLabel = "Switch to light mode"
        toggle_node.dataset.tooltip = "Switch to light mode"
    else:
        toggle_node.ariaPressed = "false"
        toggle_node.ariaLabel = "Switch to dark mode"
        toggle_node.dataset.tooltip = "Switch to dark mode"


def update_theme_select(theme_value):
    theme_select = get("settings-theme-select")  # ty:ignore[unresolved-reference]  # noqa: F821
    if not theme_select:
        return

    theme_select.value = normalize_theme(theme_value)


async def set_theme(theme_value, persist=True):
    normalized_theme = normalize_theme(theme_value)
    apply_theme(normalized_theme)
    update_theme_toggle(normalized_theme)
    update_theme_select(normalized_theme)

    if persist:
        await set_setting("theme", normalized_theme)  # ty:ignore[unresolved-reference]  # noqa: F821


@when("click", "[data-theme-toggle]")
async def on_theme_toggle_click(_event):
    root = first("html")  # ty:ignore[unresolved-reference]  # noqa: F821
    is_dark = bool(root and root.classList.contains("dark"))
    next_theme = "light" if is_dark else "dark"
    await set_theme(next_theme)


async def start():
    saved_theme = await read_saved_theme()
    await set_theme(saved_theme, persist=False)


asyncio.create_task(start())
