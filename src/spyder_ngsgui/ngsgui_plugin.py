
# Spyder imports
from spyder.config.base import _
from spyder.utils.qthelpers import (create_action, create_toolbutton,
                                    add_actions, MENU_SEPARATOR)
# from spyder.utils import icon_manager as ima
try:
    # Spyder 4
    from spyder.api.plugins import SpyderPluginWidget
except ImportError:
    # Spyder 3
    from spyder.plugins import SpyderPluginWidget

# NGSolve imports
import ngsgui.gui as G
from ngsgui.widgets import ArrangeH

# qt imports
from qtpy import PYQT4, PYSIDE, QtCore

import ngsolve, cloudpickle
import ngsgui.thread as thread
ngsolve.ngsglobals.msg_level = 0

class NGSolvePlugin(SpyderPluginWidget):
    CONF_SECTION = "ngsolve"
    # TODO: find out why this doesn't work...
    LOCATION = QtCore.Qt.BottomDockWidgetArea

    def __init__(self, parent):
        super().__init__(parent)
        self.main = parent
        self.gui = G.GUI(flags=["--noOutputpipe", "--noConsole", "--noEditor"],startApplication=False)
        G.gui = self.gui
        self.initialize_plugin()
        self.setLayout(ArrangeH(self.gui.mainWidget))

    # SpyderPluginMixin API
    def on_first_registration(self):
        """Action to be performed on first plugin registration."""
        pass

    def update_font(self):
        """Update font from Preferences."""
        pass

    # ------ SpyderPluginWidget API -------------------------------------------
    def get_plugin_title(self):
        """Return widget title."""
        title = _('NGSolve')
        return title

    def get_plugin_icon(self):
        """Return widget icon."""
        return ima.icon('ipython_console')

    def get_focus_widget(self):
        """Return the widget to give focus to."""
        return self.gui.mainWidget

    def closing_plugin(self, cancelable=False):
        """Perform actions before parent main window is closed."""
        return True

    def refresh_plugin(self):
        """Refresh tabwidget."""
        pass

    def create_dockwidget(self):
        doc,loc = super().create_dockwidget()
        return doc, loc

    def get_plugin_actions(self):
        """Return a list of actions related to plugin."""
        return []

    def register_plugin(self):
        """Register plugin in Spyder's main window."""
        self.main.add_dockwidget(self)
        self.ipyconsole = self.main.ipyconsole
        # patch NameSpaceBrowser._handle_spyder_msg to get our ngsolve stuff...
        import spyder.plugins.ipythonconsole.widgets.namespacebrowser as nsb
        old_handle_spyder_msg = nsb.NamepaceBrowserWidget._handle_spyder_msg
        def new_handle_spyder_msg(_self, msg):
            spyder_msg_type = msg['content'].get('spyder_msg_type')
            if spyder_msg_type == 'ngsolve_draw':
                index, args, kwargs = cloudpickle.loads(bytes(msg['buffers'][0]))
                scene = ngsolve.Draw(*args, **kwargs)
                scene._redraw_index = index
            elif spyder_msg_type == 'ngsolve_redraw':
                values = cloudpickle.loads(bytes(msg['buffers'][0]))
                for scene in self.gui.getScenesFromCurrentWindow():
                    if hasattr(scene, "_redraw_index"):
                        scene.update(*(values[scene._redraw_index]))
                self.gui.window_tabber.activeGLWindow.glWidget.updateGL()
            else:
                old_handle_spyder_msg(_self, msg)
        nsb.NamepaceBrowserWidget._handle_spyder_msg = new_handle_spyder_msg


    def check_compatibility(self):
        """Check compatibility for PyQt and sWebEngine."""
        value = True
        message = ''
        if PYQT4 or PYSIDE:
            message = _("You are working with Qt4 and in order to use this "
                        "plugin you need to have Qt5.<br><br>"
                        "Please update your Qt and/or PyQt packages to "
                        "meet this requirement.")
            value = False
        return value, message