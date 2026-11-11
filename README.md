# PyFormat.info: Using %, .format() and f-strings for great good!

With this project @ulope and @zerok wanted to document Python's awesome string
formatting system with practical examples. While the official documentation on
python.org contains a great deal of information regarding the actual syntax
specification of the formatters and some examples, we felt it would be nice to
see %-formatting, `.format()` and f-strings side-by-side and provide even more
practical examples.


## What is Where?

The website you can find on https://pyformat.info is statically generated using
the `main.py`. This script parses the test cases specified in
`tests/test_content.py` which is more or less where all the content of the
final site comes from.

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
* An optional `@since(3, 12)` decorator for examples that need a Python version
  newer than 3.6. It is shown as a version badge on the website.

The code is shown on the website exactly as it is written in the test case. If
a style is missing from an example, the website notes that it is not possible
with that style.

A small style picker at the top of the page lets visitors choose which styles
they want to see.


## How to Contribute

If you have another awesome example of what can be done with Python's
formatters please create a new test-case in `tests/test_content.py` including a
short info message about what is going on there as the docstring. Every
`*_result` you add must be checked by the example's assertion; a test makes
sure of that.

Once you have that, simply open a pull-request! Please make sure that you code
is PEP8-compliant (except for the line length).


## Running the tests

We use [`pytest`](https://pytest.org) to both test the functionality of the
script generating the static HTML output as well as ensuring that the examples
on the page are syntactically correct and produce the desired output.

The examples use the newest Python syntax (e.g. t-strings), so the tests and
the site generation require Python 3.14 or newer:

    pip install -e .
    pytest tests
    pyformat generate

Alternatively you can use [`tox`](https://tox.wiki), for which this repository
contains a configuration file.
