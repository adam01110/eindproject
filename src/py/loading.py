from pyscript import web

page = web.page

LOADING_BADGE_ID = "pyscript-loading"


def hide_loading_badge():
    badge_matches = page.find(f"#{LOADING_BADGE_ID}")
    if badge_matches:
        badge_matches[0].remove()


hide_loading_badge()
