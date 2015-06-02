from setuptools import setup

setup(
    name='pyformat_site',
    install_requires=[
        "click==4.0",
        "jinja2==2.7.3",
        "python-rex==0.4",
        "libsass==0.8.2",
        "Markdown==2.6.2",
        "pytest==2.7.1",
        "Pygments==2.0.2",
        "astunparse==1.2.2",
        "pytz==2015.4",
    ],
    entry_points={
        'console_scripts': [
            'pyformat = main:main',
        ]
    },
)
