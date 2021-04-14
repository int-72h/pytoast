from setuptools import setup, find_packages
import pathlib
here = pathlib.Path(__file__).parent.resolve()
long_description = (here / 'README.md').read_text(encoding='utf-8')
setup(
    name='ofatomic',
    version='0.4.0',
    description='A command line launcher for Open Fortress',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/int-72h/ofatomic',
    author='int',
    packages=['ofatomic'],
    python_requires='>=3.4',
    package_data={ 
        'ofatomic': ['ofpublic.pem','gameinfo.txt'],
    },
    entry_points={ 
        'console_scripts': [
            'ofatomic=ofatomic:main',
        ],
    },
)
