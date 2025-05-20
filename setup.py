from setuptools import setup, find_packages

setup(
    name="airflow_plugins",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'apache-airflow>=2.0.0',
    ],
)
