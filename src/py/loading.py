from pyscript.ffi import create_proxy

LOADING_BADGE_ID = "pyscript-loading"
LOADING_HIDE_EVENTS = ("py:ready", "py:done")
BADGE_HIDE_PROXIES = []
BADGE_REMOVED = False


def hide_loading_badge(_event=None):
    global BADGE_REMOVED

    badge = get(LOADING_BADGE_ID)  # ty:ignore[unresolved-reference]  # noqa: F821
    if BADGE_REMOVED or not badge:
        return

    badge.remove()
    BADGE_REMOVED = True


def start():
    root = first("html")  # ty:ignore[unresolved-reference]  # noqa: F821
    if not root:
        return

    for loading_event in LOADING_HIDE_EVENTS:
        hide_proxy = create_proxy(hide_loading_badge)
        BADGE_HIDE_PROXIES.append(hide_proxy)
        root.addEventListener(loading_event, hide_proxy)


start()
