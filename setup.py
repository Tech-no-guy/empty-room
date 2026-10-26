from setuptools import setup, find_packages

setup(
    name="empty-room",
    version="1.0.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "opencv-contrib-python>=4.8.0",
        "numpy>=1.24.0",
        "Flask>=3.0.0",
        "Werkzeug>=3.0.0",
    ],
    entry_points={
        "console_scripts": [
            "empty-room=core.cli:main",
        ],
    },
)
