#!/usr/bin/env python3
import gi
import subprocess
import os
from pathlib import Path
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
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

        # Update list with output text view
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        
        self.output_view = Gtk.TextView()
        self.output_view.set_editable(False)
        self.output_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self.output_buffer = self.output_view.get_buffer()
        
        scrolled.set_child(self.output_view)
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
        self.output_buffer.set_text("")
            
        try:
            # Run pacman -Sy to sync repos
            process = subprocess.Popen(['sudo', 'pacman', '-Sy'], 
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    universal_newlines=True)
            
            def update_sync_output():
                if process.poll() is None:
                    output = process.stdout.readline()
                    if output:
                        end_iter = self.output_buffer.get_end_iter()
                        self.output_buffer.insert(end_iter, output)
                    return True
                
                if process.returncode == 0:
                    # After sync, check for updates
                    result = subprocess.run(['pacman', '-Qu'], capture_output=True, text=True)
                    if result.stdout:
                        updates = result.stdout.strip()
                        end_iter = self.output_buffer.get_end_iter()
                        self.output_buffer.insert(end_iter, "\nAvailable updates:\n" + updates)
                        self.status_label.set_text(f"Found {len(updates.split())} updates available")
                    else:
                        self.status_label.set_text("System is up to date!")
                else:
                    stderr = process.stderr.read()
                    end_iter = self.output_buffer.get_end_iter()
                    self.output_buffer.insert(end_iter, f"Error: {stderr}")
                return False
            
            GLib.timeout_add(100, update_sync_output)
                
        except Exception as e:
            self.status_label.set_text(f"Error checking updates: {str(e)}")

    def check_drivers(self, button):
        self.status_label.set_text("Checking drivers...")
        self.output_buffer.set_text("")
            
        try:
            # Check for missing drivers using lspci
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
                self.output_buffer.set_text(output_text)
                self.status_label.set_text(f"Found {len(missing_drivers)} devices without drivers")
            else:
                self.output_buffer.set_text("All devices have drivers installed!")
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
        self.output_buffer.set_text("")
        
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
            
            def update_driver_output():
                if process.poll() is None:
                    output = process.stdout.readline()
                    if output:
                        end_iter = self.output_buffer.get_end_iter()
                        self.output_buffer.insert(end_iter, output)
                    return True
                
                if process.returncode == 0:
                    self.status_label.set_text(f"Driver {driver} installed successfully!")
                    self.check_drivers(None)  # Refresh driver list
                else:
                    stderr = process.stderr.read()
                    end_iter = self.output_buffer.get_end_iter()
                    self.output_buffer.insert(end_iter, f"Error: {stderr}")
                return False
            
            GLib.timeout_add(100, update_driver_output)
            
        except Exception as e:
            self.status_label.set_text(f"Error installing driver: {str(e)}")

    def install_updates(self, button):
        self.status_label.set_text("Installing updates...")
        self.output_buffer.set_text("")
        
        try:
            # Run the update process and monitor output
            process = subprocess.Popen(['pkexec', 'pacman', '-Syu', '--noconfirm'], 
                                    stdout=subprocess.PIPE, 
                                    stderr=subprocess.PIPE,
                                    universal_newlines=True)
            
            def update_output():
                if process.poll() is None:
                    output = process.stdout.readline()
                    if output:
                        end_iter = self.output_buffer.get_end_iter()
                        self.output_buffer.insert(end_iter, output)
                    return True
                
                if process.returncode == 0:
                    self.status_label.set_text("Updates installed successfully!")
                else:
                    stderr = process.stderr.read()
                    end_iter = self.output_buffer.get_end_iter()
                    self.output_buffer.insert(end_iter, f"Error: {stderr}")
                return False
            
            GLib.timeout_add(100, update_output)
            
        except Exception as e:
            self.status_label.set_text(f"Error installing updates: {str(e)}")

if __name__ == '__main__':
    app = UpdateChecker()
    app.run(None)
