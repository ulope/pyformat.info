import sys

import pytest


def since(*version):
    """
    Mark an example as needing at least the given Python version.

    The version is also shown as a badge next to the example on the page.
    """
    return pytest.mark.skipif(
        sys.version_info < version,
        reason="Needs Python {}+".format(".".join(map(str, version))),
    )


def test_simple():
    """
    # Basic formatting

    Simple positional formatting is probably the most common use-case. Use it
    if the order of your arguments is not likely to change and you only have
    very few elements you want to concatenate.

    Since the elements are not represented by something as descriptive as a
    name this simple style should only be used to format a relatively small
    number of elements.

    f-strings don't have this problem: the values are written directly into
    the placeholders.
    """
    a, b = 'one', 'two'

    percent_result = '%s %s' % (a, b)
    format_result = '{} {}'.format(a, b)
    fstring_result = f'{a} {b}'

    assert percent_result == format_result == fstring_result == 'one two'  # output


def test_simple_2():
    a, b = 1, 2

    percent_result = '%d %d' % (a, b)
    format_result = '{} {}'.format(a, b)
    fstring_result = f'{a} {b}'

    assert percent_result == format_result == fstring_result == '1 2'  # output


def test_simple_3():
    """
    With `.format()` it is possible to give placeholders an explicit
    positional index. This allows for re-arranging the order of display
    without changing the arguments.

    With f-strings you simply write the values in the order you want them.
    """
    a, b = 'one', 'two'

    format_result = '{1} {0}'.format(a, b)
    fstring_result = f'{b} {a}'

    assert format_result == fstring_result == 'two one'  # output


def test_conversion_flags():
    """
    # Value conversion

    `.format()` and f-strings call by default the [`__format__()`][1] method
    of an object for its representation. If you just want to render the
    output of `str(...)` or `repr(...)` you can use the `!s` or `!r`
    conversion flags.

    In %-style you usually use `%s` for the string representation but there
    is `%r` for a `repr(...)` conversion.

    [1]: https://docs.python.org/3/reference/datamodel.html#object.__format__
    """
    class Data:
        def __str__(self):
            return 'str'

        def __repr__(self):
            return 'repr'

    data = Data()

    percent_result = '%s %r' % (data, data)
    format_result = '{0!s} {0!r}'.format(data)
    fstring_result = f'{data!s} {data!r}'

    assert percent_result == format_result == fstring_result == 'str repr'  # output


def test_ascii_conversion():
    """
    There is also a conversion flag that uses the output of `ascii(...)`
    instead of `repr(...)`, which escapes all non-ASCII characters:
    """
    class Data:
        def __repr__(self):
            return 'räpr'

    data = Data()

    percent_result = '%r %a' % (data, data)
    format_result = '{0!r} {0!a}'.format(data)
    fstring_result = f'{data!r} {data!a}'

    assert percent_result == format_result == fstring_result == 'räpr r\\xe4pr'  # output


def test_string_pad_align():
    """
    # Padding and aligning strings

    By default values are formatted to take up only as many characters as
    needed to represent the content. It is however also possible to define that
    a value should be padded to a specific length.

    Unfortunately the default alignment for strings differs: %-formatting
    aligns them right, while `.format()` and f-strings align them left.

    Align right:
    """
    text = 'test'

    percent_result = '%10s' % text
    format_result = '{:>10}'.format(text)
    fstring_result = f'{text:>10}'

    assert percent_result == format_result == fstring_result == '      test'  # output


def test_string_pad_align_2():
    """
    Align left:
    """
    text = 'test'

    percent_result = '%-10s' % text
    format_result = '{:10}'.format(text)
    fstring_result = f'{text:10}'

    assert percent_result == format_result == fstring_result == 'test      '  # output


def test_string_pad_align_3():
    """
    Again, `.format()` and f-strings surpass %-formatting by providing more
    control over how values are padded and aligned.

    You are able to choose the padding character:
    """
    text = 'test'

    format_result = '{:_<10}'.format(text)
    fstring_result = f'{text:_<10}'

    assert format_result == fstring_result == 'test______'  # output


