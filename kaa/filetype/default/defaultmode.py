import copy
from collections import defaultdict
import kaa
from kaa.commands import (appcommand, filecommand, editorcommand, 
    editmodecommand)
from . import keybind, theme, modebase, menu
from kaa import highlight


class DefaultMode(modebase.ModeBase):
    DOCUMENT = True
    MODENAME = 'default'
    SHOW_LINENO = False
    KEY_BINDS = [
        keybind.app_keys,
        keybind.cursor_keys,
        keybind.edit_command_keys,
        keybind.addtional_edit_command_keys,
        keybind.emacs_keys,
        keybind.search_command_keys,
        keybind.macro_command_keys,
        keybind.rerun_keys,
    ]

    VI_KEY_BIND = [
#        keybind.command_mode_keys
    ]

    VI_VISUAL_MODE_KEY_BIND = [
#        keybind.visual_mode_keys
    ]
    VI_VISUAL_LINEWISE_MODE_KEY_BIND = [
#        keybind.visual_linewise_mode_keys
    ]

    def init_keybind(self):
        super().init_keybind()
        self.register_keys(self.keybind, self.KEY_BINDS)
        self.register_keys(self.keybind_vi_commandmode, self.VI_KEY_BIND)
        self.register_keys(self.keybind_vi_visualmode,
                           self.VI_VISUAL_MODE_KEY_BIND)
        self.register_keys(self.keybind_vi_visuallinewisemode,
                           self.VI_VISUAL_LINEWISE_MODE_KEY_BIND)

    def init_commands(self):
        super().init_commands()

        self.app_commands = appcommand.ApplicationCommands()
        self.register_command(self.app_commands)

        self.file_commands = filecommand.FileCommands()
        self.register_command(self.file_commands)

        self.cursor_commands = editorcommand.CursorCommands()
        self.register_command(self.cursor_commands)

        self.edit_commands = editorcommand.EditCommands()
        self.register_command(self.edit_commands)

        self.code_commands = editorcommand.CodeCommands()
        self.register_command(self.code_commands)

        self.screen_commands = editorcommand.ScreenCommands()
        self.register_command(self.screen_commands)

        self.macro_commands = editorcommand.MacroCommands()
        self.register_command(self.macro_commands)

        self.search_commands = editorcommand.SearchCommands()
        self.register_command(self.search_commands)

        self.rerun_commands = editorcommand.RerunCommand()
        self.register_command(self.rerun_commands)

        self.mode_commands = editmodecommand.EditModeCommands()
        self.register_command(self.mode_commands)

    def init_menu(self):
        self.menu = copy.deepcopy(menu.MENUS)

    def init_themes(self):
        super().init_themes()
        self.themes.append(theme.DefaultThemes)

    def init_tokenizers(self):
        self.tokenizers = [highlight.Tokenizer([])]

    def on_set_document(self, document):
        super().on_set_document(document)

    def close(self):
        super().close()
        self.keybind_vi_commandmode.clear()
        self.keybind_vi_visualmode.clear()
        self.keybind_vi_visuallinewisemode.clear()

    PARENTHESIS_OPEN = '({['
    PARENTHESIS_CLOSE = ')}]'
    PARENTHESIS = PARENTHESIS_OPEN + PARENTHESIS_CLOSE
    PARENSIS_PAIR = {o:c for (o, c) in
                     zip(PARENTHESIS_OPEN+PARENTHESIS_CLOSE,
                         PARENTHESIS_CLOSE+PARENTHESIS_OPEN)}

    def iter_parenthesis(self, posfrom):
        while True:
            pos = self.document.buf.findchr(
                self.PARENTHESIS, posfrom, self.document.endpos())

            if pos == -1:
                break

            attr = self.document.styles.getint(pos)
            yield pos, self.document.buf[pos], attr
            posfrom = pos+1

    def iter_rev_parenthesis(self, posfrom):
        posfrom += 1
        while True:
            pos = self.document.buf.rfindchr(
                self.PARENTHESIS, 0, posfrom)

            if pos == -1:
                break

            attr = self.document.styles.getint(pos)
            yield pos, self.document.buf[pos], attr
            posfrom = pos

    def find_match_parenthesis(self, posfrom):
        opener = self.document.buf[posfrom]
        curattr = self.document.styles.getint(posfrom)

        d = defaultdict(int)
        if opener in self.PARENTHESIS_OPEN:
            f = self.iter_parenthesis
            key = (opener, curattr)
        else:
            f = self.iter_rev_parenthesis
            key = (self.PARENSIS_PAIR[opener], curattr)


        for pos, c, attr in f(posfrom):
            if c in self.PARENTHESIS_OPEN:
                d[(c,attr)] += 1
            else:
                d[(self.PARENSIS_PAIR[c],attr)] -= 1

            if d.get(key) == 0:
                return pos

    def update_charattr(self, wnd):
        pos = wnd.cursor.pos
        d = {}
        if pos < self.document.endpos():
            c = self.document.buf[pos]
            if c in self.PARENTHESIS:
                d[pos] = self.get_styleid('parenthesis_cur')
                matchpos = self.find_match_parenthesis(pos)
                if matchpos is not None:
                    d[matchpos] = self.get_styleid('parenthesis_match')

        if d != wnd.charattrs:
            wnd.charattrs = d
            wnd.screen.style_updated()
            return True


    HIGHLIGHTBATCH = 300
    def run_highlight(self):
        return self.highlight.update_style(self.document, batch=self.HIGHLIGHTBATCH)

    def on_esc_pressed(self, wnd, event):
        super().on_esc_pressed(wnd, event)
        return

        # Pressing esc key starts command mode.
        is_available, command = self.get_command('editmode.command')
        if command:
            command(wnd)
            if kaa.app.macro.is_recording():
                kaa.app.macro.record(command)

    def on_keypressed(self, wnd, event, s, commands, candidate):
        if not commands and not candidate:
            if not s or s[0] < ' ':
                kaa.app.messagebar.set_message(kaa.app.SHOW_MENU_MESSAGE)

        return super().on_keypressed(wnd, event, s, commands, candidate)
            