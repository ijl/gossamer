# Gossamer

Gossamer watches you browse a website and record screenshots of your UI, then
recreates your browsing session and passes or fails tests depending on whether
the UI has changed. It's a way of automating in-browser visual regression
testing, using Gossamer to automate Selenium WebDriver, expose test statuses
of pass/fail/error, and provide visual diffs of failing tests. You needn't
write Selenium tests, or make and keep in sync static pages for testing UI:
this tool will test full webpages run on a development or testing webserver.
Gossamer can be integrated into your continuous integration either via the
command-line interface, or, if you're testing a Python application, via
Python unittest integration.

## Usage

Gossamer is a command-line application, called with `gossamer`. You create
tests you wish to record in a text Gossamerfile. For each test, a WebDriver
window is opened and you interact with the browser as a normal user, going
back to the command line when you wish to take a screenshot and pressing
enter. Your screenshots, and a JSON record of your test, is written to a
data directory. Playback is done by reading this directory, and comparing
against 'good' screenshots. Gossamer assumes that Selenium Server is
already running.

To start, create a file `Gossamerfile` and specify a name and URL to visit for
every test.

    [example]
    url=http://www.example.com

You can also add in additional settings:

    [example]
    url=http://www.example.com
    desc=Example.com hasn't changed
    screensize=800x1000
    browser=chrome
    expect_redirect=false

By default, Gossamer looks for a file called `Gossamerfile` in the current
directory, and stores data in `./gossamer` with one directory per test. Each
test directory contains a `record.json` containing the data to reproduce the
test, as well as good screenshots, and in a sub-directory `last`, the
last test run's (possibly failing) screenshots.

You can run your tests with:

    gossamer --file Gossamerfile --data <data_dir> --record --save-diff

If you wish to run only a subset of tests in that file, specify those tests'
names as positional arguments.

When you browse, wait for requests to finish and rendering to be complete before
moving on to another action. If you navigate to a new page, you will need
to take a screenshot before new events are observed.

If your UI has changed and you wish to update the screenshots to match, then
run with `--rerecord`: the test will be rerun automatically, and new PNGs
will be saved. To playback the tests, simply call without an `-r/-rr` flag.

If you're running Python tests, you can integrate your Gossamer tests like so:

    # myapp/test.py
    from gossamer import run_gossamerfile
    run_gossamerfile(locals(), <filename>, <data_dir>)

This mutates your module's locals to include a `unittest.TestCase` instance
for every test in the given Gossamerfile(s). Your test runner will then
detect and run them. You will, however, need to ensure that your Selenium
server and test webserver are up when your tests are run.

## Installation

Your testing machine will need
[Pillow's](https://github.com/python-imaging/Pillow) system-level
dependencies for PNG support. Gossamer can then be installed from PyPi with `pip install gossamerui`.

On that machine or another accessible to it you will need
[Selenium Server](http://docs.seleniumhq.org/download/) installed and
running. Note that Selenium Server comes with Firefox by default, needing
an additional system package for Chrome, and for Internet Explorer an
IE-specific standalone version of Selenium Server.

You'll also need your 'target' webserver running on any machine.


## Authors

See the file `AUTHORS`. Based on Facebook's
[Huxley](https://github.com/facebook/huxley), and rewritten.

## License

Apache 2.0


## Known Issues

* Scrolling is unreliable.
* Opening a slow iframe will likely timeout on playback.
* Internet Explorer < 11 (which is all Selenium supports) shouldn't work at
the moment because we use MutationObservers, but an older way of observing
changes can be added for IE<11 (see `js.pageChangingObserver`).

## Issues

Please create issues and pull requests at the [GitHub repository](https://github.com/ijl/gossamer).

## Contributing

* Once you have the repository, setup using `make develop`.
* Please add tests and use the included .pylintrc; you can run `make test`
and `make lint`.
* If any breaking changes are made to data structures, increment
`constant.DATA_VERSION` and
modify `util.import_recorded_run` to handle both new and old data.
* Feel free to contribute any functionality you want.

