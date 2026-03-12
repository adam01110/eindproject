import asyncio

import matplotlib.pyplot as plt  # ty:ignore[unresolved-import]
import numpy as np  # ty:ignore[unresolved-import]
from pyscript import when, window

from lib import (
    add_proxy_listener,
    append_tool_history,
    apply_matplotlib_theme,
    clear_matplotlib_target,
    delete_tool_history_and_refresh,
    dispatch_history_click,
    display_matplotlib_figure,
    format_number,
    get,
    parse_number,
    read_text_input_value,
    render_history_list,
    render_state_card,
    render_summary_card,
    set_element_value,
    show_tab_panel,
    sync_tool_history_view,
)

LINEAIRE_TOOL_INDEX = 1
LINEAIRE_LAST_RESULT = None
LINEAIRE_EVENT_PROXIES = []

LINEAIRE_RESULT_CONTAINER_ID = "lineaire-vergelijking-result"
LINEAIRE_CHART_TARGET_ID = "lineaire-vergelijking-mpl"
LINEAIRE_PANEL_CONFIGS = (
    (
        "tool",
        "lineaire-vergelijking-oplosser-tool-tab",
        "lineaire-vergelijking-oplosser-tool-panel",
    ),
    (
        "history",
        "lineaire-vergelijking-oplosser-history-tab",
        "lineaire-vergelijking-oplosser-history-panel",
    ),
)
LINEAIRE_HISTORY_VALUE_ICONS = {
    "a": "icon-[tabler--circle-letter-a]",
    "b": "icon-[tabler--circle-letter-b]",
    "y": "icon-[tabler--circle-letter-y]",
    "x": "icon-[tabler--circle-letter-x]",
}


def lineaire_format_value(value):
    return format_number(value)


def lineaire_clear_plot_output():
    clear_matplotlib_target(LINEAIRE_CHART_TARGET_ID)


def lineaire_get_input_state():
    return {
        "a": read_text_input_value("lineaire-vergelijking-a"),
        "b": read_text_input_value("lineaire-vergelijking-b"),
        "y": read_text_input_value("lineaire-vergelijking-y"),
    }


def lineaire_validate_input_state(state):
    field_names = ("a", "b", "y")

    if any(not state.get(name) for name in field_names):
        return None, "Vul alle velden in."

    parsed_values = {}
    for name in field_names:
        try:
            parsed_values[name] = parse_number(state[name])
        except ValueError:
            return None, f"Voer een geldig getal in voor {name}."

    if parsed_values["a"] == 0:
        return None, "a mag niet 0 zijn."

    return parsed_values, None


def lineaire_solve_linear_equation(a, b, y):
    x = (y - b) / a

    return {
        "a": a,
        "b": b,
        "y": y,
        "x": x,
    }


def lineaire_format_equation(a, b):
    operator = "+" if b >= 0 else "-"
    return f"y = {lineaire_format_value(a)}x {operator} {lineaire_format_value(abs(b))}"


def lineaire_render_result(result, error=None):
    global LINEAIRE_LAST_RESULT

    if error:
        LINEAIRE_LAST_RESULT = None
        render_state_card(
            LINEAIRE_RESULT_CONTAINER_ID,
            error,
            variant="error",
            clear_plot=lineaire_clear_plot_output,
        )
        return

    if not result:
        LINEAIRE_LAST_RESULT = None
        render_state_card(
            LINEAIRE_RESULT_CONTAINER_ID,
            "Vul waarden in en klik op berekenen.",
            clear_plot=lineaire_clear_plot_output,
        )
        return

    LINEAIRE_LAST_RESULT = result

    result_container = get(LINEAIRE_RESULT_CONTAINER_ID)
    if not result_container:
        return

    formatted_y = lineaire_format_value(result["y"])
    formatted_x = lineaire_format_value(result["x"])

    summary_cards = [
        render_summary_card(
            "Oplossing voor x",
            formatted_x,
            "icon-[tabler--circle-letter-x]",
        ),
        render_summary_card(
            "Waarde van y",
            formatted_y,
            "icon-[tabler--circle-letter-y]",
        ),
    ]

    result_container.innerHTML = f"""
        <div class="flex h-full flex-col gap-4">
            <article class="card gap-0 p-0">
                <section class="p-2">
                    <div
                        id="{LINEAIRE_CHART_TARGET_ID}"
                        class="flex min-h-80 items-center justify-center overflow-hidden [&_canvas]:size-full [&_canvas]:max-w-full [&_img]:block [&_img]:size-full [&_img]:max-w-full [&_img]:rounded-xl [&_img]:object-contain [&_svg]:size-full [&_svg]:max-w-full"
                    ></div>
                </section>
            </article>
            <div class="grid gap-3 sm:grid-cols-2">
                {"".join(summary_cards)}
            </div>
        </div>
    """

    lineaire_clear_plot_output()

    x_solution = result["x"]
    y_value = result["y"]
    a = result["a"]
    b = result["b"]
    x_range = np.linspace(x_solution - 5, x_solution + 5, 100)
    y_values = a * x_range + b

    fig, ax = plt.subplots(figsize=(8, 4.6))
    theme = apply_matplotlib_theme(fig, ax)
    chart_colors = theme["chart_colors"]

    ax.plot(
        x_range,
        y_values,
        color=chart_colors[0],
        label=lineaire_format_equation(a, b),
    )
    ax.axhline(
        y=y_value,
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
        [y_value],
        color=chart_colors[2],
        edgecolors=theme["surface_color"],
        linewidths=1.5,
        zorder=5,
        s=100,
    )
    ax.set_xlabel("x")
    ax.set_ylabel("y", rotation="horizontal", labelpad=15)
    ax.grid(True, color=theme["grid_color"], alpha=0.25)
    ax.set_axisbelow(True)

    display_matplotlib_figure(fig, LINEAIRE_CHART_TARGET_ID)


