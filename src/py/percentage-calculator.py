import asyncio

import matplotlib.pyplot as plt  # ty:ignore[unresolved-import]
from pyscript import display, when, window
from pyscript.ffi import create_proxy

PERCENTAGE_TOOL_INDEX = 3
PERCENTAGE_LAST_RESULT = None
PERCENTAGE_THEME_CHANGE_PROXY = None
PERCENTAGE_HISTORY_CLICK_PROXY = None

PERCENTAGE_MODE_CONFIGS = {
    "deel-van-totaal": {
        "badge": "Deel van totaal",
        "description": "",
        "formula": "percentage = (deel / totaal) x 100",
        "value_1": {
            "label": "Deel",
            "placeholder": "Bijvoorbeeld: 25",
            "help": "Vul het deel in dat je wilt vergelijken.",
            "history_label": "Deel",
        },
        "value_2": {
            "label": "Totaal",
            "placeholder": "Bijvoorbeeld: 80",
            "help": "Vul het totaal in waar het deel van afkomt.",
            "history_label": "Totaal",
        },
        "show_iterations": False,
        "result_label": "Percentage",
    },
    "korting": {
        "badge": "Korting",
        "description": "",
        "formula": "nieuw = oud - (percentage / 100 x oud)",
        "value_1": {
            "label": "Oude waarde",
            "placeholder": "Bijvoorbeeld: 80",
            "help": "Vul de oorspronkelijke waarde in.",
            "history_label": "Oud",
        },
        "value_2": {
            "label": "Korting (%)",
            "placeholder": "Bijvoorbeeld: 25",
            "help": "Vul het kortingspercentage in.",
            "history_label": "%",
        },
        "show_iterations": False,
        "result_label": "Nieuwe waarde",
    },
    "stijging": {
        "badge": "Stijging",
        "description": "",
        "formula": "nieuw = oud + (percentage / 100 x oud)",
        "value_1": {
            "label": "Beginwaarde",
            "placeholder": "Bijvoorbeeld: 100",
            "help": "Vul de waarde in waar je mee start.",
            "history_label": "Start",
        },
        "value_2": {
            "label": "Stijging (%)",
            "placeholder": "Bijvoorbeeld: 5",
            "help": "Vul het stijgingspercentage in.",
            "history_label": "%",
        },
        "show_iterations": True,
        "result_label": "Nieuwe waarde",
    },
    "verschil": {
        "badge": "Procentverschil",
        "description": "",
        "formula": "verschil % = ((nieuw - oud) / oud) x 100",
        "value_1": {
            "label": "Eerste getal",
            "placeholder": "Bijvoorbeeld: 40",
            "help": "Vul de beginwaarde in.",
            "history_label": "Van",
        },
        "value_2": {
            "label": "Tweede getal",
            "placeholder": "Bijvoorbeeld: 50",
            "help": "Vul de nieuwe waarde in.",
            "history_label": "Naar",
        },
        "show_iterations": False,
        "result_label": "Verschil in %",
    },
}

PERCENTAGE_DEFAULT_MODE = "deel-van-totaal"


def percentage_get_mode_config(mode):
    if mode in PERCENTAGE_MODE_CONFIGS:
        return PERCENTAGE_MODE_CONFIGS[mode]

    return PERCENTAGE_MODE_CONFIGS[PERCENTAGE_DEFAULT_MODE]


def percentage_get_mode_value():
    mode_select = get("percentage-calculator-mode")  # noqa: F821
    if not mode_select or not mode_select.value:
        return PERCENTAGE_DEFAULT_MODE

    return mode_select.value


def percentage_format_value(value):
    numeric_value = float(value)
    if numeric_value.is_integer():
        return str(int(numeric_value))

    return f"{numeric_value:.2f}".rstrip("0").rstrip(".")


def percentage_format_percent(value, include_sign=False):
    numeric_value = float(value)
    sign = ""
    if include_sign and numeric_value > 0:
        sign = "+"

    return f"{sign}{percentage_format_value(numeric_value)}%"


