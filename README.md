# Gossamer

This tool allows you to create visual regression tests by browsing normally and taking screenshots. You needn't write Selenium tests, or make and keep in sync static pages for testing UI: this tool will test full webpages run on a development or testing webserver. It uses Selenium WebDriver to run the tests, and can be run as part of continuous integration testing.


## Features

* Supports JavaScript, including single-page apps
* Allows navigating to new pages
* Records your clicks and text input
* During playback, waits for the page to be stable before taking further actions, rather than deciding on the basis of time elapsed
* Tests can be run alongside your other Python `unittest` tests. Populate a module with a `unittest.TestCase` for each test within a testfile by calling `run_gossamerfile(locals(), <filename>, <data_dir>)`.
* Configurable browser, data directories, and settings
* Data is exported and read on every run as regular JSON files and PNGs


## Usage

Specify a name and URL to visit for every test in a `Gossamerfile`.

    [example]
    url=http://www.example.com

You can also add in additional settings:

    [example]
    url=http://www.example.com
    desc=Example.com hasn't changed
    screensize=800x1000
    browser=chrome


By default, Gossamer looks for a file called `Gossamerfile` in the current
directory, and stores data in `./gossamer` with one directory per test. Each
test directory contains a `record.json` containing the data to reproduce the
test, as well as good screenshots, and in a sub-directory `last`, the
last test run's (possibly failing) screenshots.

You can run your tests with:

    gossamer --file Gossamerfile --data <data_dir> --record

If you wish to run only a subset of tests in that file, specify those tests' names as positional arguments.

    gossamer --file Gossamerfile --data <data_dir> --record example

If your UI has changed and you wish to update the screenshots to match, then
run with `--rerecord`: the test will be rerun automatically, and new PNGs
will be saved.

    gossamer --file Gossamerfile --data <data_dir> --rerecord

To playback the tests, simply call without an `-r/-rr` flag:

    gossamer --file Gossamerfile --data <data_dir>

Further command-line options:

    `--browser/-b`: browser to use
    `--save-diff/-e`: when two images don't match, save a `diff.png` which highlights pixels that differ
    `--overwrite/-o`: when recording tests, don't prompt about overwriting data
    `--local/-l`: URL to Selenium.

Command-line options take precedence over Gossamerfile options. During playback,
command-line or Gossamerfile options affecting the test itself are ignored;
only the Selenium server to test against and data directory can be changed.

If you're running Python tests, you can integrate your Gossamer tests like so:

    # myapp/test.py
    from gossamer import run_gossamerfile
    run_gossamerfile(locals(), <filename>, <data_dir>)

This populates your module's locals with a `unittest.TestCase` instance for every
test in the given Gossamerfile(s). Your test running will then detect and run them.
You will, however, need to ensure that your Selenium server and
test webserver are up when your tests are run.

## Installation

Your testing machine will need [Pillow's](https://github.com/python-imaging/Pillow) system-level dependencies for PNG support (namely `zlib1g-dev`, on Ubuntu, and Python dev). Gossamer can then be installed from PyPi with `pip install gossamer`.

On that machine or another accessible to it you will need [Selenium Server](http://docs.seleniumhq.org/download/) installed and running. Note that Selenium Server comes with Firefox by default, needing an additional system package for Chrome, and for Internet Explorer an IE-specific standalone version of Selenium Server.

You'll also need your 'target' webserver running on any machine.


## Authors

See the file `AUTHORS`. Based on Facebook's [Huxley](https://github.com/facebook/huxley), and rewritten.

## License

Apache 2.0


## Known Issues

* Need support for changing the test URL via CLI and `run_gossamerfile` to support different environments.
* Scrolling is unreliable.
* Opening a slow iframe will likely timeout on playback.
* Internet Explorer < 11 (which is all Selenium supports) shouldn't work at the moment because we use MutationObservers, but an older way of observing changes can be added for IE<11 (see `js.pageChangingObserver`).


## Contributing

* Once you have the repository, setup using `make develop`.
* Please add tests and use the included .pylintrc; you can run `make test` and `make lint`.
* If any breaking changes are made to data structures, increment `constant.DATA_VERSION` and
modify `util.import_recorded_run` to handle both new and old data.
* Feel free to contribute any functionality you want.

