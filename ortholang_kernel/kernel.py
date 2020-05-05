from ipykernel.kernelbase import Kernel
from pexpect.replwrap import REPLWrapper # TODO try this
from pexpect import spawn, EOF

import logging as LOGGING

OL_WELCOME = u'' # TODO is this needed?
OL_PROMPT  = u' —▶ '
OL_BYENOW  = u'Bye for now!'
OL_PACKAGE = '/nix/store/rmjnx4cy9zr3i3jvphmcg90k53k28g1l-OrthoLang-0.9.4' # TODO package properly
OL_CFGFILE = '/home/jefdaj/ortholang_kernel/test1.cfg'
OL_LOGFILE = '/tmp/ortholang_kernel.log' # TODO where should it go?

HANDLER = LOGGING.FileHandler(OL_LOGFILE)
HANDLER.setFormatter(LOGGING.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s'))

LOGGER = LOGGING.getLogger('ortholang_kernel')
LOGGER.setLevel(LOGGING.DEBUG)
LOGGER.addHandler(HANDLER)

LOGGER.debug('reading ortholang_kernel script')

class OrthoLangKernel(Kernel):
    implementation = 'OrthoLang'
    implementation_version = '0.1'
    language = 'ortholang'
    language_version = '0.9.5'
    language_info = {
        'name': 'OrthoLang',
        'mimetype': 'text/x-script.ortholang',
        'file_extension': '.ol',
    }
    banner = "OrthoLang"

    # TODO should the class support restarts, or is that handled by making a new object?
    def spawn_repl(self):
        LOGGER.debug('OrthoLangKernel.spawn_repl')
        # TODO if supporting restart, this is where self.kill_repl would be called
        olbin = OL_PACKAGE + '/bin/ortholang'
        args = ["--config", OL_CFGFILE, "--interactive"]
        LOGGER.info('spawning %s %s' % (olbin, str(args)))
        self.ol_process = spawn(olbin, args, encoding='utf-8', echo=False, timeout=None)
        # TODO are we supposed to wait for/expect the welcome prompt here?

    def __init__(self, *args, **kwargs):
        LOGGER.debug('OrthoLangKernel.__init__')
        self.spawn_repl()
        super(OrthoLangKernel, self).__init__(*args, **kwargs)

    # TODO write this
    def do_execute(self, code, silent, store_history=True, user_expressions=None, allow_stdin=False):
        LOGGER.debug('OrthoLangKernel.do_execute')

        self.ol_process.sendline(code + '\n')

        options = [OL_PROMPT, OL_BYENOW]
        self.ol_process.expect(options)
        index = self.ol_process.expect(options)
        out = self.ol_process.before + self.ol_process.after # TODO wait, don't include prompt now right?

        if not silent:
            stream_content = {'name': 'stdout', 'text': out}
            self.send_response(self.iopub_socket, 'stream', stream_content)

        return {'status': 'ok',
                # The base class increments the execution count
                'execution_count': self.execution_count,
                'payload': [],
                'user_expressions': {},
               }

    # TODO def do_is_complete
    # TODO def do_shutdown



if __name__ == '__main__':
    LOGGER.debug('__main__')
    from ipykernel.kernelapp import IPKernelApp
    IPKernelApp.launch_instance(kernel_class=OrthoLangKernel)

LOGGER.debug('finished without syntax errors?')
