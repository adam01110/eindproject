import asyncio

from pyscript import fetch, web, when, window
from pyscript.ffi import create_proxy

page = web.page

DEFAULT_PAGE_ID = "page-1"
PAGE_IDS = []
HASH_CHANGE_PROXY = None


def collect_page_ids():
    sections = page.find("[data-page-section]")
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
    links = page.find("[data-nav-link]")

    for link in links:
        target_page = link.href.split("#")[-1] if "#" in link.href else ""
        is_active = target_page == active_page_id

        if is_active:
            link.ariaCurrent = "page"
        else:
            link.ariaCurrent = ""


def set_active_section(active_page_id):
    sections = page.find("[data-page-section]")

    for section in sections:
        section.hidden = section.id != active_page_id


def set_page_title(active_page_id):
    title_matches = page.find("[data-current-page]")
    active_link_matches = page.find(f'[data-nav-link][href="#{active_page_id}"]')

    if not title_matches or not active_link_matches:
        return

    title_node = title_matches[0]
    active_label = active_link_matches[0].textContent
    if active_label:
        title_node.textContent = active_label


@when("click", "[data-nav-link]")
def on_navigation_click(_event):
    render()


def render(_event=None):
    active_page_id = normalize_hash(window.location.hash)
    expected_hash = f"#{active_page_id}"

    if window.location.hash != expected_hash:
        window.history.replaceState(None, "", expected_hash)

    set_active_navigation(active_page_id)
    set_active_section(active_page_id)
    set_page_title(active_page_id)


async def load_page_partials():
    sections = page.find("[data-page-section]")

    for section in sections:
        partial_path = f"./pages/{section.id}.html"
        if not partial_path:
            continue

        try:
            response = await fetch(partial_path)
            if response.ok:
                section.innerHTML = await response.text()
        except Exception:
            continue


def start():
    global PAGE_IDS

    PAGE_IDS = collect_page_ids()

    global HASH_CHANGE_PROXY

    HASH_CHANGE_PROXY = create_proxy(render)
    window.addEventListener("hashchange", HASH_CHANGE_PROXY)

    render()
    asyncio.create_task(load_page_partials())


start()
