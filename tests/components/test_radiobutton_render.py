from components import RadioButton
from components.themes import default_theme


def test_radiobutton_render() -> None:
    """Render RadioButton and check selected state."""
    rb = RadioButton(["Red", "Blue"], value="Blue").render()

    assert rb.id.startswith("radio-")
    assert rb.options[1]["label"] == "Blue"
    assert rb.value == "Blue"

    assert rb.style["color"] == default_theme.text_light