def percentage_parse_number(value):
    normalized_value = str(value).strip().replace(",", ".")
    if not normalized_value:
        raise ValueError("missing")

    return float(normalized_value)


def percentage_parse_iterations(value):
    normalized_value = str(value).strip()
    if not normalized_value:
        return 1

    parsed_value = int(normalized_value)
    if parsed_value < 1:
        raise ValueError("iterations")

    return parsed_value


def percentage_get_input_state():
    mode = percentage_get_mode_value()
    value_1_input = get("percentage-calculator-waarde-1")  # noqa: F821
    value_2_input = get("percentage-calculator-waarde-2")  # noqa: F821
    iterations_input = get("percentage-calculator-iterations")  # noqa: F821

    return {
        "mode": mode,
        "value_1": value_1_input.value.strip() if value_1_input else "",
        "value_2": value_2_input.value.strip() if value_2_input else "",
        "iterations": iterations_input.value.strip() if iterations_input else "1",
    }


def percentage_validate_input_state(state):
    mode = state.get("mode", PERCENTAGE_DEFAULT_MODE)
    value_1_raw = state.get("value_1", "")
    value_2_raw = state.get("value_2", "")
    iterations_raw = state.get("iterations", "1")

    if not value_1_raw or not value_2_raw:
        return None, "Vul alle verplichte velden in."

    try:
        value_1 = percentage_parse_number(value_1_raw)
        value_2 = percentage_parse_number(value_2_raw)
    except ValueError:
        return None, "Voer geldige getallen in."

    try:
        iterations = percentage_parse_iterations(iterations_raw)
    except ValueError:
        return None, "Het aantal keer toepassen moet een positief geheel getal zijn."

    if mode == "deel-van-totaal":
        if value_1 < 0:
            return None, "Het deel mag niet negatief zijn."
        if value_2 <= 0:
            return None, "Het totaal moet groter zijn dan 0."

    elif mode == "korting":
        if value_1 < 0:
            return None, "De oude waarde mag niet negatief zijn."
        if value_2 < 0:
            return None, "Het kortingspercentage mag niet negatief zijn."

    elif mode == "stijging":
        if value_1 < 0:
            return None, "De beginwaarde mag niet negatief zijn."
        if value_2 < 0:
            return None, "Het stijgingspercentage mag niet negatief zijn."

    elif mode == "verschil":
        if value_1 == 0:
            return None, "Het eerste getal mag niet 0 zijn bij een procentverschil."

    return {
        "mode": mode,
        "value_1": value_1,
        "value_2": value_2,
        "iterations": iterations,
    }, None


