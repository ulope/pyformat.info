from lektor.pluginsystem import Plugin
from lektor.types.primitives import StringType


class LiteralStringType(StringType):
    widget = 'singleline-text'

    def value_from_raw(self, raw):
        if raw.value is None:
            return raw.missing_value('Missing string')
        try:
            return raw.value.splitlines()[0]
        except IndexError:
            return ""


class LiteralStringTypePlugin(Plugin):
    name = "Literal String"
    description = "Literal String type for Lektor that preserves whitespace"

    def on_setup_env(self, **extra):
        self.env.add_type(LiteralStringType)
