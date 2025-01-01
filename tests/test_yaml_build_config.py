import pytest

from textwrap import dedent

from lib.yaml_config import Build, load_resource


def test_simple_default_build_config() -> None:
    config = dedent("""
        name: simple test
        command:
            - ls
            - dir
    """)

    build = Build(load_resource(config))
    assert build.config_for("simple test")


def test_missing_config_fails() -> None:
    config = dedent("""
        name: simple test
        command:
            - ls
            - dir
    """)

    build = Build(load_resource(config))
    with pytest.raises(Exception):
        assert build.config_for("missing build")


def test_output_view_can_be_changed() -> None:
    config = dedent("""
        name: simple test
        output_view: "tab"
        command:
            - ls
            - dir
    """)
    build = Build(load_resource(config))
    assert "tab" == build.config_for("simple test").output_view
