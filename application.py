import gi
import subprocess
import threading
import time
import platform
gi.require_version('Gtk', '3.0')
gi.require_version('Notify', '0.7')
from gi.repository import Gtk, GLib, Notify

class AppWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="Arch Linux System Update")
        
        self.set_default_size(400, 300)
        
        # Detect the operating system
        self.detected_os = self.detect_os()
        self.show_os_popup(self.detected_os)

        # Create a box to pack widgets
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(box)
        
        # Create a password entry box
        password_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        password_label = Gtk.Label(label="Password:")
        self.password_entry = Gtk.Entry()
        self.password_entry.set_visibility(False)  # Hide the password text
        self.password_entry.set_placeholder_text("Enter your sudo password")
        password_box.pack_start(password_label, False, False, 0)
        password_box.pack_start(self.password_entry, True, True, 0)
        box.pack_start(password_box, False, False, 10)
        
        # Create a button to trigger the system update
        self.update_button = Gtk.Button(label="Update Arch Linux")
        self.update_button.connect("clicked", self.on_update_button_clicked)
        box.pack_start(self.update_button, False, False, 10)
        
        # Create a button to reload the application
        self.reload_button = Gtk.Button(label="Reload Application")
        self.reload_button.connect("clicked", self.on_reload_button_clicked)
        box.pack_start(self.reload_button, False, False, 10)
        
        # Create a text view to display logs
        self.log_view = Gtk.TextView()
        self.log_view.set_editable(False)
        self.log_buffer = self.log_view.get_buffer()
        log_scrolled_window = Gtk.ScrolledWindow()
        log_scrolled_window.add(self.log_view)
        box.pack_start(log_scrolled_window, True, True, 0)
        
        # Initialize notification library
        Notify.init("Arch Linux Update")

    def detect_os(self):
        """Detect the operating system."""
        return platform.system()

    def show_os_popup(self, os_name):
        """Show a popup dialog with the detected operating system."""
        dialog = Gtk.MessageDialog(
            parent=self,
            flags=Gtk.DialogFlags.MODAL,
            type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            message_format=f"Detected Operating System: {os_name}"
        )
        dialog.format_secondary_text(
            "This application is intended for Arch Linux. "
            "Functionality may vary on other systems."
        )
        dialog.run()
        dialog.destroy()

    def on_update_button_clicked(self, button):
        self.append_to_log("Starting Arch Linux update...\n")
        
        # Get password from the password entry
        password = self.password_entry.get_text().strip()
        if not password:
            self.append_to_log("Password field is empty. Please enter a password.\n")
            self.send_notification("Arch Linux Update", "Password field is empty.", "dialog-error")
            return
        
        # Run system update in a separate thread with the entered password
        threading.Thread(target=self.run_update_process, args=(password,), daemon=True).start()

    def run_update_process(self, password):
        try:
            # Run the update command using the provided password
            self.update_process = subprocess.Popen(
                ['sudo', '-S', 'pacman', '-Syu', '--noconfirm'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Send password to the subprocess
            self.update_process.stdin.write(f"{password}\n".encode())
            self.update_process.stdin.flush()

            # Send notification about update progress
            self.send_notification("Arch Linux Update", "Update in progress...", "system-software-update")
            
            # Start capturing output in real-time
            while True:
                # Read stdout and stderr
                stdout_line = self.update_process.stdout.readline()
                stderr_line = self.update_process.stderr.readline()
                
                # If the process has finished and no output is left, break
                if not stdout_line and not stderr_line and self.update_process.poll() is not None:
                    break
                
                if stdout_line:
                    GLib.idle_add(self.append_to_log, stdout_line.decode())
                if stderr_line:
                    GLib.idle_add(self.append_to_log, stderr_line.decode())
                
                # Pause for a short time to simulate millisecond updates
                time.sleep(0.001)

            # Send notification when update finishes successfully
            self.send_notification("Arch Linux Update", "Update process finished successfully.", "dialog-information")

        except Exception as e:
            self.append_to_log(f"Error during update: {str(e)}\n")
            self.send_notification("Arch Linux Update", f"Error: {str(e)}", "dialog-error")

    def on_reload_button_clicked(self, button):
        """Reload the application."""
        self.append_to_log("Reloading application...\n")
        self.send_notification("Arch Linux Update", "Reloading application...", "dialog-information")
        script_path = './upgrade.sh'
        subprocess.run(['bash', script_path], check=False)

    def append_to_log(self, message):
        """Append text to the log view."""
        # Get the current text in the log
        current_text = self.log_buffer.get_text(self.log_buffer.get_start_iter(), self.log_buffer.get_end_iter(), False)
        
        # Append new log message
        self.log_buffer.set_text(current_text + message)

    def send_notification(self, title, message, icon="dialog-information"):
        """Send a notification using libnotify."""
        notification = Notify.Notification.new(title, message, icon)
        notification.show()

def main():
    window = AppWindow()
    window.connect("destroy", Gtk.main_quit)
    window.show_all()
    Gtk.main()

if __name__ == "__main__":
    main()