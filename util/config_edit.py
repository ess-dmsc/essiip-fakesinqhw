#!/usr/bin/env python
"""Provides a sics_config.ini file viewer and editor.
"""
# vim: tabstop=8  softtabstop=4  shiftwidth=4  nocin  si et ft=python

# View Screen has 3 parts
# (Instrument Configuration), (Configuration Options), (Option Implementation)
# Uses MVC as InstConfigData<M>, InstConfigView<V>, InstConfigManager<C>
 
# InstConfigData <>--- ConfigParser.SafeConfig
#  |--set_cfparse()

# InstConfigManager <>--- InstConfigData, PresentationData
#  |--set_cfdata(), set_presdata()
#  |--set_xyz_data() call self.cfgdata.set_xyz() methods
#

# urwid.Pile
#     ^
#     |
# InstConfigView <>--- InstConfigManager, PresentationData
#  |--set_cfedit(), set_presdata()


import os
import shutil
import argparse
import ConfigParser
import urwid
from collections import defaultdict

PALETTE = [
    ('body', 'dark cyan', '', 'standout'),
    ('focus', 'dark red', '', 'standout'),
    ('head', 'yellow', 'black'),
]


class RadioButtonListWalker(urwid.SimpleListWalker):

    """Extend urwid.SimpleListWalker to generate a radio button listwalker.

    Attributes:
        button_dict (dict): Maps radiobutton labels to an urwid.RadioButton.
    """

    def __init__(self, item_states, on_state_change=None, user_data=None):
        """
        Args:
            item_states (list of tuples): [(button name, state)].
            on_state_change: 'change' signal handler for each radiobutton.
            user_data: data passed to signal handler.
        """
        radio_grp = []
        mapped_rb_list = []
        self.button_dict = {}
        for item, stateval in item_states:
            _rb = urwid.RadioButton( radio_grp, item, state=stateval,
              on_state_change=on_state_change, user_data=user_data )
            self.button_dict[item] = _rb
            mapped_rb = urwid.AttrMap(_rb, 'body', 'focus')
            mapped_rb_list.append(mapped_rb)

        super(RadioButtonListWalker, self).__init__(mapped_rb_list)
        return 

    def set_modified_callback(self, callback):
        """This is an abstract method in SimpleListWalker.
        The urwid doc says use connect_signal(lw, 'modified', callback) instead.
        """
        slw = super(RadioButtonListWalker, self)
        urwid.connect_signal(slw, 'modified', callback)
        return

class CheckBoxListWalker(urwid.SimpleListWalker):

    """Extend urwid.SimpleListWalker to generate a checkbox listwalker.
    Attributes:
        button_dict (dict): Maps checkbox labels to an urwid.CheckBox.
    """

    def __init__(self, item_states, on_state_change = None, user_data = None):
        """
        Args:
            item_states (list of tuples): [(button name, state)].
            on_state_change: 'change' signal handler for each radiobutton.
            user_data: data passed to signal handler.
        """
        mapped_cb_list = []
        self.button_dict = {}
        for item, stateval in item_states:
            _cb = urwid.CheckBox( item, state = stateval,
                                on_state_change = on_state_change,
                                user_data = user_data )
            self.button_dict[item] = _cb
            mapped_cb = urwid.AttrMap(_cb, 'body', 'focus')
            mapped_cb_list.append(mapped_cb)

        super(CheckBoxListWalker, self).__init__(mapped_cb_list)
        return

    def set_modified_callback(self, callback):
        """This is an abstract method in SimpleListWalker.
        The urwid doc says use connect_signal(lw, 'modified', callback) instead.
        """
        slw = super(CheckBoxListWalker, self)
        urwid.connect_signal(slw, 'modified', callback)
        return


class OptionListWalker(CheckBoxListWalker):
    
    """Extend CheckBoxListWalker to generate a listwalker from an
    InstConfigData option description.
    """

    def __init__(self, opt_dict, statechange_cb):
        """
        Args:
            opt_dict: InstConfigData option description dictionary.
            statechange_cb: 'change' signal handler for each checkbox.
        """
        urwid.register_signal(OptionListWalker, ['focus_change'])
        item_states = [(i, d['enabled']) for i, d in opt_dict.iteritems()]
        item_states.sort()

        super(OptionListWalker, self).__init__(item_states, statechange_cb)
        return

    def set_focus(self, pos):
        """Emit 'focus_change' signal with position of button.
        """
        urwid.emit_signal(self, 'focus_change', pos)
        return super(OptionListWalker, self).set_focus(pos)


