from pyscript import when, window
from pyscript.ffi import create_proxy

DEFAULT_PAGE_ID = "home"
PAGE_IDS = []
HASH_CHANGE_PROXY = None


def collect_page_ids():
    sections = find("[data-page-section]")  # ty:ignore[unresolved-reference]  # noqa: F821
    page_ids = []
    for section in sections:
        section_id = section.id
        if section_id:
            page_ids.append(section_id)
    return page_ids


def normalize_hash(hash_value):
    if not hash_value:
        return DEFAULT_PAGE_ID

    page_id = hash_value.replace("#", "")
    if page_id in PAGE_IDS:
        return page_id

    return DEFAULT_PAGE_ID


def set_active_navigation(active_page_id):
    links = find("[data-nav-link]")  # ty:ignore[unresolved-reference]  # noqa: F821

    for link in links:
        target_page = link.href.split("#")[-1] if "#" in link.href else ""
        is_active = target_page == active_page_id

        if is_active:
            link.ariaCurrent = "page"
        else:
            link.ariaCurrent = ""


def set_active_section(active_page_id):
    sections = find("[data-page-section]")  # ty:ignore[unresolved-reference]  # noqa: F821

    for section in sections:
        section.hidden = section.id != active_page_id


def set_page_title(active_page_id):
    title_node = first("[data-current-page]")  # ty:ignore[unresolved-reference]  # noqa: F821
    active_link = first(f'[data-nav-link][href="#{active_page_id}"]')  # ty:ignore[unresolved-reference]  # noqa: F821

    if not title_node or not active_link:
        return

    active_label = active_link.textContent
    if active_label:
        title_node.textContent = active_label


@when("click", "[data-nav-link]")
def on_navigation_click(_event):
    close_sidebar_on_mobile()  # ty:ignore[unresolved-reference]  # noqa: F821
    render()


@when("click", "[data-sidebar-open]")
def on_sidebar_open_click(_event):
    set_sidebar_state(True)  # ty:ignore[unresolved-reference]  # noqa: F821


@when("click", "[data-sidebar-collapse]")
def on_sidebar_collapse_click(_event):
    set_sidebar_state(False)  # ty:ignore[unresolved-reference]  # noqa: F821


@when("click", "[data-sidebar-pin]")
def on_sidebar_pin_click(_event):
    set_sidebar_state(True)  # ty:ignore[unresolved-reference]  # noqa: F821


def render(_event=None):
    active_page_id = normalize_hash(window.location.hash)
    expected_hash = f"#{active_page_id}"

    if window.location.hash != expected_hash:
        window.history.replaceState(None, "", expected_hash)

    set_active_navigation(active_page_id)
    set_active_section(active_page_id)
    set_page_title(active_page_id)


def start():
    global PAGE_IDS

    PAGE_IDS = collect_page_ids()

    global HASH_CHANGE_PROXY

    HASH_CHANGE_PROXY = create_proxy(render)
    window.addEventListener("hashchange", HASH_CHANGE_PROXY)

    setup_sidebar_behavior()  # ty:ignore[unresolved-reference]  # noqa: F821

    render()


start()
