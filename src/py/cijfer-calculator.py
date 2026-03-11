import asyncio
from html import escape

import matplotlib.pyplot as plt  # ty:ignore[unresolved-import]
import numpy as np  # ty:ignore[unresolved-import]
from pyscript import when, window

CIJFER_TOOL_INDEX = 2
MINIMUM_ROW_COUNT = 2
CIJFER_LAST_RESULT = None
CIJFER_EVENT_PROXIES = []

CIJFER_RESULT_CONTAINER_ID = "cijfer-calculator-result"
CIJFER_CHART_TARGET_ID = "cijfer-calculator-chart"
CIJFER_PANEL_CONFIGS = (
    ("tool", "cijfer-calculator-tool-tab", "cijfer-calculator-tool-panel"),
    (
        "history",
        "cijfer-calculator-history-tab",
        "cijfer-calculator-history-panel",
    ),
)


def cijfer_format_value(value):
    return format_number(value, decimal_separator=",", empty_value="-")  # ty:ignore[unresolved-reference]  # noqa: F821


def cijfer_normalize_decimal_value(value):
    return normalize_decimal_input(value, decimal_separator=",")  # ty:ignore[unresolved-reference]  # noqa: F821


def cijfer_parse_decimal_value(value):
    return parse_number(value)  # ty:ignore[unresolved-reference]  # noqa: F821


def cijfer_clear_plot_output():
    clear_matplotlib_target(CIJFER_CHART_TARGET_ID)  # ty:ignore[unresolved-reference]  # noqa: F821


def cijfer_build_grade_row_markup(index, value=""):
    safe_value = escape(cijfer_normalize_decimal_value(value), quote=True)
    row_number = index + 1

    return f"""
        <tr data-grade-row data-grade-index="{index}">
            <th class="font-semibold text-base-content/60">{row_number}</th>
            <td>
                <input
                    type="text"
                    inputmode="decimal"
                    class="input w-full"
                    data-grade-input
                    data-grade-index="{index}"
                    aria-label="Cijfer {row_number}"
                    placeholder="Bijvoorbeeld: 7,5"
                    value="{safe_value}"
                />
            </td>
            <td class="text-right">
                <button
                    type="button"
                    class="btn-outline h-9 w-9 p-0"
                    data-grade-remove
                    data-grade-index="{index}"
                    aria-label="Verwijder rij {row_number}"
                >
                    <i class="icon-[tabler--trash] mx-auto size-4" aria-hidden="true"></i>
                </button>
            </td>
        </tr>
    """


def cijfer_normalize_grade_row_values(values):
    normalized_values = [cijfer_normalize_decimal_value(value) for value in values]

    while normalized_values and not normalized_values[-1]:
        normalized_values.pop()

    target_count = max(MINIMUM_ROW_COUNT, len(normalized_values) + 1)

    while len(normalized_values) < target_count:
        normalized_values.append("")

    return normalized_values


def cijfer_get_grade_rows_container():
    return get("cijfer-calculator-grade-rows")  # ty:ignore[unresolved-reference]  # noqa: F821


def cijfer_get_grade_inputs():
    rows_container = cijfer_get_grade_rows_container()
    if not rows_container:
        return []

    return list(rows_container.querySelectorAll("[data-grade-input]"))


def cijfer_get_grade_values():
    return [
        cijfer_normalize_decimal_value(input_element.value)
        for input_element in cijfer_get_grade_inputs()
    ]


def cijfer_get_grade_input(index):
    rows_container = cijfer_get_grade_rows_container()
    if not rows_container:
        return None

    return rows_container.querySelector(
        f'[data-grade-input][data-grade-index="{index}"]'
    )


def cijfer_focus_grade_input(index, select=False):
    input_element = cijfer_get_grade_input(index)
    if not input_element:
        return False

    input_element.focus()
    if select and hasattr(input_element, "select"):
        input_element.select()

    return True


def cijfer_get_grade_input_selection(input_element):
    if not input_element:
        return None

    try:
        selection_start = input_element.selectionStart
        selection_end = input_element.selectionEnd
    except AttributeError:
        return None

    if selection_start is None or selection_end is None:
        return None

    return selection_start, selection_end


