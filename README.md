# Development branch for "Version 2"

This is the development branch `v2` for "Version 2" of pyformat.info.  We're
currently migrating the page to use [Lektor][]. Therefore
the description below may not be completely accurate anymore.

The current plan is for this migration to be finished somewhen in the first
second of 2017. But - no promises :)


# PyFormat.info: Using %, f-strings, and .format() for great good!

With this project @ulope and @zerok wanted to document Python's awesome string
formatting system with practical examples. While the official documentation on
python.org contains a great deal of information regarding the actual syntax
specification of the formatters and some examples, we felt it would be nice to
see the new and old style of formatting side-by-side and provide even more
practical examples.


## What is Where?

The website you can find on https://pyformat.info is statically generated
using [Lektor][]. All examples are sub-pages of the `examples` page and consist
of one or multiple code-blocks providing the %, .format, or f-string syntax for
a specific use-case.

All the examples can be automatically tested using [tox][]:

```
$ tox
```


## Development setup

* Create a Python 3.6 virtualenv
* `pip install fabric3`
* `fab sync`

Now, you can execute `lektor` directly from your virtualenv in order to build
the website or start the development server.


## How to Contribute

If you have another awesome example of what can be done with Python's formatters
please create a `examples` subpage with all the formatting variants you want to
cover. Please also include a short summary describing why this example is
interesting.

Once you have that, simply open a pull-request! Please make sure that you code
is PEP8-compliant and that all tests are still passing.


[tox]: http://tox.testrun.org
[lektor]: https://getlektor.com
