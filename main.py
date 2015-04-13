import click
import hashlib
import importlib
import inspect
import jinja2
import markdown
import sass

from collections import namedtuple
from pathlib import Path
from rex import rex
from textwrap import dedent, indent


CONTENT_MODULE = "tests.test_content"

OUTPUT_RE = rex("""s/^.*?assert .*? == ['"](.*)['"].*?# output$/\\1/""")

Example = namedtuple("Example", ('name', 'title', 'details', 'setup', 'old', 'new', 'output'))


def compile_sass(source_path, target_path_pattern):
    output = sass.compile(filename=str(source_path))
    hash = hashlib.sha512(output.encode('utf-8')).hexdigest()[:8]
    target_path = str(target_path_pattern).format(hash)
    with open(target_path, 'w') as fp:
        fp.write(output)
    return Path(target_path)


def generate_css(base_folder, target_folder):
    file_mapping = {}
    for file_ in Path(base_folder).glob('*.scss'):
        if not file_.name.startswith('_'):
            target_path = Path(target_folder) / (file_.stem + '.{}.css')
            target_path = compile_sass(file_, target_path)
            file_mapping[file_.name] = target_path.name
    return file_mapping


def generate_html(content, output_file):
    env = jinja2.Environment(loader=jinja2.FileSystemLoader('templates'))
    env.filters['markdown'] = markdown.markdown
    tmpl = env.get_template('index.html')
    style_mapping = generate_css('assets/sass', 'assets/css')
    with open(output_file, 'w', encoding='utf-8') as fp:
        fp.write(tmpl.render(examples=list(content), styles=style_mapping))


def parse_docstring(docstring):
    lines = docstring.split('\n')
    if len(lines) < 1:
        return (None, None)
    if len(lines) < 3:
        return (lines[0], None)
    return (lines[0], '\n'.join(lines[2:]))


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

    docstr = inspect.getdoc(function)
    title, details = parse_docstring(docstr)

    return Example(
        function.__code__.co_name,
        title,
        details,
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
@click.option('-o', '--output', default='index.html', help="Path to the output HTML file")
def generate(output):
    generate_html(get_content(), output)


@main.command()
@click.option('-v', '--verbose', is_flag=True, help="Print function definitions")
def extract(verbose):
    cnt = 0
    for example in get_content():
        cnt += 1
        if verbose:
            print("Function: {}".format(example.name))
            print("    Title:\n{}".format(indent(example.title, " " * 8)))
            print("    Details:\n{}".format(indent(example.details, " " * 8)))
            print("    Example:")
            print("        Setup:\n{}".format(indent(example.setup, " " * 14)))
            print("        Old: {}".format(example.old))
            print("        New: {}".format(example.new))
            print("        Output: {}".format(example.output))
            print()
    print("Extracted {} examples.".format(cnt))


if __name__ == "__main__":
    main()