def percentage_calculate_percentage_result(validated_state):
    mode = validated_state["mode"]
    value_1 = validated_state["value_1"]
    value_2 = validated_state["value_2"]
    iterations = validated_state["iterations"]

    if mode == "deel-van-totaal":
        ratio = value_1 / value_2
        percentage = ratio * 100
        remainder_percentage = max(((value_2 - value_1) / value_2) * 100, 0)
        return {
            "mode": mode,
            "headline": f"{percentage_format_value(value_1)} is {percentage_format_percent(percentage)} van {percentage_format_value(value_2)}.",
            "summary": "Je deelt eerst het deel door het totaal en zet die uitkomst daarna om naar procenten.",
            "part": value_1,
            "total": value_2,
            "percentage": percentage,
            "remainder_percentage": remainder_percentage,
            "cards": (
                {"label": "Percentage", "value": percentage_format_percent(percentage)},
                {"label": "Rest", "value": percentage_format_percent(remainder_percentage)},
            ),
            "steps": (
                f"Deel het deel door het totaal: {percentage_format_value(value_1)} / {percentage_format_value(value_2)} = {percentage_format_value(ratio)}.",
                f"Vermenigvuldig met 100: {percentage_format_value(ratio)} x 100 = {percentage_format_percent(percentage)}.",
            ),
            "history_result": percentage,
        }

    if mode == "korting":
        discount_amount = (value_2 / 100) * value_1
        new_value = value_1 - discount_amount
        return {
            "mode": mode,
            "headline": f"Na {percentage_format_percent(value_2)} korting blijft {percentage_format_value(new_value)} over.",
            "summary": "De tool berekent eerst hoeveel het percentage van de oude waarde is en haalt dat bedrag daarna eraf.",
            "old_value": value_1,
            "percentage": value_2,
            "change_amount": discount_amount,
            "new_value": new_value,
            "cards": (
                {"label": "Korting", "value": percentage_format_value(discount_amount)},
                {"label": "Nieuwe waarde", "value": percentage_format_value(new_value)},
            ),
            "steps": (
                f"Bereken de korting: {percentage_format_percent(value_2)} van {percentage_format_value(value_1)} = {percentage_format_value(discount_amount)}.",
                f"Haal de korting eraf: {percentage_format_value(value_1)} - {percentage_format_value(discount_amount)} = {percentage_format_value(new_value)}.",
            ),
            "history_result": new_value,
        }

    if mode == "stijging":
        current_value = value_1
        progression = [value_1]
        step_lines = []

        for step_index in range(iterations):
            previous_value = current_value
            increase_amount = (value_2 / 100) * current_value
            next_value = current_value + increase_amount
            progression.append(next_value)
            step_lines.append(
                f"Stap {step_index + 1}: {percentage_format_percent(value_2)} van {percentage_format_value(previous_value)} = {percentage_format_value(increase_amount)}; {percentage_format_value(previous_value)} + {percentage_format_value(increase_amount)} = {percentage_format_value(next_value)}."
            )
            current_value = next_value

        total_increase = current_value - value_1
        summary = "De stijging wordt elke keer opnieuw op de nieuwste waarde toegepast."
        if iterations == 1:
            summary = "De tool telt het berekende percentage op bij de beginwaarde."

        return {
            "mode": mode,
            "headline": f"Na {iterations} keer {percentage_format_percent(value_2)} stijging wordt {percentage_format_value(value_1)} gelijk aan {percentage_format_value(current_value)}.",
            "summary": summary,
            "start_value": value_1,
            "percentage": value_2,
            "new_value": current_value,
            "total_increase": total_increase,
            "progression": tuple(progression),
            "cards": (
                {"label": "Totale toename", "value": percentage_format_value(total_increase)},
                {"label": "Nieuwe waarde", "value": percentage_format_value(current_value)},
            ),
            "steps": tuple(step_lines),
            "history_result": current_value,
        }

    change_amount = value_2 - value_1
    percentage_change = (change_amount / value_1) * 100
    direction = "stijging" if change_amount >= 0 else "daling"
    return {
        "mode": mode,
        "headline": f"Van {percentage_format_value(value_1)} naar {percentage_format_value(value_2)} is een {direction} van {percentage_format_percent(abs(percentage_change))}.",
        "summary": "Je bekijkt eerst het verschil tussen de twee getallen en vergelijkt dat daarna met de beginwaarde.",
        "old_value": value_1,
        "new_value": value_2,
        "change_amount": change_amount,
        "percentage_change": percentage_change,
        "cards": (
            {
                "label": "Verschil in %",
                "value": percentage_format_percent(percentage_change, include_sign=True),
            },
        ),
        "steps": (
            f"Bereken het verschil: {percentage_format_value(value_2)} - {percentage_format_value(value_1)} = {percentage_format_value(change_amount)}.",
            f"Deel door de beginwaarde: {percentage_format_value(change_amount)} / {percentage_format_value(value_1)} = {percentage_format_value(change_amount / value_1)}.",
            f"Vermenigvuldig met 100: {percentage_format_value(change_amount / value_1)} x 100 = {percentage_format_percent(percentage_change, include_sign=True)}.",
        ),
        "history_result": percentage_change,
    }


def percentage_clear_plot_output():
    plt.close("all")

    target_div = get("percentage-calculator-mpl")  # ty:ignore[unresolved-reference]  # noqa: F821
    if target_div:
        target_div.innerHTML = ""