def test_string_pad_align_4():
    """
    And also center align values:
    """
    text = 'test'

    format_result = '{:^10}'.format(text)
    fstring_result = f'{text:^10}'

    assert format_result == fstring_result == '   test   '  # output


def test_string_pad_align_5():
    """
    When using center alignment where the length of the string leads to an
    uneven split of the padding characters the extra character will be placed
    on the right side:
    """
    text = 'zip'

    format_result = '{:^6}'.format(text)
    fstring_result = f'{text:^6}'

    assert format_result == fstring_result == ' zip  '  # output


def test_string_truncating():
    """
    # Truncating long strings

    Inverse to padding it is also possible to truncate overly long values
    to a specific number of characters.

    The number behind a `.` in the format specifies the precision of the
    output. For strings that means that the output is truncated to the
    specified length. In our example this would be 5 characters.
    """
    text = 'xylophone'

    percent_result = '%.5s' % text
    format_result = '{:.5}'.format(text)
    fstring_result = f'{text:.5}'

    assert percent_result == format_result == fstring_result == 'xylop'  # output


def test_string_trunc_pad():
    """
    # Combining truncating and padding

    It is also possible to combine truncating and padding:
    """
    text = 'xylophone'

    percent_result = '%-10.5s' % text
    format_result = '{:10.5}'.format(text)
    fstring_result = f'{text:10.5}'

    assert percent_result == format_result == fstring_result == 'xylop     '  # output


def test_number():
    """
    # Numbers

    Of course it is also possible to format numbers.

    Integers:
    """
    number = 42

    percent_result = '%d' % number
    format_result = '{:d}'.format(number)
    fstring_result = f'{number:d}'

    assert percent_result == format_result == fstring_result == '42'  # output


def test_number_2():
    """
    Floats:
    """
    pi = 3.141592653589793

    percent_result = '%f' % pi
    format_result = '{:f}'.format(pi)
    fstring_result = f'{pi:f}'

    assert percent_result == format_result == fstring_result == '3.141593'  # output


def test_number_padding():
    """
    # Padding numbers

    Similar to strings numbers can also be constrained to a specific width.
    """
    number = 42

    percent_result = '%4d' % number
    format_result = '{:4d}'.format(number)
    fstring_result = f'{number:4d}'

    assert percent_result == format_result == fstring_result == '  42'  # output


def test_number_padding_2():
    """
    Again similar to truncating strings the precision for floating point
    numbers limits the number of positions after the decimal point.

    For floating points the padding value represents the length of the complete
    output. In the example below we want our output to have at least 6
    characters with 2 after the decimal point.
    """
    pi = 3.141592653589793

    percent_result = '%06.2f' % pi
    format_result = '{:06.2f}'.format(pi)
    fstring_result = f'{pi:06.2f}'

    assert percent_result == format_result == fstring_result == '003.14'  # output


def test_number_padding_3():
    """
    For integer values providing a precision doesn't make much sense and is
    actually forbidden with `.format()` and f-strings (it will result in a
    ValueError).
    """
    number = 42

    percent_result = '%04d' % number
    format_result = '{:04d}'.format(number)
    fstring_result = f'{number:04d}'

    with pytest.raises(ValueError):
        '{:04.2d}'.format(number)
    with pytest.raises(ValueError):
        f'{number:04.2d}'

    assert percent_result == format_result == fstring_result == '0042'  # output


def test_number_sign():
    """
    # Signed numbers

    By default only negative numbers are prefixed with a sign. This can be
    changed of course.
    """
    number = 42

    percent_result = '%+d' % number
    format_result = '{:+d}'.format(number)
    fstring_result = f'{number:+d}'

    assert percent_result == format_result == fstring_result == '+42'  # output


def test_number_sign_2():
    """
    Use a space character to indicate that negative numbers should be prefixed
    with a minus symbol and a leading space should be used for positive ones.
    """
    number = -23

    percent_result = '% d' % number
    format_result = '{: d}'.format(number)
    fstring_result = f'{number: d}'

    assert percent_result == format_result == fstring_result == '-23'  # output


