import logging
import pexpect
import re
import struct
import imghdr

from IPython              import kernel
from IPython.display      import display, Image
from base64               import b64encode
from ipykernel.kernelbase import Kernel
from os                   import getcwd, makedirs
from os.path              import join, realpath, basename

OL_ENCODING = 'utf-8'
OL_ARROW    = u' —▶ '
OL_BYENOW   = u'Bye for now!'

def get_kernel_id():
    # This must be run from inside a kernel.
    # Based on: https://stackoverflow.com/a/13055551/429898
    # TODO is the id persistent across sessions with the same notebook?
    connection_file_path = kernel.get_connection_file()
    connection_file = basename(connection_file_path)
    kernel_id = connection_file.split('-', 1)[1].split('.')[0]
    return kernel_id

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
    txt = remove_ansi_escapes(txt)
    txt = remove_prompt(txt)
    return txt

def contains_plot(txt):
    return 'plot image "' in txt

def get_image_size(fname):
    # from https://stackoverflow.com/a/20380514/429898
    with open(fname, 'rb') as fhandle:
        head = fhandle.read(24)
        if len(head) != 24:
            return
        if imghdr.what(fname) == 'png':
            check = struct.unpack('>i', head[4:8])[0]
            if check != 0x0d0a1a0a:
                return
            width, height = struct.unpack('>ii', head[16:24])
        elif imghdr.what(fname) == 'gif':
            width, height = struct.unpack('<HH', head[6:10])
        elif imghdr.what(fname) == 'jpeg':
            try:
               fhandle.seek(0) # Read 0xff next
               size = 2
               ftype = 0
               while not 0xc0 <= ftype <= 0xcf:
                   fhandle.seek(size, 1)
                   byte = fhandle.read(1)
                   while ord(byte) == 0xff:
                       byte = fhandle.read(1)
                   ftype = ord(byte)
                   size = struct.unpack('>H', fhandle.read(2))[0] - 2
               # We are at a SOFn block
               fhandle.seek(1, 1)  # Skip `precision' byte.
               height, width = struct.unpack('>HH', fhandle.read(4))
            except Exception: #IGNORE:W0703
                return
        else:
            return
        return width, height

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

    def write_config(self):
        cfgtext = '''workdir = "{workdir}"
tmpdir  = "{tmpdir}"
report  = "$(tmpdir)/report.html"
logfile = "$(tmpdir)/log.txt"
history = "$(tmpdir)/history.txt"
shellaccess = false
progressbar = false
showtypes   = false
autosave    = false
showhidden  = false
'''.format(**self.__dict__)
        with open(self.cfgfile, 'w') as f:
            f.write(cfgtext)

    # TODO add this to the main syslog instead?
    def init_logger(self):
        self.logger = logging.getLogger('ortholang-kernel')
        self.logger.setLevel(logging.DEBUG)
        handler = logging.FileHandler(self.logfile)
        handler.setFormatter(logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s'))
        self.logger.addHandler(handler)

    def init_repl(self):
        self.logger.debug('OrthoLangKernel.init_repl')
        args = ['--config', self.cfgfile, '--interactive']
        self.logger.info('spawning ortholang %s' % args)
        self.ol_process = pexpect.spawn('ortholang', args, encoding=OL_ENCODING, echo=False, timeout=10)
        self.ol_process.expect_exact(OL_ARROW)
        self.logger.debug("before: '%s'" % self.ol_process.before)
        self.logger.debug("after: '%s'" % self.ol_process.after)
        self.logger.info('REPL should be ready for input')

    def __init__(self, *args, **kwargs):
        self.kernel_id = get_kernel_id()
        self.workdir = getcwd()

        # TODO get the top-level jupyter-lab dir from nixos config
        self.tmpdir  = join('/mnt/data/jupyter-lab', '.ortholang-kernels', self.kernel_id)

        self.cfgfile = join(self.tmpdir, 'ortholang.cfg')
        self.logfile = join(self.tmpdir, 'kernel.log')
        makedirs(self.tmpdir, exist_ok=True)
        self.init_logger()
        self.write_config()
        self.init_repl()
        super(OrthoLangKernel, self).__init__(*args, **kwargs)

    def load_plots(self, txt):
        regex = u'\[?plot image "(.*?)"'
        paths = re.findall(regex, txt)
        self.logger.debug('image paths: %s' % paths)
        plots = []
        for path in paths:
            path = realpath(path)
            self.logger.debug('loading image from "%s"' % path)
            utf8_b64 = b64encode(open(path, "rb").read()).decode(OL_ENCODING)
            width, height = get_image_size(path)
            plots.append((utf8_b64, width, height))
        return plots

    def split_statements(self, code):
        # Break into statements based on blank lines
        # from https://stackoverflow.com/a/27003351/429898
        statements = [[]]
        for line in code.splitlines():
            line = line.split('#', 1)[0]
            if len(line) == 0 or '=' in line or line.strip().startswith(':'):
                if len(statements[-1]) > 0:
                    statements.append([])
            if len(line) > 0:
                statements[-1].append(line)
        statements = [' '.join(s) for s in statements]
        self.logger.debug("statements: '%s'" % statements)
        return statements

    def do_execute(self, code, silent, store_history=True, user_expressions=None, allow_stdin=False):
        self.logger.debug("OrthoLangKernel.do_execute: '%s'" % code)
        statements = self.split_statements(code)
        outputs = []
        for s in statements:

            try:
                outputs.append(self.do_execute_statement(s))
            except pexpect.exceptions.TIMEOUT as e:
                self.logger.error("do_execute_statement timeout: %s" % e)
                outputs.append(str(e))
                self.restart()
            except pexpect.exceptions.EOF as e:
                self.logger.error("do_execute_statement OEF: %s" % e)
                outputs.append(str(e))
                self.restart()

        output = '\n'.join(outputs).strip()
        self.logger.debug("output: '%s'" % output)

        if not silent:
            if contains_plot(output):
                plots = self.load_plots(output)
                for (plot, width, height) in plots:

                    # Jupyter lab seems to respect width, but not max-width or height.
                    # TODO this works on flowcharts + venn diagrams, but adjust for other plots too
                    if width > 600 or height > 600:
                        display_width = width / 3
                    else:
                        display_width = width

                    content = {
                        'data': {'image/png': plot},
                        'metadata' : {
                            'image/png' : {'width': str(display_width) + 'px'}
                        }
                    }
                    self.logger.debug('content: %s' % content)
                    self.logger.debug('sending content...')
                    self.send_response(self.iopub_socket, 'display_data', content)
                    self.logger.debug('ok')
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
        self.logger.debug("do_execute_statement '%s'" % code)
        self.ol_process.sendline(code)
        options = [OL_ARROW, OL_BYENOW]
        # see https://stackoverflow.com/a/35134678/429898
        i = self.ol_process.expect_exact(options, timeout=None)
        self.logger.debug("expect index: %d" % i)
        output = clean_lines(self.ol_process.before + self.ol_process.after)
        self.logger.debug("statement output: '%s'" % output)
        if i == 1:
            self.restart()
        return output

    def quit_repl(self):
        try:
            self.logger.info('quitting repl...')
            self.ol_process.sendline(':quit\n')
            self.ol_process.expect_exact(OL_BYENOW, timeout=5)
            self.logger.debug('final output: "%s"' % (self.ol_process.before + self.ol_process.after))
            self.ol_process.kill(0)
            self.ol_process.close(force=True)
            self.logger.debug('quit successfully')
        except:
            self.logger.error('failed to kill REPL')

    def restart(self):
        self.logger.info('restarting...')
        self.init_repl()

    def do_shutdown(self, restart):
        self.quit_repl()
        if restart:
            self.restart()

if __name__ == '__main__':
    from ipykernel.kernelapp import IPKernelApp
    IPKernelApp.launch_instance(kernel_class=OrthoLangKernel)
