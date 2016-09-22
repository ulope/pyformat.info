# -*- coding: utf-8 -*-
from lektor.pluginsystem import Plugin
from pathlib import Path

from pygments.formatters.html import HtmlFormatter


class SassCompilerPlugin(Plugin):
    name = 'Sass Compiler'
    description = u'Add your description here.'

    def on_before_build_all(self, builder, **extra):
        root = Path(self.env.root_path)
        with open(str(root / 'assets' / 'static' / 'pygments.css'), 'w') as fp:
            fp.write(HtmlFormatter().get_style_defs('.highlight'))


def generate_css(base_folder, target_folder):
    file_mapping = {}
    target_folder = target_folder
    try:
        target_folder.mkdir(parents=True)
    except FileExistsError:
        pass

    pygments_css = base_folder / '_pygments.scss'
    with open(str(pygments_css), 'w') as fp:
        fp.write(pygments.formatters.HtmlFormatter().get_style_defs(
            '.highlight'))

    for file_ in base_folder.glob('*.scss'):
        if not file_.name.startswith('_'):
            target_path = target_folder / (file_.stem + '.{}.css')
            target_path = compile_sass(file_, target_path)
            file_mapping[file_.name] = target_path.name
    return file_mapping
