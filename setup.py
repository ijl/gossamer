"""
setup
"""

from setuptools import setup# , find_packages
import os, re

DIRNAME = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(os.path.dirname(__file__), 'gossamer', '__init__.py')) as v:
    VERSION = re.compile(r".*__version__ = '(.*?)'", re.S).match(v.read()).group(1)

setup(
    name = 'Gossamer',
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
    package_data={'': ['requirements.txt']},
    entry_points = {
        'console_scripts': [
            'gossamer=gossamer.cmdline:main'
        ]
    },
    license = 'Apache 2.0',
    keywords = [
      'selenium', 'webdriver', 'testing', 'regression',
      'automated', 'visual', 'diff', 'screenshot', 'huxley'
    ],
    description = 'Watches you browse, takes screenshots, tells you when they change.',
    url = 'https://github.com/ijl/gossamer',
    download_url = 'https://github.com/ijl/gossamer/tarball/%s' % VERSION,
    author = 'Jack Lutz',
    author_email = '',
)
