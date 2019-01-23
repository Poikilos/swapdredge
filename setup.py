#!/usr/bin/env python
from setuptools import setup

def readme():
    with open('README.md') as f:
        return f.read()

setup(name='swapdredge',
      version='0.1',
      description='Minimal Game Engine for Pygame',
      long_description=readme(),
      classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6',
        'Topic :: System :: Recovery Tools',
      ],
      keywords='python file recovery swap swapfile linux swapdredge',
      url='http://github.com/poikilos/swapdredge',
      author='Jacob Gustafson',
      author_email='7557867+poikilos@users.noreply.github.com',
      license='GPLv3+',
      packages=['swapdredge'],
      install_requires=[
      ],
      test_suite='nose.collector',
      tests_require=['nose', 'nose-cover3'],
      entry_points={
          'console_scripts': ['swapdredge=swapdredge.command_line:main'],
      },
      include_package_data=True,
      zip_safe=False) 
