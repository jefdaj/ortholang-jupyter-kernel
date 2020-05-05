from ipykernel.kernelapp import IPKernelApp
from . import OrthoLangKernel

IPKernelApp.launch_instance(kernel_class=OrthoLangKernel)
