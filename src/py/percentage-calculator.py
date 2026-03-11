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
PERCENTAGE_KNOWN_MODES = frozenset(PERCENTAGE_MODE_CONFIGS)
PERCENTAGE_RESULT_CONTAINER_ID = "percentage-calculator-result"
PERCENTAGE_CHART_TARGET_ID = "percentage-calculator-mpl"
PERCENTAGE_CHART_FALLBACK_MESSAGE = "Geen grafiek beschikbaar voor deze invoer."
PERCENTAGE_PANEL_CONFIGS = (
    ("tool", "percentage-calculator-tool-tab", "percentage-calculator-tool-panel"),
    (
        "history",
        "percentage-calculator-history-tab",
        "percentage-calculator-history-panel",
    ),
)


def percentage_dom(element_id):
    return get(element_id)  # noqa: F821


def percentage_apply_chart_theme(fig, ax):
    return apply_matplotlib_theme(fig, ax)  # noqa: F821


async def percentage_get_history_entries():
    return await get_tool_history(PERCENTAGE_TOOL_INDEX)  # noqa: F821


async def percentage_set_history_entries(entries):
    return await set_tool_history(PERCENTAGE_TOOL_INDEX, entries)  # noqa: F821


async def percentage_append_history_entry(entry):
    return await append_tool_history(PERCENTAGE_TOOL_INDEX, entry)  # noqa: F821


async def percentage_delete_history_item(history_index):
    return await delete_tool_history_entry(PERCENTAGE_TOOL_INDEX, history_index)  # noqa: F821


def percentage_get_mode_config(mode):
    return PERCENTAGE_MODE_CONFIGS.get(
        mode, PERCENTAGE_MODE_CONFIGS[PERCENTAGE_DEFAULT_MODE]
    )


def percentage_get_mode_value():
    mode_select = percentage_dom("percentage-calculator-mode")
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
    sign = "+" if include_sign and numeric_value > 0 else ""
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


def percentage_read_input_value(element_id, default=""):
    input_element = percentage_dom(element_id)
    if not input_element:
        return default

    return input_element.value.strip()


def percentage_get_input_state():
    return {
        "mode": percentage_get_mode_value(),
        "value_1": percentage_read_input_value("percentage-calculator-waarde-1"),
        "value_2": percentage_read_input_value("percentage-calculator-waarde-2"),
        "iterations": percentage_read_input_value(
            "percentage-calculator-iterations", "1"
        ),
    }


def percentage_validate_deel_van_totaal(value_1, value_2):
    if value_1 < 0:
        return "Het deel mag niet negatief zijn."
    if value_2 <= 0:
        return "Het totaal moet groter zijn dan 0."
    return None


def percentage_validate_korting(value_1, value_2):
    if value_1 < 0:
        return "De oude waarde mag niet negatief zijn."
    if value_2 < 0:
        return "Het kortingspercentage mag niet negatief zijn."
    return None


def percentage_validate_stijging(value_1, value_2):
    if value_1 < 0:
        return "De beginwaarde mag niet negatief zijn."
    if value_2 < 0:
        return "Het stijgingspercentage mag niet negatief zijn."
    return None


def percentage_validate_verschil(value_1, _value_2):
    if value_1 == 0:
        return "Het eerste getal mag niet 0 zijn bij een procentverschil."
    return None


