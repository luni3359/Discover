import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GtkLayerShell
import cairo
import logging
import sys


class OverlayWindow(Gtk.Window):
    def detect_type(self):
        window = Gtk.Window()
        screen = window.get_screen()
        screen_type = "%s" % (screen)
        if "Wayland" in screen_type:
            print("Using Wayland GDK. Expect bugs")
            return Gtk.WindowType.TOPLEVEL
        return Gtk.WindowType.POPUP

    def __init__(self):
        Gtk.Window.__init__(self, type=self.detect_type())
        screen = self.get_screen()
        self.set_size_request(50, 50)

        self.connect('draw', self.draw)

        self.compositing = False
        # Set RGBA
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if not self.get_display().supports_input_shapes():
            logging.info(
                "Input shapes not available. Quitting")
            sys.exit(1)
        if visual:
            # Set the visual even if we can't use it right now
            self.set_visual(visual)
        if screen.is_composited():
            self.compositing = True

        self.set_app_paintable(True)
        self.set_untouchable()
        self.set_skip_pager_hint(True)
        self.set_skip_taskbar_hint(True)
        self.set_keep_above(True)
        self.set_decorated(True)
        self.set_accept_focus(False)
        self.set_wayland_hax()

        self.show_all()
        self.monitor = 0
        self.align_right = True
        self.align_vert = 1
        self.floating = False
        self.force_xshape= False

    def set_wayland_hax(self):
        GtkLayerShell.init_for_window(self)
        GtkLayerShell.set_layer(GtkLayerShell.Layer.TOP)

    def draw(self, widget, context):
        pass

    def do_draw(self, context):
        pass

    def set_font(self, name, size):
        self.text_font = name
        self.text_size = size
        self.redraw()

    def set_floating(self, floating, x, y, w, h):
        self.floating = floating
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.force_location()

    def set_untouchable(self):
        (w, h) = self.get_size()
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
        surface_ctx = cairo.Context(surface)
        surface_ctx.set_source_rgba(0.0, 0.0, 0.0, 0.0)
        surface_ctx.set_operator(cairo.OPERATOR_SOURCE)
        surface_ctx.paint()
        reg = Gdk.cairo_region_create_from_surface(surface)
        self.input_shape_combine_region(reg)
        # self.shape_combine_region(reg)

    def unset_shape(self):
        self.get_window().shape_combine_region(None, 0, 0)

    def force_location(self):
        self.set_decorated(False)
        self.set_keep_above(True)
        display = Gdk.Display.get_default()
        if "get_monitor" in dir(display):
            monitor = display.get_monitor(self.monitor)
            geometry = monitor.get_geometry()
            scale_factor = monitor.get_scale_factor()
            if not self.floating:
                w = scale_factor * geometry.width
                h = scale_factor * geometry.height
                x = geometry.x
                y = geometry.y
                self.resize(w, h)
                self.move(x, y)
            else:
                self.move(self.x, self.y)
                self.resize(self.w, self.h)
        else:
            if not self.floating:
                screen = display.get_default_screen()
                w = screen.width()
                h = screen.height()
                x = 0
                y = 0
            else:
                self.move(self.x, self.y)
                self.resize(self.w, self.h)

        self.redraw()

    def redraw(self):
        gdkwin = self.get_window()

        if gdkwin:
            if not self.compositing or self.force_xshape:
                (w, h) = self.get_size()
                surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
                surface_ctx = cairo.Context(surface)
                self.do_draw(surface_ctx)
                reg = Gdk.cairo_region_create_from_surface(surface)
                gdkwin.shape_combine_region(reg, 0, 0)
            else:
                gdkwin.shape_combine_region(None, 0, 0)
        self.queue_draw()

    def set_monitor(self, idx):
        self.monitor = idx
        self.force_location()
        self.redraw()

    def set_align_x(self, b):
        self.align_right = b
        self.force_location()
        self.redraw()

    def set_align_y(self, i):
        self.align_vert = i
        self.force_location()
        self.redraw()

    def col(self, c, a=1.0):
        self.context.set_source_rgba(c[0], c[1], c[2], c[3] * a)

    def set_force_xshape(self, force):
        self.force_xshape = force
