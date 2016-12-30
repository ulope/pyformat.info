from setuptools import setup

setup(
    name='lektor-sass-compiler',
    version='0.1',
    author='Ulrich Petri',
    author_email='ulo@ulo.pe',
    license='MIT',
    py_modules=['lektor_sass_compiler'],
    install_requires=[
        'libsass==0.12.1',
        'pygments==2.1.3',
    ],
    entry_points={
        'lektor.plugins': [
            'sass-compiler = lektor_sass_compiler:SassCompilerPlugin',
        ]
    }
)