PERCENTAGE_MODE_VALIDATORS = {
    "deel-van-totaal": percentage_validate_deel_van_totaal,
    "korting": percentage_validate_korting,
    "stijging": percentage_validate_stijging,
    "verschil": percentage_validate_verschil,
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

    validator = PERCENTAGE_MODE_VALIDATORS.get(mode)
    if validator:
        error = validator(value_1, value_2)
        if error:
            return None, error

    return {
        "mode": mode,
        "value_1": value_1,
        "value_2": value_2,
        "iterations": iterations,
    }, None


def percentage_calculate_deel_van_totaal(value_1, value_2, _iterations):
    ratio = value_1 / value_2
    percentage = ratio * 100
    remainder_percentage = max(((value_2 - value_1) / value_2) * 100, 0)

    return {
        "mode": "deel-van-totaal",
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


def percentage_calculate_korting(value_1, value_2, _iterations):
    discount_amount = (value_2 / 100) * value_1
    new_value = value_1 - discount_amount

    return {
        "mode": "korting",
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


def percentage_calculate_stijging(value_1, value_2, iterations):
    current_value = value_1
    progression = [value_1]
    step_lines = []

    for step_index in range(iterations):
        previous_value = current_value
        increase_amount = (value_2 / 100) * previous_value
        current_value = previous_value + increase_amount
        progression.append(current_value)
        step_lines.append(
            f"Stap {step_index + 1}: {percentage_format_percent(value_2)} van {percentage_format_value(previous_value)} = {percentage_format_value(increase_amount)}; {percentage_format_value(previous_value)} + {percentage_format_value(increase_amount)} = {percentage_format_value(current_value)}."
        )

    total_increase = current_value - value_1
    summary = "De stijging wordt elke keer opnieuw op de nieuwste waarde toegepast."
    if iterations == 1:
        summary = "De tool telt het berekende percentage op bij de beginwaarde."

    return {
        "mode": "stijging",
        "headline": f"Na {iterations} keer {percentage_format_percent(value_2)} stijging wordt {percentage_format_value(value_1)} gelijk aan {percentage_format_value(current_value)}.",
        "summary": summary,
        "start_value": value_1,
        "percentage": value_2,
        "new_value": current_value,
        "total_increase": total_increase,
        "progression": tuple(progression),
        "cards": (
            {
                "label": "Totale toename",
                "value": percentage_format_value(total_increase),
            },
            {"label": "Nieuwe waarde", "value": percentage_format_value(current_value)},
        ),
        "steps": tuple(step_lines),
        "history_result": current_value,
    }


def percentage_calculate_verschil(value_1, value_2, _iterations):
    change_amount = value_2 - value_1
    percentage_change = (change_amount / value_1) * 100
    direction = "stijging" if change_amount >= 0 else "daling"

    return {
        "mode": "verschil",
        "headline": f"Van {percentage_format_value(value_1)} naar {percentage_format_value(value_2)} is een {direction} van {percentage_format_percent(abs(percentage_change))}.",
        "summary": "Je bekijkt eerst het verschil tussen de twee getallen en vergelijkt dat daarna met de beginwaarde.",
        "old_value": value_1,
        "new_value": value_2,
        "change_amount": change_amount,
        "percentage_change": percentage_change,
        "cards": (
            {
                "label": "Verschil in %",
                "value": percentage_format_percent(
                    percentage_change, include_sign=True
                ),
            },
        ),
        "steps": (
            f"Bereken het verschil: {percentage_format_value(value_2)} - {percentage_format_value(value_1)} = {percentage_format_value(change_amount)}.",
            f"Deel door de beginwaarde: {percentage_format_value(change_amount)} / {percentage_format_value(value_1)} = {percentage_format_value(change_amount / value_1)}.",
            f"Vermenigvuldig met 100: {percentage_format_value(change_amount / value_1)} x 100 = {percentage_format_percent(percentage_change, include_sign=True)}.",
        ),
        "history_result": percentage_change,
    }


PERCENTAGE_MODE_CALCULATORS = {
    "deel-van-totaal": percentage_calculate_deel_van_totaal,
    "korting": percentage_calculate_korting,
    "stijging": percentage_calculate_stijging,
    "verschil": percentage_calculate_verschil,
}


def percentage_calculate_percentage_result(validated_state):
    calculator = PERCENTAGE_MODE_CALCULATORS.get(
        validated_state["mode"], percentage_calculate_verschil
    )

    return calculator(
        validated_state["value_1"],
        validated_state["value_2"],
        validated_state["iterations"],
    )


def percentage_resolve_result(state):
    validated_state, error = percentage_validate_input_state(state)
    if error:
        return None, None, error

    result = percentage_calculate_percentage_result(validated_state)
    return validated_state, result, None


def percentage_clear_plot_output():
    plt.close("all")

    target_div = percentage_dom(PERCENTAGE_CHART_TARGET_ID)
    if target_div:
        target_div.innerHTML = ""


def percentage_render_result_message(message, classes):
    percentage_clear_plot_output()

    result_container = percentage_dom(PERCENTAGE_RESULT_CONTAINER_ID)
    if not result_container:
        return

    result_container.innerHTML = f'''
        <div class="{classes}">
            {message}
        </div>
    '''


def percentage_render_placeholder():
    percentage_render_result_message(
        "Kies een berekening, vul de waarden in en klik op berekenen.",
        "flex h-full min-h-96 items-center justify-center rounded-xl border border-dashed border-border/70 bg-background/60 p-6 text-center text-base-content/60",
    )


def percentage_render_error(message):
    percentage_render_result_message(
        message,
        "flex h-full min-h-96 items-center justify-center rounded-xl border border-destructive/40 bg-destructive/10 p-6 text-center text-destructive",
    )


def percentage_render_chart_fallback(message):
    target_div = percentage_dom(PERCENTAGE_CHART_TARGET_ID)
    if not target_div:
        return

    target_div.innerHTML = f"""
        <div class="flex h-full w-full items-center justify-center rounded-xl border border-dashed border-border/70 bg-background/60 p-6 text-center text-base-content/60">
            {message}
        </div>
    """


def percentage_get_chart_data(result, theme):
    chart_colors = theme["chart_colors"]
    mode = result.get("mode")

    if mode == "deel-van-totaal":
        part = max(result["part"], 0)
        remainder = max(result["total"] - result["part"], 0)
        overflow = max(result["part"] - result["total"], 0)

        if overflow > 0:
            return {
                "values": [result["total"], overflow],
                "colors": [chart_colors[1], chart_colors[0]],
            }

        return {
            "values": [part, remainder],
            "colors": [chart_colors[0], chart_colors[1]],
        }

    if mode == "korting":
        return {
            "values": [max(result["new_value"], 0), max(result["change_amount"], 0)],
            "colors": [chart_colors[2], theme["danger_color"]],
        }

    if mode == "stijging":
        return {
            "values": [max(result["start_value"], 0), max(result["total_increase"], 0)],
            "colors": [chart_colors[0], chart_colors[2]],
        }

    if mode == "verschil":
        change_color = chart_colors[2]
        if result["change_amount"] < 0:
            change_color = theme["danger_color"]

        return {
            "values": [abs(result["old_value"]), abs(result["change_amount"])],
            "colors": [chart_colors[0], change_color],
        }

    return None


def percentage_render_matplotlib_chart(result):
    target_div = percentage_dom(PERCENTAGE_CHART_TARGET_ID)
    if not target_div:
        return

    if not isinstance(result, dict) or result.get("mode") not in PERCENTAGE_KNOWN_MODES:
        percentage_render_chart_fallback(PERCENTAGE_CHART_FALLBACK_MESSAGE)
        return

    fig, ax = plt.subplots(figsize=(6, 4.2))
    theme = percentage_apply_chart_theme(fig, ax)
    chart_data = percentage_get_chart_data(result, theme)

    if not chart_data or sum(chart_data["values"]) <= 0:
        plt.close(fig)
        percentage_render_chart_fallback(PERCENTAGE_CHART_FALLBACK_MESSAGE)
        return

    ax.pie(
        chart_data["values"],
        labels=None,
        colors=chart_data["colors"],
        startangle=90,
        counterclock=False,
        autopct=None,
        wedgeprops={"edgecolor": theme.get("surface_color"), "linewidth": 2},
        textprops={"color": theme.get("text_color")},
    )
    ax.axis("equal")

    fig.subplots_adjust(left=0.08, right=0.92, top=0.86, bottom=0.14)
    display(fig, target=PERCENTAGE_CHART_TARGET_ID)
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
        "</section>"
        "</article>"
    )


def percentage_render_result_step(step):
    if step is None:
        return ""

    return f'<li class="card gap-0 px-4 py-3">{step}</li>'


def percentage_normalize_render_items(items):
    if isinstance(items, (list, tuple)):
        return items

    return ()


def percentage_get_cards_grid_class(card_count):
    if card_count <= 1:
        return "grid gap-3 md:grid-cols-1"
    if card_count == 2:
        return "grid gap-3 md:grid-cols-2"
    return "grid gap-3 md:grid-cols-3"


def percentage_render_result_details(headline, summary, steps):
    steps_html = "".join(percentage_render_result_step(step) for step in steps)

    return (
        '<article class="card gap-0 p-0">'
        '<section class="p-5">'
        f'<p class="text-lg font-semibold">{headline}</p>'
        f'<p class="mt-2 text-sm text-base-content/60">{summary}</p>'
        "</section>"
        "</article>"
        '<article class="card gap-0 p-0">'
        '<section class="p-5">'
        '<h3 class="text-base font-semibold">Tussenstappen</h3>'
        '<ol class="mt-3 space-y-3 text-sm text-base-content/80">'
        f"{steps_html}"
        "</ol>"
        "</section>"
        "</article>"
    )


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
    result_container = percentage_dom(PERCENTAGE_RESULT_CONTAINER_ID)
    if not result_container:
        return

    percentage_clear_plot_output()
    cards = percentage_normalize_render_items(result.get("cards"))
    cards_html = "".join(percentage_render_result_card(card) for card in cards)
    details_html = ""
    mode = str(result.get("mode", ""))

    if mode not in PERCENTAGE_KNOWN_MODES:
        details_html = percentage_render_result_details(
            str(result.get("headline", "")),
            str(result.get("summary", "")),
            percentage_normalize_render_items(result.get("steps")),
        )

    result_container.innerHTML = (
        '<div class="flex h-full flex-col gap-4">'
        '<article class="card gap-0 p-0">'
        '<section class="p-2">'
        '<div id="percentage-calculator-mpl" '
        'class="flex min-h-80 items-center justify-center overflow-hidden [&_canvas]:size-full [&_canvas]:max-w-full [&_img]:block [&_img]:size-full [&_img]:max-w-full [&_img]:object-contain [&_svg]:size-full [&_svg]:max-w-full"></div>'
        "</section>"
        "</article>"
        f"{details_html}"
        f'<div class="{percentage_get_cards_grid_class(len(cards))}">'
        f"{cards_html}"
        "</div>"
        "</div>"
    )

    percentage_render_matplotlib_chart(result)


def percentage_set_text_content(element_id, value):
    element = percentage_dom(element_id)
    if element:
        element.textContent = value


def percentage_set_element_value(element_id, value):
    element = percentage_dom(element_id)
    if element:
        element.value = value


def percentage_update_mode_input(field_name, field_config):
    base_id = f"percentage-calculator-{field_name}"
    label = percentage_dom(f"{base_id}-label")
    input_element = percentage_dom(base_id)
    help_text = percentage_dom(f"{base_id}-help")

    if label:
        label.textContent = field_config["label"]
    if input_element:
        input_element.placeholder = field_config["placeholder"]
        input_element.setAttribute("aria-label", field_config["label"])
    if help_text:
        help_text.textContent = field_config["help"]


def percentage_update_mode_ui(mode=None):
    active_mode = mode or percentage_get_mode_value()
    mode_config = percentage_get_mode_config(active_mode)

    percentage_set_text_content(
        "percentage-calculator-mode-description", mode_config["description"]
    )
    percentage_set_text_content("percentage-calculator-formula", mode_config["formula"])
    percentage_update_mode_input("waarde-1", mode_config["value_1"])
    percentage_update_mode_input("waarde-2", mode_config["value_2"])

    iterations_field = percentage_dom("percentage-calculator-iterations-field")
    if iterations_field:
        iterations_field.hidden = not mode_config["show_iterations"]

    iterations_input = percentage_dom("percentage-calculator-iterations")
    if iterations_input and not iterations_input.value.strip():
        iterations_input.value = "1"


def percentage_set_input_state(state):
    mode = state.get("mode", PERCENTAGE_DEFAULT_MODE)
    percentage_set_element_value("percentage-calculator-mode", mode)
    percentage_update_mode_ui(mode)
    percentage_set_element_value(
        "percentage-calculator-waarde-1",
        percentage_format_value(state.get("value_1", 0)),
    )
    percentage_set_element_value(
        "percentage-calculator-waarde-2",
        percentage_format_value(state.get("value_2", 0)),
    )
    percentage_set_element_value(
        "percentage-calculator-iterations", str(state.get("iterations", 1))
    )


def percentage_reset_inputs():
    percentage_set_element_value("percentage-calculator-mode", PERCENTAGE_DEFAULT_MODE)
    percentage_set_element_value("percentage-calculator-waarde-1", "")
    percentage_set_element_value("percentage-calculator-waarde-2", "")
    percentage_set_element_value("percentage-calculator-iterations", "1")
    percentage_update_mode_ui(PERCENTAGE_DEFAULT_MODE)


def percentage_show_panel(panel_name):
    for name, tab_id, panel_id in PERCENTAGE_PANEL_CONFIGS:
        is_active = panel_name == name
        tab = percentage_dom(tab_id)
        panel = percentage_dom(panel_id)

        if tab:
            tab.setAttribute("aria-selected", "true" if is_active else "false")
            tab.setAttribute("tabindex", "0" if is_active else "-1")

        if panel:
            panel.hidden = not is_active


def percentage_normalize_history_entry(entry):
    if not isinstance(entry, dict):
        return None

    mode = entry.get("mode")
    if mode not in PERCENTAGE_KNOWN_MODES:
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


def percentage_build_history_entry(validated_state, result):
    return {
        "mode": validated_state["mode"],
        "value_1": validated_state["value_1"],
        "value_2": validated_state["value_2"],
        "iterations": validated_state["iterations"],
        "result": result["history_result"],
    }


def percentage_format_history_result(entry):
    if entry["mode"] in {"deel-van-totaal", "verschil"}:
        return percentage_format_percent(
            entry["result"], include_sign=entry["mode"] == "verschil"
        )

    return percentage_format_value(entry["result"])


def percentage_render_history_value(label, value):
    return f"""
        <div class="flex items-center gap-2 text-sm font-semibold">
            <p class="text-base-content/60">{label}</p>
            <p>{value}</p>
        </div>
    """


def percentage_get_history_input_values(entry, mode_config):
    input_values = [
        (
            mode_config["value_1"]["history_label"],
            percentage_format_value(entry["value_1"]),
        ),
        (
            mode_config["value_2"]["history_label"],
            percentage_format_value(entry["value_2"]),
        ),
    ]

    if mode_config["show_iterations"]:
        input_values.append(("Keer", str(entry["iterations"])))

    return input_values


def percentage_render_history_entry(entry, index):
    mode_config = percentage_get_mode_config(entry["mode"])
    input_values_html = "".join(
        percentage_render_history_value(label, value)
        for label, value in percentage_get_history_input_values(entry, mode_config)
    )
    output_value_html = percentage_render_history_value(
        mode_config["result_label"], percentage_format_history_result(entry)
    )

    return f'''
        <article class="card p-0">
            <section class="flex flex-wrap items-center gap-3 p-4 xl:flex-nowrap">
                <div class="min-w-0 flex flex-1 flex-wrap items-center gap-x-5 gap-y-3 rounded-xl border border-border/70 bg-card/85 p-3">
                    <div class="flex items-center gap-2">
                        <span class="badge-outline">{mode_config["badge"]}</span>
                    </div>
                    {input_values_html}
                </div>
                <div class="min-w-0 flex flex-1 flex-wrap items-center gap-x-5 gap-y-3 rounded-xl border border-border/70 bg-card/85 p-3">
                    <div class="flex items-center gap-2">
                        <span class="badge-secondary">Resultaat</span>
                    </div>
                    {output_value_html}
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
    '''


def percentage_render_history_entries(history_entries):
    history_list = percentage_dom("percentage-calculator-history-list")
    empty_state = percentage_dom("percentage-calculator-history-empty")
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
    history_entries = await percentage_get_history_entries()
    sanitized_entries, changed = percentage_sanitize_history_entries(history_entries)

    if changed:
        sanitized_entries = await percentage_set_history_entries(sanitized_entries)

    percentage_render_history_entries(sanitized_entries)
    return sanitized_entries


async def percentage_restore_history_entry(history_index):
    history_entries = await percentage_sync_history_view()
    if history_index < 0 or history_index >= len(history_entries):
        return

    entry = history_entries[history_index]
    percentage_set_input_state(entry)
    _validated_state, result, error = percentage_resolve_result(entry)
    if error:
        percentage_render_result(None, error)
        return

    percentage_render_result(result)
    percentage_show_panel("tool")


async def percentage_delete_history_entry(history_index):
    await percentage_delete_history_item(history_index)
    await percentage_sync_history_view()


async def percentage_handle_history_action(action, history_index):
    if action == "restore":
        await percentage_restore_history_entry(history_index)
        return

    if action == "delete":
        await percentage_delete_history_entry(history_index)


def percentage_on_history_list_click(event):
    history_list = percentage_dom("percentage-calculator-history-list")
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
    validated_state, result, error = percentage_resolve_result(
        percentage_get_input_state()
    )
    if error:
        percentage_render_result(None, error)
        return

    percentage_render_result(result)
    await percentage_append_history_entry(
        percentage_build_history_entry(validated_state, result)
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

    history_list = percentage_dom("percentage-calculator-history-list")
    if history_list:
        PERCENTAGE_HISTORY_CLICK_PROXY = create_proxy(percentage_on_history_list_click)
        history_list.addEventListener("click", PERCENTAGE_HISTORY_CLICK_PROXY)

    percentage_show_panel("tool")
    asyncio.create_task(percentage_sync_history_view())


percentage_start()
