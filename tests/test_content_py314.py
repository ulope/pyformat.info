"""
Examples that need Python 3.14+ syntax.

They live in their own module so the rest of the content can still be
tested on older Python versions. Their position on the page is defined in
``toc.toml``, and the version badge is taken from the module name.
"""


def test_tstring():
    """
    # Template strings

    t-strings look like f-strings, but they don't produce a `str`. Instead
    they create a [`Template`][1] object that keeps the literal text and the
    interpolated values apart. The code receiving the template decides how to
    combine them, for example to escape HTML, build safe SQL queries or
    produce structured logs.

    Iterating over a template yields its strings and [`Interpolation`][2]
    objects, which carry the value:

    [1]: https://docs.python.org/3/library/string.templatelib.html
    [2]: https://docs.python.org/3/library/string.templatelib.html#string.templatelib.Interpolation
    """
    from html import escape
    from string.templatelib import Interpolation

    def safe_html(template):
        result = ''
        for part in template:
            if isinstance(part, Interpolation):
                part = escape(str(part.value))
            result += part
        return result

    user = '<script>'

    tstring_result = safe_html(t'<p>Hello {user}!</p>')

    assert tstring_result == '<p>Hello &lt;script&gt;!</p>'  # output


def test_tstring_2():
    """
    Each interpolation also remembers the expression it came from:
    """
    import json

    def to_json(template):
        data = {}
        for interpolation in template.interpolations:
            data[interpolation.expression] = interpolation.value
        return json.dumps(data)

    user, action = 'eric', 'login'

    tstring_result = to_json(t'{user} did {action}')

    assert tstring_result == '{"user": "eric", "action": "login"}'  # output
