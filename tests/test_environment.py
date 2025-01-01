from getpass import getuser

from lib.environment import merge_and_substitute_environment_variables

def test_environment_variables_in_dict_expands() -> None:
    env = {"greeting": "Hello ${USER}"}
    result = merge_and_substitute_environment_variables(env)
    assert result["greeting"].endswith(getuser())
    assert "${USER}" not in result["greeting"]


def test_merging_environment_precedence() -> None:
    os_env = {"important_key": "overwritten value"}
    sublime_env = {
        "important_key": "also overriden",
        "other_key": "stays",
    }
    user_env = {
        "important_key": "stays",
        "user_key": "stays",
    }

    result = merge_and_substitute_environment_variables(user_env, sublime_env, os_env)
    assert "stays" == result["important_key"]
    assert "stays" == result["other_key"]
    assert "stays" == result["user_key"]
