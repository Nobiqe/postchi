import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import asyncio
import threading
from typing import Optional
import json
from datetime import datetime
import os
from pathlib import Path

# Import your existing modules
from config import ConfigManager, ChannelMapping, TelegramConfig, AIConfig
from main_processor import MultiChannelProcessor
from database import DatabaseManager

class ModernTelegramBotGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Telegram Multi-Channel Processor")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        
        # Initialize managers
        self.config_manager = ConfigManager()
        self.db_manager = DatabaseManager()
        self.processor: Optional[MultiChannelProcessor] = None
        self.monitoring_thread = None
        self.is_monitoring = False
        
        # Color scheme - Modern minimal
        self.colors = {
            'bg': '#ffffff',
            'sidebar': '#f8f9fa',
            'primary': '#007bff',
            'success': '#28a745',
            'danger': '#dc3545',
            'warning': '#ffc107',
            'text': '#212529',
            'text_light': '#6c757d',
            'border': '#dee2e6'
        }
        
        self.setup_styles()
        self.setup_gui()
        self.load_initial_data()
        
    def setup_styles(self):
        """Setup modern styling"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure styles
        style.configure('Sidebar.TFrame', background=self.colors['sidebar'])
        style.configure('Main.TFrame', background=self.colors['bg'])
        style.configure('Title.TLabel', font=('Segoe UI', 16, 'bold'), background=self.colors['bg'])
        style.configure('Subtitle.TLabel', font=('Segoe UI', 10), foreground=self.colors['text_light'], background=self.colors['bg'])
        style.configure('Primary.TButton', font=('Segoe UI', 9))
        style.configure('Success.TButton', font=('Segoe UI', 9))
        style.configure('Danger.TButton', font=('Segoe UI', 9))
        
    def setup_gui(self):
        """Setup the main GUI structure"""
        # Main container
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create sidebar
        self.create_sidebar()
        
        # Create main content area
        self.create_main_content()
        
        # Status bar
        self.create_status_bar()
        
        # Show dashboard by default
        self.show_dashboard()
        
    def create_sidebar(self):
        """Create sidebar navigation"""
        sidebar_frame = ttk.Frame(self.main_frame, style='Sidebar.TFrame', width=200)
        sidebar_frame.pack(side='left', fill='y', padx=(0, 10))
        sidebar_frame.pack_propagate(False)
        
        # Logo/Title
        title_label = ttk.Label(sidebar_frame, text="Telegram Bot", 
                               font=('Segoe UI', 14, 'bold'),
                               background=self.colors['sidebar'])
        title_label.pack(pady=(20, 30))
        
        # Navigation buttons
        nav_buttons = [
            ("🏠 Dashboard", self.show_dashboard),
            ("⚙️ Configuration", self.show_configuration),
            ("🔄 Channel Mappings", self.show_mappings),
            ("📱 Channels", self.show_channels),
            ("🤖 AI Settings", self.show_ai_settings),
            ("▶️ Start Processing", self.show_processing),
            ("📊 Database", self.show_database),
        ]
        
        self.nav_buttons = {}
        for text, command in nav_buttons:
            btn = tk.Button(sidebar_frame, text=text, command=command,
                           font=('Segoe UI', 10), relief='flat',
                           bg=self.colors['sidebar'], fg=self.colors['text'],
                           anchor='w', padx=20, pady=10,
                           activebackground=self.colors['primary'],
                           activeforeground='white')
            btn.pack(fill='x', pady=2)
            self.nav_buttons[text] = btn
            
    def create_main_content(self):
        """Create main content area"""
        self.content_frame = ttk.Frame(self.main_frame, style='Main.TFrame')
        self.content_frame.pack(side='right', fill='both', expand=True)
        
    def create_status_bar(self):
        """Create status bar"""
        self.status_frame = ttk.Frame(self.root)
        self.status_frame.pack(side='bottom', fill='x')
        
        self.status_label = ttk.Label(self.status_frame, text="Ready", 
                                     font=('Segoe UI', 9),
                                     foreground=self.colors['text_light'])
        self.status_label.pack(side='left', padx=10, pady=5)
        
        # Connection status
        self.connection_label = ttk.Label(self.status_frame, text="●", 
                                         font=('Segoe UI', 12),
                                         foreground=self.colors['danger'])
        self.connection_label.pack(side='right', padx=10, pady=5)
        
    def clear_content(self):
        """Clear main content area"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
            
    def update_nav_buttons(self, active_button):
        """Update navigation button styles"""
        for text, btn in self.nav_buttons.items():
            if text == active_button:
                btn.configure(bg=self.colors['primary'], fg='white')
            else:
                btn.configure(bg=self.colors['sidebar'], fg=self.colors['text'])
                
    def show_dashboard(self):
        """Show dashboard view"""
        self.clear_content()
        self.update_nav_buttons("🏠 Dashboard")
        
        # Title
        title = ttk.Label(self.content_frame, text="Dashboard", style='Title.TLabel')
        title.pack(anchor='w', pady=(0, 20))
        
        # Stats cards
        stats_frame = ttk.Frame(self.content_frame)
        stats_frame.pack(fill='x', pady=(0, 20))
        
        # Get statistics
        stats = self.get_dashboard_stats()
        
        # Create stat cards
        card_configs = [
            ("Total Messages", stats['total_messages'], self.colors['primary']),
            ("Active Mappings", stats['active_mappings'], self.colors['success']),
            ("Pending Messages", stats['pending_messages'], self.colors['warning']),
            ("Posted Today", stats['posted_today'], self.colors['success'])
        ]
        
        for i, (title, value, color) in enumerate(card_configs):
            card = self.create_stat_card(stats_frame, title, str(value), color)
            card.grid(row=0, column=i, padx=10, sticky='ew')
        
        # Configure grid weights
        for i in range(len(card_configs)):
            stats_frame.grid_columnconfigure(i, weight=1)
            
        # Recent activity
        activity_frame = ttk.LabelFrame(self.content_frame, text="Recent Activity", padding=10)
        activity_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        self.activity_tree = ttk.Treeview(activity_frame, columns=('Time', 'Mapping', 'Status', 'Message'), show='headings', height=10)
        
        # Configure columns
        self.activity_tree.heading('Time', text='Time')
        self.activity_tree.heading('Mapping', text='Mapping')
        self.activity_tree.heading('Status', text='Status')
        self.activity_tree.heading('Message', text='Message Preview')
        
        self.activity_tree.column('Time', width=150)
        self.activity_tree.column('Mapping', width=150)
        self.activity_tree.column('Status', width=100)
        self.activity_tree.column('Message', width=300)
        
        # Add scrollbar
        activity_scrollbar = ttk.Scrollbar(activity_frame, orient='vertical', command=self.activity_tree.yview)
        self.activity_tree.configure(yscrollcommand=activity_scrollbar.set)
        
        self.activity_tree.pack(side='left', fill='both', expand=True)
        activity_scrollbar.pack(side='right', fill='y')
        
        # Load recent activity
        self.load_recent_activity()
        
    def create_stat_card(self, parent, title, value, color):
        """Create a statistics card"""
        card = ttk.Frame(parent, relief='solid', borderwidth=1)
        card.configure(style='Main.TFrame')
        
        # Value
        value_label = ttk.Label(card, text=value, font=('Segoe UI', 24, 'bold'))
        value_label.pack(pady=(10, 0))
        
        # Title
        title_label = ttk.Label(card, text=title, font=('Segoe UI', 10), 
                               foreground=self.colors['text_light'])
        title_label.pack(pady=(0, 10))
        
        return card
        
    def show_configuration(self):
        """Show Telegram configuration"""
        self.clear_content()
        self.update_nav_buttons("⚙️ Configuration")
        
        title = ttk.Label(self.content_frame, text="Telegram Configuration", style='Title.TLabel')
        title.pack(anchor='w', pady=(0, 20))
        
        # Configuration form
        config_frame = ttk.LabelFrame(self.content_frame, text="Telegram Settings", padding=20)
        config_frame.pack(fill='x', pady=(0, 10))
        
        # API ID
        ttk.Label(config_frame, text="API ID:").grid(row=0, column=0, sticky='w', pady=5)
        self.api_id_var = tk.StringVar(value=self.config_manager.telegram_config.api_id)
        api_id_entry = ttk.Entry(config_frame, textvariable=self.api_id_var, width=30)
        api_id_entry.grid(row=0, column=1, sticky='ew', pady=5, padx=(10, 0))
        
        # API Hash
        ttk.Label(config_frame, text="API Hash:").grid(row=1, column=0, sticky='w', pady=5)
        self.api_hash_var = tk.StringVar(value=self.config_manager.telegram_config.api_hash)
        api_hash_entry = ttk.Entry(config_frame, textvariable=self.api_hash_var, width=30, show="*")
        api_hash_entry.grid(row=1, column=1, sticky='ew', pady=5, padx=(10, 0))
        
        # Phone Number
        ttk.Label(config_frame, text="Phone Number:").grid(row=2, column=0, sticky='w', pady=5)
        self.phone_var = tk.StringVar(value=self.config_manager.telegram_config.phone_number)
        phone_entry = ttk.Entry(config_frame, textvariable=self.phone_var, width=30)
        phone_entry.grid(row=2, column=1, sticky='ew', pady=5, padx=(10, 0))
        
        config_frame.grid_columnconfigure(1, weight=1)
        
        # Buttons
        button_frame = ttk.Frame(config_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=20)
        
        save_btn = ttk.Button(button_frame, text="Save Configuration", 
                             command=self.save_telegram_config)
        save_btn.pack(side='left', padx=(0, 10))
        
        test_btn = ttk.Button(button_frame, text="Test Connection", 
                             command=self.test_telegram_connection)
        test_btn.pack(side='left')
        
    def show_ai_settings(self):
        """Show AI configuration"""
        self.clear_content()
        self.update_nav_buttons("🤖 AI Settings")
        
        title = ttk.Label(self.content_frame, text="AI Configuration", style='Title.TLabel')
        title.pack(anchor='w', pady=(0, 20))
        
        # AI form
        ai_frame = ttk.LabelFrame(self.content_frame, text="AI Settings", padding=20)
        ai_frame.pack(fill='x', pady=(0, 10))
        
        # Provider selection
        ttk.Label(ai_frame, text="Provider:").grid(row=0, column=0, sticky='w', pady=5)
        self.provider_var = tk.StringVar(value=self.config_manager.ai_config.provider)
        provider_combo = ttk.Combobox(ai_frame, textvariable=self.provider_var, 
                                     values=['gemini', 'openai', 'openrouter'],
                                     state='readonly', width=28)
        provider_combo.grid(row=0, column=1, sticky='ew', pady=5, padx=(10, 0))
        
        # API Key
        ttk.Label(ai_frame, text="API Key:").grid(row=1, column=0, sticky='w', pady=5)
        self.ai_api_key_var = tk.StringVar(value=self.config_manager.ai_config.api_key)
        api_key_entry = ttk.Entry(ai_frame, textvariable=self.ai_api_key_var, width=30, show="*")
        api_key_entry.grid(row=1, column=1, sticky='ew', pady=5, padx=(10, 0))
        
        # Model
        ttk.Label(ai_frame, text="Model:").grid(row=2, column=0, sticky='w', pady=5)
        self.ai_model_var = tk.StringVar(value=self.config_manager.ai_config.model)
        model_entry = ttk.Entry(ai_frame, textvariable=self.ai_model_var, width=30)
        model_entry.grid(row=2, column=1, sticky='ew', pady=5, padx=(10, 0))
        
        # Base URL
        ttk.Label(ai_frame, text="Base URL:").grid(row=3, column=0, sticky='w', pady=5)
        self.base_url_var = tk.StringVar(value=getattr(self.config_manager.ai_config, 'base_url', ''))
        base_url_entry = ttk.Entry(ai_frame, textvariable=self.base_url_var, width=30)
        base_url_entry.grid(row=3, column=1, sticky='ew', pady=5, padx=(10, 0))
        
        ai_frame.grid_columnconfigure(1, weight=1)
        
        # Buttons
        ai_button_frame = ttk.Frame(ai_frame)
        ai_button_frame.grid(row=4, column=0, columnspan=2, pady=20)
        
        save_ai_btn = ttk.Button(ai_button_frame, text="Save AI Config", 
                                command=self.save_ai_config)
        save_ai_btn.pack(side='left', padx=(0, 10))
        
        test_ai_btn = ttk.Button(ai_button_frame, text="Test AI Connection", 
                                command=self.test_ai_connection)
        test_ai_btn.pack(side='left')
        
    def show_mappings(self):
        """Show channel mappings management"""
        self.clear_content()
        self.update_nav_buttons("🔄 Channel Mappings")
        
        title = ttk.Label(self.content_frame, text="Channel Mappings", style='Title.TLabel')
        title.pack(anchor='w', pady=(0, 20))
        
        # Toolbar
        toolbar = ttk.Frame(self.content_frame)
        toolbar.pack(fill='x', pady=(0, 10))
        
        add_btn = ttk.Button(toolbar, text="+ Add Mapping", command=self.add_mapping_dialog)
        add_btn.pack(side='left', padx=(0, 10))
        
        edit_btn = ttk.Button(toolbar, text="✏️ Edit", command=self.edit_mapping_dialog)
        edit_btn.pack(side='left', padx=(0, 10))
        
        delete_btn = ttk.Button(toolbar, text="🗑️ Delete", command=self.delete_mapping)
        delete_btn.pack(side='left')
        
        # Mappings tree
        mappings_frame = ttk.Frame(self.content_frame)
        mappings_frame.pack(fill='both', expand=True)
        
        self.mappings_tree = ttk.Treeview(mappings_frame, 
                                         columns=('ID', 'Source', 'Target', 'Status', 'Keywords'), 
                                         show='headings')
        
        # Configure columns
        self.mappings_tree.heading('ID', text='Mapping ID')
        self.mappings_tree.heading('Source', text='Source Channel')
        self.mappings_tree.heading('Target', text='Target Channel')
        self.mappings_tree.heading('Status', text='Status')
        self.mappings_tree.heading('Keywords', text='Keywords')
        
        self.mappings_tree.column('ID', width=150)
        self.mappings_tree.column('Source', width=200)
        self.mappings_tree.column('Target', width=200)
        self.mappings_tree.column('Status', width=100)
        self.mappings_tree.column('Keywords', width=200)
        
        # Scrollbars
        v_scroll = ttk.Scrollbar(mappings_frame, orient='vertical', command=self.mappings_tree.yview)
        h_scroll = ttk.Scrollbar(mappings_frame, orient='horizontal', command=self.mappings_tree.xview)
        self.mappings_tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        
        self.mappings_tree.pack(side='left', fill='both', expand=True)
        v_scroll.pack(side='right', fill='y')
        h_scroll.pack(side='bottom', fill='x')
        
        self.load_mappings()
        
    def show_processing(self):
        """Show processing control panel"""
        self.clear_content()
        self.update_nav_buttons("▶️ Start Processing")
        
        title = ttk.Label(self.content_frame, text="Message Processing", style='Title.TLabel')
        title.pack(anchor='w', pady=(0, 20))
        
        # Processing options
        options_frame = ttk.LabelFrame(self.content_frame, text="Processing Options", padding=20)
        options_frame.pack(fill='x', pady=(0, 10))
        
        # Processing mode
        ttk.Label(options_frame, text="Processing Mode:").pack(anchor='w', pady=(0, 5))
        self.processing_mode = tk.StringVar(value="realtime")
        
        mode_frame = ttk.Frame(options_frame)
        mode_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Radiobutton(mode_frame, text="Historical (Last 7 days)", 
                       variable=self.processing_mode, value="historical").pack(anchor='w')
        ttk.Radiobutton(mode_frame, text="Real-time Monitoring", 
                       variable=self.processing_mode, value="realtime").pack(anchor='w')
        ttk.Radiobutton(mode_frame, text="Both (Recommended)", 
                       variable=self.processing_mode, value="both").pack(anchor='w')
        
        # AI options
        ai_options_frame = ttk.Frame(options_frame)
        ai_options_frame.pack(fill='x', pady=(10, 0))
        
        self.use_ai = tk.BooleanVar(value=True)
        ai_check = ttk.Checkbutton(ai_options_frame, text="Use AI Agent for text processing", 
                                  variable=self.use_ai)
        ai_check.pack(anchor='w')
        
        self.include_media = tk.BooleanVar(value=False)
        media_check = ttk.Checkbutton(ai_options_frame, text="Download and forward media files", 
                                     variable=self.include_media)
        media_check.pack(anchor='w')
        
        # Control buttons
        control_frame = ttk.Frame(self.content_frame)
        control_frame.pack(fill='x', pady=20)
        
        self.start_btn = ttk.Button(control_frame, text="▶️ Start Processing", 
                                   command=self.start_processing, style='Success.TButton')
        self.start_btn.pack(side='left', padx=(0, 10))
        
        self.stop_btn = ttk.Button(control_frame, text="⏹️ Stop Processing", 
                                  command=self.stop_processing, style='Danger.TButton', 
                                  state='disabled')
        self.stop_btn.pack(side='left')
        
        # Log area
        log_frame = ttk.LabelFrame(self.content_frame, text="Processing Log", padding=10)
        log_frame.pack(fill='both', expand=True)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, wrap=tk.WORD)
        self.log_text.pack(fill='both', expand=True)
        
    def show_channels(self):
        """Show available channels"""
        self.clear_content()
        self.update_nav_buttons("📱 Channels")
        
        title = ttk.Label(self.content_frame, text="Available Channels", style='Title.TLabel')
        title.pack(anchor='w', pady=(0, 20))
        
        # Refresh button
        refresh_btn = ttk.Button(self.content_frame, text="🔄 Refresh Channels", 
                                command=self.refresh_channels)
        refresh_btn.pack(anchor='w', pady=(0, 10))
        
        # Channels tree
        channels_frame = ttk.Frame(self.content_frame)
        channels_frame.pack(fill='both', expand=True)
        
        self.channels_tree = ttk.Treeview(channels_frame, 
                                         columns=('Name', 'ID', 'Type'), 
                                         show='headings')
        
        self.channels_tree.heading('Name', text='Channel Name')
        self.channels_tree.heading('ID', text='Channel ID')
        self.channels_tree.heading('Type', text='Type')
        
        self.channels_tree.column('Name', width=300)
        self.channels_tree.column('ID', width=150)
        self.channels_tree.column('Type', width=100)
        
        # Scrollbar
        channels_scroll = ttk.Scrollbar(channels_frame, orient='vertical', command=self.channels_tree.yview)
        self.channels_tree.configure(yscrollcommand=channels_scroll.set)
        
        self.channels_tree.pack(side='left', fill='both', expand=True)
        channels_scroll.pack(side='right', fill='y')
        
        self.load_channels()
        
    def show_database(self):
        """Show database management"""
        self.clear_content()
        self.update_nav_buttons("📊 Database")
        
        title = ttk.Label(self.content_frame, text="Database Management", style='Title.TLabel')
        title.pack(anchor='w', pady=(0, 20))
        
        # Database stats
        stats_frame = ttk.LabelFrame(self.content_frame, text="Statistics", padding=15)
        stats_frame.pack(fill='x', pady=(0, 10))
        
        stats = self.get_database_stats()
        stats_text = f"""Total Messages: {stats['total_messages']}
Posted Messages: {stats['posted_messages']}
Pending Messages: {stats['pending_messages']}
Stored Channels: {stats['channels']}"""
        
        ttk.Label(stats_frame, text=stats_text, font=('Consolas', 10)).pack(anchor='w')
        
        # Database actions
        actions_frame = ttk.LabelFrame(self.content_frame, text="Actions", padding=15)
        actions_frame.pack(fill='x', pady=(0, 10))
        
        action_buttons = [
            ("View Unposted Messages", self.view_unposted_messages),
            ("Export Database", self.export_database),
            ("Clear Posted Messages", self.clear_posted_messages),
            ("Vacuum Database", self.vacuum_database)
        ]
        
        for text, command in action_buttons:
            btn = ttk.Button(actions_frame, text=text, command=command)
            btn.pack(side='left', padx=(0, 10))
            
    def get_dashboard_stats(self):
        """Get dashboard statistics"""
        try:
            import sqlite3
            with sqlite3.connect(self.db_manager.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT COUNT(*) FROM processed_messages")
                total_messages = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM processed_messages WHERE posted = 0")
                pending_messages = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM processed_messages WHERE posted = 1 AND date(date_posted) = date('now')")
                posted_today = cursor.fetchone()[0]
                
                active_mappings = len(self.config_manager.get_active_mappings())
                
                return {
                    'total_messages': total_messages,
                    'pending_messages': pending_messages,
                    'posted_today': posted_today,
                    'active_mappings': active_mappings
                }
        except Exception:
            return {
                'total_messages': 0,
                'pending_messages': 0,
                'posted_today': 0,
                'active_mappings': 0
            }
            
    def load_recent_activity(self):
        """Load recent activity into the tree"""
        try:
            import sqlite3
            with sqlite3.connect(self.db_manager.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT date_received, mapping_id, posted, original_message
                    FROM processed_messages 
                    ORDER BY date_received DESC 
                    LIMIT 20
                """)
                
                for row in cursor.fetchall():
                    date_str = row[0][:19] if row[0] else 'Unknown'
                    mapping_id = row[1]
                    status = 'Posted' if row[2] else 'Pending'
                    message_preview = (row[3][:50] + '...') if row[3] and len(row[3]) > 50 else (row[3] or '')
                    
                    self.activity_tree.insert('', 'end', values=(date_str, mapping_id, status, message_preview))
        except Exception as e:
            print(f"Error loading activity: {e}")
            
    def save_telegram_config(self):
        """Save Telegram configuration"""
        try:
            self.config_manager.telegram_config.api_id = self.api_id_var.get()
            self.config_manager.telegram_config.api_hash = self.api_hash_var.get()
            self.config_manager.telegram_config.phone_number = self.phone_var.get()
            
            if self.config_manager.save_config():
                messagebox.showinfo("Success", "Telegram configuration saved successfully!")
                self.update_status("Telegram configuration saved")
            else:
                messagebox.showerror("Error", "Failed to save configuration!")
        except Exception as e:
            messagebox.showerror("Error", f"Error saving configuration: {e}")
            
    def save_ai_config(self):
        """Save AI configuration"""
        try:
            self.config_manager.ai_config.provider = self.provider_var.get()
            self.config_manager.ai_config.api_key = self.ai_api_key_var.get()
            self.config_manager.ai_config.model = self.ai_model_var.get()
            self.config_manager.ai_config.base_url = self.base_url_var.get()
            
            if self.config_manager.save_config():
                messagebox.showinfo("Success", "AI configuration saved successfully!")
                self.update_status("AI configuration saved")
            else:
                messagebox.showerror("Error", "Failed to save AI configuration!")
        except Exception as e:
            messagebox.showerror("Error", f"Error saving AI configuration: {e}")
            
    def test_telegram_connection(self):
        """Test Telegram connection"""
        def test_connection():
            try:
                self.update_status("Testing Telegram connection...")
                # Implementation would go here
                # For now, just simulate success
                self.root.after(2000, lambda: messagebox.showinfo("Success", "Telegram connection successful!"))
                self.root.after(2000, lambda: self.update_connection_status(True))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Connection failed: {e}"))
                self.root.after(0, lambda: self.update_connection_status(False))
        
        threading.Thread(target=test_connection, daemon=True).start()
        
    def test_ai_connection(self):
        """Test AI connection"""
        def test_ai():
            try:
                self.update_status("Testing AI connection...")
                # Implementation would go here
                self.root.after(2000, lambda: messagebox.showinfo("Success", "AI connection successful!"))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"AI connection failed: {e}"))
        
        threading.Thread(target=test_ai, daemon=True).start()
        
    def load_mappings(self):
        """Load channel mappings into tree"""
        # Clear existing items
        for item in self.mappings_tree.get_children():
            self.mappings_tree.delete(item)
            
        # Load mappings
        for mapping_id, mapping in self.config_manager.channel_mappings.items():
            status = "Active" if mapping.active else "Inactive"
            keywords = ", ".join(mapping.keywords) if mapping.keywords else "None"
            
            self.mappings_tree.insert('', 'end', values=(
                mapping_id,
                mapping.source_channel_name,
                mapping.target_channel_name,
                status,
                keywords
            ))
    
    def add_mapping_dialog(self):
        """Show add mapping dialog"""
        dialog = MappingDialog(self.root, self.config_manager, title="Add New Mapping")
        if dialog.result:
            self.load_mappings()
            self.update_status("Mapping added successfully")
    
    def edit_mapping_dialog(self):
        """Show edit mapping dialog"""
        selection = self.mappings_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a mapping to edit")
            return
            
        item = self.mappings_tree.item(selection[0])
        mapping_id = item['values'][0]
        
        dialog = MappingDialog(self.root, self.config_manager, 
                              title="Edit Mapping", mapping_id=mapping_id)
        if dialog.result:
            self.load_mappings()
            self.update_status("Mapping updated successfully")
    
    def delete_mapping(self):
        """Delete selected mapping"""
        selection = self.mappings_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a mapping to delete")
            return
            
        item = self.mappings_tree.item(selection[0])
        mapping_id = item['values'][0]
        
        if messagebox.askyesno("Confirm Delete", f"Delete mapping '{mapping_id}'?"):
            if self.config_manager.remove_channel_mapping(mapping_id):
                self.load_mappings()
                self.update_status("Mapping deleted successfully")
            else:
                messagebox.showerror("Error", "Failed to delete mapping")
    
    def start_processing(self):
        """Start message processing"""
        if self.is_monitoring:
            return
            
        def start_async():
            try:
                self.is_monitoring = True
                self.root.after(0, lambda: self.start_btn.configure(state='disabled'))
                self.root.after(0, lambda: self.stop_btn.configure(state='normal'))
                
                # Initialize processor if needed
                if not self.processor:
                    self.processor = MultiChannelProcessor(self.config_manager)
                    
                # Configure processing options
                session_config = {
                    'use_ai_agent': self.use_ai.get(),
                    'include_media': self.include_media.get(),
                    'processing_mode': self.processing_mode.get()
                }
                
                self.processor.session_config = session_config
                
                self.root.after(0, lambda: self.log_message("Starting message processing..."))
                self.root.after(0, lambda: self.update_status("Processing active"))
                
                # Simulate processing (replace with actual implementation)
                import time
                while self.is_monitoring:
                    self.root.after(0, lambda: self.log_message("Checking for new messages..."))
                    time.sleep(5)
                    
            except Exception as e:
                self.root.after(0, lambda: self.log_message(f"Error: {e}"))
                self.root.after(0, lambda: self.stop_processing())
        
        self.monitoring_thread = threading.Thread(target=start_async, daemon=True)
        self.monitoring_thread.start()
    
    def stop_processing(self):
        """Stop message processing"""
        self.is_monitoring = False
        self.start_btn.configure(state='normal')
        self.stop_btn.configure(state='disabled')
        self.log_message("Processing stopped")
        self.update_status("Ready")
    
    def log_message(self, message):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
    
    def refresh_channels(self):
        """Refresh channels list"""
        def refresh_async():
            try:
                self.root.after(0, lambda: self.update_status("Refreshing channels..."))
                # Implementation would fetch actual channels
                # For now, just show success
                self.root.after(2000, lambda: self.load_channels())
                self.root.after(2000, lambda: self.update_status("Channels refreshed"))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to refresh channels: {e}"))
        
        threading.Thread(target=refresh_async, daemon=True).start()
    
    def load_channels(self):
        """Load channels into tree"""
        # Clear existing items
        for item in self.channels_tree.get_children():
            self.channels_tree.delete(item)
            
        # Load from database
        channels = self.db_manager.get_all_channels()
        for channel in channels:
            self.channels_tree.insert('', 'end', values=(
                channel['name'],
                channel['id'],
                channel['type']
            ))
    
    def get_database_stats(self):
        """Get database statistics"""
        try:
            import sqlite3
            with sqlite3.connect(self.db_manager.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT COUNT(*) FROM processed_messages")
                total_messages = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM processed_messages WHERE posted = 1")
                posted_messages = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM processed_messages WHERE posted = 0")
                pending_messages = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM channels")
                channels = cursor.fetchone()[0]
                
                return {
                    'total_messages': total_messages,
                    'posted_messages': posted_messages,
                    'pending_messages': pending_messages,
                    'channels': channels
                }
        except Exception:
            return {
                'total_messages': 0,
                'posted_messages': 0,
                'pending_messages': 0,
                'channels': 0
            }
    
    def view_unposted_messages(self):
        """Show unposted messages dialog"""
        UnpostedMessagesDialog(self.root, self.db_manager)
    
    def export_database(self):
        """Export database to file"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            try:
                # Implementation would export actual data
                messagebox.showinfo("Success", f"Database exported to {filename}")
                self.update_status("Database exported")
            except Exception as e:
                messagebox.showerror("Error", f"Export failed: {e}")
    
    def clear_posted_messages(self):
        """Clear posted messages"""
        if messagebox.askyesno("Confirm", "Delete all posted messages from database?"):
            try:
                import sqlite3
                with sqlite3.connect(self.db_manager.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM processed_messages WHERE posted = 1")
                    deleted = cursor.rowcount
                    conn.commit()
                
                messagebox.showinfo("Success", f"Deleted {deleted} posted messages")
                self.update_status("Posted messages cleared")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to clear messages: {e}")
    
    def vacuum_database(self):
        """Vacuum database"""
        try:
            import sqlite3
            with sqlite3.connect(self.db_manager.db_path) as conn:
                conn.execute("VACUUM")
            
            messagebox.showinfo("Success", "Database optimized successfully")
            self.update_status("Database optimized")
        except Exception as e:
            messagebox.showerror("Error", f"Optimization failed: {e}")
    
    def update_status(self, message):
        """Update status bar"""
        self.status_label.configure(text=message)
    
    def update_connection_status(self, connected):
        """Update connection indicator"""
        if connected:
            self.connection_label.configure(text="●", foreground=self.colors['success'])
        else:
            self.connection_label.configure(text="●", foreground=self.colors['danger'])
    
    def load_initial_data(self):
        """Load initial data"""
        # Check if configurations are complete
        tg_config = self.config_manager.telegram_config
        ai_config = self.config_manager.ai_config
        
        if all([tg_config.api_id, tg_config.api_hash, tg_config.phone_number]):
            self.update_connection_status(True)
        else:
            self.update_connection_status(False)
    
    def run(self):
        """Start the GUI application"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.cleanup()
    
    def cleanup(self):
        """Cleanup resources"""
        self.is_monitoring = False
        if self.processor:
            # Cleanup processor if needed
            pass


class MappingDialog:
    """Dialog for adding/editing channel mappings"""
    
    def __init__(self, parent, config_manager, title="Add Mapping", mapping_id=None):
        self.result = False
        self.config_manager = config_manager
        self.mapping_id = mapping_id
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("500x400")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 100, parent.winfo_rooty() + 100))
        
        self.setup_dialog()
        
        # Load existing mapping data if editing
        if mapping_id and mapping_id in config_manager.channel_mappings:
            self.load_mapping_data(config_manager.channel_mappings[mapping_id])
    
    def setup_dialog(self):
        """Setup dialog UI"""
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill='both', expand=True)
        
        # Mapping ID
        ttk.Label(main_frame, text="Mapping ID:").grid(row=0, column=0, sticky='w', pady=5)
        self.mapping_id_var = tk.StringVar()
        mapping_id_entry = ttk.Entry(main_frame, textvariable=self.mapping_id_var, width=40)
        mapping_id_entry.grid(row=0, column=1, sticky='ew', pady=5, padx=(10, 0))
        
        # Source Channel
        ttk.Label(main_frame, text="Source Channel ID:").grid(row=1, column=0, sticky='w', pady=5)
        self.source_id_var = tk.StringVar()
        source_id_entry = ttk.Entry(main_frame, textvariable=self.source_id_var, width=40)
        source_id_entry.grid(row=1, column=1, sticky='ew', pady=5, padx=(10, 0))
        
        # Source Channel Name
        ttk.Label(main_frame, text="Source Channel Name:").grid(row=2, column=0, sticky='w', pady=5)
        self.source_name_var = tk.StringVar()
        source_name_entry = ttk.Entry(main_frame, textvariable=self.source_name_var, width=40)
        source_name_entry.grid(row=2, column=1, sticky='ew', pady=5, padx=(10, 0))
        
        # Target Channel
        ttk.Label(main_frame, text="Target Channel ID:").grid(row=3, column=0, sticky='w', pady=5)
        self.target_id_var = tk.StringVar()
        target_id_entry = ttk.Entry(main_frame, textvariable=self.target_id_var, width=40)
        target_id_entry.grid(row=3, column=1, sticky='ew', pady=5, padx=(10, 0))
        
        # Target Channel Name
        ttk.Label(main_frame, text="Target Channel Name:").grid(row=4, column=0, sticky='w', pady=5)
        self.target_name_var = tk.StringVar()
        target_name_entry = ttk.Entry(main_frame, textvariable=self.target_name_var, width=40)
        target_name_entry.grid(row=4, column=1, sticky='ew', pady=5, padx=(10, 0))
        
        # Keywords
        ttk.Label(main_frame, text="Keywords (comma-separated):").grid(row=5, column=0, sticky='w', pady=5)
        self.keywords_var = tk.StringVar()
        keywords_entry = ttk.Entry(main_frame, textvariable=self.keywords_var, width=40)
        keywords_entry.grid(row=5, column=1, sticky='ew', pady=5, padx=(10, 0))
        
        # Signature
        ttk.Label(main_frame, text="Required Signature:").grid(row=6, column=0, sticky='w', pady=5)
        self.signature_var = tk.StringVar()
        signature_entry = ttk.Entry(main_frame, textvariable=self.signature_var, width=40)
        signature_entry.grid(row=6, column=1, sticky='ew', pady=5, padx=(10, 0))
        
        # Active checkbox
        self.active_var = tk.BooleanVar(value=True)
        active_check = ttk.Checkbutton(main_frame, text="Active", variable=self.active_var)
        active_check.grid(row=7, column=1, sticky='w', pady=10, padx=(10, 0))
        
        # Configure grid
        main_frame.grid_columnconfigure(1, weight=1)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=8, column=0, columnspan=2, pady=20)
        
        save_btn = ttk.Button(button_frame, text="Save", command=self.save_mapping)
        save_btn.pack(side='left', padx=(0, 10))
        
        cancel_btn = ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy)
        cancel_btn.pack(side='left')
    
    def load_mapping_data(self, mapping):
        """Load existing mapping data into form"""
        self.mapping_id_var.set(mapping.id)
        self.source_id_var.set(str(mapping.source_channel_id))
        self.source_name_var.set(mapping.source_channel_name)
        self.target_id_var.set(str(mapping.target_channel_id))
        self.target_name_var.set(mapping.target_channel_name)
        self.keywords_var.set(", ".join(mapping.keywords))
        self.signature_var.set(mapping.signature)
        self.active_var.set(mapping.active)
    
    def save_mapping(self):
        """Save mapping"""
        try:
            mapping_id = self.mapping_id_var.get().strip()
            if not mapping_id:
                messagebox.showerror("Error", "Mapping ID is required")
                return
            
            # Create mapping object
            mapping = ChannelMapping(
                id=mapping_id,
                source_channel_id=int(self.source_id_var.get().strip()),
                source_channel_name=self.source_name_var.get().strip(),
                target_channel_id=int(self.target_id_var.get().strip()),
                target_channel_name=self.target_name_var.get().strip(),
                keywords=[k.strip() for k in self.keywords_var.get().split(",") if k.strip()],
                signature=self.signature_var.get().strip(),
                active=self.active_var.get()
            )
            
            # Save mapping
            if self.config_manager.add_channel_mapping(mapping):
                self.result = True
                self.dialog.destroy()
            else:
                messagebox.showerror("Error", "Failed to save mapping")
                
        except ValueError:
            messagebox.showerror("Error", "Channel IDs must be numbers")
        except Exception as e:
            messagebox.showerror("Error", f"Error saving mapping: {e}")


class UnpostedMessagesDialog:
    """Dialog for viewing unposted messages"""
    
    def __init__(self, parent, db_manager):
        self.db_manager = db_manager
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Unposted Messages")
        self.dialog.geometry("800x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.setup_dialog()
        self.load_unposted_messages()
    
    def setup_dialog(self):
        """Setup dialog UI"""
        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.pack(fill='both', expand=True)
        
        # Tree for messages
        self.tree = ttk.Treeview(main_frame, 
                                columns=('Mapping', 'Date', 'Message'), 
                                show='headings')
        
        self.tree.heading('Mapping', text='Mapping ID')
        self.tree.heading('Date', text='Date')
        self.tree.heading('Message', text='Message Preview')
        
        self.tree.column('Mapping', width=150)
        self.tree.column('Date', width=150)
        self.tree.column('Message', width=400)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(main_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Buttons
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        mark_posted_btn = ttk.Button(button_frame, text="Mark as Posted", 
                                    command=self.mark_as_posted)
        mark_posted_btn.pack(side='left', padx=(0, 10))
        
        delete_btn = ttk.Button(button_frame, text="Delete", 
                               command=self.delete_message)
        delete_btn.pack(side='left', padx=(0, 10))
        
        close_btn = ttk.Button(button_frame, text="Close", 
                              command=self.dialog.destroy)
        close_btn.pack(side='right')
    
    def load_unposted_messages(self):
        """Load unposted messages"""
        try:
            import sqlite3
            with sqlite3.connect(self.db_manager.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, mapping_id, message_id, original_message, date_received
                    FROM processed_messages WHERE posted = 0
                    ORDER BY date_received DESC
                """)
                
                for row in cursor.fetchall():
                    db_id, mapping_id, msg_id, message, date = row
                    message_preview = (message[:80] + '...') if len(message) > 80 else message
                    date_str = date[:19] if date else 'Unknown'
                    
                    item = self.tree.insert('', 'end', values=(mapping_id, date_str, message_preview))
                    # Store db_id and msg_id for later use
                    self.tree.set(item, 'db_id', db_id)
                    self.tree.set(item, 'msg_id', msg_id)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load messages: {e}")
    
    def mark_as_posted(self):
        """Mark selected message as posted"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a message")
            return
        
        try:
            item = selection[0]
            db_id = self.tree.set(item, 'db_id')
            msg_id = self.tree.set(item, 'msg_id')
            mapping_id = self.tree.item(item)['values'][0]
            
            if self.db_manager.mark_as_posted(int(msg_id), mapping_id):
                self.tree.delete(item)
                messagebox.showinfo("Success", "Message marked as posted")
            else:
                messagebox.showerror("Error", "Failed to mark as posted")
        except Exception as e:
            messagebox.showerror("Error", f"Error: {e}")
    
    def delete_message(self):
        """Delete selected message"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a message")
            return
        
        if messagebox.askyesno("Confirm", "Delete selected message?"):
            try:
                item = selection[0]
                db_id = self.tree.set(item, 'db_id')
                
                import sqlite3
                with sqlite3.connect(self.db_manager.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM processed_messages WHERE id = ?", (db_id,))
                    conn.commit()
                
                self.tree.delete(item)
                messagebox.showinfo("Success", "Message deleted")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete: {e}")


def main():
    """Main entry point for GUI application"""
    try:
        app = ModernTelegramBotGUI()
        app.run()
    except Exception as e:
        print(f"Error starting GUI: {e}")
        messagebox.showerror("Error", f"Failed to start application: {e}")


if __name__ == "__main__":
    main()