# PyFormat.info: Using % and .format() for great good!

With this project @ulope and @zerok wanted to document Python's awesome string
formatting system with practical examples. While the official documentation on
python.org contains a great deal of information regarding the actual syntax
specification of the formatters and some examples, we felt it would be nice to
see the new and old style of formatting side-by-side and provide even more
practical examples.


## What is Where?

The website you can find on http://pyformat.info is statically generated using
the `main.py`. This script parses the test cases specified in
`tests/test_content.py` which is more or less where all the content of the
final site comes from.

Each test case can consist of following elements:

* A optional title which is encoded as the first line of the docstring prefixed
  with a `# `
* A short description on what is going on in the example which is what the rest
  of the docstring is used for
* A value computation for the old-style formatter which is assigned to a
  variable called `old_result`
* A value computation for the new-style formatter which is assigned to a
  variable called `new_result`
* A handful of assertions. The last one that has a string on the right side is
  used as output on the website.
* An optional setup section that is placed after the docstring and before the
  `old_result` asignment

If no `old_result` is provided this indicates that the feature is only
available for the new formatting style and an appropriate message is rendered
on the website.


## How to Contribute

If you have another awesome example of what can be done with Python's
formatters please create a new test-case in `tests/test_content.py` including a
short info message about what is going on there as the docstring.

Once you have that, simply open a pull-request! Please make sure that you code
is PEP8-compliant (except for the line length).
