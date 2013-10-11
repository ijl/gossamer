# Changelog

## 0.9.5

* Fix Python `unittest` integration

* Misc fixes and improvements

## 0.9.4

* Fix events not being saved unless an initial screenshot was taken.

* Refactor `local` and `remote` Selenium URLs to just `selenium`. Specify on
the command-line with `-s` or `--selenium`.

* `postdata` argument now expects a Python dictionary as JSON.

* Gossamer now recreates dropdown selections on Chrome. Firefox will likely
report the value as at the time of opening the dropdown, not selecting a value,
so needs a workaround.

* Allow an initial redirect during playback with the addition of
`expect_redirect=True` in a Gossamerfile.

* Ensured that expected exceptions caused when interacting with the CLI, such
as Selenium not being available, result in a simple message being written to
stderr rather than a traceback.

## 0.9

* Rewrite

## 0.2

* Initial open-source release

## 0.1

* Pre-beta
