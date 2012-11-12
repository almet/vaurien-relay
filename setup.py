from setuptools import setup, find_packages


install_requires = ['zerorpc', 'vaurien']

with open('README.rst') as f:
    README = f.read()


classifiers = ["Programming Language :: Python",
               "License :: OSI Approved :: Apache Software License",
               "Development Status :: 1 - Planning"]


setup(name='vaurien-relay',
      version="0.1",
      packages=find_packages(),
      description=("ZeroRPC relay for vaurien clients"),
      long_description=README,
      author="Mozilla Foundation & contributors",
      author_email="services-dev@lists.mozila.org",
      include_package_data=True,
      zip_safe=False,
      classifiers=classifiers,
      install_requires=install_requires)