# ClosedListBox implements a ListBox which prevents selection outside of the
# list using the 'up' or 'down' keys
class ClosedListBox(urwid.ListBox):

    """Extend urwid.ListBox to prevent navigating outside of the listbox.
    """

    def keypress(self, size, key):
        """Override keypress to limit navigation to within listbox.
        """
        pos = self.get_focus()[1]
        _ll = len(self.body)
        if (pos <= 0 and key == 'up') or (pos >= _ll-1 and key == 'down'):
            return
        else:
            return super(ClosedListBox, self).keypress(size, key)


# List of Checkboxes
class OptionListBox(ClosedListBox):

    """Extend ClosedListBox doesn't add anything but it may come in handy
    someday when defining behaviour of configuration option lists.
    """

    def __init__(self, listwalker):
        super(OptionListBox, self).__init__(listwalker)
        return


# List of RadioButtons
class ImpListBox(ClosedListBox):

    """Extend ClosedListBox to allow updating implementation lists when
    selecting a configuration option.
    """

    def __init__(self, listwalker):
        super(ImpListBox, self).__init__(listwalker)
        return

    def use_listwalker(self, listwalker):
        """ Select the given listwalker for display.
        """
        self.body.contents[:] = listwalker
        return


class InstConfigData(object):

    """Handles reading and writing instrument configuration data and provides
    methods to change the configuration.
    Attributes:
        config_dict: Instrument configurations by configuration name.
        opt_dict: Configuration option descriptions indexed by option name.
        imp_dict: Implementations for indexed by option type.
    """

    msg_index = 4

    def __init__(self):
        self.file_parser = ConfigParser.SafeConfigParser()
        self.config_filename = 'sics_config.ini'
        #config_dict: dict of instrument configurations as defined below,
        # {configname: {'enabled':T/F, 'cascade_list':[(option, dflt_imp)]} }
        self.config_dict = defaultdict(dict)

        #imp_dict: dict of implementations indexed by optype,
        # {optype: []|[none:impname,...] }
        self.imp_dict = defaultdict(list)

        #opt_dict: dict of configuration options as defined below,
        # {optname:{'enabled':T/F/Always, 'imptype':optype,'selected_imp':dflt}}
        self.opt_dict = defaultdict(dict)

        #imp_ip_dict: Maps each implementation to an ip and port if it has one.
        # {imp, {ip:'q4.q3.q2.q1', port:'nnnn', ...}
        self.imp_ip_dict = defaultdict(dict)

        #imp2opt_dict: Maps each implementation to an option or None,
        # {imp: opt/None}
        self.imp2opt_dict = {}

        #optypelist: list of (opt, optype) tuples
        # [(opt, optype)]
        self.optypelist = []

    def __get_configurations(self):
        """Parse instrument configuration definitions from INI file into
        config_dict attribute of InstConfigData object
        """
        for sect in self.file_parser.sections():
            cascade_list = []
            if self.file_parser.has_option(sect, 'cascade'):
                enabled = self.file_parser.get(sect, 'enabled')
                # pylint: disable = E1103
                optimp_list = self.file_parser.get(sect, 'cascade').split(',')
                # pylint: enable = E1103
                for cascade_str in optimp_list:
                    cascade_list.append(tuple(cascade_str.split(':')))
                # pylint: disable = E1103
                lower_enabled = enabled.lower()
                # pylint: enable = E1103
                if lower_enabled in ['true', 'always']:
                    stateval = True
                else:
                    stateval = False

                self.config_dict[sect]['enabled'] = stateval
                self.config_dict[sect]['cascade_list'] = cascade_list

    def __get_options(self):
        """Parse configuration options from INI file into opt_dict attribute of
        InstConfigData object.
        """
        for sect in self.file_parser.sections():
            if self.file_parser.has_option(sect, 'implementation'):
                selected_imp = self.file_parser.get(sect, 'implementation')
                imptype = self.file_parser.get(sect, 'optype')
                # pylint: disable = E1103
                enabled = self.file_parser.get(sect, 'enabled').lower()
                # pylint: enable = E1103
                if enabled == 'always':
                    stateval = True
                    permanent = True
                elif enabled == 'true':
                    stateval = True
                    permanent = False
                else:
                    stateval = False
                    permanent = False

                if self.file_parser.has_option(sect, 'id'):
                    _id = self.file_parser.get(sect, 'id')
                    self.opt_dict[sect]['id'] = _id

                self.opt_dict[sect]['permanent'] = permanent
                self.opt_dict[sect]['imptype'] = imptype
                if stateval == True:
                    imp_unavailable = (selected_imp in self.imp2opt_dict) and (
                        self.imp2opt_dict[selected_imp] != 'none' )
                    if selected_imp == 'none' or imp_unavailable:
                        self.opt_dict[sect]['enabled'] = False
                        self.opt_dict[sect]['selected_imp'] = 'none'
                    else:
                        self.opt_dict[sect]['enabled'] = True
                        self.set_imp(sect, selected_imp)
