import collections
import os
import string
from typing import (
    Dict,
)


def expand_variable(environment_variable_value: str, env: Dict[str, str]) -> str:
    defaulted_mapping: Dict[str, str] = collections.defaultdict(str)
    defaulted_mapping.update(env)
    return string.Template(environment_variable_value).substitute(env)


def merge_and_substitute_environment_variables(
    *environments: Dict[str, str]
) -> Dict[str, str]:
    merged_environment = collections.ChainMap(*environments)
    processed_environments = {
        enviornment_variable: expand_variable(
            os.path.expandvars(value), merged_environment
        )
        for enviornment_variable, value in merged_environment.items()
    }
    return processed_environments
