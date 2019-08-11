from setuptools import setup, find_packages

FULL_VERSION = '0.0.0'

with open('README.md') as f:
    readme = f.read()

setup(
    name='nitro_editor',
    version=FULL_VERSION,
    description='Library to edit audio file.',
    url='https://github.com/asahi417',
    long_description=readme,
    author='Asahi Ushio',
    author_email='asahi1992ushio@gmail.com',
    packages=find_packages(exclude=('random', 'Voice')),
    include_package_data=True,
    test_suite='test',
    install_requires=[
        'scipy>=1.2.0',
        'toml>=0.10.0',
        'numpy',
        'cython',
        'matplotlib',
        'pandas',
        'flask',
        'werkzeug',
        'soundfile',
        'urllib3',
        'moviepy',
        'pyrebase',
        'flask_cors'
    ]
)

