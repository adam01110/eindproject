from js import window
from pyodide.ffi import create_proxy
from pyscript import document


ACTIVE_CLASSES = ["border-slate-800", "bg-slate-800", "text-white", "shadow-sm"]
BASE_TEXT_CLASS = "text-stone-700"
DEFAULT_PAGE_ID = "page-1"


def collect_page_ids():
    sections = document.querySelectorAll("[data-page-section]")
    page_ids = []
    for section in sections:
        section_id = section.getAttribute("id")
        if section_id:
            page_ids.append(section_id)
    return page_ids


PAGE_IDS = collect_page_ids()


def normalize_hash(hash_value):
    if not hash_value:
        return DEFAULT_PAGE_ID

    page_id = hash_value.replace("#", "")
    if page_id in PAGE_IDS:
        return page_id

    return DEFAULT_PAGE_ID


def set_active_navigation(active_page_id):
    links = document.querySelectorAll("[data-nav-link]")

    for link in links:
        target_page = link.getAttribute("data-page-id")
        is_active = target_page == active_page_id

        if is_active:
            link.setAttribute("aria-current", "page")
            for class_name in ACTIVE_CLASSES:
                link.classList.add(class_name)
            link.classList.remove(BASE_TEXT_CLASS)
        else:
            if link.hasAttribute("aria-current"):
                link.removeAttribute("aria-current")
            for class_name in ACTIVE_CLASSES:
                link.classList.remove(class_name)
            link.classList.add(BASE_TEXT_CLASS)


def set_active_section(active_page_id):
    sections = document.querySelectorAll("[data-page-section]")

    for section in sections:
        section_id = section.getAttribute("id")
        if section_id == active_page_id:
            section.classList.remove("hidden")
        else:
            section.classList.add("hidden")


def set_page_title(active_page_id):
    title = document.querySelector("[data-current-page]")
    active_link = document.querySelector(f'[data-nav-link][data-page-id="{active_page_id}"]')

    if title is None or active_link is None:
        return

    active_label = active_link.getAttribute("data-page-label")
    if active_label:
        title.textContent = active_label


def render(_event=None):
    active_page_id = normalize_hash(window.location.hash)
    expected_hash = f"#{active_page_id}"

    if window.location.hash != expected_hash:
        window.history.replaceState(None, "", expected_hash)

    set_active_navigation(active_page_id)
    set_active_section(active_page_id)
    set_page_title(active_page_id)


hash_change_proxy = create_proxy(render)
window.addEventListener("hashchange", hash_change_proxy)
render()
