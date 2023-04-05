from setuptools import setup, find_packages

setup(
    name='signal_plotter',
    version='1.0',
    author='Hacker1337',
    author_email='amirfvb@gmail.com',
    packages=find_packages(),
    long_description="Supplies function that runs loop with taking values from given callable function. Appends new values from function to history and plots" +
    "history of cchanging values.",
    install_requires=[
        'numpy',
        'matplotlib>=3.3',
    ],

)