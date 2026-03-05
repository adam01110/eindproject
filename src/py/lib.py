from pyscript import storage, web

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
