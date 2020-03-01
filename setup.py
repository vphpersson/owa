from setuptools import setup, find_packages

setup(
    name='owa',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'aiohttp',
        'esprima',
        'pyquery',
        'beautifulsoup4'
    ]
)
