"""
Examples that need Python 3.12+ syntax.

They live in their own module so the rest of the content can still be
tested on older Python versions. Their position on the page is defined in
``toc.toml``, and the version badge is taken from the module name.
"""


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


def test_fstring_syntax_2():
    """
    Backslashes are allowed:
    """
    parts = ['C:', 'Users', 'eric']

    fstring_result = f'{'\\'.join(parts)}'

    assert fstring_result == 'C:\\Users\\eric'  # output


def test_fstring_syntax_3():
    """
    And expressions can span multiple lines and contain comments:
    """
    price, quantity = 4.5, 3

    fstring_result = f'{
        price * quantity  # the total price
    :.2f} EUR'

    assert fstring_result == '13.50 EUR'  # output
