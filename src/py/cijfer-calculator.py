import asyncio
from html import escape

import matplotlib.pyplot as plt  # ty:ignore[unresolved-import]
import numpy as np  # ty:ignore[unresolved-import]
from pyscript import display, when, window
from pyscript.ffi import create_proxy

CIJFER_TOOL_INDEX = 2
MINIMUM_ROW_COUNT = 2
CIJFER_LAST_RESULT = None
CIJFER_THEME_CHANGE_PROXY = None
CIJFER_GRADE_INPUT_PROXY = None
CIJFER_GRADE_KEYDOWN_PROXY = None
CIJFER_GRADE_CLICK_PROXY = None
CIJFER_HISTORY_CLICK_PROXY = None


def cijfer_clear_plot_output():
    plt.close("all")

    chart = get("cijfer-calculator-chart")  # ty:ignore[unresolved-reference]  # noqa: F821
    if chart:
        chart.innerHTML = ""


def cijfer_normalize_decimal_string(value):
    return str(value or "").strip().replace(".", ",")


def cijfer_parse_decimal_string(value):
    normalized_value = cijfer_normalize_decimal_string(value)
    if not normalized_value:
        return None

    return float(normalized_value.replace(",", "."))


def cijfer_format_value(value):
    if value is None:
        return "-"

    if float(value).is_integer():
        return str(int(value))

    return f"{value:.2f}".rstrip("0").rstrip(".").replace(".", ",")


def cijfer_build_grade_row_markup(index, value=""):
    safe_value = escape(cijfer_normalize_decimal_string(value), quote=True)
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
    normalized_values = [cijfer_normalize_decimal_string(value) for value in values]

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
    return [cijfer_normalize_decimal_string(input_element.value) for input_element in cijfer_get_grade_inputs()]


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
    if not input_element or selection is None or not hasattr(input_element, "setSelectionRange"):
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

    if focus_index is not None:
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
        selection = cijfer_get_grade_input_selection(cijfer_get_grade_input(focus_index))

    if current_values != normalized_values:
        cijfer_render_grade_rows(
            normalized_values,
            focus_index=focus_index,
            selection=selection,
        )


def cijfer_get_goal_input():
    return get("cijfer-calculator-doel")  # ty:ignore[unresolved-reference]  # noqa: F821


def cijfer_get_goal_value():
    goal_input = cijfer_get_goal_input()
    if not goal_input:
        return ""

    return cijfer_normalize_decimal_string(goal_input.value)


def cijfer_set_goal_value(value):
    goal_input = cijfer_get_goal_input()
    if goal_input:
        goal_input.value = cijfer_normalize_decimal_string(value)


def cijfer_read_form_values():
    return cijfer_get_grade_values(), cijfer_get_goal_value()


def cijfer_validate_inputs(grade_values, goal_value):
    parsed_grades = []

    for index, value in enumerate(grade_values, start=1):
        if not value:
            continue

        try:
            parsed_value = cijfer_parse_decimal_string(value)
        except ValueError:
            return None, f"Voer een geldig cijfer in op rij {index}."

        parsed_grades.append(parsed_value)

    if not parsed_grades:
        return None, "Vul minimaal een cijfer in."

    goal = None
    if goal_value:
        try:
            goal = cijfer_parse_decimal_string(goal_value)
        except ValueError:
            return None, "Voer een geldig gewenst gemiddelde in."

    return {"grades": parsed_grades, "goal": goal}, None


def cijfer_calculate_result(grades, goal=None):
    total = sum(grades)
    count = len(grades)
    average = total / count
    min_value = min(grades)
    max_value = max(grades)
    required_next_grade = None

    if goal is not None:
        required_next_grade = goal * (count + 1) - total

    return {
        "grades": grades,
        "goal": goal,
        "total": total,
        "count": count,
        "average": average,
        "min": min_value,
        "max": max_value,
        "required_next_grade": required_next_grade,
    }


def cijfer_render_empty_result(message):
    result_container = get("cijfer-calculator-result")  # ty:ignore[unresolved-reference]  # noqa: F821
    if not result_container:
        return

    result_container.innerHTML = f"""
        <div class="flex h-full min-h-96 items-center justify-center rounded-xl border border-dashed border-border/70 bg-background/60 p-6 text-center text-base-content/60">
            {escape(message)}
        </div>
    """


def cijfer_render_summary_card(title, value, icon_class, detail=""):
    return f"""
        <article class="card gap-0 p-0">
            <section class="p-4">
                <div class="flex items-center gap-2 text-sm font-semibold text-base-content/60">
                    <i class="{icon_class} size-4" aria-hidden="true"></i>
                    <span class="truncate">{title}</span>
                </div>
                <p class="mt-3 text-base">{value}</p>
            </section>
        </article>
    """


