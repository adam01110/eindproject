from pyscript import web, when, window

DEFAULT_THEME = "dark"
THEME_STORAGE_KEY = "theme"


def apply_theme(theme_value):
    root_matches = web.page.find("html")
    if not root_matches:
        return
    root = root_matches[0]

    if theme_value == "dark":
        root.classList.add("dark")
    else:
        root.classList.remove("dark")


def read_saved_theme():
    try:
        saved_theme = window.localStorage.getItem(THEME_STORAGE_KEY)
    except Exception:
        return DEFAULT_THEME

    return saved_theme if saved_theme == "light" else "dark"


def save_theme(theme_value):
    try:
        window.localStorage.setItem(THEME_STORAGE_KEY, theme_value)
    except Exception:
        return


def update_theme_toggle(theme_value):
    toggle_matches = web.page.find("[data-theme-toggle]")
    if not toggle_matches:
        return

    toggle_node = toggle_matches[0]
    if theme_value == "dark":
        toggle_node.ariaPressed = "true"
        toggle_node.ariaLabel = "Switch to light mode"
        toggle_node.innerHTML = (
            '<i class="icon-[tabler--moon] inline-block" aria-hidden="true"></i>'
        )
    else:
        toggle_node.ariaPressed = "false"
        toggle_node.ariaLabel = "Switch to dark mode"
        toggle_node.innerHTML = (
            '<i class="icon-[tabler--sun] inline-block" aria-hidden="true"></i>'
        )


def set_theme(theme_value):
    normalized_theme = (
        theme_value if theme_value in {"light", "dark"} else DEFAULT_THEME
    )
    apply_theme(normalized_theme)
    save_theme(normalized_theme)
    update_theme_toggle(normalized_theme)


@when("click", "[data-theme-toggle]")
def on_theme_toggle_click(_event):
    next_theme = "light" if read_saved_theme() == "dark" else "dark"
    set_theme(next_theme)


set_theme(read_saved_theme())
