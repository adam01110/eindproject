from pyscript import web
from pyscript.ffi import create_proxy

LOADING_BADGE_ID = "pyscript-loading"
LOADING_HIDE_EVENTS = ("py:ready", "py:done")
BADGE_HIDE_PROXIES = []
BADGE_REMOVED = False


def hide_loading_badge(_event=None):
    global BADGE_REMOVED

    if BADGE_REMOVED or not (badge_matches := web.page.find(f"#{LOADING_BADGE_ID}")):
        return

    badge_matches[0].remove()
    BADGE_REMOVED = True


def start():
    root_matches = web.page.find("html")
    if not root_matches:
        return

    root = root_matches[0]
    for loading_event in LOADING_HIDE_EVENTS:
        hide_proxy = create_proxy(hide_loading_badge)
        BADGE_HIDE_PROXIES.append(hide_proxy)
        root.addEventListener(loading_event, hide_proxy)


start()
