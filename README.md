# PyFormat.info: Using %, .format() and f-strings for great good!

With this project @ulope and @zerok wanted to document Python's awesome string
formatting system with practical examples. While the official documentation on
python.org contains a great deal of information regarding the actual syntax
specification of the formatters and some examples, we felt it would be nice to
see %-formatting, `.format()` and f-strings side-by-side and provide even more
practical examples.


## What is Where?

The website you can find on https://pyformat.info is statically generated using
the `main.py`. This script parses the test cases in `tests/test_content*.py`,
which is more or less where all the content of the final site comes from:

* `tests/test_content.py` holds every example that works on all supported
  Python versions.
* Examples that use newer *syntax*, which older versions can't even parse, go
  into `tests/test_content_py3NN.py` (e.g. `test_content_py314.py` for
  t-strings). Those modules are only tested on Python 3.NN and newer, and their
  examples automatically get a "Python 3.NN+" badge.

Which file an example lives in has no influence on where it shows up. The order
of the sections on the page is defined in `toc.toml`.

Each test case can consist of following elements:

* A optional title which is encoded as the first line of the docstring prefixed
  with a `# `
* A short description on what is going on in the example which is what the rest
  of the docstring is used for
* An optional setup section that is placed after the docstring and before the
  first `*_result` assignment. It usually defines the variables used by all
  formatting styles.
* One assignment per formatting style. The variable name decides which style
  it is shown as:
  * `percent_result`: %-formatting
  * `format_result`: `str.format()`
  * `fstring_result`: f-strings
  * `tstring_result`: t-strings (shown regardless of the style picker)
* An assertion that checks all results and ends with the expected output
  string, e.g.
  `assert percent_result == format_result == fstring_result == 'one two'  # output`.
  The string on the right side is used as output on the website.
* An optional `@since(3, 11)` decorator for examples that parse everywhere but
  need a newer Python version to *run* (e.g. a new format spec option). The
  example is skipped on older versions and gets a version badge on the website.

The code is shown on the website exactly as it is written in the test case. If
a style is missing from an example, the website notes that it is not possible
with that style.

A small style picker at the top of the page lets visitors choose which styles
they want to see.


## How to Contribute

If you have another awesome example of what can be done with Python's
formatters please create a new test-case in `tests/test_content.py` (or the
`test_content_py3NN.py` module matching the syntax it needs) including a short
info message about what is going on there as the docstring. Every `*_result`
you add must be checked by the example's assertion; a test makes sure of that.

If your example starts a new section (it has a `# Title`), add its name without
the `test_` prefix to `toc.toml` where it fits logically.

Once you have that, simply open a pull-request! Please make sure that you code
is PEP8-compliant (except for the line length).


## Running the tests

We use [`pytest`](https://pytest.org) to both test the functionality of the
script generating the static HTML output as well as ensuring that the examples
on the page are syntactically correct and produce the desired output.

The project is managed with [uv](https://docs.astral.sh/uv/). Once uv is
installed, it takes care of the right Python version and all dependencies:

    uv run pytest
    uv run pyformat generate

The tests run on every supported Python version (currently 3.11 to 3.15).
To run them on all of them at once, use [`tox`](https://tox.wiki) with the
[`tox-uv`](https://github.com/tox-dev/tox-uv) plugin. uv downloads any missing
Python versions:

    uvx --with tox-uv tox

Generating the site needs the newest Python version used by a
`tests/test_content_py3NN.py` module (currently 3.14), because all examples
have to be parsed. `.python-version` makes uv use a suitable version by
default.
