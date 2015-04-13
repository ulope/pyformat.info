def test_simple():
    """
    Simple formatting

    Simple positional formatting is probably the most common use-case. Use it
    if the order of your arguments is not likely to change and you only have
    very few elements you want to concatinate.

    Since the elements are not represented by something as descriptive as a
    name it is easy to confuse their positions in the format if you try to
    concatinate too many elements.
    """
    old_result = '%s %s' % ('one', 'two', )
    new_result = '{} {}'.format('one', 'two')

    assert old_result == new_result
    assert old_result == 'one two'  # output


def test_string_pad_align_right():
    """
    Pad with spaces and align right
    """
    old_result = '%10s' % ('test', )
    new_result = '{:>10}'.format('test')

    assert old_result == new_result
    assert old_result == '      test'  # output


def test_string_pad_align_left():
    """
    Pad with spaces and align left
    """
    old_result = '%-10s' % ('test', )
    new_result = '{:10}'.format('test')

    assert old_result == new_result
    assert old_result == 'test      '  # output


def test_string_truncating():
    """
    Truncate overly long strings

    ...
    """
    old_result = '%5.5s' % ('xylophone', )
    new_result = '{:5.5}'.format('xylophone')

    assert old_result == new_result
    assert old_result == 'xylop'  # output


def test_integer():
    """
    Format interger

    ...
    """
    old_result = '%d' % (42, )
    new_result = '{:d}'.format(42)

    assert old_result == new_result
    assert old_result == '42'  # output


def test_integer_padding_zero():
    """
    Format interger with zero padding

    ...
    """
    old_result = '%04d' % (42, )
    new_result = '{:04d}'.format(42)

    assert old_result == new_result
    assert old_result == '0042'  # output


def test_integer_padding_space():
    """
    Format interger with space padding

    ...
    """
    old_result = '%4d' % (42, )
    new_result = '{:4d}'.format(42)

    assert old_result == new_result
    assert old_result == '  42'  # output


def test_dictionary_access():
    """
    Dictionary Access

    ...
    """
    data = {
        'first_name': 'First',
        'last_name': 'Last',
    }

    old_result = '%(first_name)s %(last_name)s' % data
    new_result = '{first_name} {last_name}'.format(**data)

    assert old_result == new_result
    assert old_result == 'First Last'  # output


def test_nested_dictionary_access():
    """
    Nested Dictionary Access

    ...
    """
    data = {
        'person': {
            'first_name': 'First',
            'last_name': 'Last',
        }
    }

    new_result = '{data[person][first_name]} {data[person][last_name]}'.format(data=data)

    assert new_result == 'First Last'  # output
