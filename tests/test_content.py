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
