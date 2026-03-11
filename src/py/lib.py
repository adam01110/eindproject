from pyscript import document, storage, web, window

APP_STORAGE_KEY = "eindproject"
SETTINGS_STORAGE_KEY = "settings"
HISTORIES_STORAGE_KEY = "histories"

_store = None


def find(selector):
    return web.page.find(selector)


def first(selector):
    matches = find(selector)
    if not matches:
        return None
    return matches[0]


def get(element_id):
    return first(f"#{element_id}")


MATPLOTLIB_THEME_TOKENS = {
    "surface_color": "--card",
    "text_color": "--foreground",
    "border_color": "--border",
    "grid_color": "--muted-foreground",
    "danger_color": "--destructive",
}

MATPLOTLIB_CHART_TOKENS = [
    "--chart-1",
    "--chart-2",
    "--chart-3",
    "--chart-4",
    "--chart-5",
]


def _css_color_to_rgba(color_value):
    normalized_color = str(color_value).strip()
    if not normalized_color:
        return None

    if not window.CSS.supports("color", normalized_color):
        return None

    canvas = document.createElement("canvas")
    canvas.width = 1
    canvas.height = 1
    context = canvas.getContext("2d")
    if not context:
        return None

    context.clearRect(0, 0, 1, 1)
    context.fillStyle = "rgba(0, 0, 0, 0)"
    context.fillStyle = normalized_color
    context.fillRect(0, 0, 1, 1)

    pixel = context.getImageData(0, 0, 1, 1).data
    return tuple(channel / 255 for channel in pixel)


def _get_css_variable(variable_name):
    root = document.documentElement
    if not root:
        return ""

    return window.getComputedStyle(root).getPropertyValue(variable_name).strip()


def get_theme_color(variable_name):
    return _css_color_to_rgba(_get_css_variable(variable_name))


def get_matplotlib_theme():
    theme = {
        name: get_theme_color(variable_name)
        for name, variable_name in MATPLOTLIB_THEME_TOKENS.items()
    }
    theme["chart_colors"] = [
        get_theme_color(variable_name) for variable_name in MATPLOTLIB_CHART_TOKENS
    ]
    return theme


def apply_matplotlib_theme(fig, ax):
    theme = get_matplotlib_theme()
    surface_color = theme["surface_color"]
    text_color = theme["text_color"]

    if surface_color is not None:
        for setter in (
            fig.patch.set_facecolor,
            fig.patch.set_edgecolor,
            ax.set_facecolor,
        ):
            setter(surface_color)

    if text_color is not None:
        ax.tick_params(colors=text_color)

        for label in (ax.xaxis.label, ax.yaxis.label, ax.title):
            label.set_color(text_color)

    border_color = theme["border_color"]
    if border_color is not None:
        for spine in ax.spines.values():
            spine.set_color(border_color)

    return theme


async def get_store():
    global _store

    if _store is None:
        _store = await storage(APP_STORAGE_KEY)

    return _store


async def get_value(key, default=None):
    store = await get_store()

    if key in store:
        return store[key]

    return default


async def set_value(key, value, sync=True):
    store = await get_store()
    store[key] = value

    if sync:
        await store.sync()

    return value


async def read_settings():
    settings_value = await get_value(SETTINGS_STORAGE_KEY, {})

    if not isinstance(settings_value, dict):
        return {}

    return settings_value


async def get_setting(key, default=None):
    settings_value = await read_settings()
    return settings_value.get(key, default)


async def set_setting(key, value):
    settings_value = await read_settings()
    settings_value[key] = value
    await set_value(SETTINGS_STORAGE_KEY, settings_value)
    return value


async def read_histories():
    histories_value = await get_value(HISTORIES_STORAGE_KEY, [])

    if not isinstance(histories_value, list):
        return []

    normalized_histories = []

    for history_bucket in histories_value:
        if not isinstance(history_bucket, list):
            normalized_histories.append([])
            continue

        normalized_bucket = []
        for entry in history_bucket:
            if isinstance(entry, dict):
                normalized_bucket.append(entry)

        normalized_histories.append(normalized_bucket)

    return normalized_histories


async def get_tool_history(tool_index):
    histories_value = await read_histories()

    if not isinstance(tool_index, int) or tool_index < 0:
        return []

    if tool_index >= len(histories_value):
        return []

    return histories_value[tool_index]


async def set_tool_history(tool_index, entries):
    if not isinstance(tool_index, int) or tool_index < 0:
        return []

    if not isinstance(entries, list):
        return []

    histories_value = await read_histories()

    while len(histories_value) <= tool_index:
        histories_value.append([])

    normalized_entries = [entry for entry in entries if isinstance(entry, dict)]
    histories_value[tool_index] = normalized_entries

    await set_value(HISTORIES_STORAGE_KEY, histories_value)
    return normalized_entries


async def append_tool_history(tool_index, entry, limit=100):
    if not isinstance(tool_index, int) or tool_index < 0:
        return []

    if not isinstance(entry, dict):
        return []

    histories_value = await read_histories()

    while len(histories_value) <= tool_index:
        histories_value.append([])

    history_bucket = histories_value[tool_index]
    history_bucket.append(entry)

    if isinstance(limit, int) and limit > 0 and len(history_bucket) > limit:
        del history_bucket[: len(history_bucket) - limit]

    await set_value(HISTORIES_STORAGE_KEY, histories_value)
    return history_bucket


async def delete_tool_history_entry(tool_index, entry_index):
    if not isinstance(tool_index, int) or tool_index < 0:
        return []

    if not isinstance(entry_index, int) or entry_index < 0:
        return []

    histories_value = await read_histories()

    if tool_index >= len(histories_value):
        return []

    history_bucket = histories_value[tool_index]
    if entry_index >= len(history_bucket):
        return history_bucket

    del history_bucket[entry_index]

    await set_value(HISTORIES_STORAGE_KEY, histories_value)
    return history_bucket
