from pytest_mock import MockerFixture  # type: ignore

from components import Mermaid  # type: ignore
from components.themes import default_theme  # type: ignore


def test_mermaid_render_basic(mocker: MockerFixture) -> None:
    """Ensure Mermaid component renders and forwards config."""
    mermaid_mock = mocker.patch("components.mermaid.dash_extensions.Mermaid")
    m = Mermaid()
    div = m.render("diag-1", "graph TD; A-->B")

    mermaid_mock.assert_called_once()
    call_kwargs = mermaid_mock.call_args.kwargs
    assert call_kwargs["id"] == "diag-1"
    assert call_kwargs["chart"] == "graph TD; A-->B"
    assert call_kwargs["config"]["theme"] == m.default_styles["mermaid_config"]["theme"]

    assert div.children[-1] is mermaid_mock.return_value
    assert div.style["backgroundColor"] == default_theme.panel_bg