def cijfer_restore_grade_input_selection(input_element, selection):
    if (
        not input_element
        or selection is None
        or not hasattr(input_element, "setSelectionRange")
    ):
        return

    selection_start, selection_end = selection
    value_length = len(str(input_element.value or ""))
    clamped_start = max(0, min(selection_start, value_length))
    clamped_end = max(clamped_start, min(selection_end, value_length))
    input_element.setSelectionRange(clamped_start, clamped_end)


def cijfer_render_grade_rows(values, focus_index=None, select=False, selection=None):
    rows_container = cijfer_get_grade_rows_container()
    if not rows_container:
        return

    normalized_values = cijfer_normalize_grade_row_values(values)
    rows_container.innerHTML = "".join(
        cijfer_build_grade_row_markup(index, value)
        for index, value in enumerate(normalized_values)
    )

    if focus_index is None:
        return

    clamped_index = max(0, min(focus_index, len(normalized_values) - 1))
    if cijfer_focus_grade_input(clamped_index, select=select):
        cijfer_restore_grade_input_selection(
            cijfer_get_grade_input(clamped_index), selection if not select else None
        )


def cijfer_sync_grade_rows(focus_index=None):
    current_values = cijfer_get_grade_values()
    normalized_values = cijfer_normalize_grade_row_values(current_values)
    selection = None

    if focus_index is not None:
        selection = cijfer_get_grade_input_selection(
            cijfer_get_grade_input(focus_index)
        )

    if current_values != normalized_values:
        cijfer_render_grade_rows(
            normalized_values,
            focus_index=focus_index,
            selection=selection,
        )


def cijfer_get_goal_value():
    return cijfer_normalize_decimal_value(
        read_text_input_value("cijfer-calculator-doel")  # ty:ignore[unresolved-reference]  # noqa: F821
    )


def cijfer_set_goal_value(value):
    set_element_value("cijfer-calculator-doel", cijfer_normalize_decimal_value(value))  # ty:ignore[unresolved-reference]  # noqa: F821


def cijfer_read_form_values():
    return cijfer_get_grade_values(), cijfer_get_goal_value()


def cijfer_validate_inputs(grade_values, goal_value):
    parsed_grades = []

    for index, value in enumerate(grade_values, start=1):
        if not value:
            continue

        try:
            parsed_value = cijfer_parse_decimal_value(value)
        except ValueError:
            return None, f"Voer een geldig cijfer in op rij {index}."

        parsed_grades.append(parsed_value)

    if not parsed_grades:
        return None, "Vul minimaal een cijfer in."

    goal = None
    if goal_value:
        try:
            goal = cijfer_parse_decimal_value(goal_value)
        except ValueError:
            return None, "Voer een geldig gewenst gemiddelde in."

    return {"grades": parsed_grades, "goal": goal}, None


def cijfer_calculate_result(grades, goal=None):
    total = sum(grades)
    count = len(grades)
    average = total / count
    required_next_grade = None

    if goal is not None:
        required_next_grade = goal * (count + 1) - total

    return {
        "grades": grades,
        "goal": goal,
        "total": total,
        "count": count,
        "average": average,
        "min": min(grades),
        "max": max(grades),
        "required_next_grade": required_next_grade,
    }


def cijfer_render_goal_card(result):
    goal = result["goal"]
    required_next_grade = result["required_next_grade"]
    if goal is None or required_next_grade is None:
        return ""

    if result["average"] >= goal:
        return render_summary_card(  # ty:ignore[unresolved-reference]  # noqa: F821
            "Doelstatus",
            "Behaald",
            "icon-[tabler--target-arrow]",
        )

    return render_summary_card(  # ty:ignore[unresolved-reference]  # noqa: F821
        "Volgend cijfer",
        cijfer_format_value(required_next_grade),
        "icon-[tabler--chart-line]",
    )


