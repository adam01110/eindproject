import asyncio

import matplotlib.pyplot as plt  # ty:ignore[unresolved-import]
import numpy as np  # ty:ignore[unresolved-import]
from pyscript import display, when, window
from pyscript.ffi import create_proxy

TOOL_INDEX = 1
LAST_RESULT = None
THEME_CHANGE_PROXY = None
HISTORY_CLICK_PROXY = None

HISTORY_VALUE_ICONS = {
    "a": "icon-[tabler--circle-letter-a]",
    "b": "icon-[tabler--circle-letter-b]",
    "y": "icon-[tabler--circle-letter-y]",
    "x": "icon-[tabler--circle-letter-x]",
}


def clear_plot_output():
    plt.close("all")

    target_div = get("lineaire-vergelijking-mpl")  # ty:ignore[unresolved-reference]  # noqa: F821
    if target_div:
        target_div.innerHTML = ""


def get_input_values():
    a_input = get("lineaire-vergelijking-a")  # ty:ignore[unresolved-reference]  # noqa: F821
    b_input = get("lineaire-vergelijking-b")  # ty:ignore[unresolved-reference]  # noqa: F821
    y_input = get("lineaire-vergelijking-y")  # ty:ignore[unresolved-reference]  # noqa: F821

    if not a_input or not b_input or not y_input:
        return None

    return (
        a_input.value.strip(),
        b_input.value.strip(),
        y_input.value.strip(),
    )


def normalize_input_values(values):
    if not isinstance(values, (list, tuple)) or len(values) != 3:
        return None

    return tuple(str(value).strip() for value in values)


def validate_inputs(a_str, b_str, y_str):
    values = (("a", a_str), ("b", b_str), ("y", y_str))

    if any(not value for _, value in values):
        return "Vul alle velden in."

    parsed_values = {}
    for name, value in values:
        try:
            parsed_values[name] = float(value)
        except ValueError:
            return f"Voer een geldig getal in voor {name}."

    if parsed_values["a"] == 0:
        return "a mag niet 0 zijn."

    return None


def solve_linear_equation(a, b, y):
    stap1 = y - b
    x = stap1 / a

    return {
        "a": a,
        "b": b,
        "y": y,
        "stap1": stap1,
        "x": x,
    }


def format_value(value):
    if float(value).is_integer():
        return str(int(value))

    return f"{value:.2f}".rstrip("0").rstrip(".")


def render_result(result, error=None):
    global LAST_RESULT

    if error or not result:
        LAST_RESULT = None
        clear_plot_output()
        legend_card = get("lineaire-vergelijking-legend")  # ty:ignore[unresolved-reference]  # noqa: F821
        if legend_card:
            legend_card.innerHTML = '<p class="text-base-content/60">Voer waarden in om de grafiek te zien.</p>'
        return

    LAST_RESULT = result

    a = result["a"]
    b = result["b"]
    y = result["y"]
    x_solution = result["x"]
    formatted_a = format_value(a)
    formatted_b = format_value(b)
    formatted_y = format_value(y)
    formatted_x = format_value(x_solution)

    x_range = np.linspace(x_solution - 5, x_solution + 5, 100)
    y_values = a * x_range + b

    clear_plot_output()

    fig, ax = plt.subplots()
    theme = apply_matplotlib_theme(fig, ax)  # ty:ignore[unresolved-reference]  # noqa: F821
    chart_colors = theme["chart_colors"]

    ax.plot(
        x_range,
        y_values,
        color=chart_colors[0],
        label=f"y = {formatted_a}x + {formatted_b}",
    )
    ax.axhline(
        y=y,
        color=theme["danger_color"],
        linestyle="--",
        alpha=0.7,
        label=f"y = {formatted_y}",
    )
    ax.axvline(
        x=x_solution,
        color=chart_colors[2],
        linestyle="--",
        alpha=0.7,
        label=f"x = {formatted_x}",
    )
    ax.scatter(
        [x_solution],
        [y],
        color=chart_colors[2],
        edgecolors=theme["surface_color"],
        linewidths=1.5,
        zorder=5,
        s=100,
    )
    ax.set_xlabel("x")
    ax.set_ylabel("y", rotation="horizontal", labelpad=15)
    ax.grid(True, color=theme["grid_color"], alpha=0.25)

    display(fig, target="lineaire-vergelijking-mpl")
    plt.close(fig)

    legend_card = get("lineaire-vergelijking-legend")  # ty:ignore[unresolved-reference]  # noqa: F821
    if legend_card:
        legend_card.innerHTML = f"""
            <div class="flex flex-col gap-3">
                <div class="field">
                    <div class="flex items-center gap-2">
                        <i class="icon-[tabler--circle-letter-y] size-5 mr-1" aria-hidden="true"></i>
                        <div class="input w-full cursor-default">{formatted_y}</div>
                    </div>
                </div>
                <div class="field">
                    <div class="flex items-center gap-2">
                        <i class="icon-[tabler--circle-letter-x] size-5 mr-1" aria-hidden="true"></i>
                        <div class="input w-full cursor-default">{formatted_x}</div>
                    </div>
                </div>
            </div>
        """


