from setuptools import setup, find_packages

setup(name='sh-rpi-daemon',
      version='0.3.0',
      description='Sailor Hat for Raspberry Pi Daemon',
      author='Matti Airas',
      author_email='matti.airas@hatlabs.fi',
      url='https://github.com/hatlabs/SH-RPi-daemon',
      packages=find_packages(),
      py_modules=['shrpi.shrpi_device'],
      install_requires=[
        'smbus2',
      ],
      entry_points = {
        'console_scripts': [
          'sh-rpi-daemon=shrpi.shrpi:main',
          'sh-rpi-i2c-report=shrpi.shrpi_i2c_report:main'],
      }
)
