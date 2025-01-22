import dataclasses
import datetime
import os
import subprocess
import sys
import threading
import time
import signal
import html
import string
from pathlib import Path
from textwrap import dedent
from typing import (
    Callable,
    Dict,
    List,
    Optional,
)

import sublime
import sublime_plugin

from .lib.environment import expand_variable, merge_and_substitute_environment_variables
from .lib.process import (
    AsyncProcess,
    ProcessListener,
    OutputView,
    CompletedProcessInfo,
)


def log(*parts: str, **kwargs) -> None:
    if sublime.get_log_commands():
        print("[execpp]", *parts, **kwargs)


class SublimeProcessListener(ProcessListener):
    def __init__(self, view: OutputView) -> None:
        self.view = view

    def on_data(self, text: str) -> None:
        self.view.append(text)

    def on_finished(self, completed_process: CompletedProcessInfo) -> None:
        self.view.append(
            dedent(
                f"""\
        [Finished in {completed_process.elapsed_time.difference():0.2f}s with exit code {completed_process.exit_code}]
        --------------------
        """
            )
        )


class SublimeConsoleView(OutputView):
    def __init__(self, window: sublime.Window) -> None:
        self.window = window
        self.view = self.window.create_output_panel("execpp")
        self.view.settings().set("word_wrap", True)
        self.view.settings().set("scroll_past_end", False)
        self.view.settings().set("line_numbers", True)
        self.show()

    def show(self) -> None:
        self.window.run_command("show_panel", {"panel": "output.execpp"})

    def append(self, text: str) -> None:
        self.view.run_command(
            "append", {"characters": text, "force": True, "scroll_to_end": True}
        )


class SublimeTabView(OutputView):
    def __init__(self, window: sublime.Window, *, read_only: bool = False) -> None:
        self.window = window
        self.view = self._construct_view()

    def _construct_view(self) -> sublime.View:
        view = self.window.new_file()
        view.set_name("Build")
        view.set_read_only(True)
        view.set_scratch(True)

        view.settings().set("scroll_past_end", False)
        view.settings().set("line_numbers", True)
        view.settings().set("word_wrap", True)
        return view

    def show(self) -> None:
        if not self.view.is_valid():
            self.view = self._construct_view()
        self.view.show(self.view.size())

    def append(self, text: str) -> None:
        self.view.run_command(
            "append", {"characters": text, "force": True, "scroll_to_end": True}
        )


class ExecppCommand(sublime_plugin.WindowCommand):
    def __init__(self, window: sublime.Window) -> None:
        super().__init__(window)

        self.output_view: Optional[OutputView] = None
        self.build_process: Optional[AsyncProcess] = None

    def is_enabled(self, kill: bool = False, **kwargs: object) -> bool:
        if kill:
            return bool(self.build_process and self.build_process.exit_code() is None)
        return True

    def _output_view_form(self, output_view_name: str) -> OutputView:
        if not output_view_name:
            return SublimeConsoleView(self.window)
        elif output_view_name == "panel":
            return SublimeConsoleView(self.window)
        elif output_view_name == "tab":
            return SublimeTabView(self.window)

        raise ValueError(f"Unknown output view form name: {output_view_name}")

    def run(
        self,
        command: List[str] = [],
        env: Dict[str, str] = {},
        variables: Dict[str, str] = {},
        working_dir: str = str(Path.cwd()),
        output_view: str = "panel",
        kill: bool = False,
        scope: str = "",
    ) -> None:
        if kill and self.build_process and self.build_process.is_active():
            log("[execpp] Killing active process.")
            self._kill_active_process()
            return

        if self.build_process and self.build_process.is_active():
            log("[execpp] Process already on going. Canceling it.")
            self._kill_active_process()
            return

        if not command:
            raise ValueError("Empty command given")

        if not any(
            self.window.active_view().match_selector(cursor.begin(), scope)
            for cursor in self.window.active_view().sel()
        ):
            log(
                "[execpp] Current scope does not match the job's scope configuration",
                scope,
            )
            return

        system_environment = os.environ.copy()
        settings_environment = (
            self.window.active_view().settings().get("build_env") or {}
        )
        sublime_build_system_variables = self.window.extract_variables()
        process_environment = merge_and_substitute_environment_variables(
            variables,
            env,
            sublime_build_system_variables,
            settings_environment,
            system_environment,
        )

        process_command = [
            expand_variable(command_part, process_environment)
            for command_part in command
        ]
        process_cwd = Path(expand_variable(working_dir, process_environment))
        log("[execpp] Running", command, "from", process_cwd)

        if self.output_view is None:
            self.output_view = self._output_view_form(output_view)
        self.output_view.show()

        self.output_view.append(
            f"[execpp Starting {datetime.datetime.now(tz=datetime.timezone.utc).isoformat()}]\n"
        )
        self.build_process = AsyncProcess(
            process_command,
            process_environment,
            process_cwd,
            SublimeProcessListener(self.output_view),
        )
        self.build_process.start()

    def _kill_active_process(self) -> None:
        if not self.build_process:
            return

        self.build_process.kill()