def cijfer_render_result(result=None, error=None):
    global CIJFER_LAST_RESULT

    if error or not result:
        CIJFER_LAST_RESULT = None
        render_state_card(  # ty:ignore[unresolved-reference]  # noqa: F821
            CIJFER_RESULT_CONTAINER_ID,
            error or "Vul je cijfers in en klik op berekenen.",
            clear_plot=cijfer_clear_plot_output,
        )
        return

    CIJFER_LAST_RESULT = result

    result_container = get(CIJFER_RESULT_CONTAINER_ID)  # ty:ignore[unresolved-reference]  # noqa: F821
    if not result_container:
        return

    grades = result["grades"]
    average = result["average"]
    total = result["total"]
    count = result["count"]

    summary_cards = [
        render_summary_card(  # ty:ignore[unresolved-reference]  # noqa: F821
            "Gemiddelde",
            cijfer_format_value(average),
            "icon-[tabler--calculator]",
        ),
        render_summary_card(  # ty:ignore[unresolved-reference]  # noqa: F821
            "Totaal",
            cijfer_format_value(total),
            "icon-[tabler--plus]",
        ),
    ]

    goal_card = cijfer_render_goal_card(result)
    if goal_card:
        summary_cards.append(goal_card)

    result_container.innerHTML = f"""
        <div class="space-y-4">
            <div
                id="{CIJFER_CHART_TARGET_ID}"
                class="flex min-h-80 items-center justify-center overflow-hidden [&_img]:block [&_img]:size-full [&_img]:max-w-full [&_img]:object-contain"
            ></div>
            <div class="grid gap-3 sm:grid-cols-2 xl:grid-cols-2 xl:[&:has(>article:nth-child(3):last-child)]:grid-cols-3">
                {"".join(summary_cards)}
            </div>
        </div>
    """

    cijfer_clear_plot_output()

    x_positions = np.arange(1, count + 1)
    fig, ax = plt.subplots(figsize=(8, 4.6))
    theme = apply_matplotlib_theme(fig, ax)  # ty:ignore[unresolved-reference]  # noqa: F821
    chart_colors = theme["chart_colors"]
    bar_color = chart_colors[0] or theme["text_color"]
    average_color = chart_colors[2] or theme["danger_color"]
    goal_color = chart_colors[4] or theme["danger_color"]

    bars = ax.bar(
        x_positions,
        grades,
        color=bar_color,
        edgecolor=theme["border_color"] or theme["surface_color"],
        linewidth=1.2,
    )

    for bar, grade in zip(bars, grades):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            cijfer_format_value(grade),
            ha="center",
            va="bottom",
            color=theme["text_color"],
            fontsize=10,
        )

    ax.axhline(
        average,
        color=average_color,
        linestyle="--",
        linewidth=2,
    )

    if result["goal"] is not None:
        ax.axhline(
            result["goal"],
            color=goal_color,
            linestyle=":",
            linewidth=2,
        )

    values_for_limits = list(grades) + [average]
    if result["goal"] is not None:
        values_for_limits.append(result["goal"])

    min_limit = min(values_for_limits)
    max_limit = max(values_for_limits)
    padding = max(1, (max_limit - min_limit) * 0.18)
    ax.set_ylim(min(0, min_limit - padding * 0.35), max_limit + padding)
    ax.set_xticks(x_positions)
    ax.set_xticklabels([str(index) for index in x_positions])
    ax.set_xlabel("Cijfernummer")
    ax.set_ylabel("Waarde")
    ax.grid(True, axis="y", color=theme["grid_color"], alpha=0.25)
    ax.set_axisbelow(True)

    display_matplotlib_figure(fig, CIJFER_CHART_TARGET_ID, append=False)  # ty:ignore[unresolved-reference]  # noqa: F821


def cijfer_set_grade_values(values, focus_index=None, select=False):
    cijfer_render_grade_rows(
        [cijfer_format_value(value) for value in values],
        focus_index=focus_index,
        select=select,
    )


def cijfer_set_form_values(grades, goal=None, focus_index=None):
    cijfer_set_grade_values(grades, focus_index=focus_index)
    cijfer_set_goal_value("" if goal is None else cijfer_format_value(goal))


def cijfer_show_panel(panel_name):
    show_tab_panel(panel_name, CIJFER_PANEL_CONFIGS)  # ty:ignore[unresolved-reference]  # noqa: F821


def cijfer_normalize_history_entry(entry):
    if not isinstance(entry, dict):
        return None

    grades = entry.get("grades")
    if not isinstance(grades, list) or not grades:
        return None

    normalized_grades = []
    for value in grades:
        try:
            normalized_grades.append(float(value))
        except (TypeError, ValueError):
            return None

    goal_value = entry.get("goal")
    normalized_goal = None
    if goal_value not in (None, ""):
        try:
            normalized_goal = float(goal_value)
        except (TypeError, ValueError):
            return None

    return {"grades": normalized_grades, "goal": normalized_goal}