def set_input_values(a, b, y):
    input_values = {
        "lineaire-vergelijking-a": a,
        "lineaire-vergelijking-b": b,
        "lineaire-vergelijking-y": y,
    }

    for input_id, value in input_values.items():
        input_element = get(input_id)  # ty:ignore[unresolved-reference]  # noqa: F821
        if input_element:
            input_element.value = format_value(value)


def show_panel(panel_name):
    panel_pairs = (
        ("tool", "lineaire-vergelijking-oplosser-tool-tab", "lineaire-vergelijking-oplosser-tool-panel"),
        ("history", "lineaire-vergelijking-oplosser-history-tab", "lineaire-vergelijking-oplosser-history-panel"),
    )

    for name, tab_id, panel_id in panel_pairs:
        is_active = panel_name == name
        tab = get(tab_id)  # ty:ignore[unresolved-reference]  # noqa: F821
        panel = get(panel_id)  # ty:ignore[unresolved-reference]  # noqa: F821

        if tab:
            tab.setAttribute("aria-selected", "true" if is_active else "false")
            tab.setAttribute("tabindex", "0" if is_active else "-1")

        if panel:
            panel.hidden = not is_active


def normalize_history_entry(entry):
    if not isinstance(entry, dict):
        return None

    normalized_entry = {}
    for key in ("a", "b", "y", "x"):
        try:
            normalized_entry[key] = float(entry.get(key))
        except (TypeError, ValueError):
            return None

    return normalized_entry


def sanitize_history_entries(history_entries):
    sanitized_entries = []
    changed = False

    for entry in history_entries:
        normalized_entry = normalize_history_entry(entry)
        if not normalized_entry:
            changed = True
            continue

        if entry != normalized_entry:
            changed = True

        sanitized_entries.append(normalized_entry)

    return sanitized_entries, changed


def render_history_value(label, value):
    icon_class = HISTORY_VALUE_ICONS.get(label, "")

    return f"""
        <div class="flex items-center gap-2 text-sm font-semibold">
            <i class="{icon_class} size-4 text-base-content/60" aria-hidden="true"></i>
            <p>{value}</p>
        </div>
    """


def render_history_entry(entry, index):
    input_values = "".join(
        (
            render_history_value("a", format_value(entry["a"])),
            render_history_value("b", format_value(entry["b"])),
            render_history_value("y", format_value(entry["y"])),
        )
    )
    output_values = render_history_value("x", format_value(entry["x"]))

    return f"""
        <article class="card p-0">
            <section class="flex flex-wrap items-center gap-3 p-4 xl:flex-nowrap">
                <div class="min-w-0 flex flex-1 flex-wrap items-center gap-x-5 gap-y-3 rounded-xl border border-border/70 bg-card/85 p-3">
                    <div class="flex items-center gap-2">
                        <span class="badge-outline">Input</span>
                    </div>
                    {input_values}
                </div>
                <div class="min-w-0 flex flex-1 flex-wrap items-center gap-x-5 gap-y-3 rounded-xl border border-border/70 bg-card/85 p-3">
                    <div class="flex items-center gap-2">
                        <span class="badge-secondary">Output</span>
                    </div>
                    {output_values}
                </div>
                <div class="flex shrink-0 items-center gap-2 self-center">
                    <button
                        type="button"
                        class="btn-outline whitespace-nowrap"
                        data-history-action="restore"
                        data-history-index="{index}"
                    >
                        Restore
                    </button>
                    <button
                        type="button"
                        class="btn-destructive whitespace-nowrap"
                        data-history-action="delete"
                        data-history-index="{index}"
                    >
                        Delete
                    </button>
                </div>
            </section>
        </article>
    """


