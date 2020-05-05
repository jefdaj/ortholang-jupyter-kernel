from ipykernel.kernelbase import Kernel
from pexpect.replwrap import REPLWrapper # TODO try this
from pexpect import spawn, EOF

import logging as LOGGING

import re
import base64
from IPython.display import display, Image
from os.path import realpath
#from base64 import b64decode

OL_WELCOME = u'' # TODO is this needed?
OL_PROMPT  = u' —▶ '
OL_BYENOW  = u'Bye for now!'
OL_CFGFILE = '/home/jefdaj/ortholang_kernel/test1.cfg'
OL_LOGFILE = '/tmp/ortholang_kernel.log' # TODO where should it go?

HANDLER = LOGGING.FileHandler(OL_LOGFILE)
HANDLER.setFormatter(LOGGING.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s'))

LOGGER = LOGGING.getLogger('ortholang_kernel')
LOGGER.setLevel(LOGGING.DEBUG)
LOGGER.addHandler(HANDLER)

# LOGGER.debug('reading ortholang_kernel script')

def contains_plot(txt):
    return 'plot image "' in txt

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
        args = ["--config", OL_CFGFILE, "--interactive"]
        LOGGER.info('spawning ortholang %s' % str(args))
        self.ol_process = spawn('ortholang', args, encoding='utf-8', echo=False, timeout=None)
        # TODO are we supposed to wait for/expect the welcome prompt here?

    def __init__(self, *args, **kwargs):
        LOGGER.debug('OrthoLangKernel.__init__')
        self.spawn_repl()
        super(OrthoLangKernel, self).__init__(*args, **kwargs)

    def cleanup_lines(self, lines):
        # remove the prompt
        lines = lines[:-1]
        # remove any blank lines
        while True:
            if not len(lines[-1].strip()) == 0:
                break
            lines = lines[:-1]
        return lines

    def prepare_content(self, txt):
        lines = txt.split('\n')
        lines = self.cleanup_lines(lines)
        txt = '\n'.join(lines)
        # if "plot image '" in txt:
            # stream_content = {'name': }
        # else:
        # stream_content = {'name': 'stdout', 'text': txt}
        return txt

    def load_plots(self, txt):
        # TODO return a list of plots when needed (just trying one first)
        # lines = [l.strip() for l in txt.split('\n')]
        regex = u'\[?plot image "(.*?)"'
        paths = re.findall(regex, txt)
        LOGGER.debug('image paths: %s' % str(paths))
        plots = []
        for path in paths:
            # TODO make sure path is inside WORKDIR or TMPDIR for security!
            # with open(path, 'rb') as f:
            # plot = base64.b64encode(f.read())
            # plot = display.Image(f.read())
            # TODO include paths on binary files so ipython can guess based on them (and probably other programs, and humans)
            path = realpath(path)
            LOGGER.debug("loading '%s'..." % path)
            plot = display(Image(filename=path, format='png')) # TODO svg would be nicer right?
            plots.append(plot)
            LOGGER.debug('ok')
        return plots

    def do_execute(self, code, silent, store_history=True, user_expressions=None, allow_stdin=False):
        LOGGER.debug("OrthoLangKernel.do_execute: '%s'" % code)

        self.ol_process.sendline(code + '\n')

        options = [OL_PROMPT, OL_BYENOW]
        self.ol_process.expect(options)
        index = self.ol_process.expect(options)

        # TODO strip last newline thru prompt arrow
        LOGGER.debug("before: '%s'" % self.ol_process.before)
        LOGGER.debug("after: '%s'" % self.ol_process.after)
        # out = self.ol_process.before + self.ol_process.after # TODO wait, don't include prompt now right?
        # out = self.cleanup_output(self.ol_process.before)
        # LOGGER.debug('out: "%s"' % out)

        if not silent:
            # stream_content = {'name': 'stdout', 'text': out}
            txt = self.prepare_content(self.ol_process.before)
            if contains_plot(txt):
                plots = self.load_plots(txt) # TODO return the others
                for plot in plots:
                    content = {
                        # 'source': 'kernel',
                        'data': {'image/png': plot},
                        'metadata' : {
                            'image/png' : {'width': 2100,'height': 2100} # TODO set intelligently?
                        }
                    }
                    LOGGER.debug('sending plot...')
                    self.send_response(self.iopub_socket, 'display_data', content)
                    LOGGER.debug('ok')
            else:
                content = {'name': 'stdout', 'text': txt}
                self.send_response(self.iopub_socket, 'stream', content)

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

# LOGGER.debug('finished without syntax errors?')
