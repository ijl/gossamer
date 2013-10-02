"""
setup
"""

from setuptools import setup
import os, re

with open('gossamer/__init__.py') as version:
    VERSION = re.compile(r".*__version__ = '(.*?)'", re.S).match(version.read()).group(1)

# rst, written by `make doc`
README = ''
if os.path.exists('README'):
    with open('README', 'r') as readme:
        README = readme.read()

setup(
    name = 'gossamerui',
    version = VERSION,
    packages=['gossamer', ],
    install_requires = [
        'selenium >= 2.35.0',
        'plac == 0.9.1',
        'pillow >= 2.2.1'
    ],
    classifiers=[
      'Development Status :: 4 - Beta',
      'Environment :: Console',
      'Intended Audience :: Developers',
      'Operating System :: OS Independent',
      'License :: OSI Approved :: Apache Software License',
      'Programming Language :: Python',
      'Programming Language :: Python :: 2',
      'Topic :: Software Development :: Testing',
      'Topic :: Software Development :: Quality Assurance',
      'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    package_data = {
      'gossamer': [
        '*.js',
      ],
    },
    entry_points = {
        'console_scripts': [
            'gossamer = gossamer.cli:main'
        ],
        'setuptools.installation': [
            'eggsecutable = gossamer.cli:main',
        ]
    },
    license = 'Apache 2.0',
    keywords = 'selenium webdriver testing regression ui automated visual diff screenshot huxley',
    description = 'Website user interface regression testing',
    long_description = README,
    url = 'https://github.com/ijl/gossamer',
    download_url = 'https://github.com/ijl/gossamer/archive/%s.tar.gz' % VERSION,
    author = 'Jack Lutz',
    author_email = 'uijllji@gmail.com',
    zip_safe=True
)
