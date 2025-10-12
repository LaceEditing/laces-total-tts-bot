import tkinter as tk
from PIL import Image, ImageTk
from pathlib import Path


class AvatarWindow:
    def __init__(self, idle_image_path=None, speaking_image_path=None,
                 bg_color='#00FF00', transparent=False, always_on_top=True):
        """
        Create a dedicated avatar window for OBS capture

        Args:
            idle_image_path: Path to idle avatar image
            speaking_image_path: Path to speaking avatar image
            bg_color: Background color (default: green screen #00FF00)
            transparent: Use transparent background (Windows only, experimental)
            always_on_top: Keep window on top of other windows
        """
        self.window = tk.Toplevel()
        self.window.title("🎙️ AI Avatar")
        self.window.geometry("400x400")

        # Window settings
        if always_on_top:
            self.window.attributes('-topmost', True)

        # Try to make window transparent (Windows only)
        if transparent:
            try:
                self.window.attributes('-transparentcolor', bg_color)
            except:
                print("[Avatar] Transparency not supported on this platform")

        self.window.configure(bg=bg_color)

        # Store paths
        self.idle_path = idle_image_path
        self.speaking_path = speaking_image_path

        # Current state
        self.is_speaking = False

        # Create label for image display
        self.image_label = tk.Label(
            self.window,
            bg=bg_color,
            text="No Avatar Loaded\n\nConfigure in Avatar tab",
            font=('Arial', 14),
            fg='white'
        )
        self.image_label.pack(expand=True, fill='both')

        # Store PhotoImage references to prevent garbage collection
        self.idle_photo = None
        self.speaking_photo = None

        # Load images if provided
        if idle_image_path:
            self.load_images(idle_image_path, speaking_image_path)

        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self.hide)

        # Bind resize event to update image size
        self.window.bind('<Configure>', self.on_resize)

    def load_images(self, idle_path, speaking_path):
        """Load idle and speaking images"""
        self.idle_path = idle_path
        self.speaking_path = speaking_path

        try:
            # Load idle image
            if idle_path and Path(idle_path).exists():
                self.idle_photo = self.load_and_resize_image(idle_path)

            # Load speaking image
            if speaking_path and Path(speaking_path).exists():
                self.speaking_photo = self.load_and_resize_image(speaking_path)

            # Display initial image (idle)
            self.show_idle()

        except Exception as e:
            self.image_label.config(
                text=f"Error loading images:\n{e}",
                image=''
            )

    def load_and_resize_image(self, image_path):
        """Load image and resize to fit window"""
        img = Image.open(image_path)

        # Get current window size
        window_width = self.window.winfo_width()
        window_height = self.window.winfo_height()

        # Use default size if window not yet displayed
        if window_width <= 1:
            window_width = 400
            window_height = 400

        # Resize image to fit window while maintaining aspect ratio
        img.thumbnail((window_width, window_height), Image.Resampling.LANCZOS)

        return ImageTk.PhotoImage(img)

    def on_resize(self, event):
        """Handle window resize - reload images to fit new size"""
        # Only process resize events for the main window, not child widgets
        if event.widget == self.window:
            # Reload images at new size
            if self.idle_path and self.speaking_path:
                try:
                    self.idle_photo = self.load_and_resize_image(self.idle_path)
                    self.speaking_photo = self.load_and_resize_image(self.speaking_path)

                    # Refresh current display
                    if self.is_speaking:
                        self.show_speaking()
                    else:
                        self.show_idle()
                except:
                    pass  # Ignore resize errors during window creation

    def show_idle(self):
        """Display idle image"""
        self.is_speaking = False
        if self.idle_photo:
            self.image_label.config(image=self.idle_photo, text='')
            self.window.title("🎙️ AI Avatar - Idle")
        else:
            self.image_label.config(text="Idle\n(No image loaded)")

    def show_speaking(self):
        """Display speaking image"""
        self.is_speaking = True
        if self.speaking_photo:
            self.image_label.config(image=self.speaking_photo, text='')
            self.window.title("🎙️ AI Avatar - Speaking")
        else:
            self.image_label.config(text="Speaking!\n(No image loaded)")

    def show(self):
        """Show the avatar window"""
        self.window.deiconify()

    def hide(self):
        """Hide (minimize) the avatar window"""
        self.window.withdraw()

    def toggle(self):
        """Toggle window visibility"""
        if self.window.state() == 'normal':
            self.hide()
        else:
            self.show()

    def destroy(self):
        """Destroy the window"""
        self.window.destroy()

    def is_visible(self):
        """Check if window is visible"""
        return self.window.state() == 'normal'


# Test the avatar window
if __name__ == '__main__':
    import time

    root = tk.Tk()
    root.withdraw()  # Hide main window

    # Test with placeholder images (replace with actual paths)
    avatar = AvatarWindow(
        idle_image_path="images/Idle.png",
        speaking_image_path="images/speaking.png",
        bg_color='#00FF00',  # Green screen for OBS
        always_on_top=True
    )

    # Simulate speaking/idle cycle
    def test_cycle():
        avatar.show_idle()
        root.after(2000, lambda: test_speaking())

    def test_speaking():
        avatar.show_speaking()
        root.after(2000, lambda: test_cycle())

    root.after(1000, test_cycle)

    root.mainloop()