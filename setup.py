from setuptools import setup
import pathlib
here = pathlib.Path(__file__).parent.resolve()
long_description = (here / 'README.md').read_text(encoding='utf-8')
setup(
    name='ofatomic',
    version='210506.2',
    description='A command line launcher for Open Fortress',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/int-72h/ofatomic',
    zip_safe=False,
    author='int',
    include_package_data=True,
    packages=['ofatomic'],
    python_requires='>=3.4',
    entry_points={ 
        'console_scripts': [
            'ofatomic=ofatomic:main',
        ],
    },
)
