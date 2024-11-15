#!/usr/bin/env python3
import gi
import subprocess
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib, Adw

class UpdateChecker(Gtk.Application):
    def __init__(self):
        super().__init__(application_id='com.example.archupdate')
        self.connect('activate', self.on_activate)

    def on_activate(self, app):
        self.win = Gtk.ApplicationWindow(application=app)
        self.win.set_title('Arch Update Checker')
        self.win.set_default_size(400, 300)

        # Create style manager for dark mode
        style_manager = Adw.StyleManager.get_default()

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(10)
        box.set_margin_bottom(10)
        box.set_margin_start(10)
        box.set_margin_end(10)
        self.win.set_child(box)

        # Theme switch
        theme_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        theme_label = Gtk.Label(label="Dark Mode")
        theme_switch = Gtk.Switch()
        theme_switch.set_active(style_manager.get_dark())
        theme_switch.connect('state-set', self.on_theme_switch)
        theme_box.append(theme_label)
        theme_box.append(theme_switch)
        box.append(theme_box)

        # Status label
        self.status_label = Gtk.Label(label="Click Check Updates to begin")
        box.append(self.status_label)

        # Update list
        self.update_list = Gtk.ListBox()
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_child(self.update_list)
        box.append(scrolled)

        # Buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        box.append(button_box)

        check_button = Gtk.Button(label="Check Updates")
        check_button.connect('clicked', self.check_updates)
        button_box.append(check_button)

        update_button = Gtk.Button(label="Install Updates")
        update_button.connect('clicked', self.install_updates)
        button_box.append(update_button)

        self.win.present()

    def on_theme_switch(self, switch, state):
        style_manager = Adw.StyleManager.get_default()
        style_manager.set_color_scheme(
            Adw.ColorScheme.FORCE_DARK if state else Adw.ColorScheme.FORCE_LIGHT
        )

    def check_updates(self, button):
        self.status_label.set_text("Checking for updates...")
        # Clear previous list
        while self.update_list.get_first_child():
            self.update_list.remove(self.update_list.get_first_child())
            
        try:
            # Run pacman -Sy to sync repos
            subprocess.run(['sudo', 'pacman', '-Sy'], check=True)
            # Get list of updates
            result = subprocess.run(['pacman', '-Qu'], capture_output=True, text=True)
            
            if result.stdout:
                updates = result.stdout.strip().split('\n')
                for update in updates:
                    row = Gtk.ListBoxRow()
                    row.set_child(Gtk.Label(label=update))
                    self.update_list.append(row)
                self.status_label.set_text(f"Found {len(updates)} updates available")
            else:
                self.status_label.set_text("System is up to date!")
                
        except subprocess.CalledProcessError as e:
            self.status_label.set_text(f"Error checking updates: {str(e)}")

    def install_updates(self, button):
        self.status_label.set_text("Installing updates...")
        try:
            subprocess.Popen(['pkexec', 'pacman', '-Syu', '--noconfirm'])
            self.status_label.set_text("Updates installation started")
        except Exception as e:
            self.status_label.set_text(f"Error installing updates: {str(e)}")

if __name__ == '__main__':
    app = UpdateChecker()
    app.run(None)