def percentage_render_placeholder():
    percentage_clear_plot_output()

    result_container = get("percentage-calculator-result")  # noqa: F821
    if not result_container:
        return

    result_container.innerHTML = """
        <div class="flex h-full min-h-96 items-center justify-center rounded-xl border border-dashed border-border/70 bg-background/60 p-6 text-center text-base-content/60">
            Kies een berekening, vul de waarden in en klik op berekenen.
        </div>
    """


def percentage_render_error(message):
    percentage_clear_plot_output()

    result_container = get("percentage-calculator-result")  # noqa: F821
    if not result_container:
        return

    result_container.innerHTML = f"""
        <div class="flex h-full min-h-96 items-center justify-center rounded-xl border border-destructive/40 bg-destructive/10 p-6 text-center text-destructive">
            {message}
        </div>
    """


def percentage_pie_autopct(values):
    total = sum(values)

    def formatter(pct):
        if total <= 0 or pct <= 0:
            return ""

        absolute = (pct / 100) * total
        return f"{percentage_format_value(absolute)}\n({percentage_format_value(pct)}%)"

    return formatter


def percentage_render_chart_fallback(message):
    target_div = get("percentage-calculator-mpl")  # ty:ignore[unresolved-reference]  # noqa: F821
    if not target_div:
        return

    target_div.innerHTML = f"""
        <div class="flex h-full w-full items-center justify-center rounded-xl border border-dashed border-border/70 bg-background/60 p-6 text-center text-base-content/60">
            {message}
        </div>
    """


def percentage_render_matplotlib_chart(result):
    target_div = get("percentage-calculator-mpl")  # ty:ignore[unresolved-reference]  # noqa: F821
    if not target_div:
        return

    if not isinstance(result, dict):
        percentage_render_chart_fallback("Geen grafiek beschikbaar voor deze invoer.")
        return

    mode = result.get("mode")
    if mode not in PERCENTAGE_MODE_CONFIGS:
        percentage_render_chart_fallback("Geen grafiek beschikbaar voor deze invoer.")
        return

    fig, ax = plt.subplots(figsize=(6, 4.2))
    theme = apply_matplotlib_theme(fig, ax)  # ty:ignore[unresolved-reference]  # noqa: F821
    chart_colors = theme["chart_colors"]
    surface_color = theme.get("surface_color")
    text_color = theme.get("text_color")
    labels = []
    values = []
    colors = []
    title = ""
    show_chart_text = True

    if mode == "deel-van-totaal":
        part = max(result["part"], 0)
        remainder = max(result["total"] - result["part"], 0)
        overflow = max(result["part"] - result["total"], 0)
        show_chart_text = False

        if overflow > 0:
            labels = ["Totaal", "Boven totaal"]
            values = [result["total"], overflow]
            colors = [chart_colors[1], chart_colors[0]]
        else:
            labels = ["Deel", "Resterend"]
            values = [part, remainder]
            colors = [chart_colors[0], chart_colors[1]]

    elif mode == "korting":
        show_chart_text = False
        labels = ["Over", "Korting"]
        values = [max(result["new_value"], 0), max(result["change_amount"], 0)]
        colors = [chart_colors[2], theme["danger_color"]]

    elif mode == "stijging":
        show_chart_text = False
        labels = ["Beginwaarde", "Toename"]
        values = [max(result["start_value"], 0), max(result["total_increase"], 0)]
        colors = [chart_colors[0], chart_colors[2]]

    else:
        show_chart_text = False
        change_label = "Toename" if result["change_amount"] >= 0 else "Afname"
        change_color = chart_colors[2]
        if result["change_amount"] < 0:
            change_color = theme["danger_color"]

        labels = ["Beginwaarde", change_label]
        values = [abs(result["old_value"]), abs(result["change_amount"])]
        colors = [chart_colors[0], change_color]

    if sum(values) <= 0:
        plt.close(fig)
        percentage_render_chart_fallback("Geen grafiek beschikbaar voor deze invoer.")
        return

    pie_labels = labels if show_chart_text else None
    pie_autopct = percentage_pie_autopct(values) if show_chart_text else None

    pie_result = ax.pie(
        values,
        labels=pie_labels,
        colors=colors,
        startangle=90,
        counterclock=False,
        autopct=pie_autopct,
        wedgeprops={"edgecolor": surface_color, "linewidth": 2},
        textprops={"color": text_color},
    )
    wedges = pie_result[0]
    autotexts = pie_result[2] if len(pie_result) > 2 else ()
    ax.axis("equal")

    if title:
        ax.set_title(title)

    for autotext in autotexts:
        autotext.set_color(text_color)
        autotext.set_fontsize(10)

    if show_chart_text:
        legend = ax.legend(
            wedges,
            [f"{label}: {percentage_format_value(value)}" for label, value in zip(labels, values)],
            loc="lower center",
            bbox_to_anchor=(0.5, 0.02),
            ncol=2,
            frameon=False,
        )
        for text in legend.get_texts():
            text.set_color(text_color)

    fig.subplots_adjust(left=0.08, right=0.92, top=0.86, bottom=0.14)
    display(fig, target="percentage-calculator-mpl")
    plt.close(fig)


