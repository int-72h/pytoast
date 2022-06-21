from setuptools import setup
import pathlib

here = pathlib.Path(__file__).parent.resolve()
long_description = (here / 'README.md').read_text(encoding='utf-8')
setup(
    name='tvn',
    version='0.1.0',
    description='Python library for the Toast, implementing TVN',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/int-72h/toast',
    zip_safe=False,
    author='int et al.',
    include_package_data=True,
    packages=['pytoast'],
    python_requires='>=3.4',
    install_requires=["httpx"],
    entry_points={
        'console_scripts': [
            'toaster=pytoast.toaster:main',
        ],
    },
)
