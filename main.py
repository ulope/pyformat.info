import hashlib
import importlib
import inspect
import logging
import sys
from logging import getLogger
from textwrap import dedent, indent
from collections import namedtuple
from pathlib import Path

import jinja2
import sass
import click
import markdown
import pygments
import pygments.formatters
import pygments.lexers
from rex import rex


log = getLogger(__name__)

CONTENT_MODULE_PATH = "tests.test_content"

OUTPUT_RE = rex(r"""s/^.*?assert .*? == ['"](.*)['"].*?# output$\n/\1/""")

Example = namedtuple("Example", ('name', 'title', 'details', 'setup', 'old', 'new', 'output'))


def compile_sass(source_path, target_path_pattern):
    # First generate the content from which we can generate the hashname
    log.info("Compiling SCSS.")
    output = sass.compile(
        filename=str(source_path),
        output_style='compressed')
    hash = hashlib.sha512(output.encode('utf-8')).hexdigest()[:8]
    target_path = str(target_path_pattern).format(hash)
    source_map_target_path = target_path + '.map'
    output = sass.compile(
        filename=str(source_path),
        output_style='compressed',
        source_map_filename=source_map_target_path)
    with open(target_path, 'w') as fp:
        fp.write(output[0])
    with open(source_map_target_path, 'w') as fp:
        fp.write(output[1])
    return Path(target_path)


def generate_css(base_folder, target_folder):
    log.info("Generating CSS.")
    file_mapping = {}
    target_folder = Path(target_folder)
    try:
        target_folder.mkdir(parents=True)
    except FileExistsError:
        pass

    pygments_css = Path(base_folder) / '_pygments.scss'
    with open(str(pygments_css), 'w') as fp:
        fp.write(pygments.formatters.HtmlFormatter().get_style_defs(
            '.highlight'))

    for file_ in Path(base_folder).glob('*.scss'):
        if not file_.name.startswith('_'):
            target_path = target_folder / (file_.stem + '.{}.css')
            target_path = compile_sass(file_, target_path)
            file_mapping[file_.name] = target_path.name
    return file_mapping


def split_letters(value):
    return ''.join(['<i>{}</i>'.format(letter) for letter in value])


def highlight(value):
    return pygments.highlight(value, pygments.lexers.PythonLexer(),
                              pygments.formatters.HtmlFormatter())


def generate_html(content, output_file):
    log.info("Rendering HTML.")
    env = jinja2.Environment(loader=jinja2.FileSystemLoader('templates'))
    env.filters['markdown'] = markdown.markdown
    env.filters['lettering'] = split_letters
    env.filters['highlight'] = highlight
    tmpl = env.get_template('index.html')
    style_mapping = generate_css('assets/sass', 'assets/css')
    with open(output_file, 'w', encoding='utf-8') as fp:
        fp.write(tmpl.render(examples=list(content), styles=style_mapping))


def parse_docstring(docstring):
    if not docstring:
        return (None, None)
    lines = docstring.rstrip().split('\n')
    if len(lines) < 1:
        return (None, None)
    if lines[0].startswith('# '):
        return (lines[0][2:], '\n'.join(lines[2:]) or None)
    else:
        return (None, '\n'.join(lines) or None)


def parse_function(function):
    seen_doc_start = False
    seen_doc_end = False
    seen_setup_end = False
    setup = []
    old = ""
    new = ""
    output = ""
    lines, _ = inspect.getsourcelines(function)
    for i, line in enumerate(lines):
        if line.startswith(('def', '@', )):
            continue

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
            output = OUTPUT_RE(line)
            break

        if (seen_doc_end or not seen_doc_start) and not seen_setup_end:
            setup.append(line)

    docstr = inspect.getdoc(function)
    title, details = parse_docstring(docstr)

    if not output:
        log.warning("No output defined in example '%s'.", function.__name__)

    return Example(
        function.__name__.replace("test_", ""),
        title,
        details,
        dedent("".join(setup)).strip(),
        old,
        new,
        output
    )


def get_content():
    log.info("Parsing content.")
    content_module = importlib.import_module(CONTENT_MODULE_PATH)
    for name, function in sorted(
        inspect.getmembers(content_module, inspect.isfunction),
        key=lambda m: m[1].__code__.co_firstlineno
    ):
        if not name.startswith('test_'):
            log.warning("Content function without 'test_' prefix found: '%s'. Ignoring.", name)
        yield parse_function(function)


@click.group()
def main():
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG, format="%(levelname)-7s %(name)s: %(message)s")


@main.command()
@click.option('-o', '--output', default='index.html',
              help="Path to the output HTML file")
def generate(output):
    generate_html(get_content(), output)
    log.info("Done.")


@main.command()
@click.option('-v', '--verbose', is_flag=True,
              help="Print function definitions")
def extract(verbose):
    cnt = 0
    for example in get_content():
        cnt += 1
        if verbose:
            print("Function: {}".format(example.name))
            if example.title:
                print("    Title:\n{}".format(indent(example.title, " " * 8)))
            if example.details:
                print("    Details:\n{}".format(indent(example.details, " " * 8)))
            print("    Example:")
            if example.setup:
                print("        Setup:\n{}".format(indent(example.setup, " " * 14)))
            if example.old:
                print("        Old: {}".format(example.old))
            print("        New: {}".format(example.new))
            print("        Output: {}".format(example.output))
            print()
    print("Extracted {} examples.".format(cnt))


if __name__ == "__main__":
    main()
