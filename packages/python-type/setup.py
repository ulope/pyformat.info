from setuptools import setup

setup(
    name='lektor-python-type',
    version='0.1',
    author='Ulrich Petri',
    author_email='ulo@ulo.pe',
    license='MIT',
    py_modules=['lektor_python_type'],
    entry_points={
        'lektor.plugins': [
            'python-type = lektor_python_type:PythonTypePlugin',
        ]
    }
)
