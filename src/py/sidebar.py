import asyncio

from pyscript import window
from pyscript.ffi import create_proxy

SIDEBAR_EDGE_HOVER_SETTING_KEY = "sidebar_edge_hover"
SIDEBAR_EDGE_HOVER_TRIGGER_PX = 12
SIDEBAR_EDGE_HOVER_CLOSE_BUFFER_PX = 16

RESIZE_PROXY = None
POINTER_MOVE_PROXY = None
DOCUMENT_CLICK_PROXY = None
EDGE_HOVER_ENABLED = True
EDGE_HOVER_OPEN = False


def is_mobile_viewport():
    return window.innerWidth < 768


def sync_sidebar_controls(is_open):
    mobile_view = is_mobile_viewport()
    open_buttons = find("[data-sidebar-open]")  # ty:ignore[unresolved-reference]  # noqa: F821
    collapse_buttons = find("[data-sidebar-collapse]")  # ty:ignore[unresolved-reference]  # noqa: F821
    pin_buttons = find("[data-sidebar-pin]")  # ty:ignore[unresolved-reference]  # noqa: F821
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
        button.hidden = mobile_view or EDGE_HOVER_OPEN
        button.ariaHidden = "true" if (mobile_view or EDGE_HOVER_OPEN) else "false"
        button.ariaExpanded = "true" if is_open else "false"

    for button in pin_buttons:
        should_show_pin = (not mobile_view) and is_open and EDGE_HOVER_OPEN
        button.hidden = not should_show_pin
        button.ariaHidden = "false" if should_show_pin else "true"
        button.ariaExpanded = "true" if is_open else "false"


def normalize_sidebar_edge_hover(value):
    if isinstance(value, bool):
        return value

    return True


def set_sidebar_edge_hover_enabled(is_enabled):
    global EDGE_HOVER_ENABLED
    EDGE_HOVER_ENABLED = normalize_sidebar_edge_hover(is_enabled)

    if not EDGE_HOVER_ENABLED:
        close_temporary_edge_hover_sidebar()


async def read_sidebar_edge_hover_enabled():
    setting_value = await get_setting(SIDEBAR_EDGE_HOVER_SETTING_KEY, True)  # ty:ignore[unresolved-reference]  # noqa: F821
    return normalize_sidebar_edge_hover(setting_value)


async def sync_sidebar_edge_hover_state():
    is_enabled = await read_sidebar_edge_hover_enabled()
    set_sidebar_edge_hover_enabled(is_enabled)


def close_temporary_edge_hover_sidebar():
    global EDGE_HOVER_OPEN

    if not EDGE_HOVER_OPEN:
        return

    EDGE_HOVER_OPEN = False
    set_sidebar_state(False, temporary=True)


def on_pointer_move(event):
    global EDGE_HOVER_OPEN

    if is_mobile_viewport() or not EDGE_HOVER_ENABLED:
        close_temporary_edge_hover_sidebar()
        return

    pointer_x = getattr(event, "clientX", None)
    pointer_y = getattr(event, "clientY", None)

    if pointer_x is None or pointer_y is None:
        return

    sidebar = get("app-sidebar")  # ty:ignore[unresolved-reference]  # noqa: F821
    if not sidebar:
        return

    sidebar_is_open = sidebar.ariaHidden != "true"

    if not sidebar_is_open:
        if pointer_x <= SIDEBAR_EDGE_HOVER_TRIGGER_PX:
            EDGE_HOVER_OPEN = True
            set_sidebar_state(True, temporary=True)
        return

    if not EDGE_HOVER_OPEN:
        return

    sidebar_nav = first("#app-sidebar > nav")  # noqa: F821
    if not sidebar_nav:
        close_temporary_edge_hover_sidebar()
        return

    bounds = sidebar_nav.getBoundingClientRect()
    near_left_edge = pointer_x <= SIDEBAR_EDGE_HOVER_TRIGGER_PX
    inside_sidebar_x = (
        bounds.left <= pointer_x <= (bounds.right + SIDEBAR_EDGE_HOVER_CLOSE_BUFFER_PX)
    )
    inside_sidebar_y = bounds.top <= pointer_y <= bounds.bottom

    if near_left_edge or (inside_sidebar_x and inside_sidebar_y):
        return

    close_temporary_edge_hover_sidebar()


def on_document_click(event):
    if not is_mobile_viewport():
        return

    sidebar = get("app-sidebar")  # ty:ignore[unresolved-reference]  # noqa: F821
    if not sidebar or sidebar.ariaHidden == "true":
        return

    target = getattr(event, "target", None)
    if not target:
        return

    target_closest = getattr(target, "closest", None)
    if target_closest and target.closest("[data-sidebar-open]"):
        return

    sidebar_nav = first("#app-sidebar > nav")  # ty:ignore[unresolved-reference]  # noqa: F821
    if sidebar_nav and sidebar_nav.contains(target):
        return

    if sidebar_nav and target == sidebar:
        pointer_x = getattr(event, "clientX", None)
        pointer_y = getattr(event, "clientY", None)

        if pointer_x is not None and pointer_y is not None:
            bounds = sidebar_nav.getBoundingClientRect()
            clicked_inside_nav = (
                bounds.left <= pointer_x <= bounds.right
                and bounds.top <= pointer_y <= bounds.bottom
            )
            if clicked_inside_nav:
                return

    set_sidebar_state(False)


def set_sidebar_state(is_open, temporary=False):
    global EDGE_HOVER_OPEN

    if not temporary:
        EDGE_HOVER_OPEN = False

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
        close_temporary_edge_hover_sidebar()
        close_sidebar_on_mobile()
        return

    set_sidebar_state(True)


def setup_sidebar_behavior():
    global RESIZE_PROXY, POINTER_MOVE_PROXY, DOCUMENT_CLICK_PROXY

    RESIZE_PROXY = create_proxy(sync_sidebar_for_viewport)
    window.addEventListener("resize", RESIZE_PROXY)
    POINTER_MOVE_PROXY = create_proxy(on_pointer_move)
    window.addEventListener("pointermove", POINTER_MOVE_PROXY)
    DOCUMENT_CLICK_PROXY = create_proxy(on_document_click)
    window.addEventListener("click", DOCUMENT_CLICK_PROXY)
    asyncio.create_task(sync_sidebar_edge_hover_state())
    sync_sidebar_for_viewport()
