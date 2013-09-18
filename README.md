# Gossamer

This tool allows you to create visual regression tests by browsing normally and taking screenshots. You needn't write Selenium tests, or make and keep in sync static pages for testing UI: this tool will test full webpages run on a development or testing webserver. It uses Selenium WebDriver to run the tests, and can be run as part of continuous integration testing.


## Features

* Supports JavaScript, including single-page apps
* Allows navigating to new pages
* Records your clicks and text input
* During playback, waits for the page to be stable before taking further actions, rather than deciding on the basis of time elapsed
* Tests can be run alongside your other Python `unittest` tests. Create a `unittest.TestCase` from a test file by with `run_gossamerfile(<filename>)`
* Configurable browser, data directories, and settings
* Data is exported and read on every run as regular JSON files and PNGs


## Usage
Create a Gossamerfile

Then run using:

    gossamer --data <data_dir> --record


## Installation

Your testing machine will need [Selenium](http://docs.seleniumhq.org) WebDriver installed, as well as [Pillow's](https://github.com/python-imaging/Pillow) dependencies for PNG support (namely `zlib1g-dev`, on Ubuntu, and Python dev). Both are available in many distros' repositories; see their documentation for more. On that machine or another accessible to it you will need Selenium Server installed and running, and a web server running your application.


## Authors

See the file `AUTHORS`. Based on Facebook's [Huxley](https://github.com/facebook/huxley), and rewritten.

## License

Apache 2.0


## Known Issues

* Scrolling is unreliable.
* Manually opening an iframe is not handled well.


## Contributing

* See the included `Makefile`.
* Please add tests and use the included .pylintrc.
* If any breaking changes are made to data structures, increment `constant.DATA_VERSION` and
modify `util.import_recorded_run` to handle both new and old data.
* Feel free to contribute any functionality you want.

