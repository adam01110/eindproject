from pyscript import window
from pyscript.ffi import create_proxy

RESIZE_PROXY = None


def is_mobile_viewport():
    return window.innerWidth < 768


def sync_sidebar_controls(is_open):
    mobile_view = is_mobile_viewport()
    open_buttons = find("[data-sidebar-open]")  # ty:ignore[unresolved-reference]  # noqa: F821
    collapse_buttons = find("[data-sidebar-collapse]")  # ty:ignore[unresolved-reference]  # noqa: F821
    hidden_classes = [
        "invisible",
        "pointer-events-none",
        "md:invisible",
        "md:pointer-events-none",
    ]

    for button in open_buttons:
        hide_open_button = (not mobile_view) and is_open

        if hide_open_button:
            for class_name in hidden_classes:
                button.classList.add(class_name)
            button.ariaHidden = "true"
        else:
            for class_name in hidden_classes:
                button.classList.remove(class_name)
            button.ariaHidden = "false"

        button.ariaExpanded = "true" if is_open else "false"

    for button in collapse_buttons:
        button.hidden = mobile_view
        button.ariaExpanded = "true" if is_open else "false"


def set_sidebar_state(is_open):
    sidebar = get("app-sidebar")  # ty:ignore[unresolved-reference]  # noqa: F821
    if not sidebar:
        return

    sidebar.ariaHidden = "false" if is_open else "true"

    if is_open:
        sidebar.removeAttribute("inert")
    elif is_mobile_viewport():
        sidebar.setAttribute("inert", "")
    else:
        sidebar.removeAttribute("inert")

    sync_sidebar_controls(is_open)


def close_sidebar_on_mobile():
    if is_mobile_viewport():
        set_sidebar_state(False)


def sync_sidebar_for_viewport(_event=None):
    if is_mobile_viewport():
        close_sidebar_on_mobile()
        return

    set_sidebar_state(True)


def setup_sidebar_behavior():
    global RESIZE_PROXY

    RESIZE_PROXY = create_proxy(sync_sidebar_for_viewport)
    window.addEventListener("resize", RESIZE_PROXY)
    sync_sidebar_for_viewport()
