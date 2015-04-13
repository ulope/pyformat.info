from setuptools import setup

setup(
    name='pyformat_site',
    entry_points={
        'console_scripts': [
            'pyformat = main:main',
        ]
    },
)
