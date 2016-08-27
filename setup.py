from setuptools import setup

setup(
    name='pyformat_site',
    install_requires=[
        "click==6.6",
        "jinja2==2.8",
        "python-rex==0.4",
        "libsass==0.11.1",
        "Markdown==2.6.6",
        "pytest==2.9.2",
        "Pygments==2.1.3",
        "astunparse==1.4.0",
        "pytz==2016.6.1",
    ],
    entry_points={
        'console_scripts': [
            'pyformat = main:main',
        ]
    },
)
