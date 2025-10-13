import tkinter as tk
from PIL import Image, ImageTk
from pathlib import Path


class AvatarWindow:
    def __init__(self, idle_image_path=None, speaking_image_path=None,
                 bg_color='#00FF00', transparent=False, always_on_top=True):
        """
        Create a dedicated avatar window for OBS capture
        """
        self.window = tk.Toplevel()
        self.window.title("The Talking Mouth")
        self.window.geometry("400x400")

        # Window settings
        if always_on_top:
            self.window.attributes('-topmost', True)

        # Try transparency (Windows only)
        if transparent:
            try:
                self.window.attributes('-transparentcolor', bg_color)
            except:
                print("[Avatar] Transparency not supported")

        self.window.configure(bg=bg_color)

        # Store paths
        self.idle_path = idle_image_path
        self.speaking_path = speaking_image_path

        # Current state
        self.is_speaking = False
        self.is_initialized = False

        # Create label for image display
        self.image_label = tk.Label(
            self.window,
            bg=bg_color,
            text="No Avatar Loaded\n\nConfigure in Avatar tab",
            font=('Arial', 14),
            fg='white'
        )
        self.image_label.pack(expand=True, fill='both')

        # Store PhotoImage references (prevent garbage collection)
        self.idle_photo = None
        self.speaking_photo = None

        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self.hide)

        # Wait for window to be ready before loading images
        self.window.update_idletasks()

        # Load images if provided
        if idle_image_path and speaking_image_path:
            # Give the window time to initialize
            self.window.after(100, lambda: self.load_images(idle_image_path, speaking_image_path))

        # Bind resize AFTER initial load to avoid issues
        self.window.after(200, lambda: self.window.bind('<Configure>', self.on_resize))

    def load_images(self, idle_path, speaking_path):
        """Load idle and speaking images"""
        print(f"[Avatar] Loading images...")
        print(f"[Avatar] Idle: {idle_path}")
        print(f"[Avatar] Speaking: {speaking_path}")

        self.idle_path = idle_path
        self.speaking_path = speaking_path

        try:
            # Verify files exist
            if not Path(idle_path).exists():
                error_msg = f"Idle image not found: {idle_path}"
                print(f"[Avatar] ERROR: {error_msg}")
                self.image_label.config(text=f"❌ Error:\n{error_msg}", fg='#FF6B6B')
                return False

            if not Path(speaking_path).exists():
                error_msg = f"Speaking image not found: {speaking_path}"
                print(f"[Avatar] ERROR: {error_msg}")
                self.image_label.config(text=f"❌ Error:\n{error_msg}", fg='#FF6B6B')
                return False

            # Load idle image
            print(f"[Avatar] Loading idle image...")
            self.idle_photo = self.load_and_resize_image(idle_path)
            if not self.idle_photo:
                raise Exception("Failed to load idle image")

            # Load speaking image
            print(f"[Avatar] Loading speaking image...")
            self.speaking_photo = self.load_and_resize_image(speaking_path)
            if not self.speaking_photo:
                raise Exception("Failed to load speaking image")

            # Display initial image (idle)
            self.show_idle()
            self.is_initialized = True

            print(f"[Avatar] ✅ Images loaded successfully!")
            return True

        except Exception as e:
            error_msg = f"Error loading images: {str(e)}"
            print(f"[Avatar] ERROR: {error_msg}")
            import traceback
            traceback.print_exc()

            self.image_label.config(
                text=f"❌ Error:\n{str(e)}",
                image='',
                fg='#FF6B6B'
            )
            return False

    def load_and_resize_image(self, image_path):
        """Load image and resize to fit window"""
        try:
            print(f"[Avatar] Opening image: {image_path}")
            img = Image.open(image_path)
            print(f"[Avatar] Image opened: {img.size}")

            # Force window update to get correct size
            self.window.update_idletasks()

            # Get current window size
            window_width = self.window.winfo_width()
            window_height = self.window.winfo_height()

            # Use default size if window not yet displayed
            if window_width <= 1 or window_height <= 1:
                window_width = 400
                window_height = 400
                print(f"[Avatar] Using default size: {window_width}x{window_height}")
            else:
                print(f"[Avatar] Using window size: {window_width}x{window_height}")

            # Resize image to fit window while maintaining aspect ratio
            img.thumbnail((window_width - 20, window_height - 20), Image.Resampling.LANCZOS)
            print(f"[Avatar] Image resized to: {img.size}")

            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(img)
            print(f"[Avatar] PhotoImage created")

            return photo

        except Exception as e:
            print(f"[Avatar] ERROR loading/resizing image: {e}")
            import traceback
            traceback.print_exc()
            return None

    def on_resize(self, event):
        """Handle window resize - reload images to fit new size"""
        # Only process resize events for the main window, not child widgets
        if event.widget != self.window:
            return

        # Don't reload during initial setup
        if not self.is_initialized:
            return

        # Reload images at new size
        if self.idle_path and self.speaking_path:
            try:
                print(f"[Avatar] Window resized, reloading images...")
                self.idle_photo = self.load_and_resize_image(self.idle_path)
                self.speaking_photo = self.load_and_resize_image(self.speaking_path)

                # Refresh current display
                if self.is_speaking:
                    self.show_speaking()
                else:
                    self.show_idle()
            except Exception as e:
                print(f"[Avatar] Error during resize: {e}")

    def show_idle(self):
        """Display idle image"""
        self.is_speaking = False
        if self.idle_photo:
            self.image_label.config(image=self.idle_photo, text='', fg='white')
            self.window.title("The Talking Mouth")
            print("[Avatar] Showing idle image")
        else:
            self.image_label.config(text="Idle\n(No image loaded)", fg='white')
            print("[Avatar] No idle image to show")

    def show_speaking(self):
        """Display speaking image"""
        self.is_speaking = True
        if self.speaking_photo:
            self.image_label.config(image=self.speaking_photo, text='', fg='white')
            self.window.title("The Talking Mouth")
            print("[Avatar] Showing speaking image")
        else:
            self.image_label.config(text="Speaking!\n(No image loaded)", fg='white')
            print("[Avatar] No speaking image to show")

    def show(self):
        """Show the avatar window"""
        self.window.deiconify()
        print("[Avatar] Window shown")

    def hide(self):
        """Hide (minimize) the avatar window"""
        self.window.withdraw()
        print("[Avatar] Window hidden")

    def toggle(self):
        """Toggle window visibility"""
        if self.window.state() == 'normal':
            self.hide()
        else:
            self.show()

    def destroy(self):
        """Destroy the window"""
        self.window.destroy()
        print("[Avatar] Window destroyed")

    def is_visible(self):
        """Check if window is visible"""
        return self.window.state() == 'normal'