#                       dbmsg = 'Add imp2opt_dict[{0}] = {1}'
#                       print dbmsg.format(selected_imp, sect)
                else:
                    self.opt_dict[sect]['enabled'] = False
                    self.opt_dict[sect]['selected_imp'] = 'none'

    def __get_implementations(self):
        """Parse implementation lists from INI file into imp_dict attribute of
        InstConfigData object.
        """
        for sect in self.file_parser.sections():
            if self.file_parser.has_option(sect, 'imptype'):
                imptype = self.file_parser.get(sect, 'imptype')
                self.imp_dict[imptype].append(sect)
                if self.file_parser.has_option(sect, 'ip'):
                    ip_address = self.file_parser.get(sect, 'ip')
                    self.imp_ip_dict[sect]['ip'] = ip_address

                if self.file_parser.has_option(sect, 'port'):
                    port = self.file_parser.get(sect, 'port')
                    self.imp_ip_dict[sect]['port'] = port

                if sect not in self.imp2opt_dict:
                    self.imp2opt_dict[sect] = 'none'
#                   print 'Add imp2opt_dict[{0}] = none'.format(sect)

    def consistency_check(self):
        """Check that there is a one to one mapping between options and
        implementations.
        """
        for opt, opt_def in self.opt_dict.iteritems():
            selected_imp = opt_def['selected_imp']
            if selected_imp == 'none':
                continue
            else:
                mapped_opt = self.imp2opt_dict[selected_imp]

            if mapped_opt != opt:
                emsg = 'ERROR: imp2opt_dict fails to map {i} to {o}'
                print emsg.format(i=selected_imp, o=opt)

        for imp, opt in self.imp2opt_dict.iteritems():
            if imp == 'none':
                print 'ERROR: Found "none" as a keyword in imp2opt_dict'
                continue
            elif opt == 'none':
                continue
            else:
                selected_imp = self.opt_dict[opt]['selected_imp']

            if imp != selected_imp:
                emsg = 'ERROR: imp2opt_dict fails to map {i} to {o}'
                print emsg.format(i=selected_imp, o=opt)

    def read_config_file(self, **kwargs):
        """ Load and parse a sics_config.ini file """
        if 'config_filename' in kwargs:
            self.config_filename = kwargs['config_filename']
        self.file_parser.read(self.config_filename)
        self.__get_options()
        self.__get_implementations()
        self.__get_configurations()
        self.consistency_check()
        for opt, opt_desc in self.opt_dict.iteritems():
            self.optypelist.append((opt, opt_desc['imptype']))

        for imptype in self.imp_dict.keys():
            if 'none' not in self.imp_dict[imptype]:
                self.imp_dict[imptype].insert(0, 'none')

    def backup_files(self):
        """ Backup configuration files """
        for idx in range(8, 0, -1):
            if os.path.exists(self.config_filename + "." + str(idx)):
                os.rename(self.config_filename + "." + str(idx),
                        self.config_filename + "." + str(idx + 1))

        if os.path.exists(self.config_filename):
            shutil.copy2(self.config_filename, self.config_filename + ".1")

    def write_section(self, fhandle, sect):
        """Write a configuration section with sorted options"""
        fhandle.write("[%s]\n" % sect)
        for opt in sorted(self.file_parser.options(sect)):
            fhandle.write('{0} = {1}\n'.format(opt, self.file_parser.get(sect, opt)))

    def write_config_file(self):
        """ Write out InstConfigData values to the configuration file."""
        for opt, opt_desc in self.opt_dict.iteritems():
            if 'permanent' in opt_desc and opt_desc['permanent'] == True:
                enabled = 'Always'
            else:
                enabled = opt_desc['enabled'].__str__()

            self.file_parser.set(opt, 'enabled', enabled)
            self.file_parser.set(opt, 'implementation',
                                 opt_desc['selected_imp'])
            self.file_parser.set(opt, 'optype', opt_desc['imptype'])

        for config, config_desc in self.config_dict.iteritems():
            enabled = config_desc['enabled'].__str__()
            self.file_parser.set(config, 'enabled', enabled)

        scratch_file = self.config_filename + '.scratch'
        with open(scratch_file, 'w') as cfile:
            for config in sorted(self.config_dict.keys()):
                self.write_section(cfile, config)

            for opt in sorted(self.opt_dict.keys()):
                self.write_section(cfile, opt)

            for imp in sorted(self.imp2opt_dict.keys()):
                self.write_section(cfile, imp)

                cfile.write("\n")

        os.rename(scratch_file, self.config_filename)

    def set_imp(self, opt, new_imp):
        """Keep option dictionaray and implementation -> option map in sync."""
        if 'selected_imp' in self.opt_dict[opt]:
            old_imp = self.opt_dict[opt]['selected_imp']
            if old_imp != 'none':
                self.imp2opt_dict[old_imp] = 'none'

        self.opt_dict[opt]['selected_imp'] = new_imp
        if new_imp != 'none':
            self.imp2opt_dict[new_imp] = opt

    def get_optypelist (self):
        """Return a list of (option, optype) tuples."""
        return self.optypelist

    def iter_implementations(self, opt):
        """Iterate over implementation names for the given option."""
        opt_desc = self.opt_dict[opt]
        for imp in self.imp_dict[opt_desc['imptype']]:
            yield imp

    def cf_statechange(self, cfg_id, new_state):
        """Change the given instrument configuration state."""
        self.config_dict[cfg_id]['enabled'] = new_state

    def opt_statechange(self, opt, new_state):
        """Change the given option state."""
        self.opt_dict[opt]['enabled'] = new_state

    def imp_statechange(self, selected_imp, new_state, opt):
        """Change the given implementation state."""
        self.msg_index = (self.msg_index - 3) % 2 + 4
        if new_state == True:
            self.opt_dict[opt]['selected_imp'] = selected_imp


