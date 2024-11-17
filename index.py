import gi
import subprocess
import threading
import time

gi.require_version('Gtk', '3.0')
gi.require_version('Notify', '0.7')

from gi.repository import Gtk, GLib, Notify

class AppWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="Arch Linux System Update")
        
        self.set_default_size(400, 300)
        
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
        
        # Create a text view to display logs
        self.log_view = Gtk.TextView()
        self.log_view.set_editable(False)
        self.log_buffer = self.log_view.get_buffer()
        log_scrolled_window = Gtk.ScrolledWindow()
        log_scrolled_window.add(self.log_view)
        box.pack_start(log_scrolled_window, True, True, 0)
        
        # Initialize notification library
        Notify.init("Arch Linux Update")

        # Prepare to capture output and error in real-time
        self.update_process = None
        self.stdout_output = ""
        self.stderr_output = ""

    def on_update_button_clicked(self, button):
        self.append_to_log("Starting Arch Linux update...\n")
        
        # Get password from the password entry
        password = self.password_entry.get_text().strip()
        if not password:
            self.append_to_log("Password field is empty. Please enter a password.\n")
            self.send_notification("Arch Linux Update", "Password field is empty.")
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
            self.send_notification("Arch Linux Update", "Update in progress...")
            
            # Start capturing output in real-time
            while True:
                # Read stdout and stderr
                stdout_line = self.update_process.stdout.readline()
                stderr_line = self.update_process.stderr.readline()
                
                # If the process has finished and no output is left, break
                if not stdout_line and not stderr_line and self.update_process.poll() is not None:
                    break
                
                if stdout_line:
                    self.stdout_output += stdout_line.decode()
                if stderr_line:
                    self.stderr_output += stderr_line.decode()
                
                # Update the log
                GLib.idle_add(self.update_log)
                
                # Pause for a short time to simulate millisecond updates
                time.sleep(0.001)

            # Send notification when update finishes successfully
            self.send_notification("Arch Linux Update", "Update process finished successfully.")

        except Exception as e:
            self.append_to_log(f"Error during update: {str(e)}\n")
            self.send_notification("Arch Linux Update", f"Error: {str(e)}")

    def update_log(self):
        """Update the log view with the new captured output."""
        # Update log with stdout and stderr content
        if self.stdout_output:
            self.append_to_log(self.stdout_output)
            self.stdout_output = ""  # Clear the stdout buffer
        
        if self.stderr_output:
            self.append_to_log(self.stderr_output)
            self.stderr_output = ""  # Clear the stderr buffer

    def append_to_log(self, message):
        # Get the current text in the log
        current_text = self.log_buffer.get_text(self.log_buffer.get_start_iter(), self.log_buffer.get_end_iter(), False)
        
        # Append new log message
        self.log_buffer.set_text(current_text + message)

    def send_notification(self, title, message):
        """Send a notification using libnotify."""
        notification = Notify.Notification.new(title, message)
        notification.show()

def main():
    window = AppWindow()
    window.connect("destroy", Gtk.main_quit)
    window.show_all()
    Gtk.main()

if __name__ == "__main__":
    main()
