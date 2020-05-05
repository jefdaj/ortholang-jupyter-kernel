from ipykernel.kernelapp import IPKernelApp
from . import OrthoLangKernel

with open('/tmp/ortholang_kernel.log', 'a') as f:
    f.write('running __main__\n')

IPKernelApp.launch_instance(kernel_class=OrthoLangKernel)

with open('/tmp/ortholang_kernel.log', 'a') as f:
    f.write('__main__ finished\n')
