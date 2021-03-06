import os, unicodedata, sys, locale
import kaa
import kaa.log
from kaa import document, encodingdef
from kaa.filetype.default import defaultmode
from kaa import consts

class FileStorage:
    def get_textio(self, fileinfo):
        try:
            # use surrogateescape to preserve file contents intact.
            textio = open(fileinfo.fullpathname, 'r',
                        encoding=fileinfo.encoding, 
                        errors='surrogateescape', 
                        newline=fileinfo.nlchars)
        
        except FileNotFoundError:
            return None

        return textio

    def get_fileinfo(self, filename, encoding=None, newline=None):
        if sys.platform == 'darwin':
            filename = unicodedata.normalize('NFC', filename)
    
        if encoding is None:
            encoding = kaa.app.config.DEFAULT_ENCODING
    
        if newline is None:
            newline = kaa.app.config.DEFAULT_NEWLINE
    
        fileinfo = FileInfo()

        fullpath = os.path.abspath(filename)
        dirname, filename = os.path.split(filename)

        fileinfo.storage = self
        fileinfo.fullpathname = fullpath
        fileinfo.dirname = dirname
        fileinfo.filename = filename

        try:
            fileinfo.stat = os.stat(filename)
        except FileNotFoundError:
            fileinfo.stat = None

        fileinfo.encoding = encoding
        fileinfo.newline = newline
        
        return fileinfo
        
    def listdir(self, dirname):
        dirs = []
        files = []
        for name in os.listdir(dirname):
            if os.path.isdir(os.path.join(dirname, name)):
                dirs.append(name)
            else:
                files.append(name)
        if sys.platform == 'darwin':
            dirs = [unicodedata.normalize('NFC', n) for n in dirs]
            files = [unicodedata.normalize('NFC', n) for n in files]
        return dirs, files

    def _save_hist(self, filename):
        abspath = os.path.abspath(filename)
        dirname = os.path.dirname(abspath)
        if dirname.endswith(os.pathsep):
            dirname = dirname[:-1]

        kaa.app.config.hist_files.add(abspath)
        kaa.app.config.hist_dirs.add(dirname)
        kaa.app.last_dir = dirname

    def openfile(self, filename, encoding=None, newline=None, nohist=False):
        if not nohist:
            self._save_hist(filename)
        return openfile(filename, encoding, newline)

    def save_document(self, doc, filename, encoding=None, newline=None):
        self._save_hist(filename)

        if not doc.fileinfo:
            fileinfo = kaa.app.storage.get_fileinfo(filename, encoding, newline)
        else:
            if encoding is not None:
                doc.fileinfo.encoding = encoding

            if doc.fileinfo.encoding is None:
                doc.fileinfo.encoding = kaa.app.config.DEFAULT_ENCODING

            if newline is not None:
                doc.fileinfo.newline = newline
                
            if doc.fileinfo.newline is None:
                doc.fileinfo.newline = kaa.app.config.DEFAULT_NEWLINE

        with open(filename, 'w', encoding=doc.fileinfo.encoding,
                 newline=consts.NEWLINE_CHARS[doc.fileinfo.newline],
                 errors='surrogateescape') as f:

            # TODO: save as another file and rename.
            # TODO: fsync
            f.write(doc.gettext(0, doc.endpos()))

        doc.fileinfo = self.get_fileinfo(filename)
        doc.set_title(None)
        doc.provisional = False
        if doc.undo:
            doc.undo.saved()

        mode = select_mode(filename)
        if type(doc.mode) is not mode:
            doc.setmode(mode())

        dir, file = os.path.split(filename)
        if not dir.endswith(os.path.sep):
            dir += os.path.sep

        kaa.app.messagebar.set_message('Written to {}({})'.format(file, dir))


class FileInfo:
    storage = None
    fullpathname = ''
    dirname = ''
    filename = ''
    stat = None
    encoding = None
    newline = None

    @property
    def nlchars(self):
        return consts.NEWLINE_CHARS[self.newline]

    def __init__(self):
        self.encoding = kaa.app.config.DEFAULT_ENCODING
        self.newline= kaa.app.config.DEFAULT_NEWLINE

def select_mode(filename):
    ext = os.path.splitext(filename)[1].lower()

    for pkg in kaa.app.config.get_mode_packages():
        if ext in getattr(pkg, 'FILE_EXT', ()):
            return pkg.get_modetype()

    return defaultmode.DefaultMode


def openfile(filename, encoding=None, newline=None):
    # Open file
    fileinfo = kaa.app.storage.get_fileinfo(filename, encoding, newline)
    textio = kaa.app.storage.get_textio(fileinfo)

    buf = document.Buffer()
    if textio:
        src = textio.read()
        if fileinfo.nlchars is not None:
            src = src.replace(fileinfo.nlchars, '\n')
        buf.insert(0, src)

    doc = document.Document(buf)
    doc.fileinfo = fileinfo
    doc.setmode(select_mode(filename)())

    dir, file = os.path.split(fileinfo.fullpathname)
    if not dir.endswith(os.path.sep):
        dir += os.path.sep

    kaa.app.messagebar.set_message('Read from {}({})'.format(file, dir))

    return doc

NUM_NEWFILE = 1
def newfile(mode=None, s='', provisional=False):
    buf = document.Buffer()
    if s:
        buf.insert(0, s)

    doc = document.Document(buf)
    doc.provisional = provisional

    global NUM_NEWFILE
    doc.title = '<Untitled {}>'.format(NUM_NEWFILE)
    NUM_NEWFILE += 1

    doc.fileinfo = FileInfo()
    if not mode:
        mode = defaultmode.DefaultMode()
    doc.setmode(mode)
    return doc