def test_number_sign_3():
    number = 42

    percent_result = '% d' % number
    format_result = '{: d}'.format(number)
    fstring_result = f'{number: d}'

    assert percent_result == format_result == fstring_result == ' 42'  # output


def test_number_sign_4():
    """
    `.format()` and f-strings are also able to control the position of the
    sign symbol relative to the padding.
    """
    number = -23

    format_result = '{:=5d}'.format(number)
    fstring_result = f'{number:=5d}'

    assert format_result == fstring_result == '-  23'  # output


def test_number_sign_5():
    number = 23

    format_result = '{:=+5d}'.format(number)
    fstring_result = f'{number:=+5d}'

    assert format_result == fstring_result == '+  23'  # output


def test_number_sign_6():
    """
    Rounding a small negative number can lead to a confusing negative zero:
    """
    number = -0.001

    percent_result = '%.2f' % number
    format_result = '{:.2f}'.format(number)
    fstring_result = f'{number:.2f}'

    assert percent_result == format_result == fstring_result == '-0.00'  # output


@since(3, 11)
def test_number_sign_7():
    """
    The `z` option turns negative zero into a regular zero:
    """
    number = -0.001

    format_result = '{:z.2f}'.format(number)
    fstring_result = f'{number:z.2f}'

    assert format_result == fstring_result == '0.00'  # output


def test_number_grouping():
    """
    # Grouping digits

    Long numbers are easier to read with a thousands separator. Use `,` or
    `_` to group the digits:
    """
    number = 1234567

    format_result = '{:,}'.format(number)
    fstring_result = f'{number:,}'

    assert format_result == fstring_result == '1,234,567'  # output


def test_number_grouping_2():
    number = 1234567

    format_result = '{:_}'.format(number)
    fstring_result = f'{number:_}'

    assert format_result == fstring_result == '1_234_567'  # output


def test_number_grouping_3():
    """
    Grouping can be combined with all other options, e.g. a precision:
    """
    number = 1234567.891

    format_result = '{:,.2f}'.format(number)
    fstring_result = f'{number:,.2f}'

    assert format_result == fstring_result == '1,234,567.89'  # output


def test_number_grouping_4():
    """
    For binary, octal and hexadecimal numbers `_` groups four digits:
    """
    number = 0xDEADBEEF

    format_result = '{:_x}'.format(number)
    fstring_result = f'{number:_x}'

    assert format_result == fstring_result == 'dead_beef'  # output


@since(3, 14)
def test_number_grouping_5():
    """
    The digits after the decimal point can be grouped too:
    """
    number = 1234567.891011

    format_result = '{:_.6_f}'.format(number)
    fstring_result = f'{number:_.6_f}'

    assert format_result == fstring_result == '1_234_567.891_011'  # output


def test_named_placeholders():
    """
    # Named placeholders

    %-formatting and `.format()` both support named placeholders. f-strings
    don't need them: you write the names (or any other expression) directly
    into the string.
    """
    data = {'first': 'Hodor', 'last': 'Hodor!'}

    percent_result = '%(first)s %(last)s' % data
    format_result = '{first} {last}'.format(**data)
    fstring_result = f"{data['first']} {data['last']}"

    assert percent_result == format_result == fstring_result == 'Hodor Hodor!'  # output


def test_named_placeholders_2():
    """
    `.format()` also accepts keyword arguments.
    """
    first, last = 'Hodor', 'Hodor!'

    format_result = '{first} {last}'.format(first=first, last=last)
    fstring_result = f'{first} {last}'

    assert format_result == fstring_result == 'Hodor Hodor!'  # output


def test_getitem_and_getattr():
    """
    # Getitem and Getattr

    `.format()` and f-strings allow even greater flexibility in accessing
    nested data structures.

    They support accessing containers that support `__getitem__` like for
    example dictionaries and lists. Note the difference: `.format()` has its
    own syntax where dictionary keys are written without quotes, while inside
    an f-string you write regular Python, so the keys need quotes:
    """
    person = {'first': 'Jean-Luc', 'last': 'Picard'}

    format_result = '{p[first]} {p[last]}'.format(p=person)
    fstring_result = f"{person['first']} {person['last']}"

    assert format_result == fstring_result == 'Jean-Luc Picard'  # output


