# pylint: disable=missing-docstring
import sys
import importlib.util
import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, Gtk, GObject # pylint: disable=wrong-import-position


WINDOW_WIDTH = 400
WINDOW_HEIGHT = 250
HIDE_PIN = True
HIDE_PASSWORD = True
EXIT_TIMEOUT_MS = 3000


class Window(Gtk.Window):
    def __init__(self, generator):
        self.generator = generator

        Gtk.Window.__init__(self, title="dpass")

        self.clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        self.clipboard.request_text(self.on_clipboard_text)

        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10, border_width=10)
        self.add(self.box)

        self.service_name_entry = Gtk.Entry(placeholder_text="Service name")
        self.service_name_entry.connect("changed", self.on_service_name_changed)
        self.service_name_entry.connect("activate", self.on_entry_activate)
        self.box.pack_start(self.service_name_entry, True, True, 0)

        self.pin_entry = Gtk.Entry(placeholder_text="PIN", max_length=4, visibility=not HIDE_PIN)
        self.pin_entry.connect("changed", self.on_pin_changed)
        self.pin_entry.connect("activate", self.on_entry_activate)
        self.box.pack_start(self.pin_entry, True, True, 0)

        self.generate_button = Gtk.Button("Generate")
        self.generate_button.connect("clicked", self.on_generate_clicked)
        self.box.pack_start(self.generate_button, True, True, 0)

        self.box.pack_start(Gtk.Separator(), True, True, 0)

        self.password_entry = Gtk.Entry(
            sensitive=False,
            editable=False,
            placeholder_text="Generated password",
            visibility=not HIDE_PASSWORD
        )
        self.box.pack_start(self.password_entry, True, True, 0)

    def on_entry_activate(self, widget): # pylint: disable=unused-argument
        self.on_generate_clicked(None)

    def on_clipboard_text(self, clipboard, text): # pylint: disable=unused-argument
        if text:
            self.service_name_entry.set_text(text)
            self.service_name_entry.grab_focus()
            self.service_name_entry.select_region(0, -1)

    def on_service_name_changed(self, widget): # pylint: disable=unused-argument
        style_ctx = self.service_name_entry.get_style_context()
        style_ctx.remove_class("invalid")

    def on_pin_changed(self, widget):
        text = widget.get_text().strip()
        widget.set_text("".join([c for c in text if c in "0123456789"]))
        widget.get_style_context().remove_class("invalid")

    def on_generate_clicked(self, widget): # pylint: disable=unused-argument
        service_name = self.service_name_entry.get_text()
        pin = self.pin_entry.get_text()

        if not service_name:
            self.service_name_entry.get_style_context().add_class("invalid")
            return
        if not is_pin_valid(pin):
            self.pin_entry.get_style_context().add_class("invalid")
            return

        password = self.generator.generate(service_name, pin)
        self.password_entry.set_text(password)
        self.password_entry.grab_focus()
        self.password_entry.select_region(0, -1)

        self.clipboard.set_text(password, -1)

        GObject.timeout_add(EXIT_TIMEOUT_MS, Gtk.main_quit)


def is_pin_valid(pin):
    return len(pin) == 4 and pin.isdigit()


def run_gui(generator):
    css = b"""
        * {
            font-size: 24px;
        }

        entry, button {
            padding: 0.5em;
        }

        .invalid {
            background-color: #ffcccc;
        }
    """

    style_provider = Gtk.CssProvider()
    style_provider.load_from_data(css)
    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(),
        style_provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )

    win = Window(generator)
    win.connect("delete-event", Gtk.main_quit)
    win.set_size_request(WINDOW_WIDTH, WINDOW_HEIGHT)
    win.show_all()
    Gtk.main()


def run_cli(generator, service_name, pin):
    if not is_pin_valid(pin):
        sys.exit("PIN should be a four-digit number")

    password = generator.generate(service_name, pin)
    print(password)


def main(argv=None):
    if argv is None:
        argv = sys.argv

    try:
        generator_module_spec = importlib.util.spec_from_file_location(
            "dpass_generator",
            "dpass_generator.py"
        )
        generator = importlib.util.module_from_spec(generator_module_spec)
        generator_module_spec.loader.exec_module(generator)

        if not hasattr(generator, "generate"):
            sys.exit("Password generator module should implement a generate/2 function")

        if len(argv) == 3:
            run_cli(generator, argv[1], argv[2])
        elif len(argv) == 2 and argv[1] in ["-h", "--help"]:
            print("dpass\n")
            print("Usage:")
            print("  $ python dpass.py -- launches graphical interface")
            print("  $ python dpass.py SERVICE_NAME PIN -- generates password, prints it to stdout")
        else:
            run_gui(generator)
    except FileNotFoundError:
        sys.exit("Could not load password generator moudle")


if __name__ == "__main__":
    main()
