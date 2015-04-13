from collections import namedtuple
import importlib
import inspect
from textwrap import dedent, indent
import click
from rex import rex


CONTENT_MODULE = "tests.test_content"

OUTPUT_RE = rex("""s/^.*?assert .*? == ['"](.*)['"].*?# output$/\\1/""")


Example = namedtuple("Example", ('name', 'doc', 'setup', 'old', 'new', 'output'))


def parse_function(function):
    seen_doc_start = False
    seen_doc_end = False
    seen_setup_end = False
    setup = []
    old = ""
    new = ""
    output = ""
    lines, _ = inspect.getsourcelines(function)
    for line in lines:
        if not seen_doc_start and '''"""''' in line:
            seen_doc_start = True
            continue

        if not seen_doc_end and '''"""''' in line:
            seen_doc_end = True
            continue

        if not old and 'old_result' in line:
            old = line.strip().replace("old_result = ", "")
            seen_setup_end = True
            continue

        if not new and 'new_result' in line:
            new = line.strip().replace("new_result = ", "")
            seen_setup_end = True
            continue

        if seen_setup_end and not output and "# output" in line:
            output = OUTPUT_RE(line).strip()
            break

        if seen_doc_end and not seen_setup_end:
            setup.append(line)

    return Example(
        function.__code__.co_name,
        inspect.getdoc(function),
        dedent("".join(setup)).strip(),
        old,
        new,
        output
    )


def get_content():
    content_module = importlib.import_module(CONTENT_MODULE)
    for name, function in inspect.getmembers(content_module, inspect.isfunction):
        yield parse_function(function)


@click.group()
def main():
    pass


@main.command()
@click.option('-v', '--verbose', is_flag=True, help="Print function definitions")
def extract(verbose):
    cnt = 0
    for example in get_content():
        cnt += 1
        if verbose:
            print("Function: {}".format(example.name))
            print("    Doc:\n{}".format(indent(example.doc, " " * 8)))
            print("    Example:")
            print("        Setup:\n{}".format(indent(example.setup, " " * 14)))
            print("        Old: {}".format(example.old))
            print("        New: {}".format(example.new))
            print("        Output: {}".format(example.output))
            print()
    print("Extracted {} examples.".format(cnt))


if __name__ == "__main__":
    main()
