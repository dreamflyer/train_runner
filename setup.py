from setuptools import setup
import setuptools
setup(name='train_runner',
      version='0.1',
      description='train runner',
      url='https://github.com/dreamflyer/train_runner',
      author='Dreamflyer',
      author_email='formyfiles3@gmail.com',
      license='MIT',
      packages=setuptools.find_packages(),
      include_package_data=True,
      install_requires=["kaggle"],
      zip_safe=False)