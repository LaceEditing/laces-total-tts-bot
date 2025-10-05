"""
Complete AI Chatbot System - Integrated Application
UPDATED: Added Twitch TTS output controls for reading username and message
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import keyboard
import threading
from pathlib import Path
from chatbot_engine import ChatbotEngine
from PIL import Image, ImageTk
import os
from dotenv import load_dotenv, set_key

class IntegratedChatbotApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Hey besties let's talk to robots")
        self.root.geometry("900x900")
        self.root.minsize(750, 800)

        self.set_window_icon()

        self.env_file = Path('.env')
        if self.env_file.exists():
            load_dotenv(self.env_file)
            print("[App] Loaded environment variables from .env file")
        else:
            print("[App] No .env file found, creating one...")
            self.create_default_env_file()
            load_dotenv(self.env_file)

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

        self.engine = ChatbotEngine()
        self.config = self.engine.config

        self.is_recording = False
        self.hotkey_active = False

        self.voice_options = {
            'elevenlabs': ['rachel', 'drew', 'clyde', 'paul', 'domi', 'dave', 'fin',
                          'sarah', 'antoni', 'thomas', 'charlie', 'emily', 'elli',
                          'callum', 'patrick', 'harry', 'liam', 'dorothy', 'josh',
                          'arnold', 'charlotte', 'alice', 'matilda', 'james'],
            'streamelements': ['Brian', 'Ivy', 'Justin', 'Russell', 'Nicole', 'Emma',
                              'Amy', 'Joanna', 'Salli', 'Kimberly', 'Kendra', 'Joey',
                              'Matthew', 'Geraint', 'Raveena'],
            'azure': ['en-US-JennyNeural', 'en-US-GuyNeural', 'en-US-AriaNeural',
                     'en-US-DavisNeural', 'en-US-AmberNeural', 'en-US-AshleyNeural',
                     'en-US-BrandonNeural', 'en-US-ChristopherNeural'],
            'coqui-tts': ['default']
        }

        self.create_gui()

        self.engine.on_response_callback = self.display_response
        self.engine.on_speaking_start = self.on_ai_speaking_start
        self.engine.on_speaking_end = self.on_ai_speaking_end

        self.show_welcome_message()

    def load_custom_font(self, font_name, size, weight='normal'):
        """Load custom font - Windows compatible version"""
        try:
            import ctypes
            from ctypes import wintypes

            font_path = Path('fonts') / font_name

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
            icon_path = Path('icon.ico')
            if icon_path.exists():
                self.root.iconbitmap(icon_path)
                print("[App] Window icon loaded from icon.ico")
            else:
                print("[App] icon.ico not found - using default icon")
        except Exception as e:
            print(f"[App] Could not set window icon: {e}")

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
            font=('Arial', 10, 'italic'),
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
                       font=('Arial', 10))

        style.map('TNotebook.Tab',
                 background=[('selected', self.colors['accent'])],
                 foreground=[('selected', 'white')],
                 padding=[('selected', [18, 12])],
                 font=[('selected', ('Arial', 11, 'bold'))])

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

        self.chat_display.tag_config('welcome', foreground=self.colors['accent'], font=('Arial', 10))
        self.chat_display.tag_config('header', foreground=self.colors['fg'], font=('Arial', 12, 'bold'))
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
            font=('Arial', 9, 'italic')
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
            font=('Arial', 12),
            relief='flat',
            bd=0
        )
        self.text_input.pack(fill='x', padx=2, pady=2, ipady=6)
        self.text_input.bind('<Return>', lambda e: self.send_text_message())

        self.send_btn = tk.Button(
            input_row,
            text="Send",
            command=self.send_text_message,
            bg=self.colors['button'],
            fg='white',
            font=('Arial', 11, 'bold'),
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
            font=('Arial', 8, 'italic')
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

        info_frame = tk.Frame(scrollable, bg=self.colors['entry_bg'], bd=2, relief='solid')
        info_frame.pack(fill='x', padx=20, pady=20)

        info_text = """
        API Keys Configuration
        
        Enter your API keys below. They will be saved to the .env file automatically.
        Keys are optional except for OpenAI which is required for the chatbot to function.
        """

        tk.Label(
            info_frame,
            text=info_text,
            bg=self.colors['entry_bg'],
            fg=self.colors['fg'],
            font=('Arial', 10),
            justify='left'
        ).pack(padx=20, pady=20)

        keys_section = self.create_section(scrollable, "API Keys", 0)
        keys_section.grid_columnconfigure(0, weight=1)
        keys_section.grid_columnconfigure(1, weight=1)

        self.key_show_states = {}
        self.key_entries = {}

        self.create_api_key_row(
            keys_section,
            row=0,
            label="OpenAI API Key:",
            key_name="OPENAI_API_KEY",
            required=True,
            link="https://platform.openai.com/api-keys",
            description="Required for all GPT models"
        )

        self.create_api_key_row(
            keys_section,
            row=1,
            label="ElevenLabs API Key:",
            key_name="ELEVENLABS_API_KEY",
            required=False,
            link="https://elevenlabs.io/",
            description="Optional - for premium TTS voices"
        )

        self.create_api_key_row(
            keys_section,
            row=2,
            label="Azure TTS Key:",
            key_name="AZURE_TTS_KEY",
            required=False,
            link="https://portal.azure.com/",
            description="Optional - for Azure neural voices"
        )

        azure_region_frame = tk.Frame(keys_section, bg=self.colors['bg'])
        azure_region_frame.grid(row=3, column=0, columnspan=4, sticky='ew', pady=5)

        tk.Label(
            azure_region_frame,
            text="Azure Region:",
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=('Arial', 10)
        ).pack(side='left', padx=5)

        self.azure_region_entry = tk.Entry(
            azure_region_frame,
            bg=self.colors['entry_bg'],
            font=('Arial', 10),
            width=15
        )
        self.azure_region_entry.pack(side='left', padx=5)
        self.azure_region_entry.insert(0, self.get_api_key('AZURE_TTS_REGION') or 'eastus')

        self.create_api_key_row(
            keys_section,
            row=4,
            label="Twitch OAuth Token:",
            key_name="TWITCH_OAUTH_TOKEN",
            required=False,
            link="https://twitchapps.com/tmi/",
            description="Optional - format: oauth:yourtoken"
        )

        save_frame = tk.Frame(scrollable, bg=self.colors['bg'])
        save_frame.pack(pady=20)

        tk.Button(
            save_frame,
            text="💾 Save All API Keys",
            command=self.save_all_api_keys,
            bg='#4CAF50',
            fg='white',
            font=('Arial', 12, 'bold'),
            relief='raised',
            borderwidth=3,
            cursor='hand2',
            width=20,
            height=2
        ).pack()

        status_frame = self.create_section(scrollable, "API Key Status", 1)
        status_frame.grid_columnconfigure(0, weight=1)
        status_frame.grid_columnconfigure(1, weight=1)

        self.api_status_labels = {}
        status_keys = [
            ("OpenAI", "OPENAI_API_KEY", True),
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
                font=('Arial', 10, 'bold'),
                width=15,
                anchor='w'
            )
            label.pack(side='left', padx=5)

            status_label = tk.Label(
                status_row,
                text="",
                bg=self.colors['bg'],
                font=('Arial', 10),
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
            font=('Arial', 10, 'bold' if required else 'normal'),
            width=20,
            anchor='w'
        ).pack(side='left', padx=5)

        entry = tk.Entry(
            row_frame,
            bg=self.colors['entry_bg'],
            font=('Arial', 10),
            width=40,
            show='•'
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
            font=('Arial', 9),
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
            font=('Arial', 9),
            relief='flat',
            cursor='hand2'
        )
        link_btn.pack(side='left', padx=2)

        tk.Label(
            row_frame,
            text=description,
            bg=self.colors['bg'],
            fg=self.colors['accent'],
            font=('Arial', 9, 'italic')
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

        config_frame = self.create_section(scrollable, "Bot Configuration", 0)
        config_frame.grid_columnconfigure(0, weight=1)
        config_frame.grid_columnconfigure(1, weight=1)

        self.create_entry(config_frame, "Bot's Name:", 'ai_name', 0)
        self.create_entry(config_frame, "Your Name:", 'user_name', 1)

        tk.Label(config_frame, text="Model:",
                 bg=self.colors['bg'], fg=self.colors['fg'],
                 font=('Arial', 11)).grid(row=2, column=0, sticky='w', pady=5)

        models = [
            'gpt-4o',
            'gpt-4o-mini',
            'gpt-4-turbo',
            'gpt-4',
            'gpt-3.5-turbo'
        ]
        self.llm_var = tk.StringVar(value=self.config['llm_model'])
        llm_menu = ttk.Combobox(config_frame, textvariable=self.llm_var,
                                values=models, state='readonly', width=25)
        llm_menu.grid(row=2, column=1, sticky='w', pady=5)
        llm_menu.bind('<<ComboboxSelected>>',
                      lambda e: self.update_config('llm_model', self.llm_var.get()))

        info_label = tk.Label(
            config_frame,
            text=" Crazy Epic Tip: gpt-4o supports vision & is the most capable.",
            bg=self.colors['bg'],
            fg=self.colors['accent'],
            font=('Arial', 9, 'italic')
        )
        info_label.grid(row=3, column=0, columnspan=2, sticky='w', pady=5)

        response_section = self.create_section(scrollable, "Response Length & Style", 1)
        response_section.grid_columnconfigure(0, weight=1)
        response_section.grid_columnconfigure(1, weight=1)

        tk.Label(
            response_section,
            text="Control how long and detailed the bot's responses are:",
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=('Arial', 10)
        ).grid(row=0, column=0, columnspan=2, sticky='w', pady=(0, 10))

        tk.Label(response_section, text="Response Length:",
                 bg=self.colors['bg'], fg=self.colors['fg'],
                 font=('Arial', 10)).grid(row=1, column=0, sticky='w', pady=5)

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
            font=('Arial', 9, 'italic'),
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
            font=('Arial', 10)
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
            font=('Arial', 9)
        )
        self.tokens_value_label.pack(side='left', padx=5)

        self.max_response_tokens_slider.config(
            command=lambda v: self.update_token_label(int(float(v)))
        )

        self.update_custom_tokens_visibility()

        tk.Label(response_section, text="Response Style:",
                 bg=self.colors['bg'], fg=self.colors['fg'],
                 font=('Arial', 10)).grid(row=4, column=0, sticky='w', pady=5)

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
            font=('Arial', 10)
        ).pack(anchor='w', padx=5)

        self.custom_style_text = tk.Text(
            self.custom_style_frame,
            height=3,
            bg=self.colors['entry_bg'],
            fg=self.colors['fg'],
            font=('Arial', 9),
            wrap='word'
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
            font=('Arial', 8, 'italic')
        ).pack(anchor='w', padx=5)

        # Show/hide based on current selection
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
            font=('Arial', 9, 'italic')
        )
        self.style_desc_label.grid(row=5, column=0, columnspan=2, sticky='w', pady=5)

        memory_section = self.create_section(scrollable, "Memory & Context Settings", 2)
        memory_section.grid_columnconfigure(0, weight=1)
        memory_section.grid_columnconfigure(1, weight=1)

        tk.Label(
            memory_section,
            text="Configure how much the bot remembers from the conversation:",
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=('Arial', 10)
        ).grid(row=0, column=0, columnspan=2, sticky='w', pady=(0, 10))

        tk.Label(
            memory_section,
            text="Conversation history is automatically saved to: conversation_history.json",
            bg=self.colors['bg'],
            fg=self.colors['accent'],
            font=('Arial', 9, 'italic')
        ).grid(row=1, column=0, columnspan=2, sticky='w', pady=(0, 10))

        tk.Label(memory_section, text="Max Context Tokens:",
                 bg=self.colors['bg'], fg=self.colors['fg'],
                 font=('Arial', 10)).grid(row=2, column=0, sticky='w', pady=5)

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
            text="Higher = more memory but more expensive. GPT-4o supports up to 128K tokens.",
            bg=self.colors['bg'],
            fg=self.colors['accent'],
            font=('Arial', 9, 'italic')
        ).grid(row=3, column=0, columnspan=2, sticky='w', pady=5)

        tk.Label(memory_section, text="Auto-Reset Conversation:",
                 bg=self.colors['bg'], fg=self.colors['fg'],
                 font=('Arial', 10)).grid(row=4, column=0, sticky='w', pady=5)

        self.auto_reset_var = tk.BooleanVar(value=self.config.get('auto_reset', False))
        auto_reset_check = tk.Checkbutton(
            memory_section,
            text="Reset conversation when reaching token limit",
            variable=self.auto_reset_var,
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=('Arial', 9),
            selectcolor=self.colors['accent'],
            command=lambda: self.update_config('auto_reset', self.auto_reset_var.get())
        )
        auto_reset_check.grid(row=4, column=1, sticky='w', pady=5)

        reset_btn = tk.Button(
            memory_section,
            text="Clear Conversation History Now",
            command=self.clear_conversation_history,
            bg='#FF6B6B',
            fg='white',
            font=('Arial', 10, 'bold'),
            relief='flat',
            cursor='hand2'
        )
        reset_btn.grid(row=5, column=0, columnspan=2, pady=10)

        personality_section = self.create_section(scrollable, "Bot's Personality", 3)
        personality_section.grid_columnconfigure(0, weight=1)
        personality_section.grid_columnconfigure(1, weight=1)

        tk.Label(personality_section, text="System Prompt / Personality:",
                 bg=self.colors['bg'], fg=self.colors['fg'],
                 font=('Arial', 11, 'bold')).grid(row=0, column=0, columnspan=2, sticky='w', pady=(0, 10))

        text_frame = tk.Frame(personality_section, bg=self.colors['accent'], bd=2)
        text_frame.grid(row=1, column=0, columnspan=2, sticky='ew', pady=5)

        self.personality_text = tk.Text(
            text_frame,
            height=12,
            bg=self.colors['text_bg'],
            fg=self.colors['fg'],
            font=('Consolas', 10),
            wrap='word',
            relief='flat'
        )
        self.personality_text.pack(fill='both', expand=True, padx=2, pady=2)
        self.personality_text.insert('1.0', self.config['personality'])

        save_personality_btn = tk.Button(
            personality_section,
            text="💾 Save Personality",
            command=self.save_personality,
            bg=self.colors['button'],
            fg='white',
            font=('Arial', 10, 'bold'),
            relief='flat',
            cursor='hand2'
        )
        save_personality_btn.grid(row=2, column=0, columnspan=2, pady=10)

        test_section = self.create_section(scrollable, "Test Bot's Connection", 4)
        test_section.grid_columnconfigure(0, weight=1)
        test_section.grid_columnconfigure(1, weight=1)

        test_info = tk.Label(
            test_section,
            text="Test your OpenAI API key and model configuration before starting the full chatbot:",
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=('Arial', 10),
            wraplength=600,
            justify='left'
        )
        test_info.grid(row=0, column=0, columnspan=2, sticky='w', pady=(0, 10))

        test_btn = tk.Button(
            test_section,
            text="Test Bot's Connection",
            command=self.test_ai_connection,
            bg='#2196F3',
            fg='white',
            font=('Arial', 11, 'bold'),
            relief='flat',
            cursor='hand2',
            width=20
        )
        test_btn.grid(row=1, column=0, pady=10)

        self.test_status_label = tk.Label(
            test_section,
            text="",
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=('Arial', 10),
            wraplength=600,
            justify='left'
        )
        self.test_status_label.grid(row=1, column=1, sticky='w', padx=10)

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

        tts_frame = self.create_section(scrollable, "TTS Service", 0)
        tts_frame.grid_columnconfigure(0, weight=1)
        tts_frame.grid_columnconfigure(1, weight=1)

        tk.Label(tts_frame, text="TTS Service:",
                bg=self.colors['bg'], fg=self.colors['fg'],
                font=('Arial', 11)).grid(row=0, column=0, sticky='w', pady=5)

        tts_services = ['elevenlabs', 'streamelements', 'coqui-tts', 'azure']
        self.tts_var = tk.StringVar(value=self.config['tts_service'])
        tts_menu = ttk.Combobox(tts_frame, textvariable=self.tts_var,
                               values=tts_services, state='readonly', width=25)
        tts_menu.grid(row=0, column=1, sticky='w', pady=5)
        tts_menu.bind('<<ComboboxSelected>>', self.on_tts_change)

        voice_section = self.create_section(scrollable, "Voice Settings", 1)
        voice_section.grid_columnconfigure(0, weight=1)
        voice_section.grid_columnconfigure(1, weight=1)

        tk.Label(voice_section, text="Voice:",
                bg=self.colors['bg'], fg=self.colors['fg'],
                font=('Arial', 11)).grid(row=0, column=0, sticky='w', pady=5)

        self.voice_var = tk.StringVar(value=self.config.get('elevenlabs_voice', 'rachel'))
        self.voice_menu = ttk.Combobox(voice_section, textvariable=self.voice_var,
                                       values=self.voice_options['elevenlabs'],
                                       state='readonly', width=35)
        self.voice_menu.grid(row=0, column=1, sticky='w', pady=5)
        self.voice_menu.bind('<<ComboboxSelected>>',
                            lambda e: self.update_config('elevenlabs_voice', self.voice_var.get()))

        self.refresh_voices_btn = tk.Button(
            voice_section,
            text="Refresh Voices",
            command=self.refresh_elevenlabs_voices,
            bg=self.colors['button'],
            fg='white',
            font=('Arial', 9),
            relief='flat',
            cursor='hand2'
        )
        self.refresh_voices_btn.grid(row=0, column=2, padx=5)

        self.voice_info_label = tk.Label(
            voice_section,
            text="Click 'Refresh Voices' to load your custom ElevenLabs voices",
            bg=self.colors['bg'],
            fg=self.colors['accent'],
            font=('Arial', 9, 'italic')
        )
        self.voice_info_label.grid(row=1, column=0, columnspan=3, sticky='w', pady=5)

        self.elevenlabs_settings_section = self.create_section(scrollable, "ElevenLabs Voice Settings", 2)


        tk.Label(
            self.elevenlabs_settings_section,
            text="Stability:",
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=('Arial', 10)
        ).grid(row=0, column=0, sticky='w', pady=5)

        self.stability_var = tk.DoubleVar(value=self.config.get('elevenlabs_stability', 0.5))
        stability_slider = tk.Scale(
            self.elevenlabs_settings_section,
            from_=0.0,
            to=1.0,
            resolution=0.05,
            orient='horizontal',
            variable=self.stability_var,
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            highlightthickness=0,
            length=200,
            command=lambda v: self.update_config('elevenlabs_stability', float(v))
        )
        stability_slider.grid(row=0, column=1, sticky='w', pady=5, padx=10)

        tk.Label(
            self.elevenlabs_settings_section,
            text="(Lower = more variable, Higher = more stable)",
            bg=self.colors['bg'],
            fg=self.colors['accent'],
            font=('Arial', 8, 'italic')
        ).grid(row=0, column=2, sticky='w', padx=5)

        tk.Label(
            self.elevenlabs_settings_section,
            text="Similarity Boost:",
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=('Arial', 10)
        ).grid(row=1, column=0, sticky='w', pady=5)

        self.similarity_var = tk.DoubleVar(value=self.config.get('elevenlabs_similarity', 0.75))
        similarity_slider = tk.Scale(
            self.elevenlabs_settings_section,
            from_=0.0,
            to=1.0,
            resolution=0.05,
            orient='horizontal',
            variable=self.similarity_var,
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            highlightthickness=0,
            length=200,
            command=lambda v: self.update_config('elevenlabs_similarity', float(v))
        )
        similarity_slider.grid(row=1, column=1, sticky='w', pady=5, padx=10)

        tk.Label(
            self.elevenlabs_settings_section,
            text="(Higher = closer to original voice)",
            bg=self.colors['bg'],
            fg=self.colors['accent'],
            font=('Arial', 8, 'italic')
        ).grid(row=1, column=2, sticky='w', padx=5)

        tk.Label(
            self.elevenlabs_settings_section,
            text="Style Exaggeration:",
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=('Arial', 10)
        ).grid(row=2, column=0, sticky='w', pady=5)

        self.style_var = tk.DoubleVar(value=self.config.get('elevenlabs_style', 0.0))
        style_slider = tk.Scale(
            self.elevenlabs_settings_section,
            from_=0.0,
            to=1.0,
            resolution=0.05,
            orient='horizontal',
            variable=self.style_var,
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            highlightthickness=0,
            length=200,
            command=lambda v: self.update_config('elevenlabs_style', float(v))
        )
        style_slider.grid(row=2, column=1, sticky='w', pady=5, padx=10)

        tk.Label(
            self.elevenlabs_settings_section,
            text="(Higher = more expressive/dramatic)",
            bg=self.colors['bg'],
            fg=self.colors['accent'],
            font=('Arial', 8, 'italic')
        ).grid(row=2, column=2, sticky='w', padx=5)

        self.speaker_boost_var = tk.BooleanVar(value=self.config.get('elevenlabs_speaker_boost', True))
        speaker_boost_check = tk.Checkbutton(
            self.elevenlabs_settings_section,
            text="Use Speaker Boost (enhances voice similarity)",
            variable=self.speaker_boost_var,
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=('Arial', 10),
            selectcolor=self.colors['accent'],
            command=lambda: self.update_config('elevenlabs_speaker_boost', self.speaker_boost_var.get())
        )
        speaker_boost_check.grid(row=3, column=0, columnspan=3, sticky='w', pady=10)

        test_voice_section = self.create_section(scrollable, "Test Voice", 3)
        test_voice_section.grid_columnconfigure(0, weight=1)
        test_voice_section.grid_columnconfigure(1, weight=1)

        tk.Label(
            test_voice_section,
            text="Test your selected voice before using it:",
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=('Arial', 10)
        ).grid(row=0, column=0, columnspan=2, sticky='w', pady=(0, 10))

        test_voice_btn = tk.Button(
            test_voice_section,
            text="Test Voice",
            command=self.test_voice,
            bg='#2196F3',
            fg='white',
            font=('Arial', 11, 'bold'),
            relief='flat',
            cursor='hand2',
            width=15
        )
        test_voice_btn.grid(row=1, column=0, pady=10)

        self.test_voice_label = tk.Label(
            test_voice_section,
            text="",
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=('Arial', 10)
        )
        self.test_voice_label.grid(row=1, column=1, sticky='w', padx=10)

        self.update_voice_dropdown()

    def create_inputs_tab(self, notebook):
        """Inputs tab with microphone, screenshot, and ENHANCED Twitch settings"""
        tab = tk.Frame(notebook, bg=self.colors['bg'])
        notebook.add(tab, text='Inputs')

        scrollable = self.create_scrollable_frame(tab)

        mic_section = self.create_section(scrollable, "Microphone Settings", 0)
        mic_section.grid_columnconfigure(0, weight=1)
        mic_section.grid_columnconfigure(1, weight=1)

        self.mic_var = tk.BooleanVar(value=self.config['mic_enabled'])
        mic_check = tk.Checkbutton(
            mic_section,
            text="Enable Microphone Input",
            variable=self.mic_var,
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=('Arial', 11, 'bold'),
            selectcolor=self.colors['accent'],
            command=lambda: self.update_config('mic_enabled', self.mic_var.get())
        )
        mic_check.grid(row=0, column=0, columnspan=2, sticky='w', pady=5)

        tk.Label(mic_section, text="Microphone Device:",
                 bg=self.colors['bg'], fg=self.colors['fg'],
                 font=('Arial', 10)).grid(row=1, column=0, sticky='w', pady=5)

        self.mic_device_var = tk.StringVar(value="Default")
        self.mic_device_menu = ttk.Combobox(mic_section, textvariable=self.mic_device_var,
                                            state='readonly', width=35)
        self.mic_device_menu.grid(row=1, column=1, sticky='w', pady=5)

        self.refresh_microphone_list()

        refresh_btn = tk.Button(
            mic_section,
            text="Refresh",
            command=self.refresh_microphone_list,
            bg=self.colors['button'],
            fg='white',
            font=('Arial', 9),
            relief='flat',
            cursor='hand2'
        )
        refresh_btn.grid(row=1, column=2, padx=5)

        tk.Label(mic_section, text="Recording Mode:",
                 bg=self.colors['bg'], fg=self.colors['fg'],
                 font=('Arial', 10)).grid(row=2, column=0, sticky='w', pady=5)

        mode_label = tk.Label(
            mic_section,
            text="Push-to-Talk (Hold your selected hotkey to speak)",
            bg=self.colors['bg'],
            fg=self.colors['accent'],
            font=('Arial', 10, 'italic')
        )
        mode_label.grid(row=2, column=1, sticky='w', pady=5)

        screen_section = self.create_section(scrollable, "Screen Capture (Vision)", 1)
        screen_section.grid_columnconfigure(0, weight=1)
        screen_section.grid_columnconfigure(1, weight=1)

        self.screen_var = tk.BooleanVar(value=self.config['screen_enabled'])
        screen_check = tk.Checkbutton(
            screen_section,
            text="Enable Screen Capture (for vision responses)",
            variable=self.screen_var,
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=('Arial', 11),
            selectcolor=self.colors['accent'],
            command=lambda: self.update_config('screen_enabled', self.screen_var.get())
        )
        screen_check.grid(row=0, column=0, columnspan=2, sticky='w', pady=5)

        test_screenshot_btn = tk.Button(
            screen_section,
            text="Test Screenshot Capture",
            command=self.test_screenshot,
            bg='#2196F3',
            fg='white',
            font=('Arial', 10, 'bold'),
            relief='flat',
            cursor='hand2',
            width=25
        )
        test_screenshot_btn.grid(row=1, column=0, columnspan=2, pady=10)

        self.test_screenshot_label = tk.Label(
            screen_section,
            text="Takes a screenshot and has the bot describe what it sees",
            bg=self.colors['bg'],
            fg=self.colors['accent'],
            font=('Arial', 9, 'italic')
        )
        self.test_screenshot_label.grid(row=2, column=0, columnspan=2, sticky='w', pady=5)

        twitch_section = self.create_section(scrollable, "Twitch Chat Integration", 2)
        twitch_section.grid_columnconfigure(0, weight=1)
        twitch_section.grid_columnconfigure(1, weight=1)

        self.twitch_var = tk.BooleanVar(value=self.config['twitch_enabled'])
        twitch_check = tk.Checkbutton(
            twitch_section,
            text="Enable Twitch Chat",
            variable=self.twitch_var,
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=('Arial', 11, 'bold'),
            selectcolor=self.colors['accent'],
            command=lambda: self.update_config('twitch_enabled', self.twitch_var.get())
        )
        twitch_check.grid(row=0, column=0, columnspan=2, sticky='w', pady=5)

        self.twitch_entry = self.create_entry(twitch_section, "Channel Name:", 'twitch_channel', 1)

        # AI Context Settings
        tk.Label(
            twitch_section,
            text="━━━ Context Settings ━━━",
            bg=self.colors['bg'],
            fg=self.colors['accent'],
            font=('Arial', 10, 'bold')
        ).grid(row=2, column=0, columnspan=2, sticky='w', pady=(15, 5))

        tk.Label(twitch_section, text="Include Username in input:",
                 bg=self.colors['bg'], fg=self.colors['fg'],
                 font=('Arial', 10)).grid(row=3, column=0, sticky='w', pady=5)

        self.twitch_read_username_var = tk.BooleanVar(value=self.config.get('twitch_read_username', True))
        username_check = tk.Checkbutton(
            twitch_section,
            text='Send "Username says: message" to the bot',
            variable=self.twitch_read_username_var,
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=('Arial', 9),
            selectcolor=self.colors['accent'],
            command=lambda: self.update_config('twitch_read_username', self.twitch_read_username_var.get())
        )
        username_check.grid(row=3, column=1, sticky='w', pady=5)

        # NEW: TTS Output Settings
        tk.Label(
            twitch_section,
            text="━━━ TTS Output Settings ━━━",
            bg=self.colors['bg'],
            fg=self.colors['accent'],
            font=('Arial', 10, 'bold')
        ).grid(row=4, column=0, columnspan=2, sticky='w', pady=(15, 5))

        tk.Label(
            twitch_section,
            text="Control what the bot actually SAYS out loud when responding:",
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=('Arial', 9, 'italic')
        ).grid(row=5, column=0, columnspan=2, sticky='w', pady=(0, 10))

        # NEW: Speak Username checkbox
        tk.Label(twitch_section, text="Speak Username:",
                 bg=self.colors['bg'], fg=self.colors['fg'],
                 font=('Arial', 10)).grid(row=6, column=0, sticky='w', pady=5)

        self.twitch_speak_username_var = tk.BooleanVar(value=self.config.get('twitch_speak_username', True))
        speak_username_check = tk.Checkbutton(
            twitch_section,
            text='TTS says the username before responding',
            variable=self.twitch_speak_username_var,
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=('Arial', 9),
            selectcolor=self.colors['accent'],
            command=lambda: self.update_config('twitch_speak_username', self.twitch_speak_username_var.get())
        )
        speak_username_check.grid(row=6, column=1, sticky='w', pady=5)

        # NEW: Speak Message checkbox
        tk.Label(twitch_section, text="Speak Message:",
                 bg=self.colors['bg'], fg=self.colors['fg'],
                 font=('Arial', 10)).grid(row=7, column=0, sticky='w', pady=5)

        self.twitch_speak_message_var = tk.BooleanVar(value=self.config.get('twitch_speak_message', True))
        speak_message_check = tk.Checkbutton(
            twitch_section,
            text='TTS says the user\'s message before responding',
            variable=self.twitch_speak_message_var,
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=('Arial', 9),
            selectcolor=self.colors['accent'],
            command=lambda: self.update_config('twitch_speak_message', self.twitch_speak_message_var.get())
        )
        speak_message_check.grid(row=7, column=1, sticky='w', pady=5)

        # Example output
        tk.Label(
            twitch_section,
            text='Example: When both checked, TTS will say "Username said: their message. [Bot\'s response]"',
            bg=self.colors['bg'],
            fg=self.colors['accent'],
            font=('Arial', 8, 'italic'),
            wraplength=500,
            justify='left'
        ).grid(row=8, column=0, columnspan=2, sticky='w', pady=(0, 10))

        # Response Mode Settings
        tk.Label(
            twitch_section,
            text="━━━ Response Mode ━━━",
            bg=self.colors['bg'],
            fg=self.colors['accent'],
            font=('Arial', 10, 'bold')
        ).grid(row=9, column=0, columnspan=2, sticky='w', pady=(15, 5))

        tk.Label(twitch_section, text="Response Mode:",
                 bg=self.colors['bg'], fg=self.colors['fg'],
                 font=('Arial', 10)).grid(row=10, column=0, sticky='w', pady=5)

        self.twitch_response_mode_var = tk.StringVar(value=self.config.get('twitch_response_mode', 'all'))
        response_modes = ['all', 'keywords', 'random', 'disabled']
        twitch_mode_menu = ttk.Combobox(
            twitch_section,
            textvariable=self.twitch_response_mode_var,
            values=response_modes,
            state='readonly',
            width=15
        )
        twitch_mode_menu.grid(row=10, column=1, sticky='w', pady=5)
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
            font=('Arial', 9, 'italic'),
            wraplength=400,
            justify='left'
        )
        self.twitch_mode_desc.grid(row=11, column=0, columnspan=2, sticky='w', pady=5)

        self.twitch_keywords_frame = tk.Frame(twitch_section, bg=self.colors['bg'])
        self.twitch_keywords_frame.grid(row=12, column=0, columnspan=2, sticky='ew', pady=5)

        tk.Label(
            self.twitch_keywords_frame,
            text="Keywords (comma-separated):",
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=('Arial', 10)
        ).pack(side='left', padx=5)

        self.twitch_keywords_entry = tk.Entry(
            self.twitch_keywords_frame,
            bg=self.colors['entry_bg'],
            font=('Arial', 10),
            width=30
        )
        self.twitch_keywords_entry.pack(side='left', padx=5)
        self.twitch_keywords_entry.insert(0, self.config.get('twitch_keywords', '!ai,!bot,!ask'))
        self.twitch_keywords_entry.bind('<FocusOut>',
                                        lambda e: self.update_config('twitch_keywords',
                                                                     self.twitch_keywords_entry.get()))

        self.twitch_chance_frame = tk.Frame(twitch_section, bg=self.colors['bg'])
        self.twitch_chance_frame.grid(row=13, column=0, columnspan=2, sticky='w', pady=5)

        tk.Label(
            self.twitch_chance_frame,
            text="Response Chance:",
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=('Arial', 10)
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
            font=('Arial', 9)
        )
        self.chance_label.pack(side='left', padx=5)

        chance_slider.config(command=lambda v: self.update_chance_label(int(float(v))))

        tk.Label(twitch_section, text="Response Cooldown:",
                 bg=self.colors['bg'], fg=self.colors['fg'],
                 font=('Arial', 10)).grid(row=14, column=0, sticky='w', pady=5)

        cooldown_frame = tk.Frame(twitch_section, bg=self.colors['bg'])
        cooldown_frame.grid(row=14, column=1, sticky='w', pady=5)

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
            font=('Arial', 9)
        )
        self.cooldown_label.pack(side='left', padx=5)

        cooldown_slider.config(command=lambda v: self.update_cooldown_label(int(float(v))))

        tk.Label(
            twitch_section,
            text="Cooldown prevents spam - set to 0 to respond immediately to every message, which is probably a bad idea",
            bg=self.colors['bg'],
            fg=self.colors['accent'],
            font=('Arial', 9, 'italic'),
            wraplength=500,
            justify='left'
        ).grid(row=15, column=0, columnspan=2, sticky='w', pady=5)

        self.update_twitch_mode_visibility()

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

    def create_avatar_tab(self, notebook):
        """Avatar images tab with preview"""
        tab = tk.Frame(notebook, bg=self.colors['bg'])
        notebook.add(tab, text='Avatar')

        scrollable = self.create_scrollable_frame(tab)

        info_frame = tk.Frame(scrollable, bg=self.colors['entry_bg'], bd=2, relief='solid')
        info_frame.pack(fill='x', padx=40, pady=25)

        info_text = """
