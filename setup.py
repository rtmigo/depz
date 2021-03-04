from pathlib import Path

from setuptools import setup, find_packages

setup(
  name="depz",
  version="0.0.1.1",

  author="Art Galkin",
  author_email="ortemeo@gmail.com",
  url='https://github.com/rtmigo/depz',

  packages=find_packages(),
  install_requires=[],

  description="Command line tool for symlinking directories with reusable code into the working project",

  long_description=(Path(__file__).parent / 'README.md').read_text(),
  long_description_content_type='text/markdown',

  license='BSD-3-Clause',

  entry_points={
       'console_scripts': [
            'depz = depz:runmain',
        ]},

  keywords="""
  	source-code dependencies filesystem programming
  	""".split(),

  # https://pypi.org/classifiers/
  classifiers=[
    # "Development Status :: 4 - Beta",
    "Development Status :: 2 - Pre-Alpha",
    # "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    'License :: OSI Approved :: BSD License',
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Typing :: Typed",
    "Operating System :: OS Independent",
    "Topic :: Software Development :: Build Tools",
  ],

  # test_suite='nose.collector',
  # tests_require=['nose'],
  #zip_safe=False
)