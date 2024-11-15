#!/usr/bin/env python3
import gi
import subprocess
import os
from pathlib import Path
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib, Adw, Gio

class UpdateChecker(Gtk.Application):
    def __init__(self):
        super().__init__(application_id='com.example.archupdate')
        self.connect('activate', self.on_activate)

    def on_activate(self, app):
        self.win = Gtk.ApplicationWindow(application=app)
        self.win.set_title('Arch Update Checker')
        self.win.set_default_size(600, 500)
            
        # Create style manager for dark mode
        style_manager = Adw.StyleManager.get_default()

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(10)
        box.set_margin_bottom(10)
        box.set_margin_start(10)
        box.set_margin_end(10)
        self.win.set_child(box)

        # System information label
        try:
            result = subprocess.run(['uname', '-r'], capture_output=True, text=True)
            kernel = result.stdout.strip()
            system_info = f"Kernel: {kernel}"
            system_label = Gtk.Label(label=system_info)
            box.append(system_label)

            # Driver information
            driver_result = subprocess.run(['lspci', '-k'], capture_output=True, text=True)
            drivers = driver_result.stdout.strip()
            driver_info = "Drivers in use:\n" + "\n".join([line for line in drivers.split('\n') if 'Kernel driver in use:' in line])
            self.driver_label = Gtk.Label(label=driver_info)
            self.driver_label.set_wrap(True)
            self.driver_label.set_xalign(0)
            box.append(self.driver_label)
            
            # Additional driver information from hwinfo
            try:
                hwinfo_result = subprocess.run(['hwinfo', '--short'], capture_output=True, text=True)
                hw_info = hwinfo_result.stdout.strip()
                self.hw_label = Gtk.Label(label="Hardware Information:\n" + hw_info)
                self.hw_label.set_wrap(True)
                self.hw_label.set_xalign(0)
                box.append(self.hw_label)
            except FileNotFoundError:
                # hwinfo might not be installed
                pass

        except subprocess.CalledProcessError:
            system_label = Gtk.Label(label="Could not fetch system information")
            box.append(system_label)

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

        # Add driver check button
        driver_button = Gtk.Button(label="Check Drivers")
        driver_button.connect('clicked', self.check_drivers)
        button_box.append(driver_button)

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

    def check_drivers(self, button):
        self.status_label.set_text("Checking drivers...")
        while self.update_list.get_first_child():
            self.update_list.remove(self.update_list.get_first_child())
            
        try:
            # Check for missing drivers using lspci
            result = subprocess.run(['lspci', '-k'], capture_output=True, text=True)
            devices = result.stdout.strip().split('\n\n')
            missing_drivers = []
            
            for device in devices:
                if 'Kernel driver in use:' not in device:
                    missing_drivers.append(device.split('\n')[0])
            
            if missing_drivers:
                for device in missing_drivers:
                    row = Gtk.ListBoxRow()
                    label = Gtk.Label(label=f"Missing driver for: {device}")
                    button = Gtk.Button(label="Install Driver")
                    button.connect('clicked', lambda btn, dev=device: self.install_driver(dev))
                    box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
                    box.append(label)
                    box.append(button)
                    row.set_child(box)
                    self.update_list.append(row)
                self.status_label.set_text(f"Found {len(missing_drivers)} devices without drivers")
            else:
                self.status_label.set_text("All devices have drivers installed!")
                
            # Update driver information display
            driver_result = subprocess.run(['lspci', '-k'], capture_output=True, text=True)
            drivers = driver_result.stdout.strip()
            driver_info = "Drivers in use:\n" + "\n".join([line for line in drivers.split('\n') if 'Kernel driver in use:' in line])
            self.driver_label.set_text(driver_info)
                
        except subprocess.CalledProcessError as e:
            self.status_label.set_text(f"Error checking drivers: {str(e)}")

    def install_driver(self, device):
        self.status_label.set_text(f"Installing driver for {device}...")
        try:
            # Determine appropriate driver package based on device
            if "VGA" in device or "Display" in device:
                if "Intel" in device:
                    driver = "xf86-video-intel"
                elif "NVIDIA" in device:
                    driver = "nvidia"
                elif "AMD" in device or "ATI" in device:
                    driver = "xf86-video-amdgpu"
                else:
                    driver = "xf86-video-vesa"  # Generic fallback
            elif "Audio" in device:
                driver = "alsa-utils pulseaudio"
            elif "Network" in device:
                if "Wireless" in device:
                    driver = "wireless-tools wpa_supplicant"
                else:
                    driver = "networkmanager"
            else:
                self.status_label.set_text(f"Could not determine appropriate driver for: {device}")
                return

            # Run pacman to install the specific driver
            process = subprocess.Popen(['pkexec', 'pacman', '-S', '--noconfirm'] + driver.split(), 
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    universal_newlines=True)
            
            def update_driver_status():
                if process.poll() is None:
                    return True
                
                if process.returncode == 0:
                    self.status_label.set_text(f"Driver {driver} installed successfully!")
                    self.check_drivers(None)  # Refresh driver list
                else:
                    stderr = process.stderr.read()
                    self.status_label.set_text(f"Error installing driver: {stderr}")
                return False
            
            GLib.timeout_add(100, update_driver_status)
            
        except Exception as e:
            self.status_label.set_text(f"Error installing driver: {str(e)}")

    def install_updates(self, button):
        self.status_label.set_text("Installing updates...")
        try:
            # Run the update process and monitor output
            process = subprocess.Popen(['pkexec', 'pacman', '-Syu', '--noconfirm'], 
                                    stdout=subprocess.PIPE, 
                                    stderr=subprocess.PIPE,
                                    universal_newlines=True)
            
            def update_status():
                if process.poll() is None:
                    # Process still running
                    return True
                
                # Process finished
                if process.returncode == 0:
                    self.status_label.set_text("Updates installed successfully!")
                else:
                    stderr = process.stderr.read()
                    self.status_label.set_text(f"Error installing updates: {stderr}")
                return False
            
            # Check status every 100ms
            GLib.timeout_add(100, update_status)
            
        except Exception as e:
            self.status_label.set_text(f"Error installing updates: {str(e)}")

if __name__ == '__main__':
    app = UpdateChecker()
    app.run(None)
