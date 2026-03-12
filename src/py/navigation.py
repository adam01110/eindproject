from lib import find, first
from pyscript import when, window
from pyscript.ffi import create_proxy
from sidebar import close_sidebar_on_mobile, set_sidebar_state, setup_sidebar_behavior

DEFAULT_PAGE_ID = "home"
HASH_CHANGE_PROXY = None


def render(_event=None):
    sections = find("[data-page-section]")
    page_ids = {section.id for section in sections if section.id}
    active_page_id = window.location.hash.replace("#", "")
    if active_page_id not in page_ids:
        active_page_id = DEFAULT_PAGE_ID

    expected_hash = f"#{active_page_id}"
    if window.location.hash != expected_hash:
        window.history.replaceState(None, "", expected_hash)

    for link in find("[data-nav-link]"):
        target_page = link.href.split("#")[-1] if "#" in link.href else ""
        link.ariaCurrent = "page" if target_page == active_page_id else ""

    for section in sections:
        section.hidden = section.id != active_page_id

    title_node = first("[data-current-page]")
    active_link = first(f'[data-nav-link][href="#{active_page_id}"]')
    if title_node and active_link and active_link.textContent:
        title_node.textContent = active_link.textContent


@when("click", "[data-nav-link]")
def on_navigation_click(_event):
    close_sidebar_on_mobile()
    render()


@when("click", "[data-sidebar-open]")
@when("click", "[data-sidebar-pin]")
def on_sidebar_open_click(_event):
    set_sidebar_state(True)


@when("click", "[data-sidebar-collapse]")
def on_sidebar_collapse_click(_event):
    set_sidebar_state(False)


def start():
    global HASH_CHANGE_PROXY
    HASH_CHANGE_PROXY = create_proxy(render)
    window.addEventListener("hashchange", HASH_CHANGE_PROXY)
    setup_sidebar_behavior()
    render()


start()
