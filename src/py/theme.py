from pyscript import web, when, window

page = web.page

DEFAULT_THEME = "dark"
THEME_STORAGE_KEY = "theme"
CURRENT_THEME = DEFAULT_THEME


def normalize_theme(theme_value):
    if theme_value in {"light", "dark"}:
        return theme_value
    return DEFAULT_THEME


def apply_theme(theme_value):
    root = window.document.documentElement
    if root is None:
        return

    if theme_value == "dark":
        root.classList.add("dark")
    else:
        root.classList.remove("dark")


def read_saved_theme():
    try:
        saved_theme = window.localStorage.getItem(THEME_STORAGE_KEY)
    except Exception:
        return DEFAULT_THEME

    return normalize_theme(saved_theme)


def save_theme(theme_value):
    try:
        window.localStorage.setItem(THEME_STORAGE_KEY, theme_value)
    except Exception:
        return


def update_theme_toggle(theme_value):
    toggle_matches = page.find("[data-theme-toggle]")
    if not toggle_matches:
        return

    toggle_node = toggle_matches[0]
    if theme_value == "dark":
        toggle_node.ariaPressed = "true"
        toggle_node.ariaLabel = "Switch to light mode"
        toggle_node.innerHTML = '<i class="icon-[tabler--moon] inline-block" aria-hidden="true"></i>'
    else:
        toggle_node.ariaPressed = "false"
        toggle_node.ariaLabel = "Switch to dark mode"
        toggle_node.innerHTML = '<i class="icon-[tabler--sun] inline-block" aria-hidden="true"></i>'


def set_theme(theme_value):
    global CURRENT_THEME

    normalized_theme = normalize_theme(theme_value)
    CURRENT_THEME = normalized_theme
    apply_theme(normalized_theme)
    save_theme(normalized_theme)
    update_theme_toggle(normalized_theme)


@when("click", "[data-theme-toggle]")
def on_theme_toggle_click(_event):
    next_theme = "light" if CURRENT_THEME == "dark" else "dark"
    set_theme(next_theme)


def start():
    set_theme(read_saved_theme())


start()
