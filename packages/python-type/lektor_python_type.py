from pprint import pprint

import pygments
from lektor.pluginsystem import Plugin
from lektor.types import Type
from pygments.formatters.html import HtmlFormatter
from pygments.lexers.python import PythonLexer


class PygmentizedPython:
    def __init__(self, source):
        self.source = source

    def __html__(self):
        return pygments.highlight(self.source, PythonLexer(), HtmlFormatter())


class PythonType(Type):
    widget = 'multiline-text'

    def value_from_raw(self, raw):
        return PygmentizedPython(raw.value or "")


class PythonTypePlugin(Plugin):
    name = "Python"
    description = "Python source code type for Lektor"

    def on_setup_env(self, **extra):
        self.env.add_type(PythonType)
