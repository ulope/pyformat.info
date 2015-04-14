from main import parse_docstring, parse_function


def test_parse_docstring_without_docstring():
    assert parse_docstring('') == (None, None)
    assert parse_docstring('  ') == (None, None)
    assert parse_docstring(None) == (None, None)


def test_parse_docstring_with_title_and_description():
    assert parse_docstring('# title\n\ndescription') == ('title', 'description')


def test_parse_docstring_with_title_only():
    assert parse_docstring('# title') == ('title', None)
    assert parse_docstring('# title\n\n') == ('title', None)


def test_parse_docstring_without_title():
    """
    If a docstring contains multiple lines but the first one doesn't start
    with a #, the whole docstring is considered the description.
    """
    assert parse_docstring('not the title\nnot the title') == (None, 'not the title\nnot the title')
    assert parse_docstring('not the title') == (None, 'not the title')


def test_parse_function_complete():
    def dummy():
        """
        # Title

        Blah
        """

        x = {'a': 1}

        old_result = "%(a)s" % x
        new_result = "{x.a}".format(x=x)

        assert old_result == new_result
        assert new_result == "1"  # output

    example = parse_function(dummy)

    assert example.name == 'dummy'
    assert example.title == "Title"
    assert example.details == "Blah"
    assert example.setup == "x = {'a': 1}"
    assert example.old == '"%(a)s" % x'
    assert example.new == '"{x.a}".format(x=x)'
    assert example.output == "1"


def test_parse_function_minimal():
    def dummy():
        new_result = "{}".format(1)

        assert new_result == "1"  # output

    example = parse_function(dummy)

    assert example.name == 'dummy'
    assert example.title is None
    assert example.details is None
    assert example.setup == ""
    assert example.old == ""
    assert example.new == '"{}".format(1)'
    assert example.output == "1"


def test_parse_function_empty():
    def dummy():
        pass

    example = parse_function(dummy)

    assert example.name == 'dummy'
    assert example.title is None
    assert example.details is None
    assert example.setup == "pass"
    assert example.old == ""
    assert example.new == ""
    assert example.output == ""
