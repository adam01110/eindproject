from pyscript import web


def get(element_id):
    matches = web.page.find(f"#{element_id}")
    if not matches:
        return None
    return matches[0]
