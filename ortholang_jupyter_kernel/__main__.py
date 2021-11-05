from ipykernel.kernelapp import IPKernelApp
from . import OrthoLangKernel

def main():
    IPKernelApp.launch_instance(kernel_class=OrthoLangKernel)

# main()