def test_getitem_and_getattr_2():
    data = [4, 8, 15, 16, 23, 42]

    format_result = '{d[4]} {d[5]}'.format(d=data)
    fstring_result = f'{data[4]} {data[5]}'

    assert format_result == fstring_result == '23 42'  # output


def test_getitem_and_getattr_3():
    """
    As well as accessing attributes on objects via `getattr()`:
    """
    class Plant:
        type = 'tree'

    plant = Plant()

    format_result = '{p.type}'.format(p=plant)
    fstring_result = f'{plant.type}'

    assert format_result == fstring_result == 'tree'  # output


def test_getitem_and_getattr_4():
    """
    Both type of access can be freely mixed and arbitrarily nested:
    """
    class Plant:
        type = 'tree'
        kinds = [{'name': 'oak'}, {'name': 'maple'}]

    plant = Plant()

    format_result = '{p.type}: {p.kinds[0][name]}'.format(p=plant)
    fstring_result = f"{plant.type}: {plant.kinds[0]['name']}"

    assert format_result == fstring_result == 'tree: oak'  # output


def test_expressions():
    """
    # Expressions

    f-strings can contain any Python expression, for example arithmetic:
    """
    a, b = 3, 4

    fstring_result = f'{a} + {b} = {a + b}'

    assert fstring_result == '3 + 4 = 7'  # output


def test_expressions_2():
    """
    Or method and function calls:
    """
    name = 'jean-luc picard'

    fstring_result = f'{name.title()} has {len(name)} letters'

    assert fstring_result == 'Jean-Luc Picard has 15 letters'  # output


@since(3, 8)
def test_debug():
    """
    # Self-documenting expressions

    Add an `=` after the expression to output both the expression and its
    value. This is very handy for debugging. By default the value is shown
    using `repr(...)`:
    """
    user = 'eric_idle'

    fstring_result = f'{user=}'

    assert fstring_result == "user='eric_idle'"  # output


@since(3, 8)
def test_debug_2():
    """
    Whitespace around the `=` is kept in the output:
    """
    user = 'eric_idle'

    fstring_result = f'{user = }'

    assert fstring_result == "user = 'eric_idle'"  # output


@since(3, 8)
def test_debug_3():
    """
    Any expression works:
    """
    a, b = 3, 4

    fstring_result = f'{a + b = }'

    assert fstring_result == 'a + b = 7'  # output


@since(3, 8)
def test_debug_4():
    """
    A format spec is applied to the value, which then isn't shown using
    `repr(...)` anymore:
    """
    pi = 3.141592653589793

    fstring_result = f'{pi=:.2f}'

    assert fstring_result == 'pi=3.14'  # output


@since(3, 8)
def test_debug_5():
    """
    Conversion flags work as well:
    """
    user = 'eric_idle'

    fstring_result = f'{user=!s}'

    assert fstring_result == 'user=eric_idle'  # output


@since(3, 12)
def test_fstring_syntax():
    """
    # Quotes, backslashes and comments

    Since Python 3.12 the expressions inside an f-string follow the same rules
    as any other Python code.

    You can use the same kind of quotes as the f-string itself:
    """
    person = {'first': 'Jean-Luc', 'last': 'Picard'}

    fstring_result = f'{person['first']} {person['last']}'

    assert fstring_result == 'Jean-Luc Picard'  # output


@since(3, 12)
def test_fstring_syntax_2():
    """
    Backslashes are allowed:
    """
    parts = ['C:', 'Users', 'eric']

    fstring_result = f'{'\\'.join(parts)}'

    assert fstring_result == 'C:\\Users\\eric'  # output


@since(3, 12)
def test_fstring_syntax_3():
    """
    And expressions can span multiple lines and contain comments:
    """
    price, quantity = 4.5, 3

    fstring_result = f'{
        price * quantity  # the total price
    :.2f} EUR'

    assert fstring_result == '13.50 EUR'  # output


