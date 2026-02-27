from js import window
from pyscript import document


ACTIVE_CLASSES = ["border-slate-800", "bg-slate-800", "text-white", "shadow-sm"]
BASE_TEXT_CLASS = "text-stone-700"


def normalize_path(path):
    if path is None or path == "" or path == "/":
        return "index.html"
    if path.endswith("/"):
        path = path[:-1]
    return path.split("/")[-1]


def set_active_navigation():
    current_page = normalize_path(window.location.pathname)
    links = document.querySelectorAll("[data-nav-link]")
    active_label = "Page 1"

    for link in links:
        href = normalize_path(link.getAttribute("href"))
        is_current = href == current_page

        if is_current:
            link.setAttribute("aria-current", "page")
            for class_name in ACTIVE_CLASSES:
                link.classList.add(class_name)
            link.classList.remove(BASE_TEXT_CLASS)
            active_label = link.getAttribute("data-page-label")
        else:
            if link.hasAttribute("aria-current"):
                link.removeAttribute("aria-current")
            for class_name in ACTIVE_CLASSES:
                link.classList.remove(class_name)
            link.classList.add(BASE_TEXT_CLASS)

    current_page_title = document.querySelector("[data-current-page]")
    if current_page_title is not None:
        current_page_title.textContent = active_label


set_active_navigation()