Avatar Setup Instructions

The avatar is an animated PNG image that appears on screen while the bot is active.

• SPEAKING IMAGE: Shown when AI is talking (e.g., open mouth, glowing, animated)
• IDLE IMAGE: Shown when AI is silent (e.g., closed mouth, still, waiting)

These images will automatically switch during conversation.
This means you'll need to import the "current_avatar.png" image into OBS, and it will update automatically.
        """

        tk.Label(
            info_frame,
            text=info_text,
            bg=self.colors['entry_bg'],
            fg=self.colors['fg'],
            font=('Arial', 10),
            justify='left'
        ).pack(padx=30, pady=20)

        images_section = self.create_section(scrollable, "Select Avatar Images", 0)
        images_section.grid_columnconfigure(0, weight=1)
        images_section.grid_columnconfigure(1, weight=1)

        speaking_frame = tk.Frame(images_section, bg=self.colors['bg'])
        speaking_frame.pack(fill='x', pady=10)

        tk.Label(
            speaking_frame,
            text="Speaking Image:",
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=('Arial', 11, 'bold'),
            width=18,
            anchor='w'
        ).pack(side='left', padx=5)

        self.speaking_path_label = tk.Label(
            speaking_frame,
            text=self.config.get('speaking_image', 'Not selected') or 'Not selected',
            bg=self.colors['entry_bg'],
            fg=self.colors['fg'],
            font=('Arial', 9),
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
            font=('Arial', 10, 'bold'),
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
            font=('Arial', 11, 'bold'),
            width=18,
            anchor='w'
        ).pack(side='left', padx=5)

        self.idle_path_label = tk.Label(
            idle_frame,
            text=self.config.get('idle_image', 'Not selected') or 'Not selected',
            bg=self.colors['entry_bg'],
            fg=self.colors['fg'],
            font=('Arial', 9),
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
            font=('Arial', 10, 'bold'),
            relief='raised',
            borderwidth=2,
            cursor='hand2',
            padx=15,
            pady=5
        ).pack(side='left', padx=5)

        preview_section = self.create_section(scrollable, "Preview", 1)
        preview_section.grid_columnconfigure(0, weight=1)
        preview_section.grid_columnconfigure(1, weight=1)

        preview_container = tk.Frame(preview_section, bg=self.colors['bg'])
        preview_container.pack(expand=True)

        preview_border = tk.Frame(preview_container, bg=self.colors['accent'], bd=3, relief='solid')
        preview_border.pack(pady=10)

        self.preview_label = tk.Label(
            preview_border,
            text="No image selected\n\nSelect an image above to see preview",
            bg=self.colors['text_bg'],
            fg=self.colors['accent'],
            font=('Arial', 11, 'italic'),
            width=50,
            height=18,
            relief='flat'
        )
        self.preview_label.pack(padx=3, pady=3)
        self.load_existing_avatar_previews()
    def create_control_panel(self, parent):
        """Create bottom control panel - always visible"""
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
            font=('Arial', 12, 'bold')
        )
        self.status_label.pack(anchor='w')

        self.recording_label = tk.Label(
            left_frame,
            text="",
            bg=self.colors['accent'],
            fg='#FFD700',
            font=('Arial', 10)
        )
        self.recording_label.pack(anchor='w')

        center_frame = tk.Frame(inner, bg=self.colors['accent'])
        center_frame.pack(side='left', padx=40)

        self.screenshot_btn = tk.Button(
            center_frame,
            text="Screenshot & Respond",
            command=self.screenshot_and_respond,
            bg='#FF6B6B',
            fg='white',
            font=('Arial', 10, 'bold'),
            relief='raised',
            borderwidth=3,
            cursor='hand2',
            padx=15,
            pady=8
        )
        self.screenshot_btn.pack()

        right_frame = tk.Frame(inner, bg=self.colors['accent'])
        right_frame.pack(side='right')

        buttons_frame = tk.Frame(right_frame, bg=self.colors['accent'])
        buttons_frame.pack()

        save_btn = tk.Button(
            buttons_frame,
            text="💾 Save Settings",
            command=self.save_all_settings,
            bg=self.colors['button'],
            fg='white',
            font=('Arial', 11, 'bold'),
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
            font=('Arial', 13, 'bold'),
            relief='raised',
            borderwidth=3,
            cursor='hand2',
            padx=20,
            pady=10
        )
        self.start_btn.pack(side='left', padx=5)

    def create_section(self, parent, title, row):
        """Create labeled section with centered content"""
        outer = tk.Frame(parent, bg=self.colors['bg'])
        outer.pack(fill='x', padx=30, pady=15)

        section = tk.Frame(outer, bg=self.colors['bg'])
        section.pack(anchor='center')  # Center the section

        title_frame = tk.Frame(section, bg=self.colors['bg'])
        title_frame.pack(fill='x', pady=(0, 10))

        tk.Label(
            title_frame,
            text=title,
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=self.ui_font_bold  # Use custom font
        ).pack(anchor='center')

        separator = tk.Frame(title_frame, bg=self.colors['accent'], height=2)
        separator.pack(fill='x', pady=(5, 0))

        frame = tk.Frame(section, bg=self.colors['bg'])
        frame.pack(fill='both', padx=10)  # Changed from fill='x' to fill='both'

        return frame

    def create_entry(self, parent, label, config_key, row):
        """Create labeled entry - centered with proper alignment"""
        tk.Label(
            parent,
            text=label,
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=self.ui_font
        ).grid(row=row, column=0, sticky='e', pady=5, padx=(0, 10))  # Right-align labels

        entry = tk.Entry(
            parent,
            bg=self.colors['entry_bg'],
            font=self.ui_font,
            width=30
        )
        entry.grid(row=row, column=1, sticky='w', pady=5, padx=(10, 0))  # Left-align entries
        entry.insert(0, self.config[config_key])
        entry.bind('<FocusOut>',
                   lambda e, key=config_key: self.update_config(key, entry.get()))

        return entry

    def refresh_microphone_list(self):
        """Refresh list of available microphones"""
        try:
            import speech_recognition as sr
            mic_list = sr.Microphone.list_microphone_names()

            if mic_list:
                self.mic_device_menu['values'] = ['Default'] + mic_list
                print(f"[App] Found {len(mic_list)} microphone(s)")
            else:
                self.mic_device_menu['values'] = ['No microphones found']

        except Exception as e:
            print(f"[App] Error refreshing microphones: {e}")
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

                if '(' in voice and ')' in voice:
                    voice = voice.split('(')[1].split(')')[0]

                elevenlabs_settings = None
                if service == 'elevenlabs':
                    elevenlabs_settings = {
                        'stability': self.config.get('elevenlabs_stability', 0.5),
                        'similarity_boost': self.config.get('elevenlabs_similarity', 0.75),
                        'style': self.config.get('elevenlabs_style', 0.0),
                        'use_speaker_boost': self.config.get('elevenlabs_speaker_boost', True)
                    }

                tts = TTSManager(service=service, voice=voice, elevenlabs_settings=elevenlabs_settings)

                test_message = f"Hello! This is a test of the {service} voice. Do you like me? Am I what you wanted?"

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

        self.voice_menu['values'] = voices

        current_voice = self.voice_var.get()
        if current_voice not in voices:
            self.voice_var.set(voices[0])
            self.update_config('elevenlabs_voice', voices[0])

        if service == 'elevenlabs':
            self.refresh_voices_btn.grid()
            self.voice_info_label.grid()
            for widget in self.elevenlabs_settings_section.winfo_children():
                widget.grid()
        else:
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
                    text=f"Loaded {len(custom_voices)} custom voice(s) from your account"
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
        self.update_config('tts_service', self.tts_var.get())
        self.update_voice_dropdown()

    def browse_image(self, image_type):
        """Browse for avatar image"""
        filename = filedialog.askopenfilename(
            title=f"Select {image_type} image",
            filetypes=[("PNG files", "*.png"), ("All image files", "*.png *.jpg *.jpeg"), ("All files", "*.*")]
        )

        if filename:
            config_key = f'{image_type}_image'
            self.update_config(config_key, filename)

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

            # Show preview
            self.update_avatar_preview(filename)

    def update_avatar_preview(self, filename):
        """Update the avatar preview with the selected image"""
        try:
            img = Image.open(filename)

            # Resize to fit preview (max 400x400)
            img.thumbnail((400, 400), Image.Resampling.LANCZOS)

            # Create a neon green background if image has transparency
            if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                # Create neon green background
                background = Image.new('RGB', img.size, '#00FF00')  # Neon green

                # Convert image to RGBA if needed
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')

                # Composite image over green background
                background.paste(img, (0, 0), img)
                img = background

            # Convert to PhotoImage and display
            photo = ImageTk.PhotoImage(img)
            self.preview_label.config(image=photo, text="")
            self.preview_label.image = photo  # Keep reference

        except Exception as e:
            print(f"[App] Error loading preview: {e}")
            self.preview_label.config(
                text=f"Image selected but preview failed\n\n{filename}",
                fg=self.colors['fg']
            )

    def load_existing_avatar_previews(self):
        """Load preview of already configured images"""
        # Check if speaking image exists and show preview
        speaking_path = self.config.get('speaking_image', '')
        if speaking_path and Path(speaking_path).exists():
            self.update_avatar_preview(speaking_path)
        # If only idle image exists, show that instead
        elif self.config.get('idle_image', '') and Path(self.config.get('idle_image', '')).exists():
            self.update_avatar_preview(self.config.get('idle_image', ''))

    def update_config(self, key, value):
        """Update configuration"""
        self.config[key] = value
        self.engine.set_config(key, value)

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

                    prompt = "What do you see in this screenshot? Describe it in detail."
                    self.engine._process_and_respond(prompt, screen_data)
                else:
                    self.add_chat_message("System", "❌ Failed to capture screenshot")

            except Exception as e:
                import traceback
                print(f"[Screenshot] Error: {traceback.format_exc()}")
                self.add_chat_message("System", f"Screenshot error: {e}")

        threading.Thread(target=screenshot_thread, daemon=True).start()

    def remove_hotkeys(self):  # UNINDENT - should be at class level
        """Remove all hotkeys"""
        if self.hotkey_active:
            try:
                keyboard.unhook_all()
                self.hotkey_active = False
            except:
                pass

    def send_text_message(self):
        """Send text message - works in test mode or full chatbot mode"""
        text = self.text_input.get().strip()
        if not text:
            return

        self.text_input.delete(0, tk.END)
        self.add_chat_message(self.config['user_name'], text)

        if self.engine.is_running:
            # Full chatbot mode - process normally
            def process_thread():
                self.engine.process_text_input(text)

            threading.Thread(target=process_thread, daemon=True).start()
        else:
            # Test mode - get response with TTS
            self.add_chat_message("System", "Test mode: Getting response with voice...")

            def test_thread():
                try:
                    from llm_manager import LLMManager
                    from tts_manager import TTSManager

                    # Create temporary LLM instance
                    system_prompt = self.config['personality']
                    if self.config['ai_name'] != 'Assistant':
                        system_prompt += f"\n\nYour name is {self.config['ai_name']}."

                    llm = LLMManager(
                        model=self.config['llm_model'],
                        system_prompt=system_prompt
                    )

                    # Get response length setting
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

                    # Get AI response
                    response = llm.chat(text, max_response_tokens=max_tokens)
                    self.display_response(response)

                    # Speak response with TTS
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

                    # Speak the response
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
    Thank you for using my silly little software! Here's how to get started:

    QUICK SETUP CHECKLIST:

      ✓ Step 1: Configure API Keys (API Keys tab)
        • Add your OpenAI API key (REQUIRED)
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

    ═══════════════════════════════════════════════════════════════════════════════

    Ready to begin? Start by adding your OpenAI API key in the API Keys tab!
    
    Fuck OpenAI and Elon btw, I'll have open source models soon.

    """
        self.chat_display.config(state='normal')
        self.chat_display.insert('1.0', welcome_text, 'welcome')
        self.chat_display.config(state='disabled')

    def test_ai_connection(self):  # UNINDENT - should be at class level, NOT inside show_welcome_message
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

    def display_response(self, response):  # UNINDENT - should be at class level
        """Display AI response in chat"""
        self.add_chat_message(self.config['ai_name'], response)

    def add_chat_message(self, sender, message):  # UNINDENT - should be at class level
        """Add message to chat display"""
        self.chat_display.config(state='normal')
        self.chat_display.insert(tk.END, f"\n{sender}: {message}\n")
        self.chat_display.see(tk.END)
        self.chat_display.config(state='disabled')

    def on_ai_speaking_start(self):  # UNINDENT - should be at class level
        """Called when AI starts speaking"""
        self.status_label.config(text="🟢 Speaking...")

    def on_ai_speaking_end(self):  # UNINDENT - should be at class level
        """Called when AI finishes speaking"""
        self.status_label.config(text="🟢 Running")


def main():  # This should NOT be indented at all - it's outside the class
    root = tk.Tk()
    app = IntegratedChatbotApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()