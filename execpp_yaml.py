import os
from pathlib import Path
from typing import (
    Callable,
    Dict,
    List,
    Optional,
)

import sublime
import sublime_plugin

from .lib.process import (
    AsyncProcess,
    OutputView,
)
from .lib.environment import (
    expand_variable,
    merge_and_substitute_environment_variables,
)
from .lib.yaml_config import (
    Build,
    ExecppYamlBuild,
    load_resource,
)
from .execpp import (
    log,
    SublimeConsoleView,
    SublimeProcessListener,
    SublimeTabView,
)


def _no_action(_: Build) -> None:
    pass


def load_file(file: Path):
    with file.open() as f:
        return load_resource(f.read())


def find_and_load_configuration_files(window: sublime.Window) -> List[Build]:
    project_dirs = [
        Path(project["path"]) for project in window.project_data().get("folders")
    ]
    project_files = [
        file
        for project_dir in project_dirs
        for file in project_dir.glob("*.execpp-build")
    ]
    project_build_configs = [Build(load_file(file)) for file in project_files]
    project_variants = [
        variant
        for build_file in project_build_configs
        for variant in build_file.variants()
    ]

    package_build_files = [
        resource_file for resource_file in sublime.find_resources("*.execpp-build")
    ]
    package_build_configs = [
        Build(load_resource(sublime.load_resource(resource)))
        for resource in package_build_files
    ]
    package_variants = [
        variant
        for build_file in package_build_configs
        for variant in build_file.variants()
    ]

    all_variants = project_variants + package_variants
    return all_variants


def on_build_select_with_choices(
    window: sublime.Window,
    choices: List[ExecppYamlBuild],
    on_select: Callable[[Build], None] = _no_action,
) -> Callable[[int], Build]:
    def choice_function(index: int) -> Build:
        if index == -1:
            return None
        build_config = choices[index]
        chosen_build_name = build_config.name()
        on_select(build_config)

    return choice_function


def display_and_select_build(
    window: sublime.Window,
    build_variants: List[Build],
    on_select: Callable[[Build], None] = _no_action,
) -> None:
    on_select_action = on_build_select_with_choices(window, build_variants, on_select)
    window.show_quick_panel(
        [variant.name() for variant in build_variants], on_select=on_select_action
    )


class RunLastExecppBuildCommand(sublime_plugin.WindowCommand):
    def __init__(self, window: sublime.Window) -> None:
        super().__init__(window)
        self.saved_build_config: Optional[Build] = None
        self.last_build_name: Optional[str] = None

    def _on_build_select(self, selected_build: Build) -> None:
        self.saved_build_config = selected_build
        self.last_build_name = selected_build.name()
        log("Running command", self.saved_build_config.config_for(self.last_build_name), "with name", self.last_build_name)
        self.window.run_command(
            "execpp",
            args=asdict(self.saved_build_config.config_for(self.last_build_name)),
        )

    def _select_build_if_missing(self) -> None:
        all_variants = find_and_load_configuration_files(self.window)
        log(f"Found {len(all_variants)} different build systems.")
        selected_build = display_and_select_build(
            self.window, all_variants, self._on_build_select
        )

    def run(self, select_build: bool = False) -> None:
        if (
            select_build
            or self.saved_build_config is None
            or self.last_build_name is None
        ):
            self._select_build_if_missing()
        else:
            log("Running command", self.saved_build_config.config_for(self.last_build_name), "with name", self.last_build_name)
            self.window.run_command(
                "execpp",
                args=asdict(self.saved_build_config.config_for(self.last_build_name)),
            )


class ListExecppBuildsCommand(sublime_plugin.WindowCommand):
    def __init__(self, window: sublime.Window) -> None:
        super().__init__(window)

    def _on_build_select(self, selected_build: Build) -> None:
        self.window.run_command(
            "execpp", args=asdict(selected_build.config_for(selected_build.name()))
        )

    def run(self) -> None:
        all_variants = find_and_load_configuration_files(self.window)
        log(f"Found {len(all_variants)} different build systems.")
        display_and_select_build(self.window, all_variants, self._on_build_select)
