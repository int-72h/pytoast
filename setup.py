from setuptools import setup
import pathlib

here = pathlib.Path(__file__).parent.resolve()
long_description = (here / 'README.md').read_text(encoding='utf-8')
setup(
    name='oftoast',
    version='0.0.1',
    description='A delicious installer for Open Fortress',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/int-72h/OFtoast',
    zip_safe=False,
    author='int',
    include_package_data=True,
    packages=['OFtoast'],
    python_requires='>=3.4',
    entry_points={
        'console_scripts': [
            'oftoast=oftoast:main',
        ],
    },
)
