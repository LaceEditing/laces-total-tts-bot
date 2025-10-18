import os
import sys
import time
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import keyboard
import threading
from pathlib import Path
from chatbot_engine import ChatbotEngine
from PIL import Image, ImageTk
from dotenv import load_dotenv, set_key
import updater

VERSION_NUMBER = updater.CURRENT_VERSION

def get_resource_path(relative_path):
    """Get path that works in both script and PyInstaller exe"""
    try:
        base_path = sys._MEIPASS  # PyInstaller temp folder
    except Exception:
        base_path = os.path.abspath(".")  # Normal script
    return os.path.join(base_path, relative_path)

class IntegratedChatbotApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Hey besties let's commmune with robots (v{VERSION_NUMBER})")
        self.root.geometry("900x900")
        self.root.minsize(750, 800)

        self.env_file = Path('.env')
        if self.env_file.exists():
            load_dotenv(self.env_file)
            print("[App] Loaded environment variables from .env file")
        else:
            print("[App] No .env file found, creating one...")
            self.create_default_env_file()
            load_dotenv(self.env_file)

        # LAVENDER THEME - Original colors
        self.colors = {
            'bg': '#E6E6FA',
            'fg': '#4B0082',
            'accent': '#9370DB',
            'button': '#8A7BC4',
            'entry_bg': '#F8F8FF',
            'text_bg': '#FFFFFF'
        }

        # Load custom UI font
        self.ui_font = self.load_custom_font('Quicksand-Regular.ttf', 10, 'normal')
        self.ui_font_bold = self.load_custom_font('Quicksand-Bold.ttf', 10, 'bold')
        self.ui_font_large = self.load_custom_font('Quicksand-Medium.ttf', 11, 'normal')

        self.root.configure(bg=self.colors['bg'])

        self.set_window_icon()

        self.root.after(1, self.set_title_bar_color)
        self.create_menu_bar()
        self.root.after(1000, self.check_for_updates)


        self.engine = ChatbotEngine()
        self.engine.on_volume_update = lambda vol: self.update_audio_meter(vol) if hasattr(self,
                                                                                           'update_audio_meter') else None
        self.config = self.engine.config

        self.is_recording = False
        self.hotkey_active = False

        self.voice_options = {
            'elevenlabs': [],
            'streamelements': [
                'Brian', 'Ivy', 'Justin', 'Russell', 'Nicole', 'Emma',
                'Amy', 'Joanna', 'Salli', 'Kimberly', 'Kendra', 'Joey',
                'Matthew', 'Geraint', 'Raveena',
            ],
            'azure': [
                'en-US-JennyNeural (Female, Friendly)',
                'en-US-GuyNeural (Male, Conversational)',
                'en-US-AriaNeural (Female, Cheerful)',
                'en-US-DavisNeural (Male, Professional)',
                'en-US-JaneNeural (Female, Calm)',
                'en-US-JasonNeural (Male, Energetic)',
                'en-US-SaraNeural (Female, Soft)',
                'en-US-TonyNeural (Male, Authoritative)',
                'en-US-NancyNeural (Female, Warm)',
                'en-US-AmberNeural (Female, Young)',
                'en-GB-SoniaNeural (British Female)',
                'en-GB-RyanNeural (British Male)',
                'en-AU-NatashaNeural (Australian Female)',
                'en-AU-WilliamNeural (Australian Male)',
            ],
        }
        self.create_gui()

        self.engine.on_response_callback = self.display_response
        self.engine.on_speaking_start = self.on_ai_speaking_start
        self.engine.on_speaking_end = self.on_ai_speaking_end
        self.engine.on_volume_update = self.update_audio_meter

        self.show_welcome_message()

        self.root.after(1000, self.auto_load_elevenlabs_voices)

    def load_custom_font(self, font_name, size, weight='normal'):
        """Load custom font - Windows compatible version"""
        try:
            import ctypes
            from ctypes import wintypes

            font_path = Path(get_resource_path('fonts')) / font_name

            if font_path.exists():
                gdi32 = ctypes.WinDLL('gdi32', use_last_error=True)
                result = gdi32.AddFontResourceExW(
                    str(font_path.absolute()),
                    0x10,
                    0
                )

                if result > 0:
                    print(f"[App] Loaded custom font: {font_name}")
                    # Map filename to font family name
                    font_families = {
                        'BubblegumSans-Regular.ttf': 'Bubblegum Sans',
                        'Quicksand-Regular.ttf': 'Quicksand',
                        'Quicksand-Medium.ttf': 'Quicksand',
                        'Quicksand-Bold.ttf': 'Quicksand'
                    }
                    family = font_families.get(font_name, 'Arial')
                    return (family, size, weight)
                else:
                    print(f"[App] Failed to load font, using Arial")
                    return ('Arial', size, weight)
            else:
                print(f"[App] Font file not found: {font_path}")
                return ('Arial', size, weight)

        except Exception as e:
            print(f"[App] Error loading font: {e}")
            return ('Arial', size, weight)

    def set_window_icon(self):
        """Set window and taskbar icons"""
        try:
            if hasattr(sys, '_MEIPASS'):
                icon_path = os.path.join(sys._MEIPASS, 'icon.ico')
            else:
                icon_path = 'icon.ico'

            if os.path.exists(icon_path):
                self.root.iconbitmap(str(icon_path))

                if sys.platform == 'win32':
                    self.root.after(100, lambda: self._set_taskbar_icon(icon_path))

                print(f"[App] Window icon loaded from: {icon_path}")
            else:
                print(f"[App] icon.ico not found at: {icon_path}")
        except Exception as e:
            print(f"[App] Could not set window icon: {e}")

    def _set_taskbar_icon(self, icon_path):
        """Set taskbar icon using Windows API"""
        try:
            import ctypes
            from ctypes import wintypes

            self.root.update_idletasks()
            hwnd = ctypes.windll.user32.FindWindowW(None, self.root.title())

            if not hwnd:
                hwnd = self.root.winfo_id()

            if hwnd:
                LR_LOADFROMFILE = 0x00000010
                IMAGE_ICON = 1

                hicon_small = ctypes.windll.user32.LoadImageW(
                    None, icon_path, IMAGE_ICON, 16, 16, LR_LOADFROMFILE
                )

                hicon_large = ctypes.windll.user32.LoadImageW(
                    None, icon_path, IMAGE_ICON, 32, 32, LR_LOADFROMFILE
                )

                WM_SETICON = 0x0080
                ICON_SMALL = 0
                ICON_LARGE = 1

                if hicon_small:
                    ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon_small)

                if hicon_large:
                    ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_LARGE, hicon_large)

                try:
                    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("LaceAI.Chatbot.1.0")
                except:
                    pass

                print(f"[App] ✅ Taskbar icon set successfully")

        except Exception as e:
            print(f"[App] Could not set taskbar icon: {e}")

    # ADD THIS METHOD TO THE IntegratedChatbotApp CLASS IN integrated_app.py

    def set_title_bar_color(self):
        """Set Windows title bar color to lavender"""
        try:
            import ctypes

            # Get the window handle
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())

            # Lavender color in BGR format (Windows uses BGR, not RGB)
            # #E6E6FA in RGB = (230, 230, 250)
            # In BGR = (250, 230, 230) = 0x00FAE6E6
            lavender_bgr = 0x00FAE6E6

            # Windows 11 style (DWMWA_CAPTION_COLOR = 35)
            DWMWA_CAPTION_COLOR = 35
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_CAPTION_COLOR,
                ctypes.byref(ctypes.c_int(lavender_bgr)),
                ctypes.sizeof(ctypes.c_int)
            )

            # Also set text color to dark purple for visibility
            # #4B0082 in RGB = (75, 0, 130)
            # In BGR = (130, 0, 75) = 0x0082004B
            DWMWA_TEXT_COLOR = 36
            text_color_bgr = 0x0082004B
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_TEXT_COLOR,
                ctypes.byref(ctypes.c_int(text_color_bgr)),
                ctypes.sizeof(ctypes.c_int)
            )

            print("[App] ✅ Title bar color set to lavender")

        except Exception as e:
            print(f"[App] Could not set title bar color: {e}")
            print("[App] This feature requires Windows 11 or Windows 10 with latest updates")

    def create_default_env_file(self):
        """Create a default .env file if it doesn't exist"""
        default_env = """# AI Chatbot System - API Keys
OPENAI_API_KEY=
ELEVENLABS_API_KEY=
AZURE_TTS_KEY=
AZURE_TTS_REGION=eastus
TWITCH_OAUTH_TOKEN=
"""
        with open(self.env_file, 'w') as f:
            f.write(default_env)
        print("[App] Created default .env file")

    def save_api_key(self, key_name, value):
        """Save API key to .env file"""
        try:
            os.environ[key_name] = value
            set_key(self.env_file, key_name, value)
            print(f"[App] Saved {key_name} to .env file")
            return True
        except Exception as e:
            print(f"[App] Error saving API key: {e}")
            return False

    def get_api_key(self, key_name):
        """Get API key from environment"""
        return os.getenv(key_name, '')

    def create_gui(self):
        """Create the main GUI interface"""
        main_container = tk.Frame(self.root, bg=self.colors['bg'])
        main_container.pack(fill='both', expand=True)

        title_frame = tk.Frame(main_container, bg=self.colors['bg'])
        title_frame.pack(fill='x', pady=(15, 10))

        title = tk.Label(
            title_frame,
            text="Lace's Total TTS Bot",
            font=self.load_custom_font('BubblegumSans-Regular.ttf', 26, 'bold'),
            bg=self.colors['bg'],
            fg=self.colors['fg']
        )
        title.pack()

        subtitle = tk.Label(
            title_frame,
            text="Talk to fake voices in your head!",
            font=(self.ui_font[0], 10, 'italic'),
            bg=self.colors['bg'],
            fg=self.colors['accent']
        )
        subtitle.pack()

        notebook_container = tk.Frame(main_container, bg=self.colors['bg'])
        notebook_container.pack(fill='both', expand=True, padx=20, pady=(5, 10))

        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TNotebook', background=self.colors['bg'], borderwidth=0)

        style.configure('TNotebook.Tab',
                       background=self.colors['button'],
                       foreground='white',
                       padding=[15, 8],
                       font=self.ui_font)

        style.map('TNotebook.Tab',
                 background=[('selected', self.colors['accent'])],
                 foreground=[('selected', 'white')],
                 padding=[('selected', [18, 12])],
                 font=[('selected', self.ui_font_bold)])

        notebook = ttk.Notebook(notebook_container)
        notebook.pack(fill='both', expand=True)

        self.create_chat_tab(notebook)
        self.create_api_keys_tab(notebook)
        self.create_setup_tab(notebook)
        self.create_tts_tab(notebook)
        self.create_inputs_tab(notebook)
        self.create_avatar_tab(notebook)

        self.create_control_panel(main_container)

    def create_chat_tab(self, notebook):
        """Chat interface tab"""
        tab = tk.Frame(notebook, bg=self.colors['bg'])
        notebook.add(tab, text='Chat')

        container = tk.Frame(tab, bg=self.colors['bg'])
        container.pack(fill='both', expand=True, padx=25, pady=20)

        chat_border = tk.Frame(container, bg=self.colors['accent'], bd=2)
        chat_border.pack(fill='both', expand=True)

        self.chat_display = tk.Text(
            chat_border,
            bg=self.colors['text_bg'],
            fg=self.colors['fg'],
            font=('Consolas', 10),
            wrap='word',
            relief='flat',
            state='disabled',
            padx=10,
            pady=10
        )
        self.chat_display.pack(fill='both', expand=True, padx=2, pady=2)

        self.chat_display.tag_config('welcome', foreground=self.colors['accent'], font=self.ui_font)
        self.chat_display.tag_config('header', foreground=self.colors['fg'], font=self.ui_font_bold)
        self.chat_display.tag_config('system', foreground='#FF6B6B', font=('Consolas', 10, 'italic'))

        scrollbar = tk.Scrollbar(
            self.chat_display,
            bg=self.colors['accent'],
            troughcolor=self.colors['bg'],
            activebackground=self.colors['fg'],
            width=12,
            relief='flat',
            borderwidth=0
        )
        scrollbar.pack(side='right', fill='y')
        self.chat_display.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.chat_display.yview)

        input_section = tk.Frame(container, bg=self.colors['bg'])
        input_section.pack(fill='x', pady=(15, 0))

        self.chat_mode_label = tk.Label(
            input_section,
            text="Send a message below to test the bot's responses",
            bg=self.colors['bg'],
            fg=self.colors['accent'],
            font=(self.ui_font[0], 9, 'italic')
        )
        self.chat_mode_label.pack(anchor='w', pady=(0, 8))

        input_row = tk.Frame(input_section, bg=self.colors['bg'])
        input_row.pack(fill='x')

        entry_border = tk.Frame(input_row, bg=self.colors['accent'], bd=2)
        entry_border.pack(side='left', fill='x', expand=True, padx=(0, 10))

        self.text_input = tk.Entry(
            entry_border,
            bg=self.colors['entry_bg'],
            fg=self.colors['fg'],
            font=self.ui_font_large,
            relief='flat',
            bd=0,
            insertbackground=self.colors['fg']
        )
        self.text_input.pack(fill='x', padx=2, pady=2, ipady=6)
        self.text_input.bind('<Return>', lambda e: self.send_text_message())

        self.send_btn = tk.Button(
            input_row,
            text="Send",
            command=self.send_text_message,
            bg=self.colors['button'],
            fg='white',
            font=self.ui_font_bold,
            relief='raised',
            borderwidth=3,
            cursor='hand2',
            padx=20,
            pady=8
        )
        self.send_btn.pack(side='right')

        tip_label = tk.Label(
            input_section,
            text="Cool Gamer Tip: You can test bot's responses here anytime, even before starting the full chatbot",
            bg=self.colors['bg'],
            fg=self.colors['accent'],
            font=(self.ui_font[0], 8, 'italic')
        )
        tip_label.pack(anchor='w', pady=(8, 0))

    def create_scrollable_frame(self, parent):
        """Create a scrollable frame with custom styled scrollbar"""
        canvas = tk.Canvas(parent, bg=self.colors['bg'], highlightthickness=0)

        scrollbar = tk.Scrollbar(
            parent,
            orient='vertical',
            command=canvas.yview,
            bg=self.colors['accent'],
            troughcolor=self.colors['bg'],
            activebackground=self.colors['fg'],
            width=14,
            relief='flat',
            borderwidth=0
        )

        scrollable_frame = tk.Frame(canvas, bg=self.colors['bg'])

        scrollable_frame.bind(
            '<Configure>',
            lambda e: canvas.configure(scrollregion=canvas.bbox('all'))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor='n')
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        return scrollable_frame

    def create_api_keys_tab(self, notebook):
        """API Keys management tab"""
        tab = tk.Frame(notebook, bg=self.colors['bg'])
        notebook.add(tab, text='API Keys')

        scrollable = self.create_scrollable_frame(tab)

        # Add centered wrapper with padding
        wrapper = tk.Frame(scrollable, bg=self.colors['bg'])
        wrapper.pack(fill='both', expand=True, padx=(835, 0), pady=20)

        keys_section = self.create_section(wrapper, "API Keys", 0)
        keys_section.grid_columnconfigure(0, weight=1)
        keys_section.grid_columnconfigure(1, weight=1)

        self.key_show_states = {}
        self.key_entries = {}

        # OpenAI API Key
        self.create_api_key_row(
            keys_section,
            row=0,
            label="OpenAI API Key:",
            key_name="OPENAI_API_KEY",
            required=True,
            link="https://platform.openai.com/api-keys",
            description="Required for all GPT models"
        )

        # Groq API Key
        self.create_api_key_row(
            keys_section,
            row=1,
            label="Open Source API Key:",
            key_name="GROQ_API_KEY",
            required=False,
            link="https://console.groq.com/keys",
            description="Optional - for fast & free models"
        )

        # ElevenLabs API Key
        self.create_api_key_row(
            keys_section,
            row=2,
            label="ElevenLabs API Key:",
            key_name="ELEVENLABS_API_KEY",
            required=False,
            link="https://elevenlabs.io/",
            description="Optional - for premium TTS voices"
        )

        # Azure TTS Key
        self.create_api_key_row(
            keys_section,
            row=3,
            label="Azure TTS Key:",
            key_name="AZURE_TTS_KEY",
            required=False,
            link="https://portal.azure.com/",
            description="Optional - for Azure neural voices"
        )

        # Azure Region (special case)
        azure_region_frame = tk.Frame(keys_section, bg=self.colors['bg'])
        azure_region_frame.grid(row=4, column=0, columnspan=4, sticky='ew', pady=5)

        tk.Label(
            azure_region_frame,
            text="Azure Region:",
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=self.ui_font
        ).pack(side='left', padx=5)

        self.azure_region_entry = tk.Entry(
            azure_region_frame,
            bg=self.colors['entry_bg'],
            fg=self.colors['fg'],
            font=self.ui_font,
            width=15,
            insertbackground=self.colors['fg']
        )
        self.azure_region_entry.pack(side='left', padx=5)
        self.azure_region_entry.insert(0, self.get_api_key('AZURE_TTS_REGION') or 'eastus')

        # Twitch OAuth Token
        self.create_api_key_row(
            keys_section,
            row=5,
            label="Twitch OAuth Token:",
            key_name="TWITCH_OAUTH_TOKEN",
            required=False,
            link="https://twitchapps.com/tmi/",
            description="Optional - format: oauth:yourtoken"
        )

        # Save Button
        save_frame = tk.Frame(wrapper, bg=self.colors['bg'])
        save_frame.pack(pady=20)

        tk.Button(
            save_frame,
            text="💾 Save All API Keys",
            command=self.save_all_api_keys,
            bg='#4CAF50',
            fg='white',
            font=self.ui_font_bold,
            relief='raised',
            borderwidth=3,
            cursor='hand2',
            width=20,
            height=2
        ).pack()

        # Status Section
        status_frame = self.create_section(wrapper, "API Key Status", 1)
        status_frame.grid_columnconfigure(0, weight=1)
        status_frame.grid_columnconfigure(1, weight=1)

        self.api_status_labels = {}
        status_keys = [
            ("OpenAI", "OPENAI_API_KEY", True),
            ("Groq", "GROQ_API_KEY", False),
            ("ElevenLabs", "ELEVENLABS_API_KEY", False),
            ("Azure TTS", "AZURE_TTS_KEY", False),
            ("Twitch", "TWITCH_OAUTH_TOKEN", False)
        ]

        for i, (display_name, key_name, required) in enumerate(status_keys):
            status_row = tk.Frame(status_frame, bg=self.colors['bg'])
            status_row.grid(row=i, column=0, sticky='w', pady=5)

            label = tk.Label(
                status_row,
                text=f"{display_name}:",
                bg=self.colors['bg'],
                fg=self.colors['fg'],
                font=self.ui_font_bold,
                width=15,
                anchor='w'
            )
            label.pack(side='left', padx=5)

            status_label = tk.Label(
                status_row,
                text="",
                bg=self.colors['bg'],
                font=self.ui_font,
                width=30,
                anchor='w'
            )
            status_label.pack(side='left', padx=5)

            self.api_status_labels[key_name] = status_label

        self.update_api_key_status()

    def create_api_key_row(self, parent, row, label, key_name, required, link, description):
        """Create a row for entering an API key"""
        row_frame = tk.Frame(parent, bg=self.colors['bg'])
        row_frame.grid(row=row, column=0, columnspan=4, sticky='ew', pady=10)

        label_text = label + (" *" if required else "")
        tk.Label(
            row_frame,
            text=label_text,
            bg=self.colors['bg'],
            fg=self.colors['fg'] if required else self.colors['accent'],
            font=self.ui_font_bold if required else self.ui_font,
            width=20,
            anchor='w'
        ).pack(side='left', padx=5)

        entry = tk.Entry(
            row_frame,
            bg=self.colors['entry_bg'],
            fg=self.colors['fg'],
            font=self.ui_font,
            width=40,
            show='•',
            insertbackground=self.colors['fg']
        )
        entry.pack(side='left', padx=5)
        entry.insert(0, self.get_api_key(key_name))
        self.key_entries[key_name] = entry

        self.key_show_states[key_name] = False
        show_btn = tk.Button(
            row_frame,
            text="👁",
            command=lambda: self.toggle_key_visibility(key_name),
            bg=self.colors['button'],
            fg='white',
            font=(self.ui_font[0], 9),
            relief='flat',
            cursor='hand2',
            width=3
        )
        show_btn.pack(side='left', padx=2)

        link_btn = tk.Button(
            row_frame,
            text="Get Key",
            command=lambda: self.open_link(link),
            bg=self.colors['accent'],
            fg='white',
            font=(self.ui_font[0], 9),
            relief='flat',
            cursor='hand2'
        )
        link_btn.pack(side='left', padx=2)

        tk.Label(
            row_frame,
            text=description,
            bg=self.colors['bg'],
            fg=self.colors['accent'],
            font=(self.ui_font[0], 9, 'italic')
        ).pack(side='left', padx=5)

    def toggle_key_visibility(self, key_name):
        """Toggle visibility of API key"""
        entry = self.key_entries[key_name]
        self.key_show_states[key_name] = not self.key_show_states[key_name]

        if self.key_show_states[key_name]:
            entry.config(show='')
        else:
            entry.config(show='•')

    def open_link(self, url):
        """Open URL in browser"""
        import webbrowser
        webbrowser.open(url)

    def save_all_api_keys(self):
        """Save all API keys to .env file"""
        try:
            for key_name, entry in self.key_entries.items():
                value = entry.get().strip()
                if value:
                    self.save_api_key(key_name, value)

            azure_region = self.azure_region_entry.get().strip()
            if azure_region:
                self.save_api_key('AZURE_TTS_REGION', azure_region)

            self.update_api_key_status()

            messagebox.showinfo(
                "Success",
                "All API keys saved to .env file!\n\n"
                "Restart the chatbot for changes to take effect."
            )

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save API keys:\n{e}")

    def update_api_key_status(self):
        """Update API key status indicators"""
        for key_name, label in self.api_status_labels.items():
            value = self.get_api_key(key_name)

            if value and len(value) > 0:
                if 'your-' in value.lower() or value == '':
                    label.config(text="❌ Not configured", fg='#f44336')
                else:
                    masked_value = value[:8] + '...' + value[-4:] if len(value) > 12 else '***'
                    label.config(text=f"✅ Configured ({masked_value})", fg='#4CAF50')
            else:
                label.config(text="❌ Not configured", fg='#f44336')

    def create_setup_tab(self, notebook):
        """Setup tab with GPT models, personality, memory, response length"""
        tab = tk.Frame(notebook, bg=self.colors['bg'])
        notebook.add(tab, text='Setup')

        scrollable = self.create_scrollable_frame(tab)

        wrapper = tk.Frame(scrollable, bg=self.colors['bg'])
        wrapper.pack(fill='both', expand=True, padx=(55, 0), pady=20)

        config_frame = self.create_section(wrapper, "Bot Configuration", 0)
        config_frame.grid_columnconfigure(0, weight=1)
        config_frame.grid_columnconfigure(1, weight=1)

        self.create_entry(config_frame, "Bot's Name:", 'ai_name', 0)
        self.create_entry(config_frame, "Your Name:", 'user_name', 1)

        tk.Label(config_frame, text="Model:",
                 bg=self.colors['bg'], fg=self.colors['fg'],
                 font=self.ui_font_bold).grid(row=2, column=0, sticky='w', pady=5)

        models = [
            'gpt-4o',
            'gpt-4o-mini',
            'gpt-4',
            '--- Free Open Source ---',
            'llama-3.1-8b-instant',
            'llama-3.3-70b-versatile',
            'moonshotai/kimi-k2-instruct-0905',
        ]
        self.llm_var = tk.StringVar(value=self.config['llm_model'])
        llm_menu = ttk.Combobox(config_frame, textvariable=self.llm_var,
                                values=models, state='readonly', width=25)
        llm_menu.grid(row=2, column=1, sticky='w', pady=5)
        llm_menu.bind('<<ComboboxSelected>>',
                      lambda e: self.update_config('llm_model', self.llm_var.get()))

        info_label = tk.Label(
            config_frame,
            text="Crazy Epic Tip: gpt-4o supports vision & is the most capable.",
            bg=self.colors['bg'],
            fg=self.colors['accent'],
            font=(self.ui_font[0], 9, 'italic')
        )
        info_label.grid(row=3, column=0, columnspan=2, sticky='w', pady=5)

        response_section = self.create_section(wrapper, "Response Length & Style", 1)
        response_section.grid_columnconfigure(0, weight=1)
        response_section.grid_columnconfigure(1, weight=1)

        tk.Label(
            response_section,
            text="Control how long and detailed the bot's responses are:",
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=self.ui_font
        ).grid(row=0, column=0, columnspan=2, sticky='w', pady=(0, 10))

        tk.Label(response_section, text="Response Length:",
                 bg=self.colors['bg'], fg=self.colors['fg'],
                 font=self.ui_font).grid(row=1, column=0, sticky='w', pady=5)

        self.response_length_var = tk.StringVar(value=self.config.get('response_length', 'normal'))
        response_lengths = ['brief', 'normal', 'detailed', 'custom']
        response_length_menu = ttk.Combobox(
            response_section,
            textvariable=self.response_length_var,
            values=response_lengths,
            state='readonly',
            width=15
        )
        response_length_menu.grid(row=1, column=1, sticky='w', pady=5)
        response_length_menu.bind('<<ComboboxSelected>>',
                                  lambda e: self.on_response_length_change())

        length_descriptions = {
            'brief': '1-2 sentences (~20-40 words) - Good for quick chats',
            'normal': '2-4 sentences (~40-80 words) - Balanced responses',
            'detailed': '4-8 sentences (~80-150 words) - Thorough explanations',
            'custom': 'Set your own token limit below (probably not worth it tbh)'
        }

        self.length_desc_label = tk.Label(
            response_section,
            text=length_descriptions[self.response_length_var.get()],
            bg=self.colors['bg'],
            fg=self.colors['accent'],
            font=(self.ui_font[0], 9, 'italic'),
            wraplength=500,
            justify='left'
        )
        self.length_desc_label.grid(row=2, column=0, columnspan=2, sticky='w', pady=5)

        self.custom_tokens_frame = tk.Frame(response_section, bg=self.colors['bg'])
        self.custom_tokens_frame.grid(row=3, column=0, columnspan=2, sticky='w', pady=5)

        tk.Label(
            self.custom_tokens_frame,
            text="Max Response Tokens:",
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=self.ui_font
        ).pack(side='left', padx=5)

        self.max_response_tokens_var = tk.IntVar(value=self.config.get('max_response_tokens', 150))
        self.max_response_tokens_slider = tk.Scale(
            self.custom_tokens_frame,
            from_=30,
            to=500,
            orient='horizontal',
            variable=self.max_response_tokens_var,
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            highlightthickness=0,
            length=200,
            command=lambda v: self.update_config('max_response_tokens', int(v))
        )
        self.max_response_tokens_slider.pack(side='left', padx=5)

        self.tokens_value_label = tk.Label(
            self.custom_tokens_frame,
            text=f"{self.max_response_tokens_var.get()} tokens",
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=(self.ui_font[0], 9)
        )
        self.tokens_value_label.pack(side='left', padx=5)

        self.max_response_tokens_slider.config(
            command=lambda v: self.update_token_label(int(float(v)))
        )

        self.update_custom_tokens_visibility()

        tk.Label(response_section, text="Response Style:",
                 bg=self.colors['bg'], fg=self.colors['fg'],
                 font=self.ui_font).grid(row=4, column=0, sticky='w', pady=5)

        self.response_style_var = tk.StringVar(value=self.config.get('response_style', 'conversational'))
        response_styles = ['casual', 'conversational', 'professional', 'custom']
        response_style_menu = ttk.Combobox(
            response_section,
            textvariable=self.response_style_var,
            values=response_styles,
            state='readonly',
            width=15
        )
        response_style_menu.grid(row=4, column=1, sticky='w', pady=5)
        response_style_menu.bind('<<ComboboxSelected>>',
                                 lambda e: self.on_response_style_change())

        self.custom_style_frame = tk.Frame(response_section, bg=self.colors['bg'])
        self.custom_style_frame.grid(row=6, column=0, columnspan=2, sticky='ew', pady=5)

        tk.Label(
            self.custom_style_frame,
            text="Custom Style Instructions:",
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=self.ui_font
        ).pack(anchor='w', padx=5)

        self.custom_style_text = tk.Text(
            self.custom_style_frame,
            height=3,
            bg=self.colors['entry_bg'],
            fg=self.colors['fg'],
            font=(self.ui_font[0], 9),
            wrap='word',
            insertbackground=self.colors['fg']
        )
        self.custom_style_text.pack(fill='x', padx=5, pady=5)
        self.custom_style_text.insert('1.0', self.config.get('custom_response_style', ''))
        self.custom_style_text.bind('<FocusOut>',
                                    lambda e: self.update_config('custom_response_style',
                                                                 self.custom_style_text.get('1.0', 'end-1c')))

        tk.Label(
            self.custom_style_frame,
            text='Example: "Use humor when appropriate. Reference pop culture occasionally. Randomly start screaming in terror."',
            bg=self.colors['bg'],
            fg=self.colors['accent'],
            font=(self.ui_font[0], 8, 'italic')
        ).pack(anchor='w', padx=5)

        self.update_custom_style_visibility()

        style_descriptions = {
            'casual': 'Relaxed, friendly tone with informal writing',
            'conversational': 'Warm, natural conversation style',
            'professional': 'Formal, polished language',
            'custom': 'Define your own custom style below'
        }

        self.style_desc_label = tk.Label(
            response_section,
            text=style_descriptions[self.response_style_var.get()],
            bg=self.colors['bg'],
            fg=self.colors['accent'],
            font=(self.ui_font[0], 9, 'italic')
        )
        self.style_desc_label.grid(row=5, column=0, columnspan=2, sticky='w', pady=5)

        memory_section = self.create_section(wrapper, "Memory & Context Settings", 2)
        memory_section.grid_columnconfigure(0, weight=1)
        memory_section.grid_columnconfigure(1, weight=1)

        tk.Label(
            memory_section,
            text="Configure how much the bot remembers from the conversation:",
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=self.ui_font
        ).grid(row=0, column=0, columnspan=2, sticky='w', pady=(0, 10))

        tk.Label(
            memory_section,
            text="Conversation history is automatically saved to: conversation_history.json",
            bg=self.colors['bg'],
            fg=self.colors['accent'],
            font=(self.ui_font[0], 9, 'italic')
        ).grid(row=1, column=0, columnspan=2, sticky='w', pady=(0, 10))

        tk.Label(memory_section, text="Max Context Tokens:",
                 bg=self.colors['bg'], fg=self.colors['fg'],
                 font=self.ui_font).grid(row=2, column=0, sticky='w', pady=5)

        self.max_tokens_var = tk.StringVar(value=self.config.get('max_context_tokens', '8000'))
        max_tokens_options = ['4000', '8000', '16000', '32000', '128000']
        max_tokens_menu = ttk.Combobox(
            memory_section,
            textvariable=self.max_tokens_var,
            values=max_tokens_options,
            state='readonly',
            width=15
        )
        max_tokens_menu.grid(row=2, column=1, sticky='w', pady=5)
        max_tokens_menu.bind('<<ComboboxSelected>>',
                             lambda e: self.update_config('max_context_tokens', int(self.max_tokens_var.get())))

        tk.Label(
            memory_section,
            text="Higher = more memory but more expensive.",
            bg=self.colors['bg'],
            fg=self.colors['accent'],
            font=(self.ui_font[0], 9, 'italic')
        ).grid(row=3, column=0, columnspan=2, sticky='w', pady=5)

        tk.Label(memory_section, text="Auto-Reset Conversation:",
                 bg=self.colors['bg'], fg=self.colors['fg'],
                 font=self.ui_font).grid(row=4, column=0, sticky='w', pady=5)

        self.auto_reset_var = tk.BooleanVar(value=self.config.get('auto_reset', False))
        auto_reset_check = tk.Checkbutton(
            memory_section,
            text="Reset conversation when reaching token limit",
            variable=self.auto_reset_var,
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=(self.ui_font[0], 9),
            selectcolor=self.colors['entry_bg'],
            activebackground=self.colors['bg'],
            activeforeground=self.colors['fg'],
            command=lambda: self.update_config('auto_reset', self.auto_reset_var.get())
        )
        auto_reset_check.grid(row=4, column=1, sticky='w', pady=5)

        reset_btn = tk.Button(
            memory_section,
            text="Clear Conversation History Now",
            command=self.clear_conversation_history,
            bg='#FF6B6B',
            fg='white',
            font=self.ui_font_bold,
            relief='flat',
            cursor='hand2'
        )
        reset_btn.grid(row=5, column=0, columnspan=2, pady=10)

        personality_section = self.create_section(wrapper, "Bot's Personality", 3)
        personality_section.grid_columnconfigure(0, weight=1)
        personality_section.grid_columnconfigure(1, weight=1)

        tk.Label(personality_section, text="System Prompt / Personality:",
                 bg=self.colors['bg'], fg=self.colors['fg'],
                 font=self.ui_font_bold).grid(row=0, column=0, columnspan=2, sticky='w', pady=(0, 10))

        text_frame = tk.Frame(personality_section, bg=self.colors['accent'], bd=2)
        text_frame.grid(row=1, column=0, columnspan=2, sticky='ew', pady=5)

        self.personality_text = tk.Text(
            text_frame,
            height=12,
            bg=self.colors['text_bg'],
            fg=self.colors['fg'],
            font=('Consolas', 10),
            wrap='word',
            relief='flat',
            insertbackground=self.colors['fg']
        )
        self.personality_text.pack(fill='both', expand=True, padx=2, pady=2)
        self.personality_text.insert('1.0', self.config['personality'])

        save_personality_btn = tk.Button(
            personality_section,
            text="💾 Save Personality",
            command=self.save_personality,
            bg=self.colors['button'],
            fg='white',
            font=self.ui_font_bold,
            relief='flat',
            cursor='hand2'
        )
        save_personality_btn.grid(row=2, column=0, columnspan=2, pady=10)

    def on_response_length_change(self):
        """Handle response length selection change"""
        length = self.response_length_var.get()
        self.update_config('response_length', length)

        length_descriptions = {
            'brief': '1-2 sentences (~20-40 words) - Good for quick chats',
            'normal': '2-4 sentences (~40-80 words) - Balanced responses',
            'detailed': '4-8 sentences (~80-150 words) - Thorough explanations',
            'custom': 'Set your own token limit below (Probably not necessary tbh)'
        }
        self.length_desc_label.config(text=length_descriptions[length])

        self.update_custom_tokens_visibility()

    def update_custom_tokens_visibility(self):
        """Show or hide custom tokens slider based on selection"""
        if self.response_length_var.get() == 'custom':
            self.custom_tokens_frame.grid()
        else:
            self.custom_tokens_frame.grid_remove()

    def update_token_label(self, value):
        """Update the token count label"""
        self.tokens_value_label.config(text=f"{value} tokens")
        self.update_config('max_response_tokens', value)

    def update_style_description(self):
        """Update response style description"""
        style = self.response_style_var.get()
        style_descriptions = {
            'casual': 'Relaxed, friendly tone with informal writing',
            'conversational': 'Warm, natural conversation style',
            'professional': 'Formal, polished language',
            'custom': 'Define your own custom style below'
        }
        self.style_desc_label.config(text=style_descriptions.get(style, ''))

    def reinitialize_tts(self):
        """Reinitialize TTS manager with current settings"""
        if self.engine.is_running and self.engine.tts:
            elevenlabs_settings = {
                'stability': self.config.get('elevenlabs_stability', 0.5),
                'similarity_boost': self.config.get('elevenlabs_similarity', 0.75),
                'style': self.config.get('elevenlabs_style', 0.0),
                'use_speaker_boost': self.config.get('elevenlabs_speaker_boost', True)
            }

            from tts_manager import TTSManager
            self.engine.tts = TTSManager(
                service=self.config['tts_service'],
                voice=self.config['elevenlabs_voice'],
                elevenlabs_settings=elevenlabs_settings
            )

            self.engine.tts.set_audio_callbacks(
                on_start=self.engine._on_audio_start,
                on_active=self.engine._on_audio_active,
                on_silent=self.engine._on_audio_silent,
                on_end=self.engine._on_audio_end
            )

            self.engine.tts.set_volume_threshold(self.config.get('volume_threshold', 0.02))

            print(f"[App] TTS reinitialized with voice: {self.config['elevenlabs_voice']}")

    def on_response_style_change(self):
        """Handle response style selection change"""
        style = self.response_style_var.get()
        self.update_config('response_style', style)
        self.update_style_description()
        self.update_custom_style_visibility()

    def update_custom_style_visibility(self):
        """Show or hide custom style text box based on selection"""
        if self.response_style_var.get() == 'custom':
            self.custom_style_frame.grid()
        else:
            self.custom_style_frame.grid_remove()

    def create_tts_tab(self, notebook):
        """TTS tab with dynamic voice dropdown and voice testing"""
        tab = tk.Frame(notebook, bg=self.colors['bg'])
        notebook.add(tab, text='TTS')

        scrollable = self.create_scrollable_frame(tab)

        # Use balanced padding for wider content
        wrapper = tk.Frame(scrollable, bg=self.colors['bg'])
        wrapper.pack(fill='both', expand=True, padx=(950, 150), pady=20)

        tts_frame = self.create_section(wrapper, "TTS Service", 0)
        tts_frame.grid_columnconfigure(0, weight=1)
        tts_frame.grid_columnconfigure(1, weight=1)

        tk.Label(tts_frame, text="TTS Service:",
                 bg=self.colors['bg'], fg=self.colors['fg'],
                 font=self.ui_font_bold).grid(row=0, column=0, sticky='w', pady=5)

        tts_services = ['streamelements', 'elevenlabs', 'azure']
        self.tts_var = tk.StringVar(value=self.config['tts_service'])
        tts_menu = ttk.Combobox(tts_frame, textvariable=self.tts_var,
                                values=tts_services, state='readonly', width=25)
        tts_menu.grid(row=0, column=1, sticky='w', pady=5)
        tts_menu.bind('<<ComboboxSelected>>', self.on_tts_change)

        voice_section = self.create_section(wrapper, "Voice Settings", 1)
        voice_section.grid_columnconfigure(0, weight=1)
        voice_section.grid_columnconfigure(1, weight=1)

        tk.Label(voice_section, text="Voice:",
                 bg=self.colors['bg'], fg=self.colors['fg'],
                 font=self.ui_font_bold).grid(row=0, column=0, sticky='w', pady=5)

        self.voice_var = tk.StringVar(value=self.config.get('elevenlabs_voice', 'rachel'))
        self.voice_menu = ttk.Combobox(voice_section, textvariable=self.voice_var,
                                       values=self.voice_options['elevenlabs'],
                                       state='readonly', width=35)
        self.voice_menu.grid(row=0, column=1, sticky='w', pady=5)

        def on_voice_change(e):
            self.update_config('elevenlabs_voice', self.voice_var.get())
            self.reinitialize_tts()

        self.voice_menu.bind('<<ComboboxSelected>>', on_voice_change)

        self.refresh_voices_btn = tk.Button(
            voice_section,
            text="🔄 Refresh Voices",
            command=self.refresh_elevenlabs_voices,
            bg=self.colors['button'],
            fg='white',
            font=(self.ui_font[0], 9),
            relief='flat',
            cursor='hand2'
        )
        self.refresh_voices_btn.grid(row=0, column=2, padx=5)

        self.voice_info_label = tk.Label(
            voice_section,
            text="Click 'Refresh Voices' to load your custom ElevenLabs voices",
            bg=self.colors['bg'],
            fg=self.colors['accent'],
            font=(self.ui_font[0], 9, 'italic')
        )
        self.voice_info_label.grid(row=1, column=0, columnspan=3, sticky='w', pady=5)

        # Create info frame for TTS service descriptions
        self.tts_info_frame = tk.Frame(voice_section, bg=self.colors['bg'])
        self.tts_info_frame.grid(row=2, column=0, columnspan=3, sticky='ew', pady=10)

        # Create all info labels
        self.se_info = tk.Label(
            self.tts_info_frame,
            text="",
            bg=self.colors['bg'],
            fg='#4CAF50',
            font=(self.ui_font[0], 9),
            wraplength=500,
            justify='left'
        )

        self.elevenlabs_info = tk.Label(
            self.tts_info_frame,
            text="",
            bg=self.colors['bg'],
            fg=self.colors['accent'],
            font=(self.ui_font[0], 9),
            wraplength=500,
            justify='left'
        )

        self.azure_info = tk.Label(
            self.tts_info_frame,
            text="",
            bg=self.colors['bg'],
            fg=self.colors['accent'],
            font=(self.ui_font[0], 9),
            wraplength=500,
            justify='left'
        )

        # ElevenLabs settings section - always pack it in order, but hide contents
        self.elevenlabs_settings_outer = tk.Frame(wrapper, bg=self.colors['bg'])
        self.elevenlabs_settings_outer.pack(fill='x', padx=30, pady=15)  # Always pack it in position

        # Create section inside the outer container
        self.elevenlabs_settings_section = tk.Frame(self.elevenlabs_settings_outer, bg=self.colors['bg'])
        self.elevenlabs_settings_section.pack(fill='x', padx=30, pady=15)

        # Create section content
        section_inner = tk.Frame(self.elevenlabs_settings_section, bg=self.colors['bg'])
        section_inner.pack(anchor='center')

        title_frame = tk.Frame(section_inner, bg=self.colors['bg'])
        title_frame.pack(fill='x', pady=(0, 10))

        tk.Label(
            title_frame,
            text="ElevenLabs Voice Settings",
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=self.ui_font_bold
        ).pack(anchor='center')

        separator = tk.Frame(title_frame, bg=self.colors['accent'], height=2)
        separator.pack(fill='x', pady=(5, 0))

        settings_frame = tk.Frame(section_inner, bg=self.colors['bg'])
        settings_frame.pack(fill='both', padx=10)

        settings_frame.grid_columnconfigure(0, weight=0)
        settings_frame.grid_columnconfigure(1, weight=0)
        settings_frame.grid_columnconfigure(2, weight=1)

        # Stability
        tk.Label(
            settings_frame,
            text="Stability:",
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=self.ui_font,
            width=15,
            anchor='w'
        ).grid(row=0, column=0, sticky='w', pady=5)

        self.stability_var = tk.DoubleVar(value=self.config.get('elevenlabs_stability', 0.5))
        stability_slider = tk.Scale(
            settings_frame,
            from_=0.0,
            to=1.0,
            resolution=0.05,
            orient='horizontal',
            variable=self.stability_var,
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            highlightthickness=0,
            length=250,
            command=lambda v: [self.update_config('elevenlabs_stability', float(v)), self.reinitialize_tts()]
        )
        stability_slider.grid(row=0, column=1, sticky='w', pady=5, padx=10)

        tk.Label(
            settings_frame,
            text="(Lower = more variable, Higher = more stable)",
            bg=self.colors['bg'],
            fg=self.colors['accent'],
            font=(self.ui_font[0], 8, 'italic')
        ).grid(row=0, column=2, sticky='w', padx=5)

        # Similarity Boost
        tk.Label(
            settings_frame,
            text="Similarity Boost:",
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=self.ui_font,
            width=15,
            anchor='w'
        ).grid(row=1, column=0, sticky='w', pady=5)

        self.similarity_var = tk.DoubleVar(value=self.config.get('elevenlabs_similarity', 0.75))
        similarity_slider = tk.Scale(
            settings_frame,
            from_=0.0,
            to=1.0,
            resolution=0.05,
            orient='horizontal',
            variable=self.similarity_var,
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            highlightthickness=0,
            length=250,
            command=lambda v: [self.update_config('elevenlabs_similarity', float(v)), self.reinitialize_tts()]
        )
        similarity_slider.grid(row=1, column=1, sticky='w', pady=5, padx=10)

        tk.Label(
            settings_frame,
            text="(Higher = closer to original voice)",
            bg=self.colors['bg'],
            fg=self.colors['accent'],
            font=(self.ui_font[0], 8, 'italic')
        ).grid(row=1, column=2, sticky='w', padx=5)

        # Style Exaggeration
        tk.Label(
            settings_frame,
            text="Style Exaggeration:",
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=self.ui_font,
            width=15,
            anchor='w'
        ).grid(row=2, column=0, sticky='w', pady=5)

        self.style_var = tk.DoubleVar(value=self.config.get('elevenlabs_style', 0.0))
        style_slider = tk.Scale(
            settings_frame,
            from_=0.0,
            to=1.0,
            resolution=0.05,
            orient='horizontal',
            variable=self.style_var,
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            highlightthickness=0,
            length=250,
            command=lambda v: [self.update_config('elevenlabs_style', float(v)), self.reinitialize_tts()]
        )
        style_slider.grid(row=2, column=1, sticky='w', pady=5, padx=10)

        tk.Label(
            settings_frame,
            text="(Higher = more expressive/dramatic)",
            bg=self.colors['bg'],
            fg=self.colors['accent'],
            font=(self.ui_font[0], 8, 'italic')
        ).grid(row=2, column=2, sticky='w', padx=5)

        # Speaker Boost checkbox
        self.speaker_boost_var = tk.BooleanVar(value=self.config.get('elevenlabs_speaker_boost', True))
        speaker_boost_check = tk.Checkbutton(
            settings_frame,
            text="Use Speaker Boost (enhances voice similarity)",
            variable=self.speaker_boost_var,
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=self.ui_font,
            selectcolor=self.colors['entry_bg'],
            activebackground=self.colors['bg'],
            activeforeground=self.colors['fg'],
            command=lambda: self.update_config('elevenlabs_speaker_boost', self.speaker_boost_var.get())
        )
        speaker_boost_check.grid(row=3, column=0, columnspan=3, sticky='w', pady=10)

        # Initially show/hide based on current service
        if self.config['tts_service'] == 'elevenlabs':
            self.elevenlabs_settings_section.pack(fill='x', padx=30, pady=15)
        # If not elevenlabs, section frame is not packed (invisible but outer frame holds position)

        self.update_voice_dropdown()

    def create_inputs_tab(self, notebook):
        """Inputs tab with microphone, screenshot, and Twitch settings"""
        tab = tk.Frame(notebook, bg=self.colors['bg'])
        notebook.add(tab, text='Inputs')

        scrollable = self.create_scrollable_frame(tab)
        wrapper = tk.Frame(scrollable, bg=self.colors['bg'])
        wrapper.pack(fill='both', expand=True, padx=(110, 0), pady=20)

        mic_section = self.create_section(wrapper, "Microphone Settings", 0)
        mic_section.grid_columnconfigure(0, weight=1)
        mic_section.grid_columnconfigure(1, weight=1)

        self.mic_var = tk.BooleanVar(value=self.config['mic_enabled'])
        mic_check = tk.Checkbutton(
            mic_section,
            text="Enable Microphone Input",
            variable=self.mic_var,
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=self.ui_font_bold,
            selectcolor=self.colors['entry_bg'],
            activebackground=self.colors['bg'],
            activeforeground=self.colors['fg'],
            command=lambda: self.update_config('mic_enabled', self.mic_var.get())
        )
        mic_check.grid(row=0, column=0, columnspan=2, sticky='w', pady=5)

        tk.Label(mic_section, text="Microphone Device:",
                 bg=self.colors['bg'], fg=self.colors['fg'],
                 font=self.ui_font).grid(row=1, column=0, sticky='w', pady=5)

        self.mic_device_var = tk.StringVar(value="Default")
        self.mic_device_menu = ttk.Combobox(mic_section, textvariable=self.mic_device_var,
                                            state='readonly', width=35)
        self.mic_device_menu.grid(row=1, column=1, sticky='w', pady=5)
        self.mic_device_menu.bind('<<ComboboxSelected>>', lambda e: self.on_mic_device_change())

        self.refresh_microphone_list()

        refresh_btn = tk.Button(
            mic_section,
            text="🔄 Refresh",
            command=self.refresh_microphone_list,
            bg=self.colors['button'],
            fg='white',
            font=(self.ui_font[0], 9),
            relief='flat',
            cursor='hand2'
        )
        refresh_btn.grid(row=1, column=2, padx=5)

        # Hotkey Configuration
        hotkey_frame = tk.Frame(mic_section, bg=self.colors['bg'])
        hotkey_frame.grid(row=3, column=0, columnspan=3, sticky='ew', pady=10)

        tk.Label(
            hotkey_frame,
            text="Microphone Hotkey:",
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=self.ui_font_bold
        ).pack(side='left', padx=5)

        self.mic_hotkey_var = tk.StringVar(value=self.config.get('hotkey_toggle', 'f4'))
        mic_hotkey_entry = tk.Entry(
            hotkey_frame,
            textvariable=self.mic_hotkey_var,
            bg=self.colors['entry_bg'],
            fg=self.colors['fg'],
            font=self.ui_font,
            width=10,
            insertbackground=self.colors['fg']
        )
        mic_hotkey_entry.pack(side='left', padx=5)
        mic_hotkey_entry.bind('<FocusOut>', lambda e: self.update_config('hotkey_toggle', self.mic_hotkey_var.get()))

        tk.Label(
            hotkey_frame,
            text="(Hold to record, release to send)",
            bg=self.colors['bg'],
            fg=self.colors['accent'],
            font=(self.ui_font[0], 9, 'italic')
        ).pack(side='left', padx=5)

        # Screenshot Hotkey Configuration
        screenshot_hotkey_frame = tk.Frame(mic_section, bg=self.colors['bg'])
        screenshot_hotkey_frame.grid(row=4, column=0, columnspan=3, sticky='ew', pady=10)

        tk.Label(
            screenshot_hotkey_frame,
            text="Screenshot Hotkey:",
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=self.ui_font_bold
        ).pack(side='left', padx=5)

        self.screenshot_hotkey_var = tk.StringVar(value=self.config.get('hotkey_screenshot', 'f5'))
        screenshot_hotkey_entry = tk.Entry(
            screenshot_hotkey_frame,
            textvariable=self.screenshot_hotkey_var,
            bg=self.colors['entry_bg'],
            fg=self.colors['fg'],
            font=self.ui_font,
            width=10,
            insertbackground=self.colors['fg']
        )
        screenshot_hotkey_entry.pack(side='left', padx=5)
        screenshot_hotkey_entry.bind('<FocusOut>', lambda e: self.update_config('hotkey_screenshot',
                                                                                self.screenshot_hotkey_var.get()))

        tk.Label(
            screenshot_hotkey_frame,
            text="(Press to capture screen and get AI response)",
            bg=self.colors['bg'],
            fg=self.colors['accent'],
            font=(self.ui_font[0], 9, 'italic')
        ).pack(side='left', padx=5)

        # Hotkey Tips
        tips_frame = tk.Frame(mic_section, bg=self.colors['entry_bg'], bd=2, relief='solid')
        tips_frame.grid(row=5, column=0, columnspan=3, sticky='ew', pady=10, padx=20)

        tips_text = """
        Silly goofball tips:
        • Common choices: f4, f5, f6 (avoid f1/f11/f12 which may conflict)
        • Changes apply when you restart the chatbot
        • Make sure hotkeys don't conflict with other programs
        • Honestly just use your numpad, you do have one right?
        • What kinda loser buys a keyboard without a numpad
                """

        tk.Label(
            tips_frame,
            text=tips_text,
            bg=self.colors['entry_bg'],
            fg=self.colors['fg'],
            font=(self.ui_font[0], 9),
            justify='left'
        ).pack(padx=10, pady=10)

        tk.Label(mic_section, text="Recording Mode:",
                 bg=self.colors['bg'], fg=self.colors['fg'],
                 font=self.ui_font).grid(row=2, column=0, sticky='w', pady=5)

        mode_label = tk.Label(
            mic_section,
            text="Push-to-Talk (Hold your selected hotkey to speak)",
            bg=self.colors['bg'],
            fg=self.colors['accent'],
            font=(self.ui_font[0], 10, 'italic')
        )
        mode_label.grid(row=2, column=1, sticky='w', pady=5)

        screen_section = self.create_section(wrapper, "Screen Capture (Vision)", 1)
        screen_section.grid_columnconfigure(0, weight=1)
        screen_section.grid_columnconfigure(1, weight=1)

        self.screen_var = tk.BooleanVar(value=self.config['screen_enabled'])
        screen_check = tk.Checkbutton(
            screen_section,
            text="Enable Screen Capture (for vision responses)",
            variable=self.screen_var,
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=self.ui_font_bold,
            selectcolor=self.colors['entry_bg'],
            activebackground=self.colors['bg'],
            activeforeground=self.colors['fg'],
            command=lambda: self.update_config('screen_enabled', self.screen_var.get())
        )
        screen_check.grid(row=0, column=0, columnspan=2, sticky='w', pady=5)

        test_screenshot_btn = tk.Button(
            screen_section,
            text="Test Screenshot Capture",
            command=self.test_screenshot,
            bg='#2196F3',
            fg='white',
            font=self.ui_font_bold,
            relief='flat',
            cursor='hand2',
            width=25
        )
        test_screenshot_btn.grid(row=1, column=0, columnspan=2, pady=10)

        self.test_screenshot_label = tk.Label(
            screen_section,
            text="Captures a screenshot of your display and has the bot react to it",
            bg=self.colors['bg'],
            fg=self.colors['accent'],
            font=(self.ui_font[0], 9, 'italic')
        )
        self.test_screenshot_label.grid(row=2, column=0, columnspan=2, sticky='w', pady=5)

        twitch_section = self.create_section(wrapper, "Twitch Chat Integration", 2)
        twitch_section.grid_columnconfigure(0, weight=1)
        twitch_section.grid_columnconfigure(1, weight=1)

        self.twitch_var = tk.BooleanVar(value=self.config['twitch_enabled'])
        twitch_check = tk.Checkbutton(
            twitch_section,
            text="Enable Twitch Chat",
            variable=self.twitch_var,
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=self.ui_font_bold,
            selectcolor=self.colors['entry_bg'],
            activebackground=self.colors['bg'],
            activeforeground=self.colors['fg'],
            command=lambda: self.update_config('twitch_enabled', self.twitch_var.get())
        )
        twitch_check.grid(row=0, column=0, columnspan=2, sticky='w', pady=5)

        self.twitch_entry = self.create_entry(twitch_section, "Channel Name:", 'twitch_channel', 1)

        tk.Label(
            twitch_section,
            text="━━━ TTS Output Settings ━━━",
            bg=self.colors['bg'],
            fg=self.colors['accent'],
            font=self.ui_font_bold
        ).grid(row=4, column=0, columnspan=2, sticky='w', pady=(15, 5))

        tk.Label(
            twitch_section,
            text="Control what the bot actually SAYS out loud when responding:",
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=(self.ui_font[0], 9, 'italic')
        ).grid(row=5, column=0, columnspan=2, sticky='w', pady=(0, 10))

        tk.Label(twitch_section, text="Speak Username:",
                 bg=self.colors['bg'], fg=self.colors['fg'],
                 font=self.ui_font).grid(row=6, column=0, sticky='w', pady=5)

        self.twitch_speak_username_var = tk.BooleanVar(value=self.config.get('twitch_speak_username', True))
        speak_username_check = tk.Checkbutton(
            twitch_section,
            text='TTS says the username before responding',
            variable=self.twitch_speak_username_var,
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=(self.ui_font[0], 9),
            selectcolor=self.colors['entry_bg'],
            activebackground=self.colors['bg'],
            activeforeground=self.colors['fg'],
            command=lambda: self.update_config('twitch_speak_username', self.twitch_speak_username_var.get())
        )
        speak_username_check.grid(row=6, column=1, sticky='w', pady=5)

        tk.Label(twitch_section, text="Speak Message:",
                 bg=self.colors['bg'], fg=self.colors['fg'],
                 font=self.ui_font).grid(row=7, column=0, sticky='w', pady=5)

        self.twitch_speak_message_var = tk.BooleanVar(value=self.config.get('twitch_speak_message', True))
        speak_message_check = tk.Checkbutton(
            twitch_section,
            text='TTS says the user\'s message before responding',
            variable=self.twitch_speak_message_var,
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=(self.ui_font[0], 9),
            selectcolor=self.colors['entry_bg'],
            activebackground=self.colors['bg'],
            activeforeground=self.colors['fg'],
            command=lambda: self.update_config('twitch_speak_message', self.twitch_speak_message_var.get())
        )
        speak_message_check.grid(row=7, column=1, sticky='w', pady=5)

        tk.Label(twitch_section, text="Strip Emojis:",
                 bg=self.colors['bg'], fg=self.colors['fg'],
                 font=self.ui_font).grid(row=8, column=0, sticky='w', pady=5)

        self.twitch_strip_emojis_var = tk.BooleanVar(value=self.config.get('twitch_strip_emojis', True))
        strip_emojis_check = tk.Checkbutton(
            twitch_section,
            text='Remove emojis from messages before TTS',
            variable=self.twitch_strip_emojis_var,
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=(self.ui_font[0], 9),
            selectcolor=self.colors['entry_bg'],
            activebackground=self.colors['bg'],
            activeforeground=self.colors['fg'],
            command=lambda: self.update_config('twitch_strip_emojis', self.twitch_strip_emojis_var.get())
        )
        strip_emojis_check.grid(row=8, column=1, sticky='w', pady=5)

        tk.Label(
            twitch_section,
            text='Example: When both checked, TTS will say "Username said: their message. [Bot\'s response]"',
            bg=self.colors['bg'],
            fg=self.colors['accent'],
            font=(self.ui_font[0], 8, 'italic'),
            wraplength=500,
            justify='left'
        ).grid(row=9, column=0, columnspan=2, sticky='w', pady=(0, 10))

        tk.Label(
            twitch_section,
            text="━━━ Response Mode ━━━",
            bg=self.colors['bg'],
            fg=self.colors['accent'],
            font=self.ui_font_bold
        ).grid(row=10, column=0, columnspan=2, sticky='w', pady=(15, 5))

        tk.Label(twitch_section, text="Response Mode:",
                 bg=self.colors['bg'], fg=self.colors['fg'],
                 font=self.ui_font).grid(row=10, column=0, sticky='w', pady=5)

        self.twitch_response_mode_var = tk.StringVar(value=self.config.get('twitch_response_mode', 'all'))
        response_modes = ['all', 'keywords', 'random', 'disabled']
        twitch_mode_menu = ttk.Combobox(
            twitch_section,
            textvariable=self.twitch_response_mode_var,
            values=response_modes,
            state='readonly',
            width=15
        )
        twitch_mode_menu.grid(row=11, column=1, sticky='w', pady=5)
        twitch_mode_menu.bind('<<ComboboxSelected>>',
                              lambda e: self.on_twitch_mode_change())

        mode_descriptions = {
            'all': 'Respond to every message (use with cooldown)',
            'keywords': 'Only respond to messages with specific keywords',
            'random': 'Respond randomly based on chance percentage',
            'disabled': 'Read messages but never respond automatically'
        }

        self.twitch_mode_desc = tk.Label(
            twitch_section,
            text=mode_descriptions[self.twitch_response_mode_var.get()],
            bg=self.colors['bg'],
            fg=self.colors['accent'],
            font=(self.ui_font[0], 9, 'italic'),
            wraplength=400,
            justify='left'
        )
        self.twitch_mode_desc.grid(row=12, column=0, columnspan=2, sticky='w', pady=5)

        self.twitch_keywords_frame = tk.Frame(twitch_section, bg=self.colors['bg'])
        self.twitch_keywords_frame.grid(row=13, column=0, columnspan=2, sticky='ew', pady=5)

        tk.Label(
            self.twitch_keywords_frame,
            text="Keywords (comma-separated):",
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=self.ui_font
        ).pack(side='left', padx=5)

        self.twitch_keywords_entry = tk.Entry(
            self.twitch_keywords_frame,
            bg=self.colors['entry_bg'],
            fg=self.colors['fg'],
            font=self.ui_font,
            width=30,
            insertbackground=self.colors['fg']
        )
        self.twitch_keywords_entry.pack(side='left', padx=5)
        self.twitch_keywords_entry.insert(0, self.config.get('twitch_keywords', '!ai,!bot,!ask'))
        self.twitch_keywords_entry.bind('<FocusOut>',
                                        lambda e: self.update_config('twitch_keywords',
                                                                     self.twitch_keywords_entry.get()))

        self.twitch_chance_frame = tk.Frame(twitch_section, bg=self.colors['bg'])
        self.twitch_chance_frame.grid(row=14, column=0, columnspan=2, sticky='w', pady=5)

        tk.Label(
            self.twitch_chance_frame,
            text="Response Chance:",
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=self.ui_font
        ).pack(side='left', padx=5)

        self.twitch_chance_var = tk.IntVar(value=self.config.get('twitch_response_chance', 100))
        chance_slider = tk.Scale(
            self.twitch_chance_frame,
            from_=1,
            to=100,
            orient='horizontal',
            variable=self.twitch_chance_var,
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            highlightthickness=0,
            length=150,
            command=lambda v: self.update_config('twitch_response_chance', int(float(v)))
        )
        chance_slider.pack(side='left', padx=5)

        self.chance_label = tk.Label(
            self.twitch_chance_frame,
            text=f"{self.twitch_chance_var.get()}%",
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=(self.ui_font[0], 9)
        )
        self.chance_label.pack(side='left', padx=5)

        chance_slider.config(command=lambda v: self.update_chance_label(int(float(v))))

        tk.Label(twitch_section, text="Response Cooldown:",
                 bg=self.colors['bg'], fg=self.colors['fg'],
                 font=self.ui_font).grid(row=15, column=0, sticky='w', pady=5)

        cooldown_frame = tk.Frame(twitch_section, bg=self.colors['bg'])
        cooldown_frame.grid(row=15, column=1, sticky='w', pady=5)

        self.twitch_cooldown_var = tk.IntVar(value=self.config.get('twitch_cooldown', 5))
        cooldown_slider = tk.Scale(
            cooldown_frame,
            from_=0,
            to=60,
            orient='horizontal',
            variable=self.twitch_cooldown_var,
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            highlightthickness=0,
            length=150,
            command=lambda v: self.update_config('twitch_cooldown', int(float(v)))
        )
        cooldown_slider.pack(side='left', padx=5)

        self.cooldown_label = tk.Label(
            cooldown_frame,
            text=f"{self.twitch_cooldown_var.get()}s",
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=(self.ui_font[0], 9)
        )
        self.cooldown_label.pack(side='left', padx=5)

        cooldown_slider.config(command=lambda v: self.update_cooldown_label(int(float(v))))

        # Username Blacklist Section
        tk.Label(
            twitch_section,
            text="━━━ Username Blacklist ━━━",
            bg=self.colors['bg'],
            fg=self.colors['accent'],
            font=self.ui_font_bold
        ).grid(row=20, column=0, columnspan=2, sticky='w', pady=(15, 5))

        tk.Label(
            twitch_section,
            text="Blacklisted Usernames:",
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=self.ui_font
        ).grid(row=21, column=0, sticky='nw', pady=5)

        self.username_blacklist_text = tk.Text(
            twitch_section,
            width=40,
            height=4,
            bg=self.colors['entry_bg'],
            fg=self.colors['fg'],
            font=(self.ui_font[0], 9),
            insertbackground=self.colors['accent']
        )
        self.username_blacklist_text.grid(row=21, column=1, sticky='w', pady=5)

        blacklist = self.config.get('twitch_username_blacklist', [])
        self.username_blacklist_text.insert('1.0', '\n'.join(blacklist))

        tk.Label(
            twitch_section,
            text='One username per line. Bot ignores these users completely.',
            bg=self.colors['bg'],
            fg=self.colors['accent'],
            font=(self.ui_font[0], 8, 'italic'),
            wraplength=500,
            justify='left'
        ).grid(row=22, column=0, columnspan=2, sticky='w', pady=(0, 10))

        # Emote Prefix Blacklist Section
        tk.Label(
            twitch_section,
            text="━━━ Emote Prefix Blacklist ━━━",
            bg=self.colors['bg'],
            fg=self.colors['accent'],
            font=self.ui_font_bold
        ).grid(row=23, column=0, columnspan=2, sticky='w', pady=(15, 5))

        tk.Label(
            twitch_section,
            text="Blacklisted Emote Prefixes:",
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=self.ui_font
        ).grid(row=24, column=0, sticky='nw', pady=5)

        self.emote_prefix_blacklist_text = tk.Text(
            twitch_section,
            width=40,
            height=4,
            bg=self.colors['entry_bg'],
            fg=self.colors['fg'],
            font=(self.ui_font[0], 9),
            insertbackground=self.colors['accent']
        )
        self.emote_prefix_blacklist_text.grid(row=24, column=1, sticky='w', pady=5)

        prefix_blacklist = self.config.get('twitch_emote_prefix_blacklist', [])
        self.emote_prefix_blacklist_text.insert('1.0', '\n'.join(prefix_blacklist))

        tk.Label(
            twitch_section,
            text='One prefix per line. Filters custom emotes starting with these.\nExample: "bttv" blocks :bttv_emotename:',
            bg=self.colors['bg'],
            fg=self.colors['accent'],
            font=(self.ui_font[0], 8, 'italic'),
            wraplength=500,
            justify='left'
        ).grid(row=25, column=0, columnspan=2, sticky='w', pady=(0, 10))

        # Rate Limit Response Section
        tk.Label(
            twitch_section,
            text="━━━ Rate Limit Handling ━━━",
            bg=self.colors['bg'],
            fg=self.colors['accent'],
            font=self.ui_font_bold
        ).grid(row=26, column=0, columnspan=2, sticky='w', pady=(15, 5))

        tk.Label(
            twitch_section,
            text="Rate Limit Response:",
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=self.ui_font
        ).grid(row=27, column=0, sticky='nw', pady=5)

        self.rate_limit_response_text = tk.Text(
            twitch_section,
            width=40,
            height=3,
            bg=self.colors['entry_bg'],
            fg=self.colors['fg'],
            font=(self.ui_font[0], 9),
            insertbackground=self.colors['accent']
        )
        self.rate_limit_response_text.grid(row=27, column=1, sticky='w', pady=5)

        rate_limit_msg = self.config.get('rate_limit_response', "I'm a bit overwhelmed right now, give me a moment!")
        self.rate_limit_response_text.insert('1.0', rate_limit_msg)

        tk.Label(
            twitch_section,
            text='Message bot says when rate limited by AI model.',
            bg=self.colors['bg'],
            fg=self.colors['accent'],
            font=(self.ui_font[0], 8, 'italic'),
            wraplength=500,
            justify='left'
        ).grid(row=28, column=0, columnspan=2, sticky='w', pady=(0, 10))

        # Save Button
        save_twitch_btn = tk.Button(
            twitch_section,
            text='💾 Save Twitch Settings',
            command=self.save_twitch_blacklists,
            bg=self.colors['button'],
            fg='white',
            font=self.ui_font_bold,
            relief='flat',
            cursor='hand2',
            padx=20,
            pady=10
        )
        save_twitch_btn.grid(row=29, column=0, columnspan=2, pady=20)

        tk.Label(
            twitch_section,
            text="Cooldown prevents spam - set to 0 to respond immediately to every message, which is probably a bad idea",
            bg=self.colors['bg'],
            fg=self.colors['accent'],
            font=(self.ui_font[0], 9, 'italic'),
            wraplength=500,
            justify='left'
        ).grid(row=16, column=0, columnspan=2, sticky='w', pady=5)

        self.update_twitch_mode_visibility()

    def on_mic_device_change(self):
        """Save microphone device when changed"""
        device = self.mic_device_var.get()
        self.update_config('mic_device', device)
        print(f"[App] Microphone device saved: {device}")

    def on_twitch_mode_change(self):
        """Handle Twitch response mode change"""
        mode = self.twitch_response_mode_var.get()
        self.update_config('twitch_response_mode', mode)

        mode_descriptions = {
            'all': 'Respond to every message (use with cooldown!)',
            'keywords': 'Only respond to messages with specific keywords',
            'random': 'Respond randomly based on chance percentage',
            'disabled': 'Read messages but never respond automatically'
        }
        self.twitch_mode_desc.config(text=mode_descriptions[mode])

        self.update_twitch_mode_visibility()

    def update_twitch_mode_visibility(self):
        """Show/hide Twitch settings based on mode"""
        mode = self.twitch_response_mode_var.get()

        if mode == 'keywords':
            self.twitch_keywords_frame.grid()
        else:
            self.twitch_keywords_frame.grid_remove()

        if mode == 'random':
            self.twitch_chance_frame.grid()
        else:
            self.twitch_chance_frame.grid_remove()

    def update_chance_label(self, value):
        """Update response chance label"""
        self.chance_label.config(text=f"{value}%")
        self.update_config('twitch_response_chance', value)

    def update_cooldown_label(self, value):
        """Update cooldown label"""
        self.cooldown_label.config(text=f"{value}s")
        self.update_config('twitch_cooldown', value)

    def setup_push_to_talk(self):
        """Setup push-to-talk and screenshot hotkeys"""
        try:
            # Microphone hotkey
            mic_hotkey = self.config.get('hotkey_toggle', 'f4').lower()
            keyboard.on_press_key(mic_hotkey, self.on_push_to_talk_press)
            keyboard.on_release_key(mic_hotkey, self.on_push_to_talk_release)
            print(f"[App] Microphone hotkey ({mic_hotkey}) activated")

            # Screenshot hotkey
            screenshot_hotkey = self.config.get('hotkey_screenshot', 'f5').lower()
            keyboard.on_press_key(screenshot_hotkey, self.on_screenshot_hotkey_press)
            print(f"[App] Screenshot hotkey ({screenshot_hotkey}) activated")

            self.hotkey_active = True

        except Exception as e:
            print(f"[App] Hotkey setup failed: {e}")

    def on_screenshot_hotkey_press(self, event):
        """When screenshot hotkey is pressed"""
        if self.engine.is_running and not self.is_recording:
            print("[App] Screenshot hotkey pressed")
            # Run screenshot in a thread to avoid blocking
            threading.Thread(target=self.screenshot_and_respond, daemon=True).start()

    def on_push_to_talk_press(self, event):
        """When push-to-talk key is pressed"""
        if not self.is_recording and self.engine.is_running:
            self.is_recording = True
            self.recording_label.config(text="🔴 RECORDING... (release to send)")
            threading.Thread(target=self.start_recording, daemon=True).start()

    def on_push_to_talk_release(self, event):
        """When push-to-talk key is released"""
        if self.is_recording:
            self.is_recording = False
            self.recording_label.config(text="")

    def start_recording(self):
        """Start recording audio"""
        if not self.engine.is_running or not self.is_recording:
            return

        self.add_chat_message("System", "Listening...")

        import time
        start_time = time.time()

        while self.is_recording and (time.time() - start_time) < 10:
            time.sleep(0.1)

        if time.time() - start_time > 0.5:
            self.engine.process_microphone_input()

    def remove_hotkeys(self):
        """Remove all hotkeys"""
        if self.hotkey_active:
            try:
                keyboard.unhook_all()
                self.hotkey_active = False
                print("[App] Hotkeys removed")
            except:
                pass

    def create_avatar_tab(self, notebook):
        """Avatar tab with audio-reactive controls"""
        tab = tk.Frame(notebook, bg=self.colors['bg'])
        notebook.add(tab, text='Avatar')

        scrollable = self.create_scrollable_frame(tab)
        wrapper = tk.Frame(scrollable, bg=self.colors['bg'])
        wrapper.pack(fill='both', expand=True, padx=(35, 0), pady=20)

        images_section = self.create_section(wrapper, "Select Avatar Images", 0)
        images_section.grid_columnconfigure(0, weight=1)

        speaking_frame = tk.Frame(images_section, bg=self.colors['bg'])
        speaking_frame.pack(fill='x', pady=10)

        tk.Label(
            speaking_frame,
            text="Speaking Image:",
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=self.ui_font_bold,
            width=18,
            anchor='w'
        ).pack(side='left', padx=5)

        self.speaking_path_label = tk.Label(
            speaking_frame,
            text=self.config.get('speaking_image', 'Not selected') or 'Not selected',
            bg=self.colors['entry_bg'],
            fg=self.colors['fg'],
            font=(self.ui_font[0], 9),
            relief='sunken',
            anchor='w',
            padx=10,
            pady=5
        )
        self.speaking_path_label.pack(side='left', fill='x', expand=True, padx=5)

        tk.Button(
            speaking_frame,
            text="Browse",
            command=lambda: self.browse_image('speaking'),
            bg=self.colors['button'],
            fg='white',
            font=self.ui_font_bold,
            relief='raised',
            borderwidth=2,
            cursor='hand2',
            padx=15,
            pady=5
        ).pack(side='left', padx=5)

        idle_frame = tk.Frame(images_section, bg=self.colors['bg'])
        idle_frame.pack(fill='x', pady=10)

        tk.Label(
            idle_frame,
            text="Idle Image:",
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=self.ui_font_bold,
            width=18,
            anchor='w'
        ).pack(side='left', padx=5)

        self.idle_path_label = tk.Label(
            idle_frame,
            text=self.config.get('idle_image', 'Not selected') or 'Not selected',
            bg=self.colors['entry_bg'],
            fg=self.colors['fg'],
            font=(self.ui_font[0], 9),
            relief='sunken',
            anchor='w',
            padx=10,
            pady=5
        )
        self.idle_path_label.pack(side='left', fill='x', expand=True, padx=5)

        tk.Button(
            idle_frame,
            text="Browse",
            command=lambda: self.browse_image('idle'),
            bg=self.colors['button'],
            fg='white',
            font=self.ui_font_bold,
            relief='raised',
            borderwidth=2,
            cursor='hand2',
            padx=15,
            pady=5
        ).pack(side='left', padx=5)

        sensitivity_section = self.create_section(wrapper, "Audio Sensitivity Controls", 1)
        sensitivity_section.grid_columnconfigure(0, weight=1)

        tk.Label(
            sensitivity_section,
            text="Fine-tune the appearance of the png mouth movement",
            bg=self.colors['bg'],
            fg=self.colors['accent'],
            font=(self.ui_font[0], 10, 'italic')
        ).pack(pady=(0, 15))

        slider_frame = tk.Frame(sensitivity_section, bg=self.colors['bg'])
        slider_frame.pack(fill='x', padx=20, pady=10)

        tk.Label(
            slider_frame,
            text="Volume Threshold:",
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=self.ui_font_bold
        ).pack(side='left', padx=10)

        self.volume_threshold_var = tk.DoubleVar(value=self.config.get('volume_threshold', 0.02))

        threshold_slider = tk.Scale(
            slider_frame,
            from_=0.005,
            to=0.75,
            resolution=0.001,
            orient='horizontal',
            variable=self.volume_threshold_var,
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            highlightthickness=0,
            length=300,
            command=self.on_threshold_change
        )
        threshold_slider.pack(side='left', padx=10)

        self.threshold_label = tk.Label(
            slider_frame,
            text=f"{self.volume_threshold_var.get():.3f}",
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=self.ui_font_bold,
            width=8
        )
        self.threshold_label.pack(side='left', padx=5)

        guide_frame = tk.Frame(sensitivity_section, bg=self.colors['bg'])
        guide_frame.pack(fill='x', padx=40, pady=10)

        tk.Label(
            guide_frame,
            text="← MORE SENSITIVE (opens easily)",
            bg=self.colors['bg'],
            fg='#4CAF50',
            font=(self.ui_font[0], 9)
        ).pack(side='left')

        tk.Label(
            guide_frame,
            text="LESS SENSITIVE (requires louder audio) →",
            bg=self.colors['bg'],
            fg='#FF6B6B',
            font=(self.ui_font[0], 9)
        ).pack(side='right')

        meter_section = self.create_section(wrapper, "Real-Time Audio Meter", 2)
        meter_section.grid_columnconfigure(0, weight=1)

        tk.Label(
            meter_section,
            text="Watch the meter during speech to see when the png will change",
            bg=self.colors['bg'],
            fg=self.colors['accent'],
            font=(self.ui_font[0], 9, 'italic')
        ).pack(pady=(0, 10))

        meter_frame = tk.Frame(meter_section, bg=self.colors['accent'], bd=3, relief='solid')
        meter_frame.pack(padx=40, pady=10)

        self.audio_meter = tk.Canvas(
            meter_frame,
            width=500,
            height=80,
            bg='#0D0505',
            highlightthickness=0
        )
        self.audio_meter.pack(padx=3, pady=3)

        self.meter_threshold_line = None
        self.meter_volume_bar = None
        self.update_meter_threshold_line()

        meter_label_frame = tk.Frame(meter_section, bg=self.colors['bg'])
        meter_label_frame.pack()

        self.meter_status_label = tk.Label(
            meter_label_frame,
            text="IDLE (no audio)",
            bg=self.colors['bg'],
            fg=self.colors['accent'],
            font=self.ui_font_bold
        )
        self.meter_status_label.pack(pady=5)

        self.meter_value_label = tk.Label(
            meter_label_frame,
            text="Volume: 0.000",
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=(self.ui_font[0], 9)
        )
        self.meter_value_label.pack()

        test_frame = tk.Frame(meter_section, bg=self.colors['bg'])
        test_frame.pack(pady=15)

        tk.Button(
            test_frame,
            text="Test Audio Sensitivity",
            command=self.test_audio_sensitivity,
            bg='#2196F3',
            fg='white',
            font=self.ui_font_bold,
            relief='raised',
            borderwidth=3,
            cursor='hand2',
            padx=20,
            pady=10
        ).pack()

        tk.Label(
            test_frame,
            text="Plays test audio - watch meter and avatar to fine-tune sensitivity",
            bg=self.colors['bg'],
            fg=self.colors['accent'],
            font=(self.ui_font[0], 8, 'italic')
        ).pack(pady=5)

        # Background Color Settings Section
        bg_color_section = self.create_section(wrapper, "Background Color Settings", 3)
        bg_color_section.grid_columnconfigure(0, weight=1)

        tk.Label(
            bg_color_section,
            text="Choose the background color for the avatar window.\n"
                 "Use green (#00FF00) for OBS chroma key removal.",
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=self.ui_font,
            justify='left'
        ).pack(pady=(0, 10))

        color_frame = tk.Frame(bg_color_section, bg=self.colors['bg'])
        color_frame.pack(fill='x', pady=10)

        tk.Label(
            color_frame,
            text="Background Color:",
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=self.ui_font_bold,
            width=18,
            anchor='w'
        ).pack(side='left', padx=5)

        # Color preview box
        self.avatar_bg_color_preview = tk.Frame(
            color_frame,
            bg=self.config.get('avatar_bg_color', '#00FF00'),
            width=50,
            height=30,
            relief='solid',
            borderwidth=2
        )
        self.avatar_bg_color_preview.pack(side='left', padx=5)
        self.avatar_bg_color_preview.pack_propagate(False)

        # Color entry
        self.avatar_bg_color_var = tk.StringVar(value=self.config.get('avatar_bg_color', '#00FF00'))
        color_entry = tk.Entry(
            color_frame,
            textvariable=self.avatar_bg_color_var,
            bg=self.colors['entry_bg'],
            fg=self.colors['fg'],
            font=self.ui_font,
            width=15,
            insertbackground=self.colors['fg']
        )
        color_entry.pack(side='left', padx=5)
        color_entry.bind('<KeyRelease>', self.on_avatar_color_change)

        tk.Button(
            color_frame,
            text="Pick Color",
            command=self.pick_avatar_color,
            bg=self.colors['button'],
            fg='white',
            font=self.ui_font_bold,
            relief='raised',
            borderwidth=2,
            cursor='hand2',
            padx=15,
            pady=5
        ).pack(side='left', padx=5)

        # Preset colors
        preset_frame = tk.Frame(bg_color_section, bg=self.colors['bg'])
        preset_frame.pack(fill='x', pady=10)

        tk.Label(
            preset_frame,
            text="Preset Colors:",
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=self.ui_font,
            width=18,
            anchor='w'
        ).pack(side='left', padx=5)

        presets = [
            ("#00FF00", "Green (Chroma)"),
            ("#FF00FF", "Magenta"),
            ("#0000FF", "Blue"),
            ("#000000", "Black"),
            ("#FFFFFF", "White"),
        ]

        for color, name in presets:
            btn = tk.Button(
                preset_frame,
                text=name,
                command=lambda c=color: self.set_avatar_color(c),
                bg=color,
                fg='white' if color in ['#00FF00', '#0000FF', '#000000', '#FF00FF'] else 'black',
                font=(self.ui_font[0], 8),
                relief='raised',
                borderwidth=2,
                cursor='hand2',
                width=12
            )
            btn.pack(side='left', padx=2)

        # Apply button
        apply_frame = tk.Frame(bg_color_section, bg=self.colors['bg'])
        apply_frame.pack(pady=15)

        tk.Button(
            apply_frame,
            text="Apply Color & Reload Avatar",
            command=self.apply_avatar_color,
            bg='#9370DB',
            fg='white',
            font=self.ui_font_bold,
            relief='raised',
            borderwidth=3,
            cursor='hand2',
            padx=20,
            pady=10
        ).pack()

        tk.Label(
            apply_frame,
            text="Click after changing color to update the avatar window",
            bg=self.colors['bg'],
            fg=self.colors['accent'],
            font=(self.ui_font[0], 8, 'italic')
        ).pack(pady=5)

        controls_section = self.create_section(wrapper, "Avatar Window Controls", 4)
        controls_section.grid_columnconfigure(0, weight=1)

        control_frame = tk.Frame(controls_section, bg=self.colors['bg'])
        control_frame.pack(pady=10)

        self.avatar_window_btn = tk.Button(
            control_frame,
            text="Show Avatar Window",
            command=self.toggle_avatar_window,
            bg='#2196F3',
            fg='white',
            font=self.ui_font_bold,
            relief='raised',
            borderwidth=3,
            cursor='hand2',
            width=25,
            height=2
        )
        self.avatar_window_btn.pack(pady=5)

        self.avatar_status_label = tk.Label(
            control_frame,
            text="⚫ Window Hidden",
            bg=self.colors['bg'],
            fg=self.colors['accent'],
            font=(self.ui_font[0], 10, 'italic')
        )
        self.avatar_status_label.pack(pady=5)

        tk.Label(
            controls_section,
            text="Tip: Keep the window open but hidden behind other windows so that OBS can keep the capture active",
            bg=self.colors['bg'],
            fg=self.colors['accent'],
            font=(self.ui_font[0], 9, 'italic'),
            justify='center'
        ).pack(pady=10)

        self.start_audio_meter_updates()

    def choose_avatar_color(self):
        """Open color picker for avatar background"""
        from tkinter import colorchooser

        current_color = self.config.get('avatar_bg_color', '#00FF00')
        color = colorchooser.askcolor(
            color=current_color,
            title="Choose Avatar Background Color"
        )

        if color and color[1]:
            self.set_avatar_color(color[1].upper())

    def set_avatar_color(self, hex_color):
        """Set avatar background color"""
        # Update config
        self.update_config('avatar_bg_color', hex_color)

        # Update preview box
        self.color_preview.config(bg=hex_color)
        self.color_value_label.config(text=hex_color)

        # Update avatar window if it exists and is visible
        if self.engine.avatar_window:
            try:
                self.engine.avatar_window.set_background_color(hex_color)
                print(f"[App] Updated avatar background to {hex_color}")
            except Exception as e:
                print(f"[App] Error updating avatar color: {e}")

        # Save to config file
        self.save_all_settings()

    def on_avatar_color_change(self, event=None):
        """Update color preview when user types"""
        color = self.avatar_bg_color_var.get()
        try:
            # Validate hex color
            if color.startswith('#') and len(color) == 7:
                # Test if valid hex
                int(color[1:], 16)
                self.avatar_bg_color_preview.config(bg=color)
                self.update_config('avatar_bg_color', color)
        except:
            pass  # Invalid color, don't update

    def set_avatar_color(self, color):
        """Set avatar background color from preset"""
        self.avatar_bg_color_var.set(color)
        self.avatar_bg_color_preview.config(bg=color)
        self.update_config('avatar_bg_color', color)

    def pick_avatar_color(self):
        """Open color picker dialog"""
        from tkinter import colorchooser

        current_color = self.avatar_bg_color_var.get()
        color = colorchooser.askcolor(
            color=current_color,
            title="Choose Avatar Background Color"
        )

        if color[1]:  # color[1] is the hex string
            self.set_avatar_color(color[1])

    def apply_avatar_color(self):
        """Apply the new background color to the avatar window"""
        if not self.engine.avatar_window:
            messagebox.showinfo(
                "No Avatar Window",
                "The avatar window is not open yet.\n\n"
                "Open the avatar window first, then apply the color."
            )
            return

        color = self.avatar_bg_color_var.get()

        print(f"[App] Applying avatar color: {color}")

        # Update window background color
        try:
            self.engine.avatar_window.window.configure(bg=color)
            self.engine.avatar_window.image_label.config(bg=color)

            messagebox.showinfo(
                "Color Applied",
                f"✅ Background color changed to {color}"
            )

        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Failed to apply color:\n{e}"
            )

    def on_threshold_change(self, value):
        """Called when threshold slider changes"""
        threshold = float(value)
        self.threshold_label.config(text=f"{threshold:.3f}")
        self.update_config('volume_threshold', threshold)

        if self.engine and self.engine.is_running:
            self.engine.set_volume_threshold(threshold)

        self.update_meter_threshold_line()

    def update_meter_threshold_line(self):
        """Update the threshold indicator line on the audio meter"""
        if not hasattr(self, 'audio_meter'):
            return

        if self.meter_threshold_line:
            self.audio_meter.delete(self.meter_threshold_line)

        threshold = self.volume_threshold_var.get()
        x_pos = int((threshold / 0.75) * 500)

        self.meter_threshold_line = self.audio_meter.create_line(
            x_pos, 0, x_pos, 80,
            fill='#FFD700',
            width=2,
            dash=(5, 5)
        )

        self.audio_meter.create_text(
            x_pos, 10,
            text="THRESHOLD",
            fill='#FFD700',
            font=(self.ui_font[0], 8, 'bold'),
            anchor='s'
        )

    def start_audio_meter_updates(self):
        """Start updating the audio meter in real-time"""
        def update_meter():
            if self.engine and self.engine.tts and self.engine.is_speaking:
                volume = self.engine.tts.get_current_volume()
                self.update_audio_meter(volume)
            else:
                self.update_audio_meter(0.0)

            self.root.after(16, update_meter)

        self.root.after(100, update_meter)

    def update_audio_meter(self, volume):
        """Update the audio meter visualization"""
        if not hasattr(self, 'audio_meter'):
            return

        if self.meter_volume_bar:
            self.audio_meter.delete(self.meter_volume_bar)

        normalized_volume = min(volume, 0.75)
        bar_width = int((normalized_volume / 0.75) * 500)

        threshold = self.volume_threshold_var.get()
        if volume > threshold:
            color = '#4CAF50'
            status = "SPEAKING"
            status_color = '#4CAF50'
        else:
            color = '#FF6B6B'
            status = "IDLE"
            status_color = '#FF6B6B'

        if bar_width > 0:
            self.meter_volume_bar = self.audio_meter.create_rectangle(
                0, 0, bar_width, 80,
                fill=color,
                outline=''
            )

        self.meter_status_label.config(text=status, fg=status_color)
        self.meter_value_label.config(text=f"Volume: {volume:.3f}")

        if self.meter_threshold_line:
            self.audio_meter.tag_raise(self.meter_threshold_line)

    def test_audio_sensitivity(self):
        """Test audio sensitivity with sample speech"""
        if not self.engine or not self.engine.is_running:
            messagebox.showwarning(
                "Chatbot Not Running",
                "Please start the chatbot first to test audio sensitivity!"
            )
            return

        test_text = (
            "Testing audio sensitivity. "
            "Watch the audio meter and avatar. "
            "The mouth should open when volume is above the threshold. "
            "Try adjusting the sensitivity slider if needed."
        )

        self.add_chat_message("System", "Testing audio sensitivity - watch the meter and avatar!")

        def test_thread():
            self.engine._speak_response(test_text)

        threading.Thread(target=test_thread, daemon=True).start()

    def toggle_avatar_window(self):
        """Toggle the avatar window visibility with better error handling"""
        print("[App] Toggle avatar window called")

        if not self.engine.avatar_window:
            # Need to create window first
            idle = self.config.get('idle_image', '')
            speaking = self.config.get('speaking_image', '')

            print(f"[App] Idle: {idle}")
            print(f"[App] Speaking: {speaking}")

            # Validate image configuration
            if not idle or not speaking:
                messagebox.showwarning(
                    "Images Not Set",
                    "Please select both idle and speaking images first!\n\n"
                    "Use the Browse buttons in the Avatar tab to select your images."
                )
                return

            if not Path(idle).exists():
                messagebox.showerror(
                    "Image Not Found",
                    f"Idle image file not found:\n{idle}\n\n"
                    f"Please check the file path and try again."
                )
                return

            if not Path(speaking).exists():
                messagebox.showerror(
                    "Image Not Found",
                    f"Speaking image file not found:\n{speaking}\n\n"
                    f"Please check the file path and try again."
                )
                return

            # Try to create avatar window
            print("[App] Creating avatar window...")
            success = self.engine._load_images()

            if not success or not self.engine.avatar_window:
                messagebox.showerror(
                    "Failed to Load Avatar",
                    "Could not create avatar window.\n\n"
                    "Check the console for error details.\n"
                    "Make sure your image files are valid PNG/JPG files."
                )
                return

            # Show the window
            self.engine.avatar_window.show()
            self.avatar_window_btn.config(text="Hide Avatar Window")
            self.avatar_status_label.config(text="🟢 Window Visible", fg='#4CAF50')
            print("[App] ✅ Avatar window shown")

        else:
            # Toggle existing window
            is_visible = self.engine.toggle_avatar_window()
            if is_visible:
                self.avatar_window_btn.config(text="Hide Avatar Window")
                self.avatar_status_label.config(text="🟢 Window Visible", fg='#4CAF50')
                print("[App] Avatar window shown")
            else:
                self.avatar_window_btn.config(text="Show Avatar Window")
                self.avatar_status_label.config(text="⚫ Window Hidden", fg=self.colors['accent'])
                print("[App] Avatar window hidden")

    def reload_avatar_images(self):
        """Reload avatar images with better error handling"""
        print("[App] Reloading avatar images...")

        idle = self.config.get('idle_image', '')
        speaking = self.config.get('speaking_image', '')

        # Validate
        if not idle or not speaking:
            messagebox.showwarning(
                "Images Not Set",
                "Please select both idle and speaking images first!"
            )
            return

        if not Path(idle).exists():
            messagebox.showerror(
                "Image Not Found",
                f"Idle image file not found:\n{idle}"
            )
            return

        if not Path(speaking).exists():
            messagebox.showerror(
                "Image Not Found",
                f"Speaking image file not found:\n{speaking}"
            )
            return

        # Reload
        success = self.engine._load_images()

        if success:
            messagebox.showinfo(
                "Success",
                "✅ Avatar images reloaded successfully!\n\n"
                "The avatar window will now use the new images."
            )
            print("[App] ✅ Images reloaded")
        else:
            messagebox.showerror(
                "Failed to Reload",
                "Could not reload avatar images.\n\n"
                "Check the console for error details."
            )
            print("[App] ❌ Failed to reload images")

    def browse_image(self, image_type):
        """Browse for avatar image with better error handling"""
        filename = filedialog.askopenfilename(
            title=f"Select {image_type} image",
            filetypes=[
                ("PNG files", "*.png"),
                ("JPEG files", "*.jpg *.jpeg"),
                ("All image files", "*.png *.jpg *.jpeg *.gif *.bmp"),
                ("All files", "*.*")
            ]
        )

        if filename:
            print(f"[App] Selected {image_type} image: {filename}")

            # Validate the file can be opened
            try:
                from PIL import Image
                test_img = Image.open(filename)
                test_img.close()
                print(f"[App] ✅ Image file is valid")
            except Exception as e:
                messagebox.showerror(
                    "Invalid Image",
                    f"Could not open the selected image file:\n{filename}\n\n"
                    f"Error: {e}\n\n"
                    f"Please select a valid image file."
                )
                return

            # Update config
            config_key = f'{image_type}_image'
            self.update_config(config_key, filename)
            self.save_all_settings()

            # Update UI display
            display_path = filename
            if len(filename) > 60:
                path_parts = filename.split('/')
                if len(path_parts) > 1:
                    display_path = f".../{path_parts[-2]}/{path_parts[-1]}"
                else:
                    display_path = f"...{filename[-57:]}"

            if image_type == 'speaking':
                self.speaking_path_label.config(text=display_path, fg=self.colors['fg'])
            else:
                self.idle_path_label.config(text=display_path, fg=self.colors['fg'])

            # Update preview
            # self.update_avatar_preview(filename)

            # Auto-reload in avatar window if it exists
            if self.engine.avatar_window:
                print(f"[App] Auto-reloading {image_type} image in avatar window...")
                success = self.engine._load_images()
                if success:
                    print(f"[App] ✅ Auto-reload successful")
                else:
                    print(f"[App] ⚠️ Auto-reload failed")

    def create_control_panel(self, parent):
        """Create bottom control panel"""
        panel = tk.Frame(parent, bg=self.colors['accent'])
        panel.pack(fill='x', side='bottom')

        inner = tk.Frame(panel, bg=self.colors['accent'])
        inner.pack(fill='x', padx=20, pady=15)

        left_frame = tk.Frame(inner, bg=self.colors['accent'])
        left_frame.pack(side='left')

        self.status_label = tk.Label(
            left_frame,
            text="⚫ Stopped",
            bg=self.colors['accent'],
            fg='white',
            font=self.ui_font_bold
        )
        self.status_label.pack(anchor='w')

        self.recording_label = tk.Label(
            left_frame,
            text="",
            bg=self.colors['accent'],
            fg='#FFD700',
            font=self.ui_font
        )
        self.recording_label.pack(anchor='w')

        right_frame = tk.Frame(inner, bg=self.colors['accent'])
        right_frame.pack(side='right')

        buttons_frame = tk.Frame(right_frame, bg=self.colors['accent'])
        buttons_frame.pack()

        update_btn = tk.Button(
            buttons_frame,
            text="🔄 Check for Updates",
            command=self.manual_update_check,
            bg='#FF6B6B',
            fg='white',
            font=self.ui_font_bold,
            relief='raised',
            borderwidth=3,
            cursor='hand2',
            padx=15,
            pady=10
        )
        update_btn.pack(side='left', padx=5)

        save_btn = tk.Button(
            buttons_frame,
            text="💾 Save Settings",
            command=self.save_all_settings,
            bg=self.colors['button'],
            fg='white',
            font=self.ui_font_bold,
            relief='raised',
            borderwidth=3,
            cursor='hand2',
            padx=15,
            pady=10
        )
        save_btn.pack(side='left', padx=5)

        self.start_btn = tk.Button(
            buttons_frame,
            text="▶️ Start Chatbot",
            command=self.toggle_chatbot,
            bg='#4CAF50',
            fg='white',
            font=(self.ui_font[0], 13, 'bold'),
            relief='raised',
            borderwidth=3,
            cursor='hand2',
            padx=20,
            pady=10
        )
        self.start_btn.pack(side='left', padx=5)

    def create_section(self, parent, title, row):
        """Create labeled section"""
        outer = tk.Frame(parent, bg=self.colors['bg'])
        outer.pack(fill='x', padx=30, pady=15)

        section = tk.Frame(outer, bg=self.colors['bg'])
        section.pack(anchor='center')

        title_frame = tk.Frame(section, bg=self.colors['bg'])
        title_frame.pack(fill='x', pady=(0, 10))

        tk.Label(
            title_frame,
            text=title,
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=self.ui_font_bold
        ).pack(anchor='center')

        separator = tk.Frame(title_frame, bg=self.colors['accent'], height=2)
        separator.pack(fill='x', pady=(5, 0))

        frame = tk.Frame(section, bg=self.colors['bg'])
        frame.pack(fill='both', padx=10)

        return frame

    def create_entry(self, parent, label, config_key, row):
        """Create labeled entry"""
        tk.Label(
            parent,
            text=label,
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=self.ui_font
        ).grid(row=row, column=0, sticky='e', pady=5, padx=(0, 10))

        entry = tk.Entry(
            parent,
            bg=self.colors['entry_bg'],
            fg=self.colors['fg'],
            font=self.ui_font,
            width=30,
            insertbackground=self.colors['fg']
        )
        entry.grid(row=row, column=1, sticky='w', pady=5, padx=(10, 0))
        entry.insert(0, self.config[config_key])
        entry.bind('<FocusOut>',
                   lambda e, key=config_key: self.update_config(key, entry.get()))

        return entry

    def auto_load_elevenlabs_voices(self):
        """Auto-load ElevenLabs voices if API key is configured"""
        if self.config.get('tts_service') == 'elevenlabs':
            api_key = os.getenv('ELEVENLABS_API_KEY')

            if api_key and api_key != 'your-elevenlabs-key-here' and len(api_key) > 10:
                print("[App] Auto-loading ElevenLabs voices...")

                def load_voices_thread():
                    try:
                        time.sleep(0.5)
                        self.refresh_elevenlabs_voices()
                    except Exception as e:
                        print(f"[App] Auto-load failed: {e}")

                threading.Thread(target=load_voices_thread, daemon=True).start()

    def refresh_microphone_list(self):
        """Refresh list of available microphones (INPUT DEVICES ONLY)"""
        try:
            import pyaudio

            print("[App] Refreshing microphone list...")

            # Initialize PyAudio to enumerate devices
            p = pyaudio.PyAudio()
            device_count = p.get_device_count()

            print(f"[App] Scanning {device_count} audio devices...")

            # Collect ONLY input devices (microphones)
            mic_list = []

            for i in range(device_count):
                try:
                    info = p.get_device_info_by_index(i)
                    name = info.get('name', 'Unknown')
                    max_input = info.get('maxInputChannels', 0)
                    max_output = info.get('maxOutputChannels', 0)

                    # ONLY add devices that have INPUT channels
                    if max_input > 0:
                        mic_list.append(name)
                        print(f"[App]   ✓ MIC:     {name} (IN:{max_input} OUT:{max_output})")
                    else:
                        print(f"[App]   × SPEAKER: {name} (OUT:{max_output}) - SKIPPED")

                except Exception as e:
                    print(f"[App]   ? Error reading device {i}: {e}")

            p.terminate()

            # Update the dropdown menu
            if mic_list:
                self.mic_device_menu['values'] = ['Default'] + mic_list
                print(f"[App] ✅ Found {len(mic_list)} microphone(s)")
            else:
                self.mic_device_menu['values'] = ['No microphones found']
                print("[App] ❌ No input devices detected!")

        except Exception as e:
            print(f"[App] ❌ Error refreshing microphones: {e}")
            import traceback
            traceback.print_exc()
            self.mic_device_menu['values'] = ['Error detecting microphones']

    def clear_conversation_history(self):
        """Clear the conversation history"""
        result = messagebox.askyesno(
            "Clear Conversation History",
            "Are you sure you want to clear the conversation history?\n\n"
            "This will reset the bot's memory of your conversation.\n"
            "Kinda like you're murdering it, violently.\n"
            "This action cannot be undone."
        )

        if result:
            if self.engine.is_running and self.engine.llm:
                self.engine.llm.reset_conversation(self.config['personality'])
                self.add_chat_message("System", "Conversation history cleared")
                messagebox.showinfo("Success", "Conversation history has been cleared!")
            else:
                messagebox.showinfo("Note", "Chatbot is not running. History will be cleared when you start it.")

    def test_voice(self):
        """Test the selected TTS voice"""
        self.test_voice_label.config(text="Testing voice...", fg=self.colors['fg'])
        self.root.update()

        def test_thread():
            try:
                from tts_manager import TTSManager

                service = self.tts_var.get()
                voice = self.voice_var.get()

                elevenlabs_settings = None
                if service == 'elevenlabs':
                    elevenlabs_settings = {
                        'stability': self.config.get('elevenlabs_stability', 0.5),
                        'similarity_boost': self.config.get('elevenlabs_similarity', 0.75),
                        'style': self.config.get('elevenlabs_style', 0.0),
                        'use_speaker_boost': self.config.get('elevenlabs_speaker_boost', True)
                    }

                tts = TTSManager(service=service, voice=voice, elevenlabs_settings=elevenlabs_settings)

                # Connect audio callbacks to the avatar/meter system
                tts.set_volume_threshold(self.config.get('volume_threshold', 0.02))

                if self.engine and hasattr(self.engine, '_on_audio_start'):
                    tts.set_audio_callbacks(
                        on_start=self.engine._on_audio_start,
                        on_active=self.engine._on_audio_active,
                        on_silent=self.engine._on_audio_silent,
                        on_end=self.engine._on_audio_end
                    )

                test_message = f"Hello! This is a test of the {service} voice. Do you like me senpai? Am I what you want?"

                self.test_voice_label.config(
                    text=f"Playing test message...",
                    fg='#FF9800'
                )

                tts.speak(test_message)

                self.test_voice_label.config(
                    text=f"Voice test complete!",
                    fg='#4CAF50'
                )

            except Exception as e:
                self.test_voice_label.config(
                    text=f"❌ Error: {str(e)[:50]}...",
                    fg='#f44336'
                )
                messagebox.showerror(
                    "Voice Test Failed",
                    f"Failed to test voice:\n\n{e}"
                )

        threading.Thread(target=test_thread, daemon=True).start()

    def test_screenshot(self):
        """Test screenshot capture with AI response"""
        self.test_screenshot_label.config(
            text="Capturing screenshot and getting AI analysis...",
            fg=self.colors['fg']
        )
        self.root.update()

        def test_thread():
            try:
                from input_handlers import ScreenCaptureHandler
                import os
                from openai import OpenAI

                api_key = os.getenv('OPENAI_API_KEY')
                if not api_key:
                    self.test_screenshot_label.config(
                        text="❌ OpenAI API key required for vision test",
                        fg='#f44336'
                    )
                    messagebox.showerror(
                        "API Key Required",
                        "Please configure your OpenAI API key in the API Keys tab first."
                    )
                    return

                model = self.config['llm_model']
                vision_models = ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo']

                if model not in vision_models:
                    self.test_screenshot_label.config(
                        text=f"❌ {model} doesn't support vision",
                        fg='#f44336'
                    )
                    messagebox.showerror(
                        "Model Not Supported",
                        f"The selected model '{model}' doesn't support vision.\n\n"
                        f"Please select a vision-capable model in Setup tab."
                    )
                    return

                screen = ScreenCaptureHandler()
                image_data = screen.capture_screen()

                if not image_data:
                    self.test_screenshot_label.config(
                        text="❌ Failed to capture screenshot",
                        fg='#f44336'
                    )
                    return

                self.test_screenshot_label.config(
                    text="✅ Screenshot captured! Analyzing...",
                    fg='#FF9800'
                )
                self.root.update()

                client = OpenAI(api_key=api_key)

                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "What do you see in this screenshot? Please describe any text, windows, applications, UI elements, or content that's visible. Be specific and detailed."
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": image_data
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=500
                )

                ai_response = response.choices[0].message.content

                cant_see_phrases = ["can't see", "cannot see", "unable to see", "don't have access", "can't view"]
                if any(phrase in ai_response.lower() for phrase in cant_see_phrases):
                    self.test_screenshot_label.config(
                        text="The bot couldn't see the image",
                        fg='#FF9800'
                    )
                    messagebox.showwarning(
                        "Vision Not Working",
                        f"Screenshot was captured but the bot couldn't see it."
                    )
                else:
                    self.test_screenshot_label.config(
                        text="Vision working! The bot is responding...",
                        fg='#4CAF50'
                    )

                    self.add_chat_message("System", "Screenshot test - the bot saw the image!")
                    self.add_chat_message("Vision AI", ai_response)

                    if self.engine.is_running and self.engine.tts:
                        self.engine._speak_response(ai_response)
                    else:
                        self.add_chat_message("System", "Start the chatbot to hear your bot speak its responses")

            except Exception as e:
                import traceback
                print(f"[Test] Error: {traceback.format_exc()}")

                self.test_screenshot_label.config(
                    text=f"❌ Error: {str(e)[:50]}...",
                    fg='#f44336'
                )
                messagebox.showerror(
                    "Screenshot Test Failed",
                    f"Failed to test screenshot:\n\n{str(e)}"
                )

        threading.Thread(target=test_thread, daemon=True).start()

    def update_voice_dropdown(self):
        """Update voice dropdown based on selected TTS service"""
        service = self.tts_var.get()
        voices = self.voice_options.get(service, ['default'])

        # Hide all info labels first
        if hasattr(self, 'se_info'):
            for label in [self.se_info, self.elevenlabs_info]:
                label.pack_forget()

            # Show appropriate info label
            if service == 'streamelements':
                self.se_info.pack(fill='x', pady=5)
            elif service == 'elevenlabs':
                self.elevenlabs_info.pack(fill='x', pady=5)
            elif service == 'azure':
                self.azure_info.pack(fill='x', pady=5)

        if service == 'elevenlabs':
            if not voices or len(voices) == 0:
                self.voice_menu['values'] = ['⚠️ Click "Refresh Voices" to load']
                self.voice_var.set('⚠️ Click "Refresh Voices" to load')
                self.voice_info_label.config(
                    text="Click 'Refresh Voices' to load your ElevenLabs voices",
                    fg=self.colors['accent']
                )
            else:
                self.voice_menu['values'] = voices
                current_voice = self.voice_var.get()
                if current_voice not in voices:
                    self.voice_var.set(voices[0])
                    self.update_config('elevenlabs_voice', voices[0])
                self.voice_info_label.config(
                    text=f"✅ {len(voices)} voice(s) loaded from your account",
                    fg='#4CAF50'
                )

            self.refresh_voices_btn.grid()
            self.voice_info_label.grid()
            for widget in self.elevenlabs_settings_section.winfo_children():
                widget.grid()
        else:
            self.voice_menu['values'] = voices
            current_voice = self.voice_var.get()
            if current_voice not in voices and len(voices) > 0:
                self.voice_var.set(voices[0])
                self.update_config('elevenlabs_voice', voices[0])

            self.refresh_voices_btn.grid_remove()
            self.voice_info_label.grid_remove()
            for widget in self.elevenlabs_settings_section.winfo_children():
                widget.grid_remove()

    def refresh_elevenlabs_voices(self):
        """Fetch user's custom ElevenLabs voices from API"""
        import os

        api_key = os.getenv('ELEVENLABS_API_KEY')
        if not api_key or api_key == 'your-elevenlabs-key-here':
            messagebox.showwarning(
                "API Key Required",
                "Please set your ELEVENLABS_API_KEY in the .env file first."
            )
            return

        try:
            from elevenlabs.client import ElevenLabs

            self.voice_info_label.config(text="Fetching voices from ElevenLabs...")
            self.root.update()

            client = ElevenLabs(api_key=api_key)
            voices_response = client.voices.get_all()

            custom_voices = []
            for voice in voices_response.voices:
                custom_voices.append(f"{voice.name} ({voice.voice_id})")

            if custom_voices:
                all_voices = self.voice_options['elevenlabs'] + ['---Custom Voices---'] + custom_voices
                self.voice_options['elevenlabs'] = all_voices
                self.voice_menu['values'] = all_voices

                self.voice_info_label.config(
                    text=f"✅ Loaded {len(custom_voices)} custom voice(s) from your account",
                    fg='#4CAF50'
                )
            else:
                self.voice_info_label.config(text="No custom voices found in your account")

        except Exception as e:
            self.voice_info_label.config(text=f"❌ Error loading voices")
            messagebox.showerror(
                "Error Loading Voices",
                f"Failed to fetch ElevenLabs voices:\n\n{e}"
            )

    def on_tts_change(self, event=None):
        """Handle TTS service change"""
        service = self.tts_var.get()
        self.update_config('tts_service', service)
        self.update_voice_dropdown()
        self.reinitialize_tts()

        # Show/hide ElevenLabs settings by packing/unpacking the inner section
        # The outer container stays in place to maintain layout
        if service == 'elevenlabs':
            self.elevenlabs_settings_section.pack(fill='x', padx=30, pady=15)
        else:
            self.elevenlabs_settings_section.pack_forget()

    def update_avatar_preview(self, filename):
        """Update the avatar preview with the selected image"""
        try:
            img = Image.open(filename)
            img.thumbnail((400, 400), Image.Resampling.LANCZOS)

            if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                background = Image.new('RGB', img.size, '#00FF00')

                if img.mode != 'RGBA':
                    img = img.convert('RGBA')

                background.paste(img, (0, 0), img)
                img = background

            photo = ImageTk.PhotoImage(img)
            self.preview_label.config(image=photo, text="")
            self.preview_label.image = photo

        except Exception as e:
            print(f"[App] Error loading preview: {e}")
            self.preview_label.config(
                text=f"Image selected but preview failed\n\n{filename}",
                fg=self.colors['fg']
            )

    def load_existing_avatar_previews(self):
        """Load preview of already configured images"""
        speaking_path = self.config.get('speaking_image', '')
        if speaking_path and Path(speaking_path).exists():
            self.update_avatar_preview(speaking_path)
        elif self.config.get('idle_image', '') and Path(self.config.get('idle_image', '')).exists():
            self.update_avatar_preview(self.config.get('idle_image', ''))

    def update_config(self, key, value):
        """Update configuration"""
        self.config[key] = value
        self.engine.set_config(key, value)

    def save_twitch_blacklists(self):
        """Save username blacklist, emote prefix blacklist, and rate limit response"""
        # Save username blacklist
        username_text = self.username_blacklist_text.get('1.0', 'end-1c')
        usernames = [u.strip() for u in username_text.split('\n') if u.strip()]
        self.config['twitch_username_blacklist'] = usernames

        # Save emote prefix blacklist
        prefix_text = self.emote_prefix_blacklist_text.get('1.0', 'end-1c')
        prefixes = [p.strip() for p in prefix_text.split('\n') if p.strip()]
        self.config['twitch_emote_prefix_blacklist'] = prefixes

        # Save rate limit response
        rate_limit_text = self.rate_limit_response_text.get('1.0', 'end-1c').strip()
        if rate_limit_text:
            self.config['rate_limit_response'] = rate_limit_text

        # Save to file
        self.engine.config = self.config
        self.engine.save_config()

        print("[App] Twitch blacklists and rate limit response saved!")

    def save_personality(self):
        """Save personality"""
        personality = self.personality_text.get('1.0', 'end-1c')
        self.update_config('personality', personality)
        self.save_all_settings()

    def save_all_settings(self):
        """Save all settings"""
        with open(self.engine.config_file, 'w') as f:
            json.dump(self.config, f, indent=4)
        messagebox.showinfo("Success", "All settings saved!")

    def toggle_chatbot(self):
        """Toggle chatbot on/off"""
        if not self.engine.is_running:
            self.start_chatbot()
        else:
            self.stop_chatbot()

    def start_chatbot(self):
        """Start the chatbot"""
        try:
            self.engine.initialize()
            self.engine.start()

            self.status_label.config(text="🟢 Running")
            self.start_btn.config(text="⏸️ Stop Chatbot", bg='#f44336')

            self.chat_mode_label.config(
                text="Full Mode (voice, features, & inputs enabled)",
                fg='#4CAF50'
            )

            self.chat_display.config(state='normal')
            self.chat_display.delete('1.0', tk.END)
            self.chat_display.config(state='disabled')

            self.setup_push_to_talk()

            self.add_chat_message("System", f"✅ {self.config['ai_name']} is now active!")
            self.add_chat_message("System", "Hold your mic hotkey to speak, release to send")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to start:\n\n{e}")

    def stop_chatbot(self):
        """Stop the chatbot"""
        self.engine.stop()
        self.remove_hotkeys()

        self.status_label.config(text="⚫ Stopped")
        self.start_btn.config(text="▶️ Start Chatbot", bg='#4CAF50')

        self.chat_mode_label.config(
            text="Test Mode (responses only, no voice)",
            fg=self.colors['accent']
        )

        self.add_chat_message("System", "Chatbot stopped (test mode still available)")

    def setup_push_to_talk(self):
        """Setup push-to-talk hotkey"""
        try:
            hotkey = self.config.get('hotkey_toggle', 'F4').lower()

            keyboard.on_press_key(hotkey, self.on_push_to_talk_press)
            keyboard.on_release_key(hotkey, self.on_push_to_talk_release)

            self.hotkey_active = True
            print(f"[App] Push-to-talk on {hotkey} activated")

        except Exception as e:
            print(f"[App] Hotkey setup failed: {e}")

    def on_push_to_talk_press(self, event):
        """When push-to-talk key is pressed"""
        if not self.is_recording and self.engine.is_running:
            self.is_recording = True
            self.recording_label.config(text="🔴 LISTENING... (speak now, release to send)")
            self.add_chat_message("System", "🎤 Recording started - speak now!")
            # Start recording in background thread
            threading.Thread(target=self.capture_audio, daemon=True).start()

    def on_push_to_talk_release(self, event):
        """When push-to-talk key is released"""
        if self.is_recording:
            self.is_recording = False
            self.recording_label.config(text="⏳ Processing audio...")

    def capture_audio(self):
        """Capture audio and process when done"""
        import speech_recognition as sr
        import time

        try:
            recognizer = sr.Recognizer()
            microphone = sr.Microphone()

            with microphone as source:
                # Quick ambient noise adjustment
                recognizer.adjust_for_ambient_noise(source, duration=0.2)

                # Capture audio - this will wait for speech and record it
                # It blocks until phrase_time_limit is reached or silence detected
                audio = recognizer.listen(
                    source,
                    timeout=1,  # Start listening within 1 second
                    phrase_time_limit=10  # Max 10 seconds of speech
                )

            # Audio captured! Now wait a moment for key release if still held
            time.sleep(0.1)
            self.is_recording = False

            # Transcribe the captured audio
            self.add_chat_message("System", "🔄 Transcribing speech...")

            try:
                text = recognizer.recognize_google(audio)

                if text and text.strip():
                    self.recording_label.config(text="")
                    self.add_chat_message("You", text)

                    # Get screen capture if enabled
                    screen_data = None
                    if self.config.get('screen_enabled', False) and self.engine.inputs.enabled_inputs.get('screen',
                                                                                                          False):
                        self.add_chat_message("System", "📸 Capturing screen...")
                        screen_data = self.engine.inputs.capture_screen()

                    # Send to AI
                    self.engine._process_and_respond(text, screen_data)

                else:
                    self.recording_label.config(text="")
                    self.add_chat_message("System", "❌ No speech detected")

            except sr.UnknownValueError:
                self.recording_label.config(text="")
                self.add_chat_message("System", "❌ Could not understand the audio")

            except sr.RequestError as e:
                self.recording_label.config(text="")
                self.add_chat_message("System", f"❌ Google Speech Recognition error: {e}")

        except sr.WaitTimeoutError:
            self.is_recording = False
            self.recording_label.config(text="")
            self.add_chat_message("System", "❌ Timeout - didn't hear any speech")

        except Exception as e:
            self.is_recording = False
            self.recording_label.config(text="")
            self.add_chat_message("System", f"❌ Recording error: {str(e)}")
            print(f"[App] Recording error: {e}")
            import traceback
            traceback.print_exc()

    def screenshot_and_respond(self):
        """Take screenshot and get AI response"""
        if not self.engine.is_running:
            messagebox.showwarning("Not Running", "Please start the chatbot first!")
            return

        self.add_chat_message("System", "Taking screenshot...")

        def screenshot_thread():
            try:
                from input_handlers import ScreenCaptureHandler
                screen_handler = ScreenCaptureHandler()
                screen_data = screen_handler.capture_screen()

                if screen_data:
                    model = self.config['llm_model']
                    vision_models = ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo']

                    if model not in vision_models:
                        self.add_chat_message(
                            "System",
                            f"⚠️ Your model '{model}' doesn't support vision. Please switch to gpt-4o in Setup tab."
                        )
                        return

                    prompt = "In 1-2 sentences, briefly tell me what you see in this screenshot. DO NOT EXPLAIN IN DETAIL, JUST GIVE A VERY SHORT RESPONSE BASED ON WHAT YOU SEE."
                    self.engine._process_and_respond(prompt, screen_data)
                else:
                    self.add_chat_message("System", "❌ Failed to capture screenshot")

            except Exception as e:
                import traceback
                print(f"[Screenshot] Error: {traceback.format_exc()}")
                self.add_chat_message("System", f"Screenshot error: {e}")

        threading.Thread(target=screenshot_thread, daemon=True).start()

    def remove_hotkeys(self):
        """Remove all hotkeys"""
        if self.hotkey_active:
            try:
                keyboard.unhook_all()
                self.hotkey_active = False
            except:
                pass

    def send_text_message(self):
        """Send text message"""
        text = self.text_input.get().strip()
        if not text:
            return

        self.text_input.delete(0, tk.END)
        self.add_chat_message(self.config['user_name'], text)

        if self.engine.is_running:
            def process_thread():
                self.engine.process_text_input(text)

            threading.Thread(target=process_thread, daemon=True).start()
        else:
            self.add_chat_message("System", "Test mode: Getting response with voice...")

            def test_thread():
                try:
                    from llm_manager import LLMManager
                    from tts_manager import TTSManager

                    system_prompt = self.config['personality']
                    if self.config['ai_name'] != 'Assistant':
                        system_prompt += f"\n\nYour name is {self.config['ai_name']}."

                    llm = LLMManager(
                        model=self.config['llm_model'],
                        system_prompt=system_prompt
                    )

                    response_length = self.config.get('response_length', 'normal')
                    if response_length == 'brief':
                        max_tokens = 60
                    elif response_length == 'normal':
                        max_tokens = 150
                    elif response_length == 'detailed':
                        max_tokens = 300
                    elif response_length == 'custom':
                        max_tokens = self.config.get('max_response_tokens', 150)
                    else:
                        max_tokens = 150

                    response = llm.chat(text, max_response_tokens=max_tokens)
                    self.display_response(response)

                    elevenlabs_settings = {
                        'stability': self.config.get('elevenlabs_stability', 0.5),
                        'similarity_boost': self.config.get('elevenlabs_similarity', 0.75),
                        'style': self.config.get('elevenlabs_style', 0.0),
                        'use_speaker_boost': self.config.get('elevenlabs_speaker_boost', True)
                    }

                    tts = TTSManager(
                        service=self.config['tts_service'],
                        voice=self.config['elevenlabs_voice'],
                        elevenlabs_settings=elevenlabs_settings
                    )

                    self.add_chat_message("System", "Speaking response...")
                    tts.speak(response)
                    self.add_chat_message("System", "Test complete!")

                except Exception as e:
                    self.add_chat_message("Error", f"Failed to get response: {e}")
                    self.add_chat_message("System", "Make sure your OpenAI API key is configured in the API Keys tab")

            threading.Thread(target=test_thread, daemon=True).start()

    def show_welcome_message(self):
        """Show welcome message with setup instructions"""
        welcome_text = """
    Thank you so much for to using my silly little software! Here's how to get started:

    QUICK SETUP CHECKLIST:

      ✓ Step 1: Configure API Keys (API Keys tab)
        • Add your OpenAI API key (REQUIRED)
        • If wanting open source models, add your Groq API key
        • Optionally add ElevenLabs, Azure, or Twitch keys
        • Click "Save All API Keys"

      ✓ Step 2: Configure Your Bot (Setup tab)
        • Give your bot a name and personality
        • Choose your preferred response model
        • Test the connection with the test button

      ✓ Step 3: Setup Text-to-Speech (TTS tab)
        • Choose a TTS service (StreamElements is free!)
        • Select a voice
        • For ElevenLabs, click "Refresh Voices" to load your custom voices

      ✓ Step 4: Configure Inputs (Inputs tab)
        • Enable microphone if you want voice chat
        • Enable Twitch chat if streaming
        • Configure Twitch TTS output (speak username/message)

      ✓ Step 5: Begin the Delusion!
        • Click the "Start Chatbot" button at the bottom
        • Or test responses right here in chat
        • It's like talking to the real voices in your head
    
    Fuck AI btw, I'll have open source models soon.

    """
        self.chat_display.config(state='normal')
        self.chat_display.insert('1.0', welcome_text, 'welcome')
        self.chat_display.config(state='disabled')

    def test_ai_connection(self):
        """Test OpenAI API connection from Setup tab"""
        self.test_status_label.config(text="Testing connection...", fg=self.colors['fg'])
        self.root.update()

        def test_thread():
            try:
                from llm_manager import LLMManager
                import os

                api_key = os.getenv('OPENAI_API_KEY')
                if not api_key or api_key == '':
                    self.test_status_label.config(
                        text="❌ No OpenAI API key found! Add it in the API Keys tab.",
                        fg='#f44336'
                    )
                    return

                llm = LLMManager(model=self.config['llm_model'], system_prompt="You are a helpful assistant.")
                response = llm.chat("Say 'Connection successful!' and nothing else.")

                if response and len(response) > 0:
                    self.test_status_label.config(
                        text=f"✅ Success! Model: {self.config['llm_model']} | Response: {response[:50]}...",
                        fg='#4CAF50'
                    )
                    messagebox.showinfo(
                        "Connection Successful!",
                        f"✅ Your OpenAI API key is working!\n\n"
                        f"Model: {self.config['llm_model']}\n"
                        f"Response: {response}\n\n"
                        f"You're all set to use the chatbot!"
                    )
                else:
                    self.test_status_label.config(
                        text="⚠️ Got empty response. Check your API key.",
                        fg='#FF9800'
                    )

            except Exception as e:
                error_msg = str(e)
                self.test_status_label.config(
                    text=f"❌ Error: {error_msg[:80]}...",
                    fg='#f44336'
                )
                messagebox.showerror(
                    "Connection Failed",
                    f"Failed to connect to OpenAI:\n\n{error_msg}"
                )

        threading.Thread(target=test_thread, daemon=True).start()

    def display_response(self, response):
        """Display AI response in chat"""
        self.add_chat_message(self.config['ai_name'], response)

    def add_chat_message(self, sender, message):
        """Add message to chat display"""
        self.chat_display.config(state='normal')
        self.chat_display.insert(tk.END, f"\n{sender}: {message}\n")
        self.chat_display.see(tk.END)
        self.chat_display.config(state='disabled')

    def on_ai_speaking_start(self):
        """Called when AI starts speaking"""
        self.status_label.config(text="🟢 Speaking...")

    def on_ai_speaking_end(self):
        """Called when AI finishes speaking"""
        self.status_label.config(text="🟢 Running")

    def check_for_updates(self):
        """Check for updates on startup"""
        try:
            print("[App] Checking for updates...")
            update_info = updater.check_for_updates()

            if update_info:
                print(f"[App] Update available: v{update_info['version']}")

                # Show update dialog
                dialog = UpdateDialog(self.root, update_info)

                if dialog.result:
                    # User wants to update
                    print("[App] User accepted update, downloading...")

                    # Show progress window
                    dialog.show_download_progress(self.root)

                    # Download update
                    new_exe = updater.download_update(
                        update_info['url'],
                        progress_callback=dialog.update_progress
                    )

                    if new_exe:
                        print("[App] Download complete, applying update...")

                        # Apply update and restart
                        if updater.apply_update(new_exe):
                            print("[App] Update script launched, closing app...")

                            # Gracefully close everything
                            try:
                                # Stop the engine if running
                                if hasattr(self, 'engine') and self.engine:
                                    if self.engine.is_running:
                                        self.engine.stop()

                                # Process any remaining events
                                self.root.update()

                                # Destroy the window
                                self.root.destroy()
                            except:
                                pass

                            # Small delay to let window close
                            import time
                            time.sleep(0.5)

                            # Force exit
                            import os
                            os._exit(0)
                        else:
                            messagebox.showerror(
                                "Update Failed",
                                "Failed to apply update. Please try downloading manually."
                            )
                    else:
                        messagebox.showerror(
                            "Download Failed",
                            "Failed to download update. Please check your internet connection."
                        )

                    # Close progress window
                    if dialog.download_window:
                        dialog.download_window.destroy()
            else:
                print("[App] No updates available")

        except Exception as e:
            print(f"[App] Error checking for updates: {e}")

    def create_menu_bar(self):
        """Create menu bar with File menu"""
        menubar = tk.Menu(
            self.root,
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            activebackground=self.colors['accent'],
            activeforeground='white',
            relief='flat',
            borderwidth=0
        )
        self.root.config(menu=menubar)
        try:
            self.root.option_add('*Menu.background', self.colors['bg'])
            self.root.option_add('*Menu.foreground', self.colors['fg'])
            self.root.option_add('*Menu.activeBackground', self.colors['accent'])
            self.root.option_add('*Menu.activeForeground', 'white')
        except:
            pass

        # Bind keyboard shortcut
        self.root.bind('<Control-u>', lambda e: self.manual_update_check())

    def manual_update_check(self):
        """Manual update check triggered by user"""
        print("[App] Manual update check initiated by user...")

        # Show checking message
        checking_dialog = tk.Toplevel(self.root)
        checking_dialog.title("Checking for Updates")
        checking_dialog.geometry("300x100")
        checking_dialog.resizable(False, False)
        checking_dialog.transient(self.root)

        # Center the dialog
        checking_dialog.update_idletasks()
        x = (checking_dialog.winfo_screenwidth() // 2) - 150
        y = (checking_dialog.winfo_screenheight() // 2) - 50
        checking_dialog.geometry(f"300x100+{x}+{y}")

        tk.Label(
            checking_dialog,
            text="Checking for updates...",
            font=('Arial', 11)
        ).pack(pady=30)

        # Force update the dialog
        checking_dialog.update()

        try:
            update_info = updater.check_for_updates()

            # Close checking dialog
            checking_dialog.destroy()

            if update_info:
                print(f"[App] Update available: v{update_info['version']}")

                # Show update dialog
                dialog = UpdateDialog(self.root, update_info)

                if dialog.result:
                    # User wants to update
                    print("[App] User accepted update, downloading...")

                    # Show progress window
                    dialog.show_download_progress(self.root)

                    # Download update
                    new_exe = updater.download_update(
                        update_info['url'],
                        progress_callback=dialog.update_progress
                    )

                    if new_exe:
                        print("[App] Download complete, applying update...")

                        # Close progress window FIRST
                        if dialog.download_window:
                            try:
                                dialog.download_window.destroy()
                            except:
                                pass

                        # Apply update
                        if updater.apply_update(new_exe):
                            print("[App] Update script launched, closing app...")

                            # Gracefully close everything
                            try:
                                # Stop the engine if running
                                if hasattr(self, 'engine') and self.engine:
                                    if self.engine.is_running:
                                        self.engine.stop()

                                # Process any remaining events
                                self.root.update()

                                # Destroy the window
                                self.root.destroy()
                            except:
                                pass

                            # Small delay to let window close
                            import time
                            time.sleep(0.5)

                            # Force exit
                            import os
                            os._exit(0)
                        else:
                            messagebox.showerror(
                                "Update Failed",
                                "Failed to apply update. Please try downloading manually."
                            )
                    else:
                        messagebox.showerror(
                            "Download Failed",
                            "Failed to download update. Please check your internet connection."
                        )
                        # Close progress window on failure
                        if dialog.download_window:
                            try:
                                dialog.download_window.destroy()
                            except:
                                pass
            else:
                # No updates available
                print("[App] No updates available")
                messagebox.showinfo(
                    "No Updates",
                    f"You're running the latest version (v{updater.CURRENT_VERSION})!",
                    parent=self.root
                )

        except Exception as e:
            # Close checking dialog if still open
            try:
                checking_dialog.destroy()
            except:
                pass

            print(f"[App] Error checking for updates: {e}")
            messagebox.showerror(
                "Update Check Failed",
                "Could not check for updates. Please check your internet connection.",
                parent=self.root
            )


class UpdateDialog:
    """Dialog for showing update information"""

    def __init__(self, parent, update_info):
        self.result = False
        self.download_window = None

        dialog = tk.Toplevel(parent)
        dialog.title("Heyyyy xD")
        dialog.geometry("550x450")
        dialog.resizable(False, False)
        dialog.transient(parent)
        dialog.grab_set()

        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (275)
        y = (dialog.winfo_screenheight() // 2) - (225)
        dialog.geometry(f"550x450+{x}+{y}")

        # Main container with background
        main_container = tk.Frame(dialog, bg='white')
        main_container.pack(fill='both', expand=True)

        # Header
        header = tk.Frame(main_container, bg='#9370DB', height=80)
        header.pack(fill='x')
        header.pack_propagate(False)

        tk.Label(
            header,
            text="Woah an update!",
            bg='#9370DB',
            fg='white',
            font=('Arial', 16, 'bold')
        ).pack(pady=25)

        # Content area with padding
        content = tk.Frame(main_container, bg='white')
        content.pack(fill='both', expand=True, padx=25, pady=20)

        # Version info
        info_frame = tk.Frame(content, bg='#F8F9FA', relief='solid', bd=1)
        info_frame.pack(fill='x', pady=(0, 15))

        version_inner = tk.Frame(info_frame, bg='#F8F9FA')
        version_inner.pack(padx=15, pady=12)

        tk.Label(
            version_inner,
            text=f"Current Version: {updater.CURRENT_VERSION}",
            bg='#F8F9FA',
            fg='#6c757d',
            font=('Arial', 10)
        ).pack(anchor='w')

        tk.Label(
            version_inner,
            text=f"New Version: {update_info['version']}",
            bg='#F8F9FA',
            fg='#28a745',
            font=('Arial', 11, 'bold')
        ).pack(anchor='w', pady=(3, 0))

        # Release notes
        tk.Label(
            content,
            text="What's New:",
            bg='white',
            fg='#212529',
            font=('Arial', 11, 'bold')
        ).pack(anchor='w', pady=(0, 8))

        notes_frame = tk.Frame(content, bg='white')
        notes_frame.pack(fill='both', expand=True, pady=(0, 15))

        notes_text = tk.Text(
            notes_frame,
            wrap='word',
            height=8,
            bg='#FAFAFA',
            fg='#212529',
            font=('Arial', 9),
            relief='solid',
            bd=1,
            padx=10,
            pady=10
        )
        notes_text.pack(side='left', fill='both', expand=True)

        scrollbar = tk.Scrollbar(notes_frame, command=notes_text.yview)
        scrollbar.pack(side='right', fill='y')
        notes_text.config(yscrollcommand=scrollbar.set)

        notes_text.insert('1.0', update_info['notes'])
        notes_text.config(state='disabled')

        # Note about manual restart - styled better
        note_frame = tk.Frame(content, bg='#fff3cd', relief='solid', bd=1)
        note_frame.pack(fill='x', pady=(0, 15))

        note_inner = tk.Frame(note_frame, bg='#fff3cd')
        note_inner.pack(fill='x', padx=12, pady=10)

        tk.Label(
            note_inner,
            text="👁️",
            bg='#fff3cd',
            font=('Arial', 14)
        ).pack(side='left', padx=(0, 8))

        tk.Label(
            note_inner,
            text="You'll need to manually re-launch this exe after the update completes.",
            bg='#fff3cd',
            fg='#856404',
            font=('Arial', 9),
            wraplength=450,
            justify='left'
        ).pack(side='left', fill='x', expand=True)

        # Buttons
        button_frame = tk.Frame(content, bg='white')
        button_frame.pack(fill='x')

        def on_update():
            self.result = True
            dialog.destroy()

        def on_skip():
            self.result = False
            dialog.destroy()

        update_btn = tk.Button(
            button_frame,
            text="Update Now",
            command=on_update,
            bg='#4CAF50',
            fg='white',
            font=('Arial', 10, 'bold'),
            relief='flat',
            padx=35,
            pady=12,
            cursor='hand2'
        )
        update_btn.pack(side='left', padx=(0, 10))

        skip_btn = tk.Button(
            button_frame,
            text="Skip This Version",
            command=on_skip,
            bg='#9E9E9E',
            fg='white',
            font=('Arial', 10),
            relief='flat',
            padx=30,
            pady=12,
            cursor='hand2'
        )
        skip_btn.pack(side='left')

        parent.wait_window(dialog)

    def show_download_progress(self, parent):
        """Show download progress window"""
        self.download_window = tk.Toplevel(parent)
        self.download_window.title("Downloading Update")
        self.download_window.geometry("400x150")
        self.download_window.resizable(False, False)
        self.download_window.transient(parent)
        self.download_window.grab_set()

        # Center the window
        self.download_window.update_idletasks()
        x = (self.download_window.winfo_screenwidth() // 2) - 200
        y = (self.download_window.winfo_screenheight() // 2) - 75
        self.download_window.geometry(f"400x150+{x}+{y}")

        tk.Label(
            self.download_window,
            text="Downloading update...",
            font=('Arial', 12, 'bold')
        ).pack(pady=20)

        self.progress_var = tk.IntVar()
        self.progress_bar = ttk.Progressbar(
            self.download_window,
            variable=self.progress_var,
            maximum=100,
            length=350
        )
        self.progress_bar.pack(pady=10)

        self.progress_label = tk.Label(
            self.download_window,
            text="0%",
            font=('Arial', 10)
        )
        self.progress_label.pack()

        return self.download_window

    def update_progress(self, progress):
        """Update progress bar"""
        if self.download_window:
            self.progress_var.set(progress)
            self.progress_label.config(text=f"{progress}%")
            self.download_window.update()


def main():
    if sys.platform == 'win32':
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("LaceAI.Chatbot.1.0")
        except:
            pass

    root = tk.Tk()
    app = IntegratedChatbotApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()