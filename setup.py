# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

# All dependences
deps = {
    'photogrammetry-service': [
        'imageio',
        'rawpy',
        'opencv-python',
        'colour-checker-detection',
        'pillow',
        'requests',
        'opencv-contrib-python',
        'dramatiq[redis, watch]',
        'piexif',
    ],
    'test': [],
    'dev': ['pylint', 'autopep8', 'rope', 'black'],
}
deps['dev'] = deps['photogrammetry-service'] + deps['dev']
deps['dev'] = deps['dev'] + deps['dev']
deps['test'] = deps['photogrammetry-service'] + deps['test']

install_requires = deps['photogrammetry-service']
extra_requires = deps
test_requires = deps['test']

with open('README.adoc') as readme_file:
    long_description = readme_file.read()

setup(
    name='photogrammetry-service',
    version='0.0.1',
    description='Photogrammetry Service',
    long_description=long_description,
    long_description_content_type='text/asciidoc',
    include_package_data=True,
    tests_require=test_requires,
    install_requires=install_requires,
    extras_require=extra_requires,
    license='MIT',
    zip_safe=False,
    keywords='Photogrammetry Service',
    packages=find_packages(where='src', exclude=['tests', 'tests.*', '__pycache__', '*.pyc']),
    package_dir={
        '': 'src',
    },
    package_data={'': ['**/*.yml']},
    classifiers=[
        'Development Status :: 1 - Planning',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.8',
        'Operating System :: Microsoft :: Windows',
    ],
)