def percentage_render_result_card(card):
    if not isinstance(card, dict):
        return ""

    label = str(card.get("label", ""))
    value = str(card.get("value", ""))

    return (
        '<article class="card gap-0 p-0">'
        '<section class="p-4">'
        f'<p class="text-sm text-base-content/60">{label}</p>'
        f'<p class="mt-2 break-words text-base font-semibold">{value}</p>'
        '</section>'
        "</article>"
    )


def percentage_render_result_step(step):
    if step is None:
        return ""

    return (
        '<li class="card gap-0 px-4 py-3">'
        f"{step}"
        "</li>"
    )


def percentage_get_cards_grid_class(card_count):
    if card_count <= 1:
        return "grid gap-3 md:grid-cols-1"
    if card_count == 2:
        return "grid gap-3 md:grid-cols-2"
    return "grid gap-3 md:grid-cols-3"


def percentage_render_result(result, error=None):
    global PERCENTAGE_LAST_RESULT

    if error:
        PERCENTAGE_LAST_RESULT = None
        percentage_render_error(error)
        return

    if not result:
        PERCENTAGE_LAST_RESULT = None
        percentage_render_placeholder()
        return

    if not isinstance(result, dict):
        PERCENTAGE_LAST_RESULT = None
        percentage_render_error("Er ging iets mis bij het tonen van de uitkomst.")
        return

    PERCENTAGE_LAST_RESULT = result
    result_container = get("percentage-calculator-result")  # noqa: F821
    if not result_container:
        return

    percentage_clear_plot_output()
    headline = str(result.get("headline", ""))
    summary = str(result.get("summary", ""))
    cards = result.get("cards", ())
    steps = result.get("steps", ())

    if not isinstance(cards, (list, tuple)):
        cards = ()
    if not isinstance(steps, (list, tuple)):
        steps = ()

    cards_html = "".join(percentage_render_result_card(card) for card in cards)
    steps_html = "".join(percentage_render_result_step(step) for step in steps)
    cards_grid_class = percentage_get_cards_grid_class(len(cards))
    mode = str(result.get("mode", ""))
    show_details = mode not in {"deel-van-totaal", "korting", "stijging", "verschil"}
    details_html = ""

    if show_details:
        details_html = (
            '<article class="card gap-0 p-0">'
            '<section class="p-5">'
            f'<p class="text-lg font-semibold">{headline}</p>'
            f'<p class="mt-2 text-sm text-base-content/60">{summary}</p>'
            '</section>'
            '</article>'
            '<article class="card gap-0 p-0">'
            '<section class="p-5">'
            '<h3 class="text-base font-semibold">Tussenstappen</h3>'
            '<ol class="mt-3 space-y-3 text-sm text-base-content/80">'
            f'{steps_html}'
            '</ol>'
            '</section>'
            '</article>'
        )

    result_container.innerHTML = (
        '<div class="flex h-full flex-col gap-4">'
        '<article class="card gap-0 p-0">'
        '<section class="p-2">'
        '<div id="percentage-calculator-mpl" '
        'class="flex min-h-80 items-center justify-center overflow-hidden [&_canvas]:size-full [&_canvas]:max-w-full [&_img]:block [&_img]:size-full [&_img]:max-w-full [&_img]:object-contain [&_svg]:size-full [&_svg]:max-w-full"></div>'
        '</section>'
        '</article>'
        f"{details_html}"
        f'<div class="{cards_grid_class}">'
        f"{cards_html}"
        "</div>"
        "</div>"
    )

    percentage_render_matplotlib_chart(result)


