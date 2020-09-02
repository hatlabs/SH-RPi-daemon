from setuptools import setup, find_packages

setup(name='sailor_hat',
      version='0.2.0',
      description='Sailor Hat for Raspberry Pi Daemon',
      author='Matti Airas',
      author_email='mairas@iki.fi',
      url='https://github.com/mairas/sailor-hat-daemon',
      packages=find_packages(),
      py_modules=['sailor_hat.sailor_hat_device'],
      install_requires=[
        'smbus2',
      ],
      entry_points = {
        'console_scripts': [
          'sailor-hat-daemon=sailor_hat.sailor_hat:main',
          'sailor-hat-i2c-report=sailor_hat.hat_i2c_report:main'],
      }
)
