from ipykernel.kernelbase import Kernel
from pexpect import spawn, EOF

import logging as LOGGING

from os.path import realpath
import re

import base64
import urllib

from IPython.display import display, Image

OL_ENCODING = 'utf-8'
OL_ARROW    = u' —▶ ' #.encode(OL_ENCODING)
OL_BYENOW   = u'Bye for now!' #.encode(OL_ENCODING)
OL_CFGFILE  = '/home/jefdaj/ortholang_kernel/test1.cfg'
OL_LOGFILE  = '/tmp/ortholang_kernel.log'

HANDLER = LOGGING.FileHandler(OL_LOGFILE)
HANDLER.setFormatter(LOGGING.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s'))

LOGGER = LOGGING.getLogger('ortholang_kernel')
LOGGER.setLevel(LOGGING.DEBUG)
LOGGER.addHandler(HANDLER)

LOGGER.debug('reading ortholang_kernel.py...')

# def count_statements(txt):
#     # an attempt to guess how many statements are contained in a cell,
#     # so we know how many prompts to expect
#     nassigns  = len(re.findall('(^|\n)[a-zA-Z0-9]{1,}\s*=', txt, flags=re.DOTALL))
#     ncommands = len(re.findall('(^|\n)[a-z]{1,}:'         , txt, flags=re.DOTALL))
#     return max(1, nassigns + ncommands)

# from https://www.tutorialspoint.com/How-can-I-remove-the-ANSI-escape-sequences-from-a-string-in-python
def remove_ansi_escapes(txt):
    ansi_escape =re.compile(r'(\x9B|\x1B\[)[0-?]*[ -\/]*[@-~]')
    return ansi_escape.sub('', txt)

def remove_prompt(txt):
    prompt = re.compile('(\r|\n)*.*?' + OL_ARROW)
    return prompt.sub('', txt)

def collapse_newlines(txt):
    return re.sub('(\r|\n){2,}', '\n', txt)

def clean_lines(txt):
    LOGGER.debug('clean_lines txt: "%s"' % txt)
    txt = remove_ansi_escapes(txt)
    txt = remove_prompt(txt)
    LOGGER.debug('clean_lines result: "%s"' % txt)
    return txt

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
        'pygments_lexer': 'ipython3'
    }
    banner = "OrthoLang 0.9.5"

    def spawn_repl(self):
        LOGGER.debug('OrthoLangKernel.spawn_repl')
        args = ['--config', OL_CFGFILE, '--interactive']
        # args = ["--interactive"]
        # args = []
        LOGGER.info('spawning ortholang %s' % args)
        self.ol_process = spawn('ortholang', args, encoding=OL_ENCODING, echo=False, timeout=10)
        self.ol_process.expect_exact(OL_ARROW)
        LOGGER.debug("before: '%s'" % self.ol_process.before)
        LOGGER.debug("after: '%s'" % self.ol_process.after)
        LOGGER.info('REPL should be ready for input')

    def __init__(self, *args, **kwargs):
        LOGGER.debug('OrthoLangKernel.__init__')
        self.spawn_repl()
        super(OrthoLangKernel, self).__init__(*args, **kwargs)

    def load_plots(self, txt):
        regex = u'\[?plot image "(.*?)"'
        paths = re.findall(regex, txt)
        LOGGER.debug('image paths: %s' % paths)
        plots = []
        for path in paths:
            path = realpath(path)
            LOGGER.debug('loading image from "%s"' % path)
            utf8_b64 = base64.b64encode(open(path, "rb").read()).decode(OL_ENCODING)
            plots.append(utf8_b64)
        return plots

    def do_execute(self, code, silent, store_history=True, user_expressions=None, allow_stdin=False):

        # There's one extra rule for parsing in the
        # notebook interface: when a cell contains multiple statements, they
        # must be separated by blank lines.  For example the blank lines here
        # are important:
        #
        # > test1 = ["one",
        # >          "two"]
        # >
        # > test2 = ["two", "three"]
        # >
        # > :show
        #
        # Otherwise we have no obvious way to know how many prompts to expect
        # without re-implementing the OrthoLang parser in Python!

        LOGGER.debug("OrthoLangKernel.do_execute: '%s'" % code)

        # Break into statements based on blank lines
        # from https://stackoverflow.com/a/27003351/429898
        # TODO possible replacement: expect one prompt per = sign or : in the input
        statements = [[]]
        for line in code.splitlines():
            if len(line) == 0:
                if len(statements[-1]) > 0:
                    statements.append([])
            else:
                statements[-1].append(line)
        LOGGER.debug("statements: '%s'" % statements)

        # Run them individually
        statements = ['\n'.join(s) for s in statements]

        outputs = []
        for s in statements:
            outputs.append(self.do_execute_statement(s))
        output = ''.join(outputs).strip()
        LOGGER.debug("output: '%s'" % output)

        if not silent:
            if contains_plot(output):
                plots = self.load_plots(output)
                for plot in plots:
                    content = {
                        'data': {'image/png': plot},
                        'metadata' : {
                            'image/png' : {'width': 600,'height': 400} # TODO set intelligently?
                        }
                    }
                    LOGGER.debug('content: %s' % content)
                    LOGGER.debug('sending content...')
                    self.send_response(self.iopub_socket, 'display_data', content)
                    LOGGER.debug('ok')
            else:
                # note: 'data' key renamed to 'text' in messaging protocol 5.0
                # TODO which jupyter version is that?
                content = {'name': 'stdout', 'text': output}
                self.send_response(self.iopub_socket, 'stream', content)

        return {'status': 'ok',
                # The base class increments the execution count
                'execution_count': self.execution_count,
                'payload': [],
                'user_expressions': {},
               }

    def do_execute_statement(self, code):
        code = code.strip()
        LOGGER.debug("do_execute_statement '%s'" % code)
        self.ol_process.sendline(code)
        # TODO yeah, make that equivalent to restarting
        options = [OL_ARROW, OL_BYENOW] # TODO what do we do if the user :quits? restart?
        self.ol_process.expect_exact(options)
        output = clean_lines(self.ol_process.before + self.ol_process.after)
        LOGGER.debug("statement output: '%s'" % output)
        return output

    def quit_repl(self):
        try:
            LOGGER.info('quitting repl...')
            self.ol_process.sendline(':quit\n')
            self.ol_process.expect_exact(OL_BYENOW, timeout=5)
            LOGGER.debug('final output: "%s"' % (self.ol_process.before + self.ol_process.after))
            self.ol_process.kill(0)
            self.ol_process.close(force=True)
            LOGGER.debug('quit successfully')
        except:
            LOGGER.error('failed to kill REPL')

    def do_shutdown(self, restart):
        self.quit_repl()
        if restart:
            LOGGER.info('restarting...')
            self.spawn_repl()

if __name__ == '__main__':
    LOGGER.debug('__main__')
    from ipykernel.kernelapp import IPKernelApp
    IPKernelApp.launch_instance(kernel_class=OrthoLangKernel)

LOGGER.debug('finished without syntax errors')
