"""
setup
"""

from setuptools import setup
import os, re

DIRNAME = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(DIRNAME, 'gossamer', '__init__.py')) as version:
    VERSION = re.compile(r".*__version__ = '(.*?)'", re.S).match(version.read()).group(1)

# rst, written by `make doc`
README = ''
if os.path.exists('README'):
    with open('README', 'r') as readme:
        README = readme.read()

setup(
    name = 'gossamerui',
    version = VERSION,
    classifiers=[
      'Development Status :: 4 - Beta',
      'Environment :: Console',
      'Intended Audience :: Developers',
      'Programming Language :: Python',
      'Operating System :: OS Independent',
      'License :: OSI Approved :: Apache Software License',
      'Topic :: Software Development :: Testing',
      'Topic :: Software Development :: Quality Assurance',
    ],
    packages = ['gossamer', ],
    install_requires = [
        'selenium>=2.35.0',
        'plac==0.9.1',
        'pillow>=2.1.0'
    ],
    test_suite = "nose.collector",
    package_data = {
      '': [
        '*.js',
      ],
    },
    exclude_package_data = {
      '': [
        '.gitignore',
        '.coverage',
        '.pylintrc',
        'README.md',
        'test',
        'Makefile',
      ],
    },
    entry_points = {
        'console_scripts': [
            'gossamer=gossamer.cmdline:main'
        ]
    },
    license = 'Apache 2.0',
    keywords = [
      'selenium', 'webdriver', 'testing', 'regression', 'ui',
      'automated', 'visual', 'diff', 'screenshot', 'huxley',
    ],
    description = 'Web user interface regression testing via automated screenshot comparison',
    long_description = README,
    url = 'https://github.com/ijl/gossamer',
    download_url = 'https://github.com/ijl/gossamer/archive/%s.tar.gz' % VERSION,
    author = 'Jack Lutz',
    author_email = 'uijllji@gmail.com',
    zip_safe=True
)
