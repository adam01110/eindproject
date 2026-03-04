from pyscript import web


def find(selector):
    return web.page.find(selector)


def first(selector):
    matches = find(selector)
    if not matches:
        return None
    return matches[0]


def get(element_id):
    return first(f"#{element_id}")
