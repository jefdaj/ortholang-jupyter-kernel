from ipykernel.kernelbase import Kernel
from pexpect import spawn, EOF

import logging as LOGGING

from os.path import realpath
import re

import base64
import urllib

from IPython.display import display, Image

OL_WELCOME = u'Welcome to the OrthoLang interpreter!'
OL_PROMPT  = u' —▶ '
OL_BYENOW  = u'Bye for now!'
OL_CFGFILE = '/home/jefdaj/ortholang_kernel/test1.cfg'
OL_LOGFILE = '/tmp/ortholang_kernel.log' # TODO add it to the main syslog
ENCODING = 'utf-8'

HANDLER = LOGGING.FileHandler(OL_LOGFILE)
HANDLER.setFormatter(LOGGING.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s'))

LOGGER = LOGGING.getLogger('ortholang_kernel')
LOGGER.setLevel(LOGGING.DEBUG)
LOGGER.addHandler(HANDLER)

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
    banner = "OrthoLang 0.9.5"

    def spawn_repl(self):
        LOGGER.debug('OrthoLangKernel.spawn_repl')
        args = ["--config", OL_CFGFILE, "--interactive"]
        LOGGER.info('spawning ortholang %s' % str(args))
        self.ol_process = spawn('ortholang', args, encoding=ENCODING, echo=False, timeout=None)
        self.ol_process.expect(OL_WELCOME)
        LOGGER.debug("before: '%s'" % self.ol_process.before)
        LOGGER.debug("after: '%s'" % self.ol_process.after)
        LOGGER.info('REPL should be ready for input')

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
        return txt

    def load_plots(self, txt):
        regex = u'\[?plot image "(.*?)"'
        paths = re.findall(regex, txt)
        LOGGER.debug('image paths: %s' % str(paths))
        plots = []
        for path in paths:
            path = realpath(path)
            LOGGER.debug('loading image from "%s"' % path)
            utf8_b64 = base64.b64encode(open(path, "rb").read()).decode(ENCODING)
            plots.append(utf8_b64)
        return plots

    def do_execute(self, code, silent, store_history=True, user_expressions=None, allow_stdin=False):
        LOGGER.debug("OrthoLangKernel.do_execute: '%s'" % code)

        self.ol_process.sendline(code + '\n')

        options = [OL_PROMPT, OL_BYENOW]
        self.ol_process.expect(options)
        index = self.ol_process.expect(options)

        if not silent:
            txt = self.prepare_content(self.ol_process.before)
            if contains_plot(txt):
                plots = self.load_plots(txt) # TODO return the others
                for plot in plots:
                    content = {
                        # note: 'data' key renamed to 'text' in messaging protocol 5.0
                        # TODO which jupyter version is that?
                        'data': {'image/png': plot},
                        'metadata' : {
                            'image/png' : {'width': 600,'height': 400} # TODO set intelligently?
                        }
                    }
                    LOGGER.debug('content: %s' % str(content))
                    LOGGER.debug('sending content...')
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

    def quit_repl(self):
        try:
            LOGGER.info('quitting repl...')
            self.ol_process.sendline(':quit\n')
            self.ol_process.expect(OL_BYENOW, timeout=5)
            LOGGER.debug('final output: "%s"' % (self.ol_process.before + self.ol_process.after))
            self.ol_process.kill(0)
            self.ol_process.close(force=True)
            LOGGER.debug('quit successfully')
        except:
            LOGGER.error('failed to kill REPL')

    # TODO def do_is_complete? maybe always true

    def do_shutdown(self, restart):
        self.quit_repl()
        if restart:
            LOGGER.info('restarting...')
            self.spawn_repl()

if __name__ == '__main__':
    LOGGER.debug('__main__')
    from ipykernel.kernelapp import IPKernelApp
    IPKernelApp.launch_instance(kernel_class=OrthoLangKernel)

# LOGGER.debug('finished without syntax errors?')
