# Sublime package extendible-exec
`extendible-exec` is a simple (and incomplete) extension of Sublime Text's built-in build system created to solve one issue: Being able to *extend* environment variables in build configurations, not just re-define.
During development, I was tired of writing long commands in JSON, so I also added an almost identical interface for defining build system configuration in YAML.

The command name `execpp` is inspired by the convention used by C++.

## Using extendible-exec instead of built-in
To use extendible-exec instead of the built-in build system, assign key bindings to the following commands:
* `list_execpp_builds`: For selecting a build from a list, similar to the built-in functionality of `ctrl+shift+b`.
* `run_last_execpp_build`: For running the last selected build, similar to the built-in functionality of `ctrl+b`.

## Extending environment variables
Environment variables and variables defined by Sublime Text can be used anywhere in the build system configuration file.
Sublime Text built-in variables, such as `${file_path}` and `${file_base_name}`, in addition to environment variables, such as `${PATH}` and `${USER}`, can be used anywhere in the file.
All variables, whether Sublime Text build-in variables or environment variables, ***has*** to use the syntax `${variable_name}`, other variations are not substituted.

When defining environment variables, they can extend existing ones using `PATH: "${PATH}:/opt/software/`.

## Defining build system configuration in YAML files
Extendible-exec allows defining build system configuration in YAML-files using a similar interface as the built-in build system's `sublime-build` files.
The configuration is defined in files with the extension `.execpp-build`.

Following is an example of a build system defined in a `.execpp-build` file:
```yaml
name: Example build
command:
  - echo
  - Hello world
```
The example highlights one the only difference to Sublime Test's built-in build system configuration, namely `cmd` is renamed `command`, and `shell_cmd` is removed.
The reason for this is because having both `cmd` and `shell_cmd` makes sense when defining the build system in JSON files where mimicked shell scripts are annoying.
YAML syntax have good support for multiline strings, so `shell_cmd` can be achieved with the following:
```yaml
name: Example shell_cmd
command:
  - bash
  - -c
  - |
    echo "Running build"
    ./application > output.log
```

## Build system configuration file discovery
Extendible-exec files are searched for in the following locations with the `execpp-build` extension:
* In the Sublime Text configuration directory, for example "${HOME}/.config/sublime-text/Packages"
* In the project directory, if Sublime Text is opened as a project.
* In the opened directory, if Sublime Text opened a directory.

## Incomplete
The extension is incomplete and not well tested ‒ see the existing "test suite" for a good laugh :).
I am finding and fixing bugs as I go.
So use it at your own discretion!
