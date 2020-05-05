#!/usr/bin/env python

# TODO remove this and make a proper python package

import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

def main():
    from ortholang_kernel import OrthoLangKernel
    OrthoLangKernel.run_as_main()
    # from sys import argv
    # print('running main.py with args: %s' % argv)
    # with open('/mnt/data/jupyter-lab/log.txt', a) as f:
    #     f.write('running main\n')

if __name__ == '__main__':
    main()