def percentage_update_mode_ui(mode=None):
    active_mode = mode or percentage_get_mode_value()
    mode_config = percentage_get_mode_config(active_mode)

    mode_description = get("percentage-calculator-mode-description")  # noqa: F821
    formula_badge = get("percentage-calculator-formula")  # noqa: F821
    value_1_label = get("percentage-calculator-waarde-1-label")  # noqa: F821
    value_1_input = get("percentage-calculator-waarde-1")  # noqa: F821
    value_1_help = get("percentage-calculator-waarde-1-help")  # noqa: F821
    value_2_label = get("percentage-calculator-waarde-2-label")  # noqa: F821
    value_2_input = get("percentage-calculator-waarde-2")  # noqa: F821
    value_2_help = get("percentage-calculator-waarde-2-help")  # noqa: F821
    iterations_field = get("percentage-calculator-iterations-field")  # noqa: F821
    iterations_input = get("percentage-calculator-iterations")  # noqa: F821

    if mode_description:
        mode_description.textContent = mode_config["description"]
    if formula_badge:
        formula_badge.textContent = mode_config["formula"]
    if value_1_label:
        value_1_label.textContent = mode_config["value_1"]["label"]
    if value_1_input:
        value_1_input.placeholder = mode_config["value_1"]["placeholder"]
        value_1_input.setAttribute("aria-label", mode_config["value_1"]["label"])
    if value_1_help:
        value_1_help.textContent = mode_config["value_1"]["help"]
    if value_2_label:
        value_2_label.textContent = mode_config["value_2"]["label"]
    if value_2_input:
        value_2_input.placeholder = mode_config["value_2"]["placeholder"]
        value_2_input.setAttribute("aria-label", mode_config["value_2"]["label"])
    if value_2_help:
        value_2_help.textContent = mode_config["value_2"]["help"]
    if iterations_field:
        iterations_field.hidden = not mode_config["show_iterations"]
    if iterations_input and not iterations_input.value.strip():
        iterations_input.value = "1"


def percentage_set_input_state(state):
    mode = state.get("mode", PERCENTAGE_DEFAULT_MODE)
    mode_select = get("percentage-calculator-mode")  # noqa: F821
    value_1_input = get("percentage-calculator-waarde-1")  # noqa: F821
    value_2_input = get("percentage-calculator-waarde-2")  # noqa: F821
    iterations_input = get("percentage-calculator-iterations")  # noqa: F821

    if mode_select:
        mode_select.value = mode

    percentage_update_mode_ui(mode)

    if value_1_input:
        value_1_input.value = percentage_format_value(state.get("value_1", 0))
    if value_2_input:
        value_2_input.value = percentage_format_value(state.get("value_2", 0))
    if iterations_input:
        iterations_input.value = str(state.get("iterations", 1))


def percentage_reset_inputs():
    mode_select = get("percentage-calculator-mode")  # noqa: F821
    value_1_input = get("percentage-calculator-waarde-1")  # noqa: F821
    value_2_input = get("percentage-calculator-waarde-2")  # noqa: F821
    iterations_input = get("percentage-calculator-iterations")  # noqa: F821

    if mode_select:
        mode_select.value = PERCENTAGE_DEFAULT_MODE
    if value_1_input:
        value_1_input.value = ""
    if value_2_input:
        value_2_input.value = ""
    if iterations_input:
        iterations_input.value = "1"

    percentage_update_mode_ui(PERCENTAGE_DEFAULT_MODE)


