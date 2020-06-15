from setuptools import setup

with open("README.md", "r") as readme_file:
    readme = readme_file.read()

setup(
    name="Office365",
    version="0.0.1",
    author="Patrick Gagnon",
    author_email="plgagnon00@gmail.com",
    description="A package to wrap Office365 Graph API functions",
    long_description=readme,
    url="https://github.com/patrickgagnon/Office365",
    packages=['office365'],
)