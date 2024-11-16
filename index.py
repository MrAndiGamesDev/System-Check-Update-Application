#!/usr/bin/env python3
import gi
import subprocess
import os
from pathlib import Path
import threading
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, GLib, Adw, Gdk

class UpdateChecker(Gtk.Application):
    def __init__(self):
        super().__init__(application_id='com.example.archupdate')
        self.connect('activate', self.on_activate)

    def on_activate(self, app):
        self.win = Gtk.ApplicationWindow(application=app)
        self.win.set_title('Arch Update Checker')
        self.win.set_default_size(600, 500)
        self.win.set_resizable(True)  # Allow window to be resized

        # Create style manager for dark mode
        style_manager = Adw.StyleManager.get_default()

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_vexpand(True)
        self.win.set_child(scrolled_window)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(10)
        box.set_margin_bottom(10)
        box.set_margin_start(10)
        box.set_margin_end(10)
        scrolled_window.set_child(box)

        # Theme switch
        theme_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        theme_label = Gtk.Label(label="Dark Mode")
        theme_switch = Gtk.Switch()
        theme_switch.set_active(style_manager.get_dark())
        theme_switch.connect('state-set', self.on_theme_switch)
        theme_box.append(theme_label)
        theme_box.append(theme_switch)
        box.append(theme_box)

        # System information label
        try:
            kernel = subprocess.run(['uname', '-r'], capture_output=True, text=True).stdout.strip()
            system_info = f"Kernel: {kernel}"
            system_label = Gtk.Label(label=system_info)
            box.append(system_label)

            # Driver information
            drivers = subprocess.run(['lspci', '-k'], capture_output=True, text=True).stdout.strip()
            driver_info = "Drivers in use:\n" + "\n".join([line for line in drivers.split('\n') if 'Kernel driver in use:' in line])
            self.driver_label = Gtk.Label(label=driver_info)
            self.driver_label.set_wrap(True)
            self.driver_label.set_xalign(0)
            box.append(self.driver_label)
            
            # Additional driver information from hwinfo
            try:
                hw_info = subprocess.run(['hwinfo', '--short'], capture_output=True, text=True).stdout.strip()
                self.hw_label = Gtk.Label(label="Hardware Information:\n" + hw_info)
                self.hw_label.set_wrap(True)
                self.hw_label.set_xalign(0)
                box.append(self.hw_label)
            except FileNotFoundError:
                # hwinfo might not be installed
                install_hwinfo_button = Gtk.Button(label="Install hwinfo")
                install_hwinfo_button.connect('clicked', self.install_hwinfo)
                box.append(install_hwinfo_button)

        except subprocess.CalledProcessError:
            system_label = Gtk.Label(label="Could not fetch system information")
            box.append(system_label)

        # Status label
        self.status_label = Gtk.Label(label="Click Check Updates to begin")
        box.append(self.status_label)

        # Update list with output text view
        self.output_view = Gtk.TextView()
        self.output_view.set_editable(False)
        self.output_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self.output_buffer = self.output_view.get_buffer()
        self.output_scrolled_window = Gtk.ScrolledWindow()
        self.output_scrolled_window.set_vexpand(True)
        self.output_scrolled_window.set_child(self.output_view)
        box.append(self.output_scrolled_window)

        # Buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        box.append(button_box)

        check_button = Gtk.Button(label="Check Updates")
        check_button.connect('clicked', self.check_updates)
        button_box.append(check_button)

        update_button = Gtk.Button(label="Install Updates")
        update_button.connect('clicked', self.install_updates)
        button_box.append(update_button)

        driver_button = Gtk.Button(label="Check Drivers")
        driver_button.connect('clicked', self.check_drivers)
        button_box.append(driver_button)

        install_button = Gtk.Button(label="Install hwinfo")
        install_button.connect('clicked', self.install_hwinfo)
        button_box.append(install_button)

        self.win.present()

    def on_theme_switch(self, switch, state):
        style_manager = Adw.StyleManager.get_default()
        style_manager.set_color_scheme(
            Adw.ColorScheme.FORCE_DARK if state else Adw.ColorScheme.FORCE_LIGHT
        )

    def check_updates(self, button):
        self.status_label.set_text("Checking for updates...")
        self.output_buffer.set_text("")

        def update_task():
            try:
                # Run pacman -Sy to sync repos
                process = subprocess.Popen(['sudo', 'pacman', '-Sy'], 
                                           stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE,
                                           universal_newlines=True)
                
                output, error = process.communicate()

                if process.returncode == 0:
                    # After sync, check for updates
                    result = subprocess.run(['pacman', '-Qu'], capture_output=True, text=True)
                    if result.stdout:
                        updates = result.stdout.strip()
                        GLib.idle_add(self.update_output, "\nAvailable updates:\n" + updates)
                        self.status_label.set_text(f"Found {len(updates.split())} updates available")
                    else:
                        GLib.idle_add(self.update_output, "System is up to date!")
                else:
                    GLib.idle_add(self.update_output, f"Error syncing: {error}")
            except Exception as e:
                GLib.idle_add(self.update_output, f"Error checking updates: {str(e)}")

        threading.Thread(target=update_task, daemon=True).start()

    def check_drivers(self, button):
        self.status_label.set_text("Checking drivers...")
        self.output_buffer.set_text("")

        def driver_task():
            try:
                result = subprocess.run(['lspci', '-k'], capture_output=True, text=True)
                devices = result.stdout.strip().split('\n\n')
                missing_drivers = []

                for device in devices:
                    if 'Kernel driver in use:' not in device:
                        missing_drivers.append(device.split('\n')[0])

                if missing_drivers:
                    output_text = "Devices missing drivers:\n\n"
                    for device in missing_drivers:
                        output_text += f"• {device}\n"
                    GLib.idle_add(self.update_output, output_text)
                    self.status_label.set_text(f"Found {len(missing_drivers)} devices without drivers")
                else:
                    GLib.idle_add(self.update_output, "All devices have drivers installed!")
                    self.status_label.set_text("All devices have drivers installed!")
            except subprocess.CalledProcessError as e:
                GLib.idle_add(self.update_output, f"Error checking drivers: {str(e)}")

        threading.Thread(target=driver_task, daemon=True).start()

    def update_output(self, text):
        end_iter = self.output_buffer.get_end_iter()
        self.output_buffer.insert(end_iter, text)

    def install_updates(self, button):
        self.status_label.set_text("Installing updates...")
        self.output_buffer.set_text("")

        def update_task():
            try:
                process = subprocess.Popen(['pkexec', 'pacman', '-Syu', '--noconfirm'], 
                                           stdout=subprocess.PIPE, 
                                           stderr=subprocess.PIPE,
                                           universal_newlines=True)
                output, error = process.communicate()

                if process.returncode == 0:
                    GLib.idle_add(self.update_output, "Updates installed successfully!")
                else:
                    GLib.idle_add(self.update_output, f"Error installing updates: {error}")
            except Exception as e:
                GLib.idle_add(self.update_output, f"Error installing updates: {str(e)}")

        threading.Thread(target=update_task, daemon=True).start()

    def install_hwinfo(self, button):
        self.status_label.set_text("Installing hwinfo...")
        self.output_buffer.set_text("")

        def install_hwinfo_task():
            try:
                process = subprocess.Popen(['pkexec', 'pacman', '-S', '--noconfirm', 'hwinfo'], 
                                           stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE,
                                           universal_newlines=True)
                output, error = process.communicate()

                if process.returncode == 0:
                    GLib.idle_add(self.update_output, "hwinfo installed successfully!")
                    self.check_drivers(None)  # Refresh driver list
                else:
                    GLib.idle_add(self.update_output, f"Error installing hwinfo: {error}")
            except Exception as e:
                GLib.idle_add(self.update_output, f"Error installing hwinfo: {str(e)}")

        threading.Thread(target=install_hwinfo_task, daemon=True).start()

if __name__ == '__main__':
    app = UpdateChecker()
    app.run(None)