def render_history_entries(history_entries):
    history_list = get("lineaire-vergelijking-history-list")  # ty:ignore[unresolved-reference]  # noqa: F821
    empty_state = get("lineaire-vergelijking-history-empty")  # ty:ignore[unresolved-reference]  # noqa: F821
    if not history_list or not empty_state:
        return

    if not history_entries:
        history_list.innerHTML = ""
        empty_state.hidden = False
        return

    history_list.innerHTML = "".join(
        render_history_entry(entry, index)
        for index, entry in enumerate(history_entries)
    )
    empty_state.hidden = True


async def sync_history_view():
    history_entries = await get_tool_history(TOOL_INDEX)  # ty:ignore[unresolved-reference]  # noqa: F821
    sanitized_entries, changed = sanitize_history_entries(history_entries)

    if changed:
        sanitized_entries = await set_tool_history(  # ty:ignore[unresolved-reference]  # noqa: F821
            TOOL_INDEX, sanitized_entries
        )

    render_history_entries(sanitized_entries)
    return sanitized_entries


async def restore_history_entry(history_index):
    history_entries = await sync_history_view()
    if history_index < 0 or history_index >= len(history_entries):
        return

    entry = history_entries[history_index]
    set_input_values(entry["a"], entry["b"], entry["y"])
    render_result(solve_linear_equation(entry["a"], entry["b"], entry["y"]))
    show_panel("tool")


async def delete_history_entry(history_index):
    await delete_tool_history_entry(TOOL_INDEX, history_index)  # ty:ignore[unresolved-reference]  # noqa: F821
    await sync_history_view()


async def handle_history_action(action, history_index):
    if action == "restore":
        await restore_history_entry(history_index)
        return

    if action == "delete":
        await delete_history_entry(history_index)


def on_history_list_click(event):
    history_list = get("lineaire-vergelijking-history-list")  # ty:ignore[unresolved-reference]  # noqa: F821
    target = getattr(event, "target", None)
    if not history_list or not target or not hasattr(target, "closest"):
        return

    action_button = target.closest("[data-history-action]")
    if not action_button or not history_list.contains(action_button):
        return

    history_action = action_button.dataset.historyAction

    try:
        history_index = int(action_button.dataset.historyIndex)
    except (TypeError, ValueError):
        return

    asyncio.create_task(handle_history_action(history_action, history_index))


@when("click", "#lineaire-vergelijking-berekenen")
async def bereken_click(event):
    values = normalize_input_values(get_input_values())
    if not values:
        return

    a_str, b_str, y_str = values

    error = validate_inputs(a_str, b_str, y_str)
    if error:
        render_result(None, error)
        return

    a = float(a_str)
    b = float(b_str)
    y = float(y_str)

    result = solve_linear_equation(a, b, y)

    render_result(result)

    await append_tool_history(  # ty:ignore[unresolved-reference]  # noqa: F821
        TOOL_INDEX,
        {
            "a": a,
            "b": b,
            "y": y,
            "x": result["x"],
        },
    )
    await sync_history_view()


@when("click", "#lineaire-vergelijking-oplosser-tool-tab")
def tool_tab_click(_event):
    show_panel("tool")


@when("click", "#lineaire-vergelijking-oplosser-history-tab")
async def history_tab_click(_event):
    await sync_history_view()
    show_panel("history")


@when("click", "#lineaire-vergelijking-reset")
def reset_click(event):
    for input_id in (
        "lineaire-vergelijking-a",
        "lineaire-vergelijking-b",
        "lineaire-vergelijking-y",
    ):
        input_element = get(input_id)  # ty:ignore[unresolved-reference]  # noqa: F821
        if input_element:
            input_element.value = ""

    render_result(None)


def on_theme_change(_event):
    if LAST_RESULT:
        render_result(LAST_RESULT)


def start():
    global THEME_CHANGE_PROXY, HISTORY_CLICK_PROXY

    THEME_CHANGE_PROXY = create_proxy(on_theme_change)
    window.addEventListener("app:themechange", THEME_CHANGE_PROXY)
    history_list = get("lineaire-vergelijking-history-list")  # ty:ignore[unresolved-reference]  # noqa: F821
    if history_list:
        HISTORY_CLICK_PROXY = create_proxy(on_history_list_click)
        history_list.addEventListener("click", HISTORY_CLICK_PROXY)
    show_panel("tool")
    asyncio.create_task(sync_history_view())


start()
