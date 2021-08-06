from setuptools import setup, find_packages

FULL_VERSION = '0.0.0'

with open('README.md') as f:
    readme = f.read()

setup(
    name='firstcut',
    version=FULL_VERSION,
    description='FirstCut: automatic audio/movie editor',
    url='https://github.com/asahi417/firstcut',
    long_description=readme,
    author='Asahi Ushio',
    author_email='asahi1992ushio@gmail.com',
    packages=find_packages(exclude=('random', 'Voice')),
    include_package_data=True,
    test_suite='test',
    install_requires=[
        'httplib2==0.19.0',
        'scipy>=1.2.0,<2.0.0',
        'toml>=0.10.0',
        'numpy',
        'cython',
        'matplotlib',
        'soundfile',
        'pandas',
        'fastapi',  # app
        'uvicorn',
        'pydantic',
        'urllib3',
        'moviepy',
        'pydub',
        'seaborn'
    ]
)

