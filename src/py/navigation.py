import asyncio

from js import window
from pyodide.ffi import create_proxy
from pyodide.http import pyfetch
from pyscript.web import page

DEFAULT_PAGE_ID = "page-1"
PAGE_IDS = []
HASH_CHANGE_PROXY = None


def to_dom(node):
    return getattr(node, "element", getattr(node, "_dom_element", node))


def collect_page_ids():
    sections = page.find("[data-page-section]")
    page_ids = []
    for section in sections:
        section_id = to_dom(section).getAttribute("id")
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
        link_dom = to_dom(link)
        target_page = link_dom.getAttribute("data-page-id")
        is_active = target_page == active_page_id

        if is_active:
            link_dom.setAttribute("aria-current", "page")
        else:
            if link_dom.hasAttribute("aria-current"):
                link_dom.removeAttribute("aria-current")


def set_active_section(active_page_id):
    sections = page.find("[data-page-section]")

    for section in sections:
        section_dom = to_dom(section)
        section_id = section_dom.getAttribute("id")
        if section_id == active_page_id:
            section_dom.removeAttribute("hidden")
        else:
            section_dom.setAttribute("hidden", "")


def set_page_title(active_page_id):
    title_matches = page.find("[data-current-page]")
    active_link_matches = page.find(f'[data-nav-link][data-page-id="{active_page_id}"]')

    if not title_matches or not active_link_matches:
        return

    title_dom = to_dom(title_matches[0])
    active_link_dom = to_dom(active_link_matches[0])
    active_label = active_link_dom.getAttribute("data-page-label")
    if active_label:
        title_dom.textContent = active_label


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
        section_dom = to_dom(section)
        partial_path = section_dom.getAttribute("data-page-partial")
        if not partial_path:
            continue

        try:
            response = await pyfetch(partial_path)
            if response.ok:
                section_dom.innerHTML = await response.string()
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
