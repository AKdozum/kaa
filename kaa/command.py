import functools

def command(cmdid):
    def _f(f):
        f.COMMAND_ID = cmdid
        return f 
    return _f

def is_enable(cmdid):
    def _f(f):
        f.COMMAND_IS_ENABLE = cmdid
        return f
    return _f

def norec(f):
    f.NOREC = True
    return f 

def norerun(f):
    f.NORERUN = True
    return f

#def repeat(f):
#    def rep(self, wnd, *args, **kwargs):
#        n = 1 if not wnd.editmode.has_repeat() else wnd.editmode.get_repeat()
#        for i in range(n):
#            f(self, wnd, *args, **kwargs)
#    functools.update_wrapper(rep, f)
#    return rep

class Commands:
    def _find_funcs(self, attrname):
        for name in dir(self):
            f = getattr(self, name)
            cmdid = getattr(f, attrname, None)
            if cmdid:
                yield (cmdid, f)

    def get_commands(self):
        yield from self._find_funcs('COMMAND_ID')

    def get_commands_is_enable(self):
        yield from self._find_funcs('COMMAND_IS_ENABLE')




