import matplotlib.pyplot as plt  # ty:ignore[unresolved-import]
import numpy as np  # ty:ignore[unresolved-import]
from pyscript import display, when, window
from pyscript.ffi import create_proxy

TOOL_INDEX = 1
LAST_RESULT = None
THEME_CHANGE_PROXY = None


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
        "equation": f"{a}x + {b} = {y}",
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


@when("click", "#lineaire-vergelijking-berekenen")
async def bereken_click(event):
    values = get_input_values()
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
            "equation": result["equation"],
        },
    )


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
    global THEME_CHANGE_PROXY

    THEME_CHANGE_PROXY = create_proxy(on_theme_change)
    window.addEventListener("app:themechange", THEME_CHANGE_PROXY)


start()
