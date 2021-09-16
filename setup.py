from setuptools import setup, find_packages


setup(
    name="sylva_libc",
    version="0.0.1",
    packages=find_packages(),
    scripts=['scripts/sylva_libc'],
    python_requires='>=3.7.0',

    # metadata to display on PyPI
    author="Charlie Gunyon",
    author_email="charles.gunyon@gmail.com",
    description="Generates libc definitions for Sylva",
    keywords="c",
    url="https://github.com/camgunz/sylva_libc/",
    project_urls={
        "Source Code": "https://gitub.com/camgunz/sylva_libc",
    },
    classifiers=[
        'License :: OSI Approved :: GPLv3'
    ],
)
