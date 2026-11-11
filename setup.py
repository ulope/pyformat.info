from setuptools import setup

setup(
    name='pyformat_site',
    py_modules=['main'],
    python_requires='>=3.14',
    install_requires=[
        "click>=8.1",
        "jinja2>=3.1",
        "libsass>=0.23",
        "Markdown>=3.5",
        "MarkupSafe>=2.1",
        "pytest>=8",
        "Pygments>=2.19",
        "wrapt>=1.16",
    ],
    entry_points={
        'console_scripts': [
            'pyformat = main:main',
        ]
    },
)
