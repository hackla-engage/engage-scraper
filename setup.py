import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="engage_scraper",
    version="0.0.47",
    author="Engage",
    author_email="eli.j.selkin@gmail.com",
    description="An agenda scraper framework for municipalities",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/hackla-engage/engage-scraper",
    packages=setuptools.find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        'soupsieve',
        'beautifulsoup4',
        'psycopg2-binary',
        'pytz',
        'requests',
        'SQLAlchemy',
        'urllib3', 
        'python-twitter']
)