def cijfer_render_grade_badges(grades):
    return "".join(
        f'<span class="badge-outline">{cijfer_format_value(grade)}</span>'
        for grade in grades
    )


def cijfer_render_history_entry(entry, index):
    result = cijfer_calculate_result(entry["grades"], entry.get("goal"))

    output_badges = [
        f'<span class="badge-secondary">Gemiddelde {cijfer_format_value(result["average"])} </span>',
        f'<span class="badge-secondary">Totaal {cijfer_format_value(result["total"])} </span>',
        f'<span class="badge-secondary">Aantal {result["count"]}</span>',
    ]

    if result["goal"] is not None:
        output_badges.append(
            f'<span class="badge-secondary">Doel {cijfer_format_value(result["goal"])} </span>'
        )

    if result["required_next_grade"] is not None and result["goal"] is not None:
        if result["average"] < result["goal"]:
            output_badges.append(
                f'<span class="badge-secondary">Volgende {cijfer_format_value(result["required_next_grade"])} </span>'
            )

    return f"""
        <article class="card p-0">
            <section class="flex flex-wrap items-center gap-3 p-4 xl:flex-nowrap">
                <div class="min-w-0 flex flex-1 flex-wrap items-center gap-x-5 gap-y-3 rounded-xl border border-border/70 bg-card/85 p-3">
                    <div class="flex items-center gap-2">
                        <span class="badge-outline">Cijfers</span>
                    </div>
                    <div class="flex flex-wrap gap-2">{cijfer_render_grade_badges(entry["grades"])}</div>
                </div>
                <div class="min-w-0 flex flex-1 flex-wrap items-center gap-x-5 gap-y-3 rounded-xl border border-border/70 bg-card/85 p-3">
                    <div class="flex items-center gap-2">
                        <span class="badge-secondary">Resultaat</span>
                    </div>
                    <div class="flex flex-wrap gap-2">{"".join(output_badges)}</div>
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


def cijfer_render_history_entries(history_entries):
    render_history_list(  # ty:ignore[unresolved-reference]  # noqa: F821
        "cijfer-calculator-history-list",
        "cijfer-calculator-history-empty",
        history_entries,
        cijfer_render_history_entry,
    )


def cijfer_get_event_grade_input(event):
    return get_delegated_target(event, "[data-grade-input]")  # ty:ignore[unresolved-reference]  # noqa: F821


def cijfer_get_row_index(element):
    return get_dataset_int(element, "gradeIndex")  # ty:ignore[unresolved-reference]  # noqa: F821


def cijfer_move_grade_focus(current_index, backwards=False):
    if current_index is None:
        return False

    if backwards:
        if current_index <= 0:
            return False
        return cijfer_focus_grade_input(current_index - 1, select=True)

    current_values = cijfer_get_grade_values()
    normalized_values = cijfer_normalize_grade_row_values(current_values)

    if len(normalized_values) != len(current_values):
        cijfer_render_grade_rows(normalized_values, focus_index=current_index)

    next_index = current_index + 1
    if next_index >= len(normalized_values):
        normalized_values.append("")
        cijfer_render_grade_rows(normalized_values, focus_index=next_index, select=True)
        return True

    return cijfer_focus_grade_input(next_index, select=True)


def cijfer_on_grade_input(event):
    target = cijfer_get_event_grade_input(event)
    if not target:
        return

    normalized_value = cijfer_normalize_decimal_value(target.value)
    if target.value != normalized_value:
        target.value = normalized_value

    cijfer_sync_grade_rows(focus_index=cijfer_get_row_index(target))


def cijfer_on_grade_keydown(event):
    target = cijfer_get_event_grade_input(event)
    if not target:
        return

    key = getattr(event, "key", "")
    if key not in ("Enter", "Tab"):
        return

    backwards = bool(getattr(event, "shiftKey", False)) and key == "Tab"
    moved = cijfer_move_grade_focus(cijfer_get_row_index(target), backwards=backwards)

    if moved or key == "Enter":
        event.preventDefault()


def cijfer_on_grade_click(event):
    rows_container = cijfer_get_grade_rows_container()
    remove_button = get_delegated_target(event, "[data-grade-remove]", rows_container)  # ty:ignore[unresolved-reference]  # noqa: F821
    if not remove_button:
        return

    row_index = cijfer_get_row_index(remove_button)
    grade_values = cijfer_get_grade_values()

    if row_index is None or row_index < 0 or row_index >= len(grade_values):
        return

    del grade_values[row_index]
    cijfer_render_grade_rows(grade_values, focus_index=max(0, row_index - 1))


def cijfer_on_history_list_click(event):
    dispatch_history_click(  # ty:ignore[unresolved-reference]  # noqa: F821
        event,
        get("cijfer-calculator-history-list"),  # ty:ignore[unresolved-reference]  # noqa: F821
        cijfer_handle_history_action,
    )


def cijfer_on_theme_change(_event):
    if CIJFER_LAST_RESULT:
        cijfer_render_result(CIJFER_LAST_RESULT)


async def cijfer_sync_history_view():
    return await sync_tool_history_view(  # ty:ignore[unresolved-reference]  # noqa: F821
        CIJFER_TOOL_INDEX,
        cijfer_normalize_history_entry,
        cijfer_render_history_entries,
    )


async def cijfer_restore_history_entry(history_index):
    history_entries = await cijfer_sync_history_view()
    if history_index < 0 or history_index >= len(history_entries):
        return

    entry = history_entries[history_index]
    cijfer_set_form_values(entry["grades"], entry.get("goal"), focus_index=0)
    cijfer_render_result(cijfer_calculate_result(entry["grades"], entry.get("goal")))
    cijfer_show_panel("tool")


async def cijfer_delete_history_entry(history_index):
    await delete_tool_history_and_refresh(  # ty:ignore[unresolved-reference]  # noqa: F821
        CIJFER_TOOL_INDEX,
        history_index,
        cijfer_sync_history_view,
    )


async def cijfer_handle_history_action(action, history_index):
    if action == "restore":
        await cijfer_restore_history_entry(history_index)
        return

    if action == "delete":
        await cijfer_delete_history_entry(history_index)


@when("click", "#cijfer-calculator-berekenen")
async def cijfer_bereken_click(_event):
    values, error = cijfer_validate_inputs(*cijfer_read_form_values())
    if error:
        cijfer_render_result(None, error)
        return

    result = cijfer_calculate_result(values["grades"], values["goal"])
    cijfer_render_result(result)

    await append_tool_history(  # ty:ignore[unresolved-reference]  # noqa: F821
        CIJFER_TOOL_INDEX,
        {
            "grades": values["grades"],
            "goal": values["goal"],
        },
    )
    await cijfer_sync_history_view()


@when("click", "#cijfer-calculator-tool-tab")
def cijfer_tool_tab_click(_event):
    cijfer_show_panel("tool")


@when("click", "#cijfer-calculator-history-tab")
async def cijfer_history_tab_click(_event):
    await cijfer_sync_history_view()
    cijfer_show_panel("history")


@when("click", "#cijfer-calculator-reset")
def cijfer_reset_click(_event):
    cijfer_set_form_values([], None, focus_index=0)
    cijfer_render_result(None)


def cijfer_start():
    global CIJFER_EVENT_PROXIES

    cijfer_render_grade_rows([])

    rows_container = cijfer_get_grade_rows_container()
    history_list = get("cijfer-calculator-history-list")  # ty:ignore[unresolved-reference]  # noqa: F821

    CIJFER_EVENT_PROXIES = [
        add_proxy_listener(window, "app:themechange", cijfer_on_theme_change),  # ty:ignore[unresolved-reference]  # noqa: F821
    ]

    if rows_container:
        CIJFER_EVENT_PROXIES.extend(
            [
                add_proxy_listener(rows_container, "input", cijfer_on_grade_input),  # ty:ignore[unresolved-reference]  # noqa: F821
                add_proxy_listener(rows_container, "keydown", cijfer_on_grade_keydown),  # ty:ignore[unresolved-reference]  # noqa: F821
                add_proxy_listener(rows_container, "click", cijfer_on_grade_click),  # ty:ignore[unresolved-reference]  # noqa: F821
            ]
        )

    if history_list:
        CIJFER_EVENT_PROXIES.append(
            add_proxy_listener(history_list, "click", cijfer_on_history_list_click)  # ty:ignore[unresolved-reference]  # noqa: F821
        )

    CIJFER_EVENT_PROXIES = [proxy for proxy in CIJFER_EVENT_PROXIES if proxy]

    cijfer_show_panel("tool")
    asyncio.create_task(cijfer_sync_history_view())


cijfer_start()
