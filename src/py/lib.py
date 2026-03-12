import asyncio
from html import escape

from pyscript import display, document, storage, web, window
from pyscript.ffi import create_proxy

APP_STORAGE_KEY = "eindproject"
SETTINGS_STORAGE_KEY = "settings"
HISTORIES_STORAGE_KEY = "histories"

STATE_CARD_VARIANT_CLASSES = {
    "placeholder": "border border-dashed border-border/70 bg-background/60 text-base-content/60",
    "error": "border border-destructive/40 bg-destructive/10 text-destructive",
}

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

_store = None
_memory_store = {}


def find(selector):
    return web.page.find(selector)


def first(selector):
    matches = find(selector)
    if not matches:
        return None
    return matches[0]


def get(element_id):
    return first(f"#{element_id}")


def read_text_input_value(element_id, default=""):
    element = get(element_id)
    if not element:
        return default

    return str(element.value or "").strip()


def set_element_value(element_id, value):
    element = get(element_id)
    if element:
        element.value = "" if value is None else str(value)

    return element


def set_text_content(element_id, value):
    element = get(element_id)
    if element:
        element.textContent = str(value)

    return element


def normalize_decimal_input(value, decimal_separator="."):
    normalized_value = str(value or "").strip()

    if decimal_separator == ",":
        return normalized_value.replace(".", ",")

    if decimal_separator == ".":
        return normalized_value.replace(",", ".")

    return normalized_value


def parse_number(value, empty_returns_none=False):
    normalized_value = normalize_decimal_input(value, ".")
    if not normalized_value:
        if empty_returns_none:
            return None
        raise ValueError("missing")

    return float(normalized_value)


def format_number(value, decimals=2, decimal_separator=".", empty_value=""):
    if value is None:
        return empty_value

    numeric_value = float(value)
    if numeric_value.is_integer():
        formatted_value = str(int(numeric_value))
    else:
        formatted_value = f"{numeric_value:.{decimals}f}".rstrip("0").rstrip(".")

    if decimal_separator == ",":
        return formatted_value.replace(".", ",")

    return formatted_value


def build_state_markup(
    message,
    variant="placeholder",
    layout_classes="h-full min-h-96",
    escape_html=True,
):
    safe_message = escape(str(message)) if escape_html else str(message)
    variant_classes = STATE_CARD_VARIANT_CLASSES.get(
        variant, STATE_CARD_VARIANT_CLASSES["placeholder"]
    )

    return (
        f'<div class="flex {layout_classes} items-center justify-center rounded-xl '
        f'{variant_classes} p-6 text-center">{safe_message}</div>'
    )


def render_state_card(
    container_id,
    message,
    variant="placeholder",
    clear_plot=None,
    layout_classes="h-full min-h-96",
    escape_html=True,
):
    if callable(clear_plot):
        clear_plot()

    container = get(container_id)
    if not container:
        return

    container.innerHTML = build_state_markup(
        message,
        variant=variant,
        layout_classes=layout_classes,
        escape_html=escape_html,
    )


def render_summary_card(title, value, icon_class=""):
    safe_title = escape(str(title))
    safe_value = escape(str(value))
    icon_markup = ""

    if icon_class:
        safe_icon_class = escape(str(icon_class), quote=True)
        icon_markup = f'<i class="{safe_icon_class} size-4" aria-hidden="true"></i>'

    return f"""
        <article class="card gap-0 p-0">
            <section class="p-4">
                <div class="flex items-center gap-2 text-sm font-semibold text-base-content/60">
                    {icon_markup}
                    <span class="truncate">{safe_title}</span>
                </div>
                <p class="mt-3 text-base">{safe_value}</p>
            </section>
        </article>
    """


def show_tab_panel(panel_name, panel_pairs):
    for name, tab_id, panel_id in panel_pairs:
        is_active = panel_name == name
        tab = get(tab_id)
        panel = get(panel_id)

        if tab:
            tab.setAttribute("aria-selected", "true" if is_active else "false")
            tab.setAttribute("tabindex", "0" if is_active else "-1")

        if panel:
            panel.hidden = not is_active


def sanitize_history_entries(history_entries, normalize_entry):
    sanitized_entries = []
    changed = False

    for entry in history_entries:
        normalized_entry = normalize_entry(entry)
        if not normalized_entry:
            changed = True
            continue

        if entry != normalized_entry:
            changed = True

        sanitized_entries.append(normalized_entry)

    return sanitized_entries, changed


def render_history_list(history_list_id, empty_state_id, history_entries, render_entry):
    history_list = get(history_list_id)
    empty_state = get(empty_state_id)
    if not history_list or not empty_state:
        return

    if not history_entries:
        history_list.innerHTML = ""
        empty_state.hidden = False
        return

    history_list.innerHTML = "".join(
        render_entry(entry, index) for index, entry in enumerate(history_entries)
    )
    empty_state.hidden = True


async def sync_tool_history_view(tool_index, normalize_entry, render_entries):
    history_entries = await get_tool_history(tool_index)
    sanitized_entries, changed = sanitize_history_entries(
        history_entries, normalize_entry
    )

    if changed:
        sanitized_entries = await set_tool_history(tool_index, sanitized_entries)

    render_entries(sanitized_entries)
    return sanitized_entries


async def delete_tool_history_and_refresh(tool_index, history_index, sync_view):
    await delete_tool_history_entry(tool_index, history_index)
    await sync_view()


def get_delegated_target(event, selector, container=None):
    target = getattr(event, "target", None)
    if not target or not hasattr(target, "closest"):
        return None

    matched_target = target.closest(selector)
    if not matched_target:
        return None

    if container and not container.contains(matched_target):
        return None

    return matched_target


def get_dataset_int(element, dataset_name):
    if not element:
        return None

    try:
        return int(getattr(element.dataset, dataset_name))
    except (AttributeError, TypeError, ValueError):
        return None


def dispatch_history_click(event, history_list, handler):
    action_button = get_delegated_target(event, "[data-history-action]", history_list)
    if not action_button:
        return False

    history_action = getattr(action_button.dataset, "historyAction", "")
    history_index = get_dataset_int(action_button, "historyIndex")

    if not history_action or history_index is None:
        return False

    asyncio.create_task(handler(history_action, history_index))
    return True


def add_proxy_listener(target, event_name, handler):
    if not target:
        return None

    proxy = create_proxy(handler)
    target.addEventListener(event_name, proxy)
    return proxy


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


def clear_matplotlib_target(target_id, close_all=True):
    if close_all:
        import matplotlib.pyplot as plt  # ty:ignore[unresolved-import]

        plt.close("all")

    target = get(target_id)
    if target:
        target.innerHTML = ""


def render_chart_fallback(target_id, message, escape_html=True):
    target = get(target_id)
    if not target:
        return

    target.innerHTML = build_state_markup(
        message,
        layout_classes="h-full w-full",
        escape_html=escape_html,
    )


def display_matplotlib_figure(fig, target_id, append=False, close=True):
    display(fig, target=target_id, append=append)

    if close:
        import matplotlib.pyplot as plt  # ty:ignore[unresolved-import]

        plt.close(fig)


async def get_store():
    global _store

    if _store is None:
        _store = await storage(APP_STORAGE_KEY)

    if _store is None:
        return _memory_store

    return _store


async def get_value(key, default=None):
    store = await get_store()

    if key in store:
        return store[key]

    return default


async def set_value(key, value, sync=True):
    store = await get_store()
    store[key] = value

    if sync and hasattr(store, "sync"):
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
