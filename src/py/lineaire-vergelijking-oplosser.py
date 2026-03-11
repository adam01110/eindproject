
import matplotlib.pyplot as plt  # ty:ignore[unresolved-import]
import numpy as np  # ty:ignore[unresolved-import]
from pyscript import display, when

TOOL_INDEX = 1


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


def render_result(result, error=None):
    if error or not result:
        clear_plot_output()
        legend_card = get("lineaire-vergelijking-legend")  # ty:ignore[unresolved-reference]  # noqa: F821
        if legend_card:
            legend_card.innerHTML = '<p class="text-base-content/60">Voer waarden in om de grafiek te zien.</p>'
        return

    a = result["a"]
    b = result["b"]
    y = result["y"]
    x_solution = result["x"]

    x_range = np.linspace(x_solution - 5, x_solution + 5, 100)
    y_values = a * x_range + b

    plt.style.use("seaborn-v0_8-pastel")
    clear_plot_output()

    fig, ax = plt.subplots()
    ax.plot(x_range, y_values, label=f"y = {a}x + {b}")
    ax.axhline(y=y, color="r", linestyle="--", alpha=0.7, label=f"y = {y}")
    ax.axvline(x=x_solution, color="g", linestyle="--", alpha=0.7, label=f"x = {x_solution:.2f}")
    ax.scatter([x_solution], [y], color="green", zorder=5, s=100)
    ax.set_xlabel("x")
    ax.set_ylabel("y", rotation="horizontal", labelpad=15)
    ax.grid(True, alpha=0.3)

    display(fig, target="lineaire-vergelijking-mpl")
    plt.close(fig)

    legend_card = get("lineaire-vergelijking-legend")  # ty:ignore[unresolved-reference]  # noqa: F821
    if legend_card:
        legend_card.innerHTML = f"""
            <div class="flex flex-col gap-1">
                <span>y = {y}</span>
                <span>x = {x_solution:.2f}</span>
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