def percentage_show_panel(panel_name):
    panel_pairs = (
        ("tool", "percentage-calculator-tool-tab", "percentage-calculator-tool-panel"),
        (
            "history",
            "percentage-calculator-history-tab",
            "percentage-calculator-history-panel",
        ),
    )

    for name, tab_id, panel_id in panel_pairs:
        is_active = panel_name == name
        tab = get(tab_id)  # noqa: F821
        panel = get(panel_id)  # noqa: F821

        if tab:
            tab.setAttribute("aria-selected", "true" if is_active else "false")
            tab.setAttribute("tabindex", "0" if is_active else "-1")

        if panel:
            panel.hidden = not is_active


def percentage_normalize_history_entry(entry):
    if not isinstance(entry, dict):
        return None

    mode = entry.get("mode")
    if mode not in PERCENTAGE_MODE_CONFIGS:
        return None

    try:
        value_1 = float(entry.get("value_1"))
        value_2 = float(entry.get("value_2"))
        iterations = int(entry.get("iterations", 1))
        result = float(entry.get("result"))
    except (TypeError, ValueError):
        return None

    if iterations < 1:
        return None

    return {
        "mode": mode,
        "value_1": value_1,
        "value_2": value_2,
        "iterations": iterations,
        "result": result,
    }


def percentage_sanitize_history_entries(history_entries):
    sanitized_entries = []
    changed = False

    for entry in history_entries:
        normalized_entry = percentage_normalize_history_entry(entry)
        if not normalized_entry:
            changed = True
            continue

        if entry != normalized_entry:
            changed = True

        sanitized_entries.append(normalized_entry)

    return sanitized_entries, changed


def percentage_format_history_result(entry):
    if entry["mode"] in {"deel-van-totaal", "verschil"}:
        return percentage_format_percent(entry["result"], include_sign=entry["mode"] == "verschil")

    return percentage_format_value(entry["result"])


def percentage_render_history_value(label, value):
    return f"""
        <div class="flex items-center gap-2 text-sm font-semibold">
            <p class="text-base-content/60">{label}</p>
            <p>{value}</p>
        </div>
    """


