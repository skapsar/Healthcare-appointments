from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in healthcare_appointments/__init__.py
from healthcare_appointments import __version__ as version

setup(
	name="healthcare_appointments",
	version=version,
	description="healthcare_appointments",
	author="shaik Apsar",
	author_email="skaapsar8149@gmail.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