class InstConfigView(urwid.Frame):

    """Extend urwid.Pile to provide an instrument configuration viewer.
    """

    def __init__(self, cfg_lb, opt_lb, imp_lb):
        """
        Args:
            cfg_lb: Instrument configuration listbox
            opt_lb: Configuration options listbox
            imp_lb: Available implementations listbox
        """
        option_listboxes = [
            cfg_lb,
            opt_lb,
            imp_lb]


        self. main_loop = None
        self.cfg_pile = urwid.Pile(option_listboxes)
        self.help_str = 'Alt-Q (Quit), W (Write file)'
        self.header_text = urwid.Text(u'')
        self._msg_hdr('')
        self.mapped_header = urwid.AttrMap(self.header_text, 'head')

        super(InstConfigView, self).__init__(header = self.mapped_header, body = self.cfg_pile)
        return

    def _msg_hdr(self, msg):
        """Display a message after the help string"""
        hdr = self.help_str + msg
        self.header_text.set_text(hdr)

    def _msg_cb(self, main_loop, msg):
        """Wrap the message function in an urwid main loop callback"""
        self._msg_hdr(msg)

    def timed_msg(self, t_sec, msg):
        """Display a transient message for the given time"""
        self._msg_hdr(msg)
        self.main_loop.set_alarm_in(t_sec, self._msg_cb, '')

    def set_main(self, main_loop):
        """Pass a reference to the main loop to InstConfigView"""
        self.main_loop = main_loop

