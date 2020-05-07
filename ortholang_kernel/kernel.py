from ipykernel.kernelbase import Kernel
from pexpect import spawn, EOF

import logging as LOGGING

from os.path import realpath
import re

import base64
import urllib

from IPython.display import display, Image

OL_ARROW  = u'—▶'
OL_BYENOW  = u'Bye for now!'
OL_CFGFILE = '/home/jefdaj/ortholang_kernel/test1.cfg'
OL_LOGFILE = '/tmp/ortholang_kernel.log' # TODO add it to the main syslog
ENCODING = 'utf-8'

HANDLER = LOGGING.FileHandler(OL_LOGFILE)
HANDLER.setFormatter(LOGGING.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s'))

LOGGER = LOGGING.getLogger('ortholang_kernel')
LOGGER.setLevel(LOGGING.DEBUG) # TODO turn down
LOGGER.addHandler(HANDLER)

LOGGER.debug('reading ortholang_kernel.py...')

#def ensure_trailing_newline(txt):
    #return txt.strip()
#     try:
#         if txt[-1] == '\n':
#             return txt
#         else:
#             return txt + '\n'
#     except:
#         return txt + '\n'

# from https://www.tutorialspoint.com/How-can-I-remove-the-ANSI-escape-sequences-from-a-string-in-python
def remove_ansi_escapes(txt):
    ansi_escape =re.compile(r'(\x9B|\x1B\[)[0-?]*[ -\/]*[@-~]')
    return ansi_escape.sub('', txt)

# def remove_regex(regex, txt):
#     return re.sub(regex, '', txt) # TODO flags: DOTALL?

# TODO use custom prompt from the class?
def remove_prompt(txt):
    prompt = re.compile('(\r|\n)*.*?' + OL_ARROW)
    return prompt.sub('', txt)

def collapse_newlines(txt):
    return re.sub('(\r|\n){2,}', '\n', txt)

def clean_lines(txt):
    LOGGER.debug('clean_lines txt: "%s"' % txt)
    # txt = remove_regex('(\r?\n)?\r?\n(ortholang|.*?\.ol)$', txt) # TODO put the ortholang part here instead?
    # txt = remove_regex('ortholang$', txt) # TODO adjust for script?
    # lines = txt.splitlines() # TODO does \ need escaping?
    # lines = [remove_ansi_escapes(l) for l in lines]
    # lines = clean_lines(lines)
    # txt = '\n'.join(lines)
    # lines = [l for l in lines if not is_prompt(l)]
    # txt = '\n'.join(lines)
    # lines = lines[:-1] # TODO does this ever fail?

    txt = remove_ansi_escapes(txt)
    txt = remove_prompt(txt)
    #txt = collapse_newlines(txt) # TODO remove this?
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
    }
    banner = "OrthoLang 0.9.5"

    def spawn_repl(self):
        LOGGER.debug('OrthoLangKernel.spawn_repl')
        args = ["--config", OL_CFGFILE, "--interactive"]
        LOGGER.info('spawning ortholang %s' % str(args))
        self.ol_process = spawn('ortholang', args, encoding=ENCODING, echo=False, timeout=None)
        self.ol_process.expect_exact(self.ol_prompt)
        LOGGER.debug("before: '%s'" % self.ol_process.before)
        LOGGER.debug("after: '%s'" % self.ol_process.after)
        LOGGER.info('REPL should be ready for input')

    def __init__(self, *args, **kwargs):
        LOGGER.debug('OrthoLangKernel.__init__')
        self.ol_prompt = OL_ARROW + ' ' # TODO adjust when loading a script
        self.spawn_repl()
        super(OrthoLangKernel, self).__init__(*args, **kwargs)

#     def remove_prompt(self, txt):
#         return txt.replace(self.ol_prompt, '').strip()

#     def prepare_content(self, txt):
#         lines = txt.split('\n')
#         lines = clean_lines(lines)
#         txt = '\n'.join(lines)
#         return txt

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

        # There's one extra rule (TODO is it really extra?) for parsing in the
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
        LOGGER.debug("statement outputs: '%s'" % outputs)

        # TODO remove? maybe there needs to be one extra one here
        # self.ol_process.expect_exact(options)

        output = ''.join(outputs)#  + '\n'

        # nlines = len(code.splitlines())
        # LOGGER.debug('got %d lines of code, so expect %d prompts' % (nlines, nlines))

        # self.ol_process.sendline(code + '\n')
        # naecrs = len(self.ol_process.before.find('\x1b[0K'))
        # LOGGER.debug('found %d cursor-right escape codes' % naecrs)

        # options = [OL_ARROW, OL_BYENOW] # TODO what do we do if the user :quits? restart?

        # this works around a bug where multiple statements per cell causes multiple prompts to be printed
        # output = ''
#         while True:
#             self.ol_process.expect_exact(options)
#             before = self.remove_prompt(self.ol_process.before)
#             LOGGER.debug("before: '%s'" % before)
#             if len(before) == 0:
#                 break
#             output += before
#             LOGGER.debug("captured output so far: '%s'" % output)
#             # LOGGER.debug("before: '%s'" % self.ol_process.before)
#             LOGGER.debug("after: '%s'" % self.ol_process.after)
#             # TODO rethink this: what would the repl example look like for when you want to return vs not? draw it out
#             #      oh here's an idea: is output only going to be 'ortholang' over and over until the last one?
#             #      another idea: the final line should be one that DOES NOT end in a newline yet
#             # if len(self.ol_process.before.split('\n')) < 2:
#             # if self.ol_process.before.strip() == u'ortholang':
#             #     break

        # this is hacky, but more or less works to process a multi-statement cell
        # we assume that for n lines of input, there will be n prompts
        # TODO warn users that only the last line of a cell should print output
#         lines = []
#         while True:
#             self.ol_process.expect_exact(options)
#             before = clean_lines(self.ol_process.before)
#             LOGGER.debug("before: '%s'" % before)
#             lines += before
#             LOGGER.debug("lines so far: '%s'" % lines)
#             if len(before) < 3:
#                 break

        # self.ol_process.expect_exact(options)
        # output = clean_output(self.ol_process.before)
        # output = '\n'.join(lines)
        # LOGGER.debug("cleaned output: '%s'" % output)

        if not silent:
            # txt = self.prepare_content(output)
            if contains_plot(output):
                plots = self.load_plots(output) # TODO return the others
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
                content = {'name': 'stdout', 'text': output}
                self.send_response(self.iopub_socket, 'stream', content)

        return {'status': 'ok',
                # The base class increments the execution count
                'execution_count': self.execution_count, # TODO is this messed up by the statements thing?
                'payload': [],
                'user_expressions': {},
               }

    def do_execute_statement(self, code):
        #code = ensure_trailing_newline(code)
        code = code.strip()
        LOGGER.debug("do_execute_statement '%s'" % code)
        self.ol_process.sendline(code)
        options = [self.ol_prompt, OL_BYENOW] # TODO what do we do if the user :quits? restart?
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

LOGGER.debug('finished without syntax errors')