def cijfer_render_goal_card(result):
    goal = result["goal"]
    required_next_grade = result["required_next_grade"]
    if goal is None or required_next_grade is None:
        return ""

    goal_detail = cijfer_format_value(goal)
    if result["average"] >= goal:
        return cijfer_render_summary_card(
            "Doelstatus",
            "Behaald",
            "icon-[tabler--target-arrow]",
            f"Je huidige gemiddelde ligt al op of boven {cijfer_format_value(goal)}.",
        )

    if required_next_grade > 10:
        return cijfer_render_summary_card(
            "Volgend cijfer",
            cijfer_format_value(required_next_grade),
            "icon-[tabler--chart-line]",
            f"{goal_detail}. Met een 10 haal je dit doel nog niet in een extra cijfer.",
        )

    return cijfer_render_summary_card(
        "Volgend cijfer",
        cijfer_format_value(required_next_grade),
        "icon-[tabler--chart-line]",
        goal_detail,
    )


def cijfer_render_result(result=None, error=None):
    global CIJFER_LAST_RESULT

    if error or not result:
        CIJFER_LAST_RESULT = None
        cijfer_clear_plot_output()
        cijfer_render_empty_result(error or "Vul je cijfers in en klik op berekenen.")
        return

    CIJFER_LAST_RESULT = result

    result_container = get("cijfer-calculator-result")  # ty:ignore[unresolved-reference]  # noqa: F821
    if not result_container:
        return

    grades = result["grades"]
    average = result["average"]
    total = result["total"]
    count = result["count"]
    min_value = result["min"]
    max_value = result["max"]

    summary_cards = [
        cijfer_render_summary_card(
            "Gemiddelde",
            cijfer_format_value(average),
            "icon-[tabler--calculator]",
            f"{cijfer_format_value(min_value)} - {cijfer_format_value(max_value)}",
        ),
        cijfer_render_summary_card(
            "Totaal",
            cijfer_format_value(total),
            "icon-[tabler--plus]",
            "Som van alle ingevulde cijfers.",
        ),
    ]

    goal_card = cijfer_render_goal_card(result)
    if goal_card:
        summary_cards.append(goal_card)

    result_container.innerHTML = f"""
        <div class="space-y-4">
            <div
                id="cijfer-calculator-chart"
                class="flex min-h-80 items-center justify-center overflow-hidden [&_img]:block [&_img]:size-full [&_img]:max-w-full [&_img]:object-contain"
            ></div>
            <div class="grid gap-3 sm:grid-cols-2 xl:grid-cols-2 xl:[&:has(>article:nth-child(3):last-child)]:grid-cols-3">
                {''.join(summary_cards)}
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

    display(fig, target="cijfer-calculator-chart", append=False)
    plt.close(fig)


def cijfer_set_grade_values(values, focus_index=None, select=False):
    cijfer_render_grade_rows([cijfer_format_value(value) for value in values], focus_index, select)


def cijfer_set_form_values(grades, goal=None, focus_index=None):
    cijfer_set_grade_values(grades, focus_index=focus_index)
    cijfer_set_goal_value("" if goal is None else cijfer_format_value(goal))


def cijfer_show_panel(panel_name):
    panel_pairs = (
        ("tool", "cijfer-calculator-tool-tab", "cijfer-calculator-tool-panel"),
        ("history", "cijfer-calculator-history-tab", "cijfer-calculator-history-panel"),
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


def cijfer_sanitize_history_entries(history_entries):
    sanitized_entries = []
    changed = False

    for entry in history_entries:
        normalized_entry = cijfer_normalize_history_entry(entry)
        if not normalized_entry:
            changed = True
            continue

        if entry != normalized_entry:
            changed = True

        sanitized_entries.append(normalized_entry)

    return sanitized_entries, changed


def cijfer_render_grade_badges(grades):
    return "".join(
        f'<span class="badge-outline">{cijfer_format_value(grade)}</span>' for grade in grades
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

    if result["required_next_grade"] is not None and result["average"] < result["goal"]:
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
                    <div class="flex flex-wrap gap-2">{cijfer_render_grade_badges(entry['grades'])}</div>
                </div>
                <div class="min-w-0 flex flex-1 flex-wrap items-center gap-x-5 gap-y-3 rounded-xl border border-border/70 bg-card/85 p-3">
                    <div class="flex items-center gap-2">
                        <span class="badge-secondary">Resultaat</span>
                    </div>
                    <div class="flex flex-wrap gap-2">{''.join(output_badges)}</div>
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
    history_list = get("cijfer-calculator-history-list")  # ty:ignore[unresolved-reference]  # noqa: F821
    empty_state = get("cijfer-calculator-history-empty")  # ty:ignore[unresolved-reference]  # noqa: F821
    if not history_list or not empty_state:
        return

    if not history_entries:
        history_list.innerHTML = ""
        empty_state.hidden = False
        return

    history_list.innerHTML = "".join(
        cijfer_render_history_entry(entry, index)
        for index, entry in enumerate(history_entries)
    )
    empty_state.hidden = True


async def cijfer_sync_history_view():
    history_entries = await get_tool_history(CIJFER_TOOL_INDEX)  # ty:ignore[unresolved-reference]  # noqa: F821
    sanitized_entries, changed = cijfer_sanitize_history_entries(history_entries)

    if changed:
        sanitized_entries = await set_tool_history(  # ty:ignore[unresolved-reference]  # noqa: F821
            CIJFER_TOOL_INDEX, sanitized_entries
        )

    cijfer_render_history_entries(sanitized_entries)
    return sanitized_entries


async def cijfer_restore_history_entry(history_index):
    history_entries = await cijfer_sync_history_view()
    if history_index < 0 or history_index >= len(history_entries):
        return

    entry = history_entries[history_index]
    cijfer_set_form_values(entry["grades"], entry.get("goal"), focus_index=0)
    cijfer_render_result(cijfer_calculate_result(entry["grades"], entry.get("goal")))
    cijfer_show_panel("tool")


async def cijfer_delete_history_entry(history_index):
    await delete_tool_history_entry(CIJFER_TOOL_INDEX, history_index)  # ty:ignore[unresolved-reference]  # noqa: F821
    await cijfer_sync_history_view()


async def cijfer_handle_history_action(action, history_index):
    if action == "restore":
        await cijfer_restore_history_entry(history_index)
        return

    if action == "delete":
        await cijfer_delete_history_entry(history_index)


def cijfer_get_event_grade_input(event):
    target = getattr(event, "target", None)
    if not target or not hasattr(target, "closest"):
        return None

    return target.closest("[data-grade-input]")


def cijfer_get_row_index(element):
    if not element:
        return None

    try:
        return int(element.dataset.gradeIndex)
    except (AttributeError, TypeError, ValueError):
        return None


def cijfer_move_grade_focus(current_index, backwards=False):
    if current_index is None:
        return False

    if backwards:
        return (
            cijfer_focus_grade_input(current_index - 1, select=True)
            if current_index > 0
            else False
        )

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

    normalized_value = cijfer_normalize_decimal_string(target.value)
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
    target = getattr(event, "target", None)
    if not rows_container or not target or not hasattr(target, "closest"):
        return

    remove_button = target.closest("[data-grade-remove]")
    if not remove_button or not rows_container.contains(remove_button):
        return

    row_index = cijfer_get_row_index(remove_button)
    if row_index is None:
        return

    grade_values = cijfer_get_grade_values()
    if row_index < 0 or row_index >= len(grade_values):
        return

    del grade_values[row_index]
    cijfer_render_grade_rows(grade_values, focus_index=max(0, row_index - 1))


def cijfer_on_history_list_click(event):
    history_list = get("cijfer-calculator-history-list")  # ty:ignore[unresolved-reference]  # noqa: F821
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

    asyncio.create_task(cijfer_handle_history_action(history_action, history_index))


def cijfer_on_theme_change(_event):
    if CIJFER_LAST_RESULT:
        cijfer_render_result(CIJFER_LAST_RESULT)


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
    global CIJFER_THEME_CHANGE_PROXY, CIJFER_GRADE_INPUT_PROXY, CIJFER_GRADE_KEYDOWN_PROXY, CIJFER_GRADE_CLICK_PROXY, CIJFER_HISTORY_CLICK_PROXY

    cijfer_render_grade_rows([])

    rows_container = cijfer_get_grade_rows_container()
    history_list = get("cijfer-calculator-history-list")  # ty:ignore[unresolved-reference]  # noqa: F821

    CIJFER_THEME_CHANGE_PROXY = create_proxy(cijfer_on_theme_change)
    window.addEventListener("app:themechange", CIJFER_THEME_CHANGE_PROXY)

    if rows_container:
        CIJFER_GRADE_INPUT_PROXY = create_proxy(cijfer_on_grade_input)
        CIJFER_GRADE_KEYDOWN_PROXY = create_proxy(cijfer_on_grade_keydown)
        CIJFER_GRADE_CLICK_PROXY = create_proxy(cijfer_on_grade_click)
        rows_container.addEventListener("input", CIJFER_GRADE_INPUT_PROXY)
        rows_container.addEventListener("keydown", CIJFER_GRADE_KEYDOWN_PROXY)
        rows_container.addEventListener("click", CIJFER_GRADE_CLICK_PROXY)

    if history_list:
        CIJFER_HISTORY_CLICK_PROXY = create_proxy(cijfer_on_history_list_click)
        history_list.addEventListener("click", CIJFER_HISTORY_CLICK_PROXY)

    cijfer_show_panel("tool")
    asyncio.create_task(cijfer_sync_history_view())


cijfer_start()
