from collections import ChainMap
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import (
    Callable,
    Dict,
    List,
    Optional,
)


@dataclass(frozen=True)
class ExecppYamlBuild:
    command: List[str] = field(default=list)
    env: Dict[str, str] = field(default=dict)
    variables: Dict[str, str] = field(default=dict)
    working_dir: str = str(Path.cwd())
    output_view: str = "panel"
    kill: bool = False


class Build:
    def __init__(self, loaded_config) -> None:
        self.loaded_config = loaded_config

    def name(self) -> str:
        return self.loaded_config.get("name")

    def names(self) -> List[str]:
        return [build.name() for build in self.variants()]

    def variants(self) -> List["Build"]:
        return [self] + [Build(ChainMap(variant, {"variant": []}, self.loaded_config)) for variant in self.loaded_config.get("variants", [])]

    def _find_variant(self, name: str) -> "Build":
        if name == self.name():
            return self

        variant = [build for build in self.variants() if build.name() == name]
        if not variant:
            raise ValueError(f"No build variant called {name}")
        return variant[0]

    def config_for(self, name: str) -> ExecppYamlBuild:
        if name not in self.names():
            raise ValueError(f"No build named {name}")

        build = self._find_variant(name)
        return ExecppYamlBuild(
            command=build.loaded_config.get("command", []),
            env=build.loaded_config.get("env", {}),
            variables=build.loaded_config.get("variables", {}),
            working_dir=build.loaded_config.get("working_dir", str(Path.cwd())),
            output_view=build.loaded_config.get("output_view", "panel"),
            kill=build.loaded_config.get("kill", False),
        )


def load_resource(yaml_content: str):
    try:
        import yaml
    except ImportError:
        sublime.error_dialog("Unable to load .execpp-build file. Found no yaml parser to import.")

    return yaml.safe_load(yaml_content)