def percentage_render_history_entry(entry, index):
    mode_config = percentage_get_mode_config(entry["mode"])
    input_values = "".join(
        (
            percentage_render_history_value(
                mode_config["value_1"]["history_label"], percentage_format_value(entry["value_1"])
            ),
            percentage_render_history_value(
                mode_config["value_2"]["history_label"], percentage_format_value(entry["value_2"])
            ),
        )
    )

    if mode_config["show_iterations"]:
        input_values += percentage_render_history_value("Keer", str(entry["iterations"]))

    output_value = percentage_render_history_value(
        mode_config["result_label"], percentage_format_history_result(entry)
    )

    return f"""
        <article class="card p-0">
            <section class="flex flex-wrap items-center gap-3 p-4 xl:flex-nowrap">
                <div class="min-w-0 flex flex-1 flex-wrap items-center gap-x-5 gap-y-3 rounded-xl border border-border/70 bg-card/85 p-3">
                    <div class="flex items-center gap-2">
                        <span class="badge-outline">{mode_config["badge"]}</span>
                    </div>
                    {input_values}
                </div>
                <div class="min-w-0 flex flex-1 flex-wrap items-center gap-x-5 gap-y-3 rounded-xl border border-border/70 bg-card/85 p-3">
                    <div class="flex items-center gap-2">
                        <span class="badge-secondary">Resultaat</span>
                    </div>
                    {output_value}
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


def percentage_render_history_entries(history_entries):
    history_list = get("percentage-calculator-history-list")  # noqa: F821
    empty_state = get("percentage-calculator-history-empty")  # noqa: F821
    if not history_list or not empty_state:
        return

    if not history_entries:
        history_list.innerHTML = ""
        empty_state.hidden = False
        return

    history_list.innerHTML = "".join(
        percentage_render_history_entry(entry, index)
        for index, entry in enumerate(history_entries)
    )
    empty_state.hidden = True


async def percentage_sync_history_view():
    history_entries = await get_tool_history(PERCENTAGE_TOOL_INDEX)  # noqa: F821
    sanitized_entries, changed = percentage_sanitize_history_entries(history_entries)

    if changed:
        sanitized_entries = await set_tool_history(PERCENTAGE_TOOL_INDEX, sanitized_entries)  # noqa: F821

    percentage_render_history_entries(sanitized_entries)
    return sanitized_entries


async def percentage_restore_history_entry(history_index):
    history_entries = await percentage_sync_history_view()
    if history_index < 0 or history_index >= len(history_entries):
        return

    entry = history_entries[history_index]
    percentage_set_input_state(entry)
    validated_state, error = percentage_validate_input_state(entry)
    if error:
        percentage_render_result(None, error)
        return

    percentage_render_result(percentage_calculate_percentage_result(validated_state))
    percentage_show_panel("tool")


async def percentage_delete_history_entry(history_index):
    await delete_tool_history_entry(PERCENTAGE_TOOL_INDEX, history_index)  # noqa: F821
    await percentage_sync_history_view()


async def percentage_handle_history_action(action, history_index):
    if action == "restore":
        await percentage_restore_history_entry(history_index)
        return

    if action == "delete":
        await percentage_delete_history_entry(history_index)


def percentage_on_history_list_click(event):
    history_list = get("percentage-calculator-history-list")  # noqa: F821
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

    asyncio.create_task(percentage_handle_history_action(history_action, history_index))


@when("change", "#percentage-calculator-mode")
def percentage_mode_change(_event):
    percentage_update_mode_ui(percentage_get_mode_value())
    percentage_render_result(None)


@when("click", "#percentage-calculator-berekenen")
async def percentage_bereken_click(_event):
    input_state = percentage_get_input_state()
    validated_state, error = percentage_validate_input_state(input_state)
    if error:
        percentage_render_result(None, error)
        return

    result = percentage_calculate_percentage_result(validated_state)
    percentage_render_result(result)

    await append_tool_history(  # noqa: F821
        PERCENTAGE_TOOL_INDEX,
        {
            "mode": validated_state["mode"],
            "value_1": validated_state["value_1"],
            "value_2": validated_state["value_2"],
            "iterations": validated_state["iterations"],
            "result": result["history_result"],
        },
    )
    await percentage_sync_history_view()


@when("click", "#percentage-calculator-tool-tab")
def percentage_tool_tab_click(_event):
    percentage_show_panel("tool")


@when("click", "#percentage-calculator-history-tab")
async def percentage_history_tab_click(_event):
    await percentage_sync_history_view()
    percentage_show_panel("history")


@when("click", "#percentage-calculator-reset")
def percentage_reset_click(_event):
    percentage_reset_inputs()
    percentage_render_result(None)


def percentage_on_theme_change(_event):
    if PERCENTAGE_LAST_RESULT:
        percentage_render_result(PERCENTAGE_LAST_RESULT)


def percentage_start():
    global PERCENTAGE_THEME_CHANGE_PROXY, PERCENTAGE_HISTORY_CLICK_PROXY

    percentage_update_mode_ui(PERCENTAGE_DEFAULT_MODE)
    percentage_render_placeholder()
    PERCENTAGE_THEME_CHANGE_PROXY = create_proxy(percentage_on_theme_change)
    window.addEventListener("app:themechange", PERCENTAGE_THEME_CHANGE_PROXY)
    history_list = get("percentage-calculator-history-list")  # noqa: F821
    if history_list:
        PERCENTAGE_HISTORY_CLICK_PROXY = create_proxy(percentage_on_history_list_click)
        history_list.addEventListener("click", PERCENTAGE_HISTORY_CLICK_PROXY)
    percentage_show_panel("tool")
    asyncio.create_task(percentage_sync_history_view())


percentage_start()