def test_datetime():
    """
    # Datetime

    `.format()` and f-strings also allow objects to control their own
    rendering. This for example allows datetime objects to be formatted
    inline:
    """
    from datetime import datetime
    dt = datetime(2001, 2, 3, 4, 5)

    format_result = '{:%Y-%m-%d %H:%M}'.format(dt)
    fstring_result = f'{dt:%Y-%m-%d %H:%M}'

    assert format_result == fstring_result == '2001-02-03 04:05'  # output


def test_param_align():
    """
    # Parametrized formats

    Additionally, `.format()` and f-strings allow all of the components of
    the format to be specified dynamically using parametrization.
    Parametrized formats are nested expressions in braces that can appear
    anywhere in the parent format after the colon.

    %-formatting also supports some parametrization but is much more
    limited. Namely it only allows parametrization of the width and precision
    of the output.

    Parametrized alignment and width:
    """
    text = 'test'
    align, width = '^', 10

    format_result = '{:{align}{width}}'.format(text, align=align, width=width)
    fstring_result = f'{text:{align}{width}}'

    assert format_result == fstring_result == '   test   '  # output


def test_param_prec():
    """
    Parametrized precision:
    """
    text, number, prec = 'Gibberish', 2.7182, 3

    percent_result = '%.*s = %.*f' % (prec, text, prec, number)
    format_result = '{:.{prec}} = {:.{prec}f}'.format(text, number, prec=prec)
    fstring_result = f'{text:.{prec}} = {number:.{prec}f}'

    assert percent_result == format_result == fstring_result == 'Gib = 2.718'  # output


def test_param_width_prec():
    """
    Width and precision:
    """
    number, width, prec = 2.7182, 5, 2

    percent_result = '%*.*f' % (width, prec, number)
    format_result = '{:{width}.{prec}f}'.format(number, width=width, prec=prec)
    fstring_result = f'{number:{width}.{prec}f}'

    assert percent_result == format_result == fstring_result == ' 2.72'  # output


def test_param_prec_2():
    """
    The nested format can be used to replace *any* part of the format
    spec, so the precision example above could be rewritten as:
    """
    text, number, prec = 'Gibberish', 2.7182, '.3'

    format_result = '{:{prec}} = {:{prec}}'.format(text, number, prec=prec)
    fstring_result = f'{text:{prec}} = {number:{prec}}'

    assert format_result == fstring_result == 'Gib = 2.72'  # output


def test_param_date():
    """
    The components of a date-time can be set separately:
    """
    from datetime import datetime
    dt = datetime(2001, 2, 3, 4, 5)
    dfmt, tfmt = '%Y-%m-%d', '%H:%M'

    format_result = '{:{dfmt} {tfmt}}'.format(dt, dfmt=dfmt, tfmt=tfmt)
    fstring_result = f'{dt:{dfmt} {tfmt}}'

    assert format_result == fstring_result == '2001-02-03 04:05'  # output


def test_param_order_1():
    """
    With `.format()` the nested formats can be positional arguments. Position
    depends on the order of the opening curly braces:
    """
    number = 2.7182818284

    format_result = '{:{}{}{}.{}}'.format(number, '>', '+', 10, 3)

    assert format_result == '     +2.72'  # output


def test_param_order_2():
    """
    And of course keyword arguments can be added to the mix as before:
    """
    number = 2.7182818284

    format_result = '{:{}{sign}{}.{}}'.format(number, '>', 10, 3, sign='+')

    assert format_result == '     +2.72'  # output


def test_custom_1():
    """
    # Custom objects

    The datetime example works through the use of the `__format__()` magic
    method. You can define custom format handling in your own objects by
    overriding this method. This gives you complete control over the format
    syntax used.
    """
    class HAL9000:
        def __format__(self, format):
            if format == 'open-the-pod-bay-doors':
                return "I'm afraid I can't do that."
            return 'HAL 9000'

    hal = HAL9000()

    format_result = '{:open-the-pod-bay-doors}'.format(hal)
    fstring_result = f'{hal:open-the-pod-bay-doors}'

    assert format_result == fstring_result == "I'm afraid I can't do that."  # output


@since(3, 14)
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


@since(3, 14)
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