def lineaire_set_input_values(a, b, y):
    set_element_value("lineaire-vergelijking-a", a)
    set_element_value("lineaire-vergelijking-b", b)
    set_element_value("lineaire-vergelijking-y", y)


def lineaire_show_panel(panel_name):
    show_tab_panel(panel_name, LINEAIRE_PANEL_CONFIGS)


def lineaire_normalize_history_entry(entry):
    if not isinstance(entry, dict):
        return None

    normalized_entry = {}
    for key in ("a", "b", "y", "x"):
        try:
            normalized_entry[key] = float(entry.get(key))
        except (TypeError, ValueError):
            return None

    return normalized_entry


def lineaire_render_history_value(label, value):
    icon_class = LINEAIRE_HISTORY_VALUE_ICONS.get(label, "")

    return f"""
        <div class="flex items-center gap-2 text-sm font-semibold">
            <i class="{icon_class} size-4 text-base-content/60" aria-hidden="true"></i>
            <p>{value}</p>
        </div>
    """


def lineaire_render_history_entry(entry, index):
    input_values = "".join(
        (
            lineaire_render_history_value("a", lineaire_format_value(entry["a"])),
            lineaire_render_history_value("b", lineaire_format_value(entry["b"])),
            lineaire_render_history_value("y", lineaire_format_value(entry["y"])),
        )
    )
    output_values = lineaire_render_history_value(
        "x", lineaire_format_value(entry["x"])
    )

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


def lineaire_render_history_entries(history_entries):
    render_history_list(
        "lineaire-vergelijking-history-list",
        "lineaire-vergelijking-history-empty",
        history_entries,
        lineaire_render_history_entry,
    )


def lineaire_on_history_list_click(event):
    dispatch_history_click(
        event,
        get("lineaire-vergelijking-history-list"),
        lineaire_handle_history_action,
    )


def lineaire_on_theme_change(_event):
    if LINEAIRE_LAST_RESULT:
        lineaire_render_result(LINEAIRE_LAST_RESULT)


async def lineaire_sync_history_view():
    return await sync_tool_history_view(
        LINEAIRE_TOOL_INDEX,
        lineaire_normalize_history_entry,
        lineaire_render_history_entries,
    )


async def lineaire_restore_history_entry(history_index):
    history_entries = await lineaire_sync_history_view()
    if history_index < 0 or history_index >= len(history_entries):
        return

    entry = history_entries[history_index]
    lineaire_set_input_values(
        lineaire_format_value(entry["a"]),
        lineaire_format_value(entry["b"]),
        lineaire_format_value(entry["y"]),
    )
    lineaire_render_result(
        lineaire_solve_linear_equation(entry["a"], entry["b"], entry["y"])
    )
    lineaire_show_panel("tool")


async def lineaire_delete_history_entry(history_index):
    await delete_tool_history_and_refresh(
        LINEAIRE_TOOL_INDEX,
        history_index,
        lineaire_sync_history_view,
    )


async def lineaire_handle_history_action(action, history_index):
    if action == "restore":
        await lineaire_restore_history_entry(history_index)
        return

    if action == "delete":
        await lineaire_delete_history_entry(history_index)


@when("click", "#lineaire-vergelijking-berekenen")
async def lineaire_bereken_click(_event):
    validated_state, error = lineaire_validate_input_state(lineaire_get_input_state())
    if error:
        lineaire_render_result(None, error)
        return

    result = lineaire_solve_linear_equation(
        validated_state["a"],
        validated_state["b"],
        validated_state["y"],
    )
    lineaire_render_result(result)

    await append_tool_history(
        LINEAIRE_TOOL_INDEX,
        {
            "a": validated_state["a"],
            "b": validated_state["b"],
            "y": validated_state["y"],
            "x": result["x"],
        },
    )
    await lineaire_sync_history_view()


@when("click", "#lineaire-vergelijking-oplosser-tool-tab")
def lineaire_tool_tab_click(_event):
    lineaire_show_panel("tool")


@when("click", "#lineaire-vergelijking-oplosser-history-tab")
async def lineaire_history_tab_click(_event):
    await lineaire_sync_history_view()
    lineaire_show_panel("history")


@when("click", "#lineaire-vergelijking-reset")
def lineaire_reset_click(_event):
    lineaire_set_input_values("", "", "")
    lineaire_render_result(None)


def lineaire_start():
    global LINEAIRE_EVENT_PROXIES

    LINEAIRE_EVENT_PROXIES = [
        add_proxy_listener(window, "app:themechange", lineaire_on_theme_change),
    ]

    history_list = get("lineaire-vergelijking-history-list")
    if history_list:
        LINEAIRE_EVENT_PROXIES.append(
            add_proxy_listener(history_list, "click", lineaire_on_history_list_click)
        )

    LINEAIRE_EVENT_PROXIES = [proxy for proxy in LINEAIRE_EVENT_PROXIES if proxy]

    lineaire_render_result(None)
    lineaire_show_panel("tool")
    asyncio.create_task(lineaire_sync_history_view())


lineaire_start()
