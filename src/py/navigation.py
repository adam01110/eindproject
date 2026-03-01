import asyncio

from pyscript import fetch, web, when, window
from pyscript.ffi import create_proxy

DEFAULT_PAGE_ID = "page-1"
PAGE_IDS = []
HASH_CHANGE_PROXY = None
PARTIAL_HTML_CACHE = {}


def collect_page_ids():
    sections = web.page.find("[data-page-section]")
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
    links = web.page.find("[data-nav-link]")

    for link in links:
        target_page = link.href.split("#")[-1] if "#" in link.href else ""
        is_active = target_page == active_page_id

        if is_active:
            link.ariaCurrent = "page"
        else:
            link.ariaCurrent = ""


def set_active_section(active_page_id):
    sections = web.page.find("[data-page-section]")

    for section in sections:
        section.hidden = section.id != active_page_id


def set_page_title(active_page_id):
    title_matches = web.page.find("[data-current-page]")
    active_link_matches = web.page.find(f'[data-nav-link][href="#{active_page_id}"]')

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
    sections = web.page.find("[data-page-section]")

    tasks = []

    for section in sections:
        partial_path = section.getAttribute("data-page-partial")
        if partial_path:
            partial_path = partial_path.strip()

        if not partial_path:
            section_id = section.id or ""
            if not section_id:
                continue
            partial_path = f"./pages/{section_id}.html"

        tasks.append(load_section_partial(section, partial_path))

    if not tasks:
        return

    await asyncio.gather(*tasks, return_exceptions=True)


async def load_section_partial(section, partial_path):
    if partial_path in PARTIAL_HTML_CACHE:
        section.innerHTML = PARTIAL_HTML_CACHE[partial_path]
        return

    try:
        response = await fetch(partial_path)
        if not response.ok:
            return

        html = await response.text()
        PARTIAL_HTML_CACHE[partial_path] = html
        section.innerHTML = html
    except Exception:
        return


def start():
    global PAGE_IDS

    PAGE_IDS = collect_page_ids()

    global HASH_CHANGE_PROXY

    HASH_CHANGE_PROXY = create_proxy(render)
    window.addEventListener("hashchange", HASH_CHANGE_PROXY)

    render()
    asyncio.create_task(load_page_partials())


start()
