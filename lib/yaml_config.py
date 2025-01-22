from collections import ChainMap
from dataclasses import dataclass, field
from pathlib import Path
from typing import (
    Any,
    Dict,
    List,
    MutableMapping,
)

try:
    import yaml
except ImportError as error:
    raise ImportError(
        "Unable to load .execpp-build file. Found no yaml parser to import."
    ) from error


@dataclass(frozen=True)
class ExecppYamlBuild:
    command: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)
    variables: Dict[str, str] = field(default_factory=dict)
    working_dir: str = str(Path.cwd())
    output_view: str = "panel"
    scope: str = ""
    kill: bool = False


class Build:
    def __init__(self, loaded_config: MutableMapping[str, Any]) -> None:
        self.loaded_config = loaded_config

    def name(self) -> str:
        if "name" not in self.loaded_config:
            raise KeyError("Build does not contain a name.")

        # This default value is only to convince Mypy it's a string until
        # self.loaded config has defined types.
        return self.loaded_config.get("name", "")

    def names(self) -> List[str]:
        return [build.name() for build in self.variants()]

    def variants(self) -> List["Build"]:
        return [self] + [
            Build(ChainMap(variant, {"variant": []}, self.loaded_config))
            for variant in self.loaded_config.get("variants", [])
        ]

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
            scope=build.loaded_config.get("scope", ""),
            kill=build.loaded_config.get("kill", False),
        )

    def scope(self) -> str:
        return self.loaded_config.get("scope", "")


def load_resource(yaml_content: str) -> MutableMapping[str, Any]:
    # Ignore this until the value in the file can be assigned types.
    return yaml.safe_load(yaml_content)  # type: ignore
