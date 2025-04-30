from components.radiobutton import RadioButton
from utils.colour_palette import default_theme


def test_radiobutton_render():
    rb = RadioButton(["Red", "Blue"], value="Blue").render()

    assert rb.id.startswith("radio-")
    assert rb.options[1]["label"] == "Blue"
    assert rb.value == "Blue"

    assert rb.style["color"] == default_theme.text_light
