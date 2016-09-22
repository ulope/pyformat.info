from setuptools import setup

setup(
    name='lektor-literal-string-type',
    version='0.1',
    author='Ulrich Petri',
    author_email='ulo@ulo.pe',
    license='MIT',
    py_modules=['lektor_literal_string_type'],
    entry_points={
        'lektor.plugins': [
            'literal-string-type = lektor_literal_string_type:LiteralStringTypePlugin',
        ]
    }
)
