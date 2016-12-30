import hashlib
from logging import getLogger
from pathlib import Path

import pygments
import sass
from lektor.pluginsystem import Plugin
from pygments.formatters.html import HtmlFormatter

log = getLogger(__name__)


class SassCompilerPlugin(Plugin):
    name = 'Sass Compiler'
    description = u'Add your description here.'

    def on_before_build_all(self, builder, **extra):
        print("on before build")
        root = Path(self.env.root_path)
        css_map = generate_css(root.joinpath('assets_src', 'sass'), root.joinpath('assets', 'static', 'css'))

        self.env.jinja_env.globals.update(
            css_files=list(css_map.values())
        )


def generate_css(base_folder, target_folder):
    file_mapping = {}
    target_folder = target_folder
    try:
        target_folder.mkdir(parents=True)
    except FileExistsError:
        pass

    pygments_css = base_folder.joinpath('_pygments.scss')
    pygments_css.write_text(
        pygments.formatters.HtmlFormatter().get_style_defs(
            '.highlight'
        )
    )

    for file_ in base_folder.glob('*.scss'):
        if not file_.name.startswith('_'):
            target_path = target_folder / (file_.stem + '.{}.css')
            target_path = compile_sass(file_, target_path)
            file_mapping[file_.name] = target_path.name
    return file_mapping


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