# Contains OptionListWalker dict indexed by option
# Contains ImpListBox
# Connects OptionListWalker 'focus_change' signal to update_imp_lb handler
# Tracks selected implementation for each option
# and sets selection on ImpListBox
class InstConfigManager(object):

    """Provides controller which keeps data and viewer in sync."""

    def __init__(self, cf_dat):
        self.cf_dat = cf_dat
        urwid.register_signal(InstConfigManager, ['focus_change'])
        self.opt_optype_list = self.cf_dat.get_optypelist()
        
        self.opt_optype_list.sort()
        firstopt = self.opt_optype_list[0][0]
        self.imp_lw = self.__gen_imp_listwalker(firstopt)
        self.opt_lw = OptionListWalker(cf_dat.opt_dict, self.opt_statechange)
        for label, button in self.opt_lw.button_dict.iteritems():
            button.set_label('{0}:{1}'.format(
              label, self.cf_dat.opt_dict[label]['selected_imp']) )

        self.imp_lb = ImpListBox(self.imp_lw)
        urwid.connect_signal(self.opt_lw, 'focus_change', self.update_imp_lb)
        item_states = [(i, d['enabled']) for i, d in
                       cf_dat.config_dict.iteritems()]
        item_states.sort()
        self.cfg_lw = RadioButtonListWalker(item_states, on_state_change =
                                            self.cf_statechange)
        self.cfg_lb = OptionListBox(self.cfg_lw)
        self.opt_lb = OptionListBox(self.opt_lw)
        self.opt_lb.set_focus(0)
        return

    def __imp_unavailable(self, opt, imp, action):
        """Return True if an implementation is unavailable because it is used
        by an enabled option.
        """
        if imp == 'none':
            return False

        ckopt = self.cf_dat.imp2opt_dict[imp]
        if ckopt == 'none':
            return False

        opt_imp = self.cf_dat.opt_dict[opt]['selected_imp']
        if (action == 'focus'):
            if opt_imp == imp:
                return False
            elif self.cf_dat.opt_dict[ckopt]['enabled']:
                return True
            else:
                return False
        elif (action == 'state_change'):
            if self.cf_dat.opt_dict[ckopt]['enabled']:
                return True
            else:
                return False
        else:
            return False

    def __gen_imp_listwalker(self, opt):
        """Generate the appropriate listwalker for the given option."""
        imp_items = []
        for imp in self.cf_dat.iter_implementations(opt):
            if self.__imp_unavailable(opt, imp, 'focus'):
                continue
            elif imp == 'none' and self.cf_dat.opt_dict[opt]['permanent']:
                continue

            if imp == self.cf_dat.opt_dict[opt]['selected_imp']:
                imp_items.append((imp, True))
            else:
                imp_items.append((imp, False))

            imp_items = imp_items[:1] + sorted(imp_items[1:])

        rb_lw = RadioButtonListWalker(imp_items,
                                      on_state_change=self.imp_statechange,
                                      user_data=opt)

        for imp, button in rb_lw.button_dict.iteritems():
            if imp != 'none':
                if 'ip' in self.cf_dat.imp_ip_dict[imp]:
                    address = self.cf_dat.imp_ip_dict[imp]['ip']
                    if 'port' in self.cf_dat.imp_ip_dict[imp]:
                        port = self.cf_dat.imp_ip_dict[imp]['port']
                        address += ':'
                        address += port

                    button.set_label('{0:20}{1}'.format(imp, address))
                else:
                    button.set_label('{0}'.format(imp))

        return rb_lw

    def cf_statechange(self, button, new_state):
        """Update option list when an instrument configuration is selected and
        notify InstConfigData object.
        """
        cfg_id = button.get_label()
        self.cf_dat.cf_statechange(cfg_id, new_state)
        cascade = self.cf_dat.config_dict[cfg_id]['cascade_list']
        if new_state == True:
            for opt in self.cf_dat.opt_dict.keys():
                self.opt_lw.button_dict[opt].set_state(False)

            for opt, imp in cascade:
                self.cf_dat.set_imp(opt, imp)
                self.opt_lw.button_dict[opt].set_state(True)

            for opt in self.cf_dat.opt_dict.keys():
                if self.cf_dat.opt_dict[opt]['permanent'] == True:
                    self.opt_lw.button_dict[opt].set_state(True)

                if self.opt_lw.button_dict[opt].get_state() == False:
                    self.cf_dat.set_imp(opt, 'none')
                    self.opt_lw.button_dict[opt].set_label('{0}:none'.format(opt))

        return

    def opt_statechange(self, button, new_state):
        """Update option label when it changes state and notify InstConfigData
        object.
        """
        opt = button.get_label().split(':')[0]
        imp = self.cf_dat.opt_dict[opt]['selected_imp']
        if new_state == True:
            if self.__imp_unavailable(opt, imp, 'state_change'):
                self.cf_dat.opt_dict[opt]['selected_imp'] = 'none'
                imp_none_button = self.imp_lw.button_dict['none']
                imp_none_button.set_state(True)
                opt_button = self.opt_lw.button_dict[opt]
                opt_button.set_label('{0}:none'.format(opt))
                self.imp_lw = self.__gen_imp_listwalker(opt)
                self.imp_lb.use_listwalker(self.imp_lw)
            else:
                opt_button = self.opt_lw.button_dict[opt]
                opt_button.set_label('{0}:{1}'.format(opt, imp))
                self.cf_dat.set_imp(opt, imp)

        self.cf_dat.opt_statechange(opt, new_state)

    def imp_statechange(self, button, new_state, opt):
        """Update label on the configuration option when it's implementation is
        changed.
        """
        imp = button.get_label().split()[0]
        if new_state == True:
            self.cf_dat.set_imp(opt, imp)
            opt_button = self.opt_lw.button_dict[opt]
            opt_button.set_label('{0}:{1}'.format(opt, imp))

        self.cf_dat.imp_statechange(imp, new_state, opt)
        return

    def update_imp_lb(self, pos):
        """Update implementation list when an option gets focus."""
        optname = self.opt_optype_list[pos][0]
        self.imp_lw = self.__gen_imp_listwalker(optname)
        self.imp_lb.use_listwalker(self.imp_lw)
        return


def gen_input_handler(cf_man, cf_dat, cf_viewer):
    """Generate keyinput handler with references to the controller object, the
    data object and the viewer object.
    """
    def keyinput(key):
        """Switch between lists, save data and quit on key input."""
        if key == 'meta q':
            raise urwid.ExitMainLoop()
        elif key == 'w':
            cf_dat.backup_files()
            cf_viewer.timed_msg(1, ': Saving file')
            cf_dat.write_config_file()
        elif key in ['right', 'tab']:
            if cf_viewer.cfg_pile.get_focus() == cf_man.cfg_lb:
                cf_viewer.cfg_pile.set_focus(cf_man.opt_lb)
            elif cf_viewer.cfg_pile.get_focus() == cf_man.opt_lb:
                cf_viewer.cfg_pile.set_focus(cf_man.imp_lb)
            else:
                cf_viewer.cfg_pile.set_focus(cf_man.cfg_lb)
        elif key in ['left', 'shift tab']:
            if cf_viewer.cfg_pile.get_focus() == cf_man.cfg_lb:
                cf_viewer.cfg_pile.set_focus(cf_man.imp_lb)
            elif cf_viewer.cfg_pile.get_focus() == cf_man.opt_lb:
                cf_viewer.cfg_pile.set_focus(cf_man.cfg_lb)
            else:
                cf_viewer.cfg_pile.set_focus(cf_man.opt_lb)

    return keyinput


def main(config_ini):
    """Create configuration editor."""
#   global cf_dat, cf_man, cf_viewer

    # Make configuration data
    cf_dat = InstConfigData()
    cf_dat.read_config_file(config_filename = config_ini)

    # Make configuration editor
    cf_man = InstConfigManager(cf_dat)

    # Make configuration viewer
    cf_viewer = InstConfigView(cf_man.cfg_lb, cf_man.opt_lb, cf_man.imp_lb)

    keyinput = gen_input_handler(cf_man, cf_dat, cf_viewer)
    main_loop = urwid.MainLoop(cf_viewer, PALETTE, unhandled_input=keyinput)
    cf_viewer.set_main(main_loop)
    main_loop.run()
    return

if '__main__' == __name__:
    DEFAULT_INI = "/usr/local/sics/sics_config.ini"
    PARSER = argparse.ArgumentParser(description = """
        Edit a configuration (*.ini) file using python urwid widget library.
        Options can be enabled or disabled with mouse or spacebar.
        Navigate with arrow keys.
        Press W to save.
        Press Alt-Q to quit.
        The default configuration filename is %s.
    """ % DEFAULT_INI)
    PARSER.add_argument(
      "-v", "--verbose", action="store_true",
      help="give more info in the footer")
    PARSER.add_argument(
      "path", nargs="?", default = DEFAULT_INI,
      help="name of file to edit [%s]" % DEFAULT_INI)
    ARGS = PARSER.parse_args()
    DEFAULT_INI = os.path.abspath(ARGS.path)
    main(DEFAULT_INI)
