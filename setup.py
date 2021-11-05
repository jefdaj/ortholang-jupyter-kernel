from distutils.core import setup

# with open('README.rst') as f:
    # readme = f.read()
readme = "README HERE"

setup(
    name='ortholang_jupyter_kernel',
    version='0.1',
    packages=['ortholang_jupyter_kernel'],
    description='OrthoLang kernel for Jupyter',
    long_description=readme,
    author='Jeffrey David Johnson',
    author_email='jefdaj@berkeley.edu',
    url='https://github.com/jefdaj/ortholang-jupyter-kernel',
    install_requires=[
        'jupyter_client', 'ipython', 'ipykernel'
    ],
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3',
    ],
    entry_points = {
        'console_scripts': ['ortholang_jupyter_kernel = ortholang_jupyter_kernel.__main__:main']
    }
)
