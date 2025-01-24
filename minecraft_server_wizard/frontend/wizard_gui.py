import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import sys
import threading
import queue
import os
import time
import subprocess
sys.path.append('..')
from backend.server_manager import MinecraftServerManager
from backend.dns_manager import DNSManager

class ServerWizard:
    def __init__(self, base_dir):
        self.root = tk.Tk()
        self.root.title("Minecraft Sunucu Sihirbazı")
        self.root.geometry("900x600")
        
        self.base_dir = base_dir
        self.server_manager = MinecraftServerManager(base_dir, self.log_to_app_console)
        self.output_queue = queue.Queue()
        self.server_process = None
        self.dns_manager = DNSManager(base_dir, self.server_manager)
        
        # Uygulama kapatılırken temizlik yap
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.setup_gui()  # Direkt GUI'yi kur, Ngrok kontrolünü DNS ayarlarına taşıdık
    
    def log_to_app_console(self, message, level="INFO", show_progress=False, progress_msg=""):
        """Uygulama konsoluna detaylı log yazar"""
        def _write():
            timestamp = time.strftime("%H:%M:%S")
            self.app_console.config(state='normal')
            
            # Mesaj renklerini ayarla
            if level == "ERROR":
                tag = "error"
                self.app_console.tag_config(tag, foreground="red")
            elif level == "SUCCESS":
                tag = "success"
                self.app_console.tag_config(tag, foreground="green")
            elif level == "WARNING":
                tag = "warning"
                self.app_console.tag_config(tag, foreground="orange")
            else:
                tag = "info"
                self.app_console.tag_config(tag, foreground="blue")
            
            # Mesajı ekle
            log_line = f"[{timestamp}] [{level}] {message}\n"
            self.app_console.insert(tk.END, log_line, tag)
            self.app_console.see(tk.END)
            self.app_console.config(state='disabled')
            
            # Progress bar'ı güncelle
            if show_progress:
                self.show_progress(True, progress_msg or message)
            else:
                self.show_progress(False)
        
        # Ana thread'de çalıştır
        if threading.current_thread() is threading.main_thread():
            _write()
        else:
            self.root.after(0, _write)
    
    def setup_gui(self):
        # Ana frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Sol panel (Ayarlar ve Uygulama Konsolu)
        left_panel = ttk.Frame(main_frame)
        left_panel.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        
        # Ayarlar frame
        settings_frame = ttk.LabelFrame(left_panel, text="Sunucu Ayarları", padding="5")
        settings_frame.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # Sunucu Seçimi Frame
        self.server_select_frame = ttk.LabelFrame(settings_frame, text="Sunucu Yönetimi", padding="10")
        self.server_select_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=2)
        
        # Üst bilgi etiketi
        info_text = "Minecraft sunucularınızı buradan yönetebilirsiniz."
        ttk.Label(self.server_select_frame, text=info_text, 
                 wraplength=400, justify="left").grid(row=0, column=0, columnspan=4, sticky=tk.W, pady=(0,10))
        
        # Sunucu listesi başlığı
        ttk.Label(self.server_select_frame, text="Kayıtlı Sunucular:", 
                 font=("", 10, "bold")).grid(row=1, column=0, columnspan=4, sticky=tk.W, pady=(0,5))
        
        # Sunucu listesi
        self.server_list = ttk.Treeview(self.server_select_frame, 
                                       columns=("version", "last_played"), 
                                       height=6,
                                       selectmode="browse")
        self.server_list.grid(row=2, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0,10))
        
        # Sütun başlıkları
        self.server_list.heading("#0", text="Sunucu Adı", anchor=tk.W)
        self.server_list.heading("version", text="Sürüm", anchor=tk.W)
        self.server_list.heading("last_played", text="Son Oynama", anchor=tk.W)
        
        # Sütun genişlikleri
        self.server_list.column("#0", width=200, minwidth=150)
        self.server_list.column("version", width=100, minwidth=80)
        self.server_list.column("last_played", width=150, minwidth=120)
        
        # Scrollbar ekle
        scrollbar = ttk.Scrollbar(self.server_select_frame, orient="vertical", command=self.server_list.yview)
        scrollbar.grid(row=2, column=4, sticky=(tk.N, tk.S))
        self.server_list.configure(yscrollcommand=scrollbar.set)
        
        # Buton çerçevesi
        button_frame = ttk.Frame(self.server_select_frame)
        button_frame.grid(row=3, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(10,0))
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        button_frame.columnconfigure(2, weight=1)
        button_frame.columnconfigure(3, weight=1)
        
        # Butonlar
        create_btn = ttk.Button(button_frame, text="✨ Yeni Sunucu", 
                               command=self.show_create_server_frame, width=20)
        create_btn.grid(row=0, column=0, padx=5)
        
        start_btn = ttk.Button(button_frame, text="▶️ Sunucuyu Başlat",
                              command=self.load_selected_server, width=20)
        start_btn.grid(row=0, column=1, padx=5)
        
        self.stop_button = ttk.Button(button_frame, text="⏹️ Sunucuyu Durdur", 
                                     command=self.stop_server, state='disabled', width=20)
        self.stop_button.grid(row=0, column=2, padx=5)
        
        settings_btn = ttk.Button(button_frame, text="⚙️ Ayarlar", 
                                 command=self.show_dns_config, width=20)
        settings_btn.grid(row=0, column=3, padx=5)
        
        # Durum çerçevesi
        status_frame = ttk.Frame(self.server_select_frame)
        status_frame.grid(row=4, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(10,0))
        
        # Durum etiketi
        self.status_label = ttk.Label(status_frame, text="Hazır", foreground="green")
        self.status_label.pack(side=tk.LEFT)
        
        # Sunucu listesini güncelle
        self.update_server_list()
        
        # Yeni Sunucu Frame
        self.create_server_frame = ttk.Frame(settings_frame)
        self.create_server_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=2)
        self.create_server_frame.grid_remove()  # Başlangıçta gizle
        
        # Yeni Sunucu Frame içeriği
        # Temel Ayarlar Frame
        basic_frame = ttk.LabelFrame(self.create_server_frame, text="Temel Ayarlar", padding="5")
        basic_frame.pack(fill=tk.X, pady=5)
        
        # Grid için frame
        basic_grid = ttk.Frame(basic_frame)
        basic_grid.pack(fill=tk.X, padx=5)
        
        # Sunucu Adı
        ttk.Label(basic_grid, text="Sunucu Adı:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.name_entry = ttk.Entry(basic_grid, width=40)
        self.name_entry.grid(row=0, column=1, sticky=tk.W, pady=2)
        self.name_entry.insert(0, "Yeni Minecraft Sunucum")
        
        # Sunucu Tipi
        ttk.Label(basic_grid, text="Sunucu Tipi:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.server_type = ttk.Combobox(basic_grid, values=["Vanilla", "Fabric"], width=37)
        self.server_type.grid(row=1, column=1, sticky=tk.W, pady=2)
        self.server_type.set("Vanilla")
        
        # Minecraft Sürümü
        ttk.Label(basic_grid, text="Minecraft Sürümü:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.version_combo = ttk.Combobox(basic_grid, values=list(self.server_manager.versions.keys()), width=37)
        self.version_combo.grid(row=2, column=1, sticky=tk.W, pady=2)
        self.version_combo.set("1.21.4")
        
        # Fabric Frame
        self.fabric_frame = ttk.Frame(basic_grid)
        self.fabric_frame.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=2)
        
        ttk.Label(self.fabric_frame, text="Fabric Sürümü:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.fabric_version = ttk.Combobox(self.fabric_frame, values=self.server_manager.fabric_versions, width=37)
        self.fabric_version.grid(row=0, column=1, sticky=tk.W, pady=2)
        self.fabric_version.set("0.16.10")
        self.fabric_frame.grid_remove()  # Başlangıçta gizli
        
        def on_type_change(event):
            if self.server_type.get() == "Fabric":
                self.fabric_frame.grid()
            else:
                self.fabric_frame.grid_remove()
        
        self.server_type.bind('<<ComboboxSelected>>', on_type_change)
        
        # Sistem Ayarları Frame
        system_frame = ttk.LabelFrame(self.create_server_frame, text="Sistem Ayarları", padding="5")
        system_frame.pack(fill=tk.X, pady=5)
        
        system_grid = ttk.Frame(system_frame)
        system_grid.pack(fill=tk.X, padx=5)
        
        # RAM
        ttk.Label(system_grid, text="RAM (GB):").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.ram_spinbox = ttk.Spinbox(system_grid, from_=1, to=32, width=10)
        self.ram_spinbox.grid(row=0, column=1, sticky=tk.W, pady=2)
        self.ram_spinbox.set("2")
        
        # Port
        ttk.Label(system_grid, text="Port:").grid(row=0, column=2, sticky=tk.W, pady=2, padx=(20,0))
        self.port_spinbox = ttk.Spinbox(system_grid, from_=1024, to=65535, width=10)
        self.port_spinbox.grid(row=0, column=3, sticky=tk.W, pady=2)
        self.port_spinbox.set("25565")
        
        # Oyun Ayarları Frame
        game_frame = ttk.LabelFrame(self.create_server_frame, text="Oyun Ayarları", padding="5")
        game_frame.pack(fill=tk.X, pady=5)
        
        game_grid = ttk.Frame(game_frame)
        game_grid.pack(fill=tk.X, padx=5)
        
        # Sol Kolon
        # Oyun Modu
        ttk.Label(game_grid, text="Oyun Modu:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.gamemode_combo = ttk.Combobox(game_grid, values=["survival", "creative", "adventure"], width=15)
        self.gamemode_combo.grid(row=0, column=1, sticky=tk.W, pady=2)
        self.gamemode_combo.set("survival")
        
        # Zorluk
        ttk.Label(game_grid, text="Zorluk:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.difficulty_combo = ttk.Combobox(game_grid, values=["peaceful", "easy", "normal", "hard"], width=15)
        self.difficulty_combo.grid(row=1, column=1, sticky=tk.W, pady=2)
        self.difficulty_combo.set("normal")
        
        # Sağ Kolon
        # PvP
        ttk.Label(game_grid, text="PvP:").grid(row=0, column=2, sticky=tk.W, pady=2, padx=(20,0))
        self.pvp_combo = ttk.Combobox(game_grid, values=["true", "false"], width=15)
        self.pvp_combo.grid(row=0, column=3, sticky=tk.W, pady=2)
        self.pvp_combo.set("true")
        
        # Online Mode
        ttk.Label(game_grid, text="Online Mode:").grid(row=1, column=2, sticky=tk.W, pady=2, padx=(20,0))
        self.online_mode_combo = ttk.Combobox(game_grid, values=["true", "false"], width=15)
        self.online_mode_combo.grid(row=1, column=3, sticky=tk.W, pady=2)
        self.online_mode_combo.set("true")
        
        # Dünya Ayarları Frame
        world_frame = ttk.LabelFrame(self.create_server_frame, text="Dünya Ayarları", padding="5")
        world_frame.pack(fill=tk.X, pady=5)
        
        world_grid = ttk.Frame(world_frame)
        world_grid.pack(fill=tk.X, padx=5)
        
        # Sol Kolon
        # Görüş Mesafesi
        ttk.Label(world_grid, text="Görüş Mesafesi:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.view_distance = ttk.Spinbox(world_grid, from_=3, to=32, width=10)
        self.view_distance.grid(row=0, column=1, sticky=tk.W, pady=2)
        self.view_distance.set("10")
        
        # Spawn Protection
        ttk.Label(world_grid, text="Spawn Koruması:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.spawn_protection = ttk.Spinbox(world_grid, from_=0, to=100, width=10)
        self.spawn_protection.grid(row=1, column=1, sticky=tk.W, pady=2)
        self.spawn_protection.set("16")
        
        # Sol Kolon - Mevcut ayarlardan sonra
        # Allow Nether
        ttk.Label(world_grid, text="Nether:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.allow_nether = ttk.Combobox(world_grid, values=["true", "false"], width=10)
        self.allow_nether.grid(row=2, column=1, sticky=tk.W, pady=2)
        self.allow_nether.set("true")
        
        # Allow End
        ttk.Label(world_grid, text="The End:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.allow_end = ttk.Combobox(world_grid, values=["true", "false"], width=10)
        self.allow_end.grid(row=3, column=1, sticky=tk.W, pady=2)
        self.allow_end.set("true")
        
        # Sağ Kolon
        # Max Players
        ttk.Label(world_grid, text="Max Oyuncu:").grid(row=0, column=2, sticky=tk.W, pady=2, padx=(20,0))
        self.max_players_spin = ttk.Spinbox(world_grid, from_=1, to=100, width=10)
        self.max_players_spin.grid(row=0, column=3, sticky=tk.W, pady=2)
        self.max_players_spin.set("20")
        
        # Command Blocks
        ttk.Label(world_grid, text="Command Blocks:").grid(row=1, column=2, sticky=tk.W, pady=2, padx=(20,0))
        self.command_blocks = ttk.Combobox(world_grid, values=["true", "false"], width=7)
        self.command_blocks.grid(row=1, column=3, sticky=tk.W, pady=2)
        self.command_blocks.set("true")
        
        # Sağ Kolon - Mevcut ayarlardan sonra
        # Hardcore Mode
        ttk.Label(world_grid, text="Hardcore:").grid(row=2, column=2, sticky=tk.W, pady=2, padx=(20,0))
        self.hardcore = ttk.Combobox(world_grid, values=["true", "false"], width=7)
        self.hardcore.grid(row=2, column=3, sticky=tk.W, pady=2)
        self.hardcore.set("false")
        
        # Force Gamemode
        ttk.Label(world_grid, text="Force Gamemode:").grid(row=3, column=2, sticky=tk.W, pady=2, padx=(20,0))
        self.force_gamemode = ttk.Combobox(world_grid, values=["true", "false"], width=7)
        self.force_gamemode.grid(row=3, column=3, sticky=tk.W, pady=2)
        self.force_gamemode.set("false")
        
        # Yeni bir frame ekleyelim - Oyuncu Ayarları
        player_frame = ttk.LabelFrame(self.create_server_frame, text="Oyuncu Ayarları", padding="5")
        player_frame.pack(fill=tk.X, pady=5)

        player_grid = ttk.Frame(player_frame)
        player_grid.pack(fill=tk.X, padx=5)

        # Sol Kolon
        # Player Idle Timeout
        ttk.Label(player_grid, text="AFK Timeout (dk):").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.player_idle_timeout = ttk.Spinbox(player_grid, from_=0, to=120, width=10)
        self.player_idle_timeout.grid(row=0, column=1, sticky=tk.W, pady=2)
        self.player_idle_timeout.set("0")

        # Max World Size
        ttk.Label(player_grid, text="Max Dünya Boyutu:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.max_world_size = ttk.Spinbox(player_grid, from_=1000, to=29999984, width=10)
        self.max_world_size.grid(row=1, column=1, sticky=tk.W, pady=2)
        self.max_world_size.set("29999984")

        # Sağ Kolon
        # Allow Flight
        ttk.Label(player_grid, text="Uçuş İzni:").grid(row=0, column=2, sticky=tk.W, pady=2, padx=(20,0))
        self.allow_flight = ttk.Combobox(player_grid, values=["true", "false"], width=7)
        self.allow_flight.grid(row=0, column=3, sticky=tk.W, pady=2)
        self.allow_flight.set("false")

        # White List
        ttk.Label(player_grid, text="White List:").grid(row=1, column=2, sticky=tk.W, pady=2, padx=(20,0))
        self.white_list = ttk.Combobox(player_grid, values=["true", "false"], width=7)
        self.white_list.grid(row=1, column=3, sticky=tk.W, pady=2)
        self.white_list.set("false")
        
        # Butonlar
        button_frame = ttk.Frame(self.create_server_frame)
        button_frame.pack(fill=tk.X, pady=10)
        ttk.Button(button_frame, text="Oluştur", 
                   command=self.create_server).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="İptal", 
                   command=self.show_server_list_frame).pack(side=tk.LEFT, padx=5)
        
        # Uygulama konsolu
        app_console_frame = ttk.LabelFrame(left_panel, text="Uygulama Konsolu", padding="5")
        app_console_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        self.app_console = scrolledtext.ScrolledText(app_console_frame, wrap=tk.WORD, width=40, height=10)
        self.app_console.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.app_console.config(state='disabled')
        
        # Progress bar
        self.progress_frame = ttk.Frame(left_panel)
        self.progress_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=5)
        
        self.progress_label = ttk.Label(self.progress_frame, text="")
        self.progress_label.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        self.progress_bar = ttk.Progressbar(self.progress_frame, mode='indeterminate')
        self.progress_bar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        self.progress_bar.grid_remove()  # Başlangıçta gizle
        
        # Sağ panel (Sunucu Konsolu)
        self.right_panel = ttk.Frame(main_frame)
        self.right_panel.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Sunucu konsolu
        server_console_frame = ttk.LabelFrame(self.right_panel, text="Sunucu Konsolu", padding="5")
        server_console_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.server_console = scrolledtext.ScrolledText(server_console_frame, wrap=tk.WORD, width=40, height=20)
        self.server_console.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.server_console.config(state='disabled')
        
        # DNS Ayarları Frame'i ekle (başlangıçta gizli)
        self.dns_config_frame = ttk.Frame(settings_frame)
        self.dns_config_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=2)
        self.dns_config_frame.grid_remove()
        
        # Çalışma modu seçimi
        mode_frame = ttk.LabelFrame(self.dns_config_frame, text="Çalışma Modu", padding="5")
        mode_frame.pack(fill=tk.X, pady=5)
        
        self.operation_mode = ttk.Combobox(mode_frame, values=["Değişken IP Kullan", "Cloudflare Domain Kullan"])
        self.operation_mode.pack(fill=tk.X, pady=2)
        self.operation_mode.bind('<<ComboboxSelected>>', self.on_dns_mode_change)
        
        # Cloudflare ayarları
        self.cf_frame = ttk.LabelFrame(self.dns_config_frame, text="Cloudflare Ayarları", padding="5")
        self.cf_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(self.cf_frame, text="Domain Adı:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.domain_name = ttk.Entry(self.cf_frame, width=40)
        self.domain_name.grid(row=0, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(self.cf_frame, text="API Token:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.cf_token = ttk.Entry(self.cf_frame, width=40, show="•")
        self.cf_token.grid(row=1, column=1, sticky=tk.W, pady=2)
        
        # Token göster/gizle butonu
        self.cf_token_btn = ttk.Button(self.cf_frame, text="👁", width=3,
                                      command=lambda: self.toggle_token_visibility(self.cf_token))
        self.cf_token_btn.grid(row=1, column=2, padx=5)
        
        # Zone ID
        ttk.Label(self.cf_frame, text="Zone ID:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.zone_id = ttk.Entry(self.cf_frame, width=40, show="•")
        self.zone_id.grid(row=2, column=1, sticky=tk.W, pady=2)

        # Zone ID göster/gizle butonu
        self.zone_id_btn = ttk.Button(self.cf_frame, text="👁", width=3,
                                     command=lambda: self.toggle_token_visibility(self.zone_id))
        self.zone_id_btn.grid(row=2, column=2, padx=5)

        # DNS Record ID
        ttk.Label(self.cf_frame, text="DNS Record ID:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.record_id = ttk.Entry(self.cf_frame, width=40, show="•")
        self.record_id.grid(row=3, column=1, sticky=tk.W, pady=2)

        # Record ID göster/gizle butonu
        self.record_id_btn = ttk.Button(self.cf_frame, text="👁", width=3,
                                       command=lambda: self.toggle_token_visibility(self.record_id))
        self.record_id_btn.grid(row=3, column=2, padx=5)

        # Subdomain
        ttk.Label(self.cf_frame, text="Subdomain:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.record_name = ttk.Entry(self.cf_frame, width=40)
        self.record_name.grid(row=4, column=1, sticky=tk.W, pady=2)

        # Subdomain için yardım etiketi
        ttk.Label(self.cf_frame, text="Örnek: minecraft").grid(row=4, column=2, sticky=tk.W, padx=5)

        # Ngrok ayarları
        ngrok_frame = ttk.LabelFrame(self.dns_config_frame, text="Ngrok Ayarları", padding="5")
        ngrok_frame.pack(fill=tk.X, pady=5)

        ttk.Label(ngrok_frame, text="Auth Token:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.ngrok_token = ttk.Entry(ngrok_frame, width=40, show="•")
        self.ngrok_token.grid(row=0, column=1, sticky=tk.W, pady=2)

        # Ngrok token göster/gizle butonu
        self.ngrok_token_btn = ttk.Button(ngrok_frame, text="👁", width=3,
                                         command=lambda: self.toggle_token_visibility(self.ngrok_token))
        self.ngrok_token_btn.grid(row=0, column=2, padx=5)

        # Ngrok token yardım butonu
        def open_ngrok_site():
            import webbrowser
            webbrowser.open("https://dashboard.ngrok.com/get-started/your-authtoken")

        ttk.Button(ngrok_frame, text="Token Al", 
                  command=open_ngrok_site).grid(row=0, column=3, padx=5)

        # DNS Ayarları butonları
        dns_button_frame = ttk.Frame(self.dns_config_frame)
        dns_button_frame.pack(fill=tk.X, pady=10)
        ttk.Button(dns_button_frame, text="Kaydet", 
                   command=self.save_dns_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(dns_button_frame, text="Geri", 
                   command=self.show_server_list_frame).pack(side=tk.LEFT, padx=5)
        
        # Grid yapılandırması
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)
        left_panel.columnconfigure(0, weight=1)
        left_panel.rowconfigure(1, weight=1)
        app_console_frame.columnconfigure(0, weight=1)
        app_console_frame.rowconfigure(0, weight=1)
        server_console_frame.columnconfigure(0, weight=1)
        server_console_frame.rowconfigure(0, weight=1)
    
    def update_console(self):
        """Konsol çıktısını günceller"""
        try:
            while True:
                line = self.output_queue.get_nowait()
                self.root.after(0, lambda l=line: [
                    self.server_console.config(state='normal'),
                    self.server_console.insert(tk.END, l),
                    self.server_console.see(tk.END),
                    self.server_console.config(state='disabled')
                ])
        except queue.Empty:
            if self.server_process and self.server_process.poll() is None:
                self.root.after(100, self.update_console)
    
    def read_output(self, process):
        """Sunucu çıktısını okur ve kuyruğa ekler"""
        for line in iter(process.stdout.readline, ''):
            self.output_queue.put(line)
        process.stdout.close()
    
    def show_dns_config(self):
        """DNS ayarları frame'ini gösterir"""
        self.server_select_frame.grid_remove()
        self.create_server_frame.grid_remove()
        self.dns_config_frame.grid()
        
        # Konsolları ve çerçevelerini gizle
        self.app_console.master.master.grid_remove()
        self.server_console.master.master.grid_remove()
        self.progress_frame.grid_remove()
        self.right_panel.grid_remove()
        
        # Kayıtlı değerleri yükle
        self.load_dns_config()
    
    def load_dns_config(self):
        """Kayıtlı DNS ayarlarını form alanlarına yükler"""
        def set_masked_value(entry_widget, value):
            if value:
                entry_widget.delete(0, tk.END)
                entry_widget.insert(0, value)
                entry_widget.configure(show="•")
        
        if self.dns_manager.domain_name:
            self.domain_name.delete(0, tk.END)
            self.domain_name.insert(0, self.dns_manager.domain_name)
        if self.dns_manager.cloudflare_token:
            set_masked_value(self.cf_token, self.dns_manager.cloudflare_token)
        if self.dns_manager.zone_id:
            set_masked_value(self.zone_id, self.dns_manager.zone_id)
        if self.dns_manager.dns_record_id:
            set_masked_value(self.record_id, self.dns_manager.dns_record_id)
        if self.dns_manager.dns_record_name:
            # Record name'den subdomain'i ayıkla
            full_record = self.dns_manager.dns_record_name
            subdomain = full_record.replace("_minecraft._tcp.", "")
            self.record_name.delete(0, tk.END)
            self.record_name.insert(0, subdomain)
        if self.dns_manager.ngrok_token:
            set_masked_value(self.ngrok_token, self.dns_manager.ngrok_token)
        
        mode = "Cloudflare Domain Kullan" if self.dns_manager.operation_mode == "cloudflare" else "Değişken IP Kullan"
        self.operation_mode.set(mode)
        self.on_dns_mode_change(None)
    
    def on_dns_mode_change(self, event):
        """DNS çalışma modunu değiştirir"""
        if self.operation_mode.get() == "Cloudflare Domain Kullan":
            self.cf_frame.pack(fill=tk.X, pady=5)
        else:
            self.cf_frame.pack_forget()
    
    def save_dns_config(self):
        """DNS ayarlarını kaydeder"""
        try:
            # Ngrok token'ı yapılandır
            ngrok_token = self.ngrok_token.get().strip()
            if ngrok_token:
                success, message = self.dns_manager.server_manager._setup_ngrok_auth(ngrok_token)
                if not success:
                    raise Exception(f"Ngrok token hatası: {message}")
            
            # Operation mode'u belirle
            operation_mode = "cloudflare" if self.operation_mode.get() == "Cloudflare Domain Kullan" else "ngrok"
            
            # Cloudflare bilgilerini sadece Cloudflare modu seçiliyse güncelle
            if operation_mode == "cloudflare":
                cf_token = self.cf_token.get().strip()
                zone_id = self.zone_id.get().strip()
                record_id = self.record_id.get().strip()
                domain_name = self.domain_name.get().strip()
                
                # Cloudflare ayarlarını kontrol et
                if not all([cf_token, zone_id, record_id, domain_name]):
                    raise Exception("Cloudflare modu için tüm alanlar doldurulmalıdır")
            else:
                # Ngrok modunda mevcut Cloudflare ayarlarını koru
                cf_token = self.dns_manager.cloudflare_token
                zone_id = self.dns_manager.zone_id
                record_id = self.dns_manager.dns_record_id
                domain_name = self.dns_manager.domain_name
            
            # Subdomain'i record_name formatına çevir
            subdomain = self.record_name.get().strip()
            record_name = f"_minecraft._tcp.{subdomain}"
            
            self.dns_manager.setup_credentials(
                cf_token,
                zone_id,
                record_id,
                record_name,
                domain_name,
                ngrok_token,
                operation_mode
            )
            
            self.show_server_list_frame()
            messagebox.showinfo("Başarılı", "Yapılandırma kaydedildi")
            
        except Exception as e:
            messagebox.showerror("Hata", f"Yapılandırma kaydedilemedi: {str(e)}")
    
    def show_server_list_frame(self):
        """Ana sunucu listesi frame'ini gösterir"""
        self.create_server_frame.grid_remove()
        self.dns_config_frame.grid_remove()
        self.server_select_frame.grid()
        
        # Konsolları ve çerçevelerini tekrar göster
        self.app_console.master.master.grid()
        self.server_console.master.master.grid()
        self.progress_frame.grid()
        self.right_panel.grid()
        
        self.update_server_list()

    def create_server(self):
        """Yeni sunucu oluşturur"""
        try:
            name = self.name_entry.get().strip()
            ram = int(self.ram_spinbox.get())  # ram_scale yerine ram_spinbox kullan
            port = int(self.port_spinbox.get())
            gamemode = self.gamemode_combo.get().lower()
            version = self.version_combo.get()
            s_type = self.server_type.get().lower()
            fab_version = self.fabric_version.get() if s_type == "fabric" else None
            
            if not name:
                raise ValueError("Sunucu adı boş olamaz")
            
            # Server properties için ayarları topla
            properties = {
                "difficulty": self.difficulty_combo.get(),
                "pvp": self.pvp_combo.get(),
                "online-mode": self.online_mode_combo.get(),
                "max-players": self.max_players_spin.get(),
                "motd": name,
                "view-distance": self.view_distance.get(),
                "spawn-protection": self.spawn_protection.get(),
                "enable-command-block": self.command_blocks.get(),
                "allow-nether": self.allow_nether.get(),
                "allow-end": self.allow_end.get(),
                "hardcore": self.hardcore.get(),
                "force-gamemode": self.force_gamemode.get(),
                "player-idle-timeout": self.player_idle_timeout.get(),
                "max-world-size": self.max_world_size.get(),
                "allow-flight": self.allow_flight.get(),
                "white-list": self.white_list.get()
            }
            
            success = self.server_manager.initialize_server(
                name, ram, port, gamemode, version, 
                server_type=s_type,
                fabric_version=fab_version,
                properties=properties
            )
            
            if success:
                self.show_server_list_frame()
                self.update_status("Sunucu başarıyla oluşturuldu!", "green")
            else:
                self.update_status("Sunucu oluşturulamadı!", "red")
                
        except Exception as e:
            self.update_status(f"Hata: {str(e)}", "red")

    def load_selected_server(self):
        """Seçili sunucuyu yükler ve başlatır"""
        # Eğer zaten bir sunucu çalışıyorsa engelle
        if self.server_process and self.server_process.poll() is None:
            messagebox.showwarning("Uyarı", "Zaten bir sunucu çalışıyor! Önce çalışan sunucuyu durdurun.")
            return
        
        selected = self.server_list.selection()
        if not selected:
            messagebox.showwarning("Uyarı", "Lütfen bir sunucu seçin")
            return
        
        server_path = self.server_list.item(selected[0])['tags'][0]
        if self.server_manager.load_server(server_path):
            # Sunucuyu başlat
            self.start_server()
        else:
            messagebox.showerror("Hata", "Sunucu yüklenemedi")

    def start_server(self):
        """Var olan bir sunucuyu başlatır"""
        # Eğer zaten bir sunucu çalışıyorsa engelle
        if self.server_process and self.server_process.poll() is None:
            messagebox.showwarning("Uyarı", "Zaten bir sunucu çalışıyor! Önce çalışan sunucuyu durdurun.")
            return

        def _start():
            try:
                # GUI güncellemelerini yap
                self.root.after(0, lambda: [
                    self.stop_button.config(state='normal'),
                    self.server_console.config(state='normal'),
                    self.server_console.delete(1.0, tk.END),
                    self.server_console.insert(tk.END, "Sunucu başlatılıyor...\n"),
                    self.server_console.config(state='disabled')
                ])
                
                # Log mesajları
                self.log_to_app_console("Sunucu başlatma işlemi başladı", "INFO", True, "Sunucu başlatılıyor...")
                self.log_to_app_console(f"Sunucu Adı: {self.server_manager.config['server_name']}", "INFO")
                self.log_to_app_console(f"RAM: {self.server_manager.config['ram_allocation']}GB", "INFO")
                self.log_to_app_console(f"Port: {self.server_manager.config['server_port']}", "INFO")
                self.log_to_app_console(f"Oyun Modu: {self.server_manager.config['gamemode']}", "INFO")
                
                # Sunucuyu başlat
                success, result = self.server_manager.start_server()
                
                if success:
                    self.server_process = result
                    threading.Thread(target=self.read_output, args=(result,), daemon=True).start()
                    self.update_console()
                    
                    self.log_to_app_console("Sunucu başarıyla başlatıldı", "SUCCESS")
                    
                    # DNS güncelleme
                    self.log_to_app_console("DNS kayıtları güncelleniyor...", "INFO", True, "DNS güncelleniyor...")
                    dns_success, dns_message = self.dns_manager.update_all()
                    if dns_success:
                        # Bağlantı bilgisini göster
                        self.log_to_app_console("-" * 50, "INFO")
                        self.log_to_app_console("BAĞLANTI BİLGİSİ", "SUCCESS")
                        self.log_to_app_console(dns_message, "SUCCESS")
                        self.log_to_app_console("-" * 50, "INFO")
                        
                        # Sunucu konsoluna da ekle
                        self.root.after(0, lambda: [
                            self.server_console.config(state='normal'),
                            self.server_console.insert(tk.END, "\n" + "-" * 50 + "\n"),
                            self.server_console.insert(tk.END, "BAĞLANTI BİLGİSİ\n"),
                            self.server_console.insert(tk.END, dns_message + "\n"),
                            self.server_console.insert(tk.END, "-" * 50 + "\n"),
                            self.server_console.see(tk.END),
                            self.server_console.config(state='disabled')
                        ])
                    else:
                        self.log_to_app_console(f"DNS hatası: {dns_message}", "ERROR")
                else:
                    if result == "NGROK_AUTH_NEEDED":
                        self.log_to_app_console("Ngrok yapılandırması gerekli", "WARNING")
                        self.root.after(0, self.show_dns_config)
                        return
                    raise Exception(str(result))
                
                self.show_progress(False)
                
                # Başarılı başlatma sonrası sunucu listesini güncelle
                self.update_server_list()
                
                self.update_status("Sunucu çalışıyor", "green")
                
            except Exception as e:
                error_msg = str(e)
                self.log_to_app_console(f"Kritik hata: {error_msg}", "ERROR")
                self.root.after(0, lambda: [
                    messagebox.showerror("Hata", error_msg),
                    self.stop_button.config(state='disabled')
                ])
                self.show_progress(False)
        
        threading.Thread(target=_start, daemon=True).start()
    
    def stop_server(self):
        """Sunucuyu durdurur"""
        if self.server_process:
            try:
                # Konsola durdurma mesajı yaz
                self.server_console.config(state='normal')
                self.server_console.insert(tk.END, "\nSunucu durduruluyor...\n")
                self.server_console.config(state='disabled')
                
                # Sunucuya stop komutu gönder
                self.server_process.stdin.write('stop\n')
                self.server_process.stdin.flush()
                
                # 5 saniye bekle ve hala çalışıyorsa zorla kapat
                time.sleep(5)
                if self.server_process.poll() is None:
                    self.server_process.terminate()
                    time.sleep(2)
                    if self.server_process.poll() is None:
                        self.server_process.kill()
                
                # Ngrok'u durdur
                self.server_manager._stop_ngrok()
                
                self.server_console.config(state='normal')
                self.server_console.insert(tk.END, "Sunucu ve Ngrok durduruldu.\n")
                self.server_console.config(state='disabled')
                
                # Butonları güncelle
                self.stop_button.config(state='disabled')
                
                # Referansı temizle
                self.server_process = None
                
                self.update_status("Sunucu durduruldu", "green")
                
            except Exception as e:
                messagebox.showerror("Hata", f"Sunucu durdurulurken hata oluştu: {str(e)}")
    
    def on_closing(self):
        """Uygulama kapatılırken çağrılır"""
        try:
            if self.server_process:
                if messagebox.askokcancel("Çıkış", "Sunucu çalışıyor. Kapatmak istediğinize emin misiniz?"):
                    self.log_to_app_console("Uygulama kapatılıyor...", "INFO")
                    self.log_to_app_console("Sunucu durduruluyor...", "INFO")
                    self.stop_server()
                else:
                    return
            
            self.log_to_app_console("Kaynaklar temizleniyor...", "INFO")
            
            # Sadece aktif process'leri temizle
            try:
                # Sunucu process'ini kontrol et ve kapat
                if self.server_process and self.server_process.poll() is None:
                    self.server_process.kill()
                
                # Ngrok process'ini durdur (dosyayı silmeden)
                self.server_manager._stop_ngrok()
                
                # Sadece geçici dosyaları temizle
                temp_files = [
                    os.path.join(self.base_dir, "java_installer.msi"),
                    os.path.join(self.base_dir, "java.zip")
                ]
                for file in temp_files:
                    if os.path.exists(file):
                        try:
                            os.remove(file)
                        except:
                            pass
                
                # Çalışan process'leri nazikçe sonlandır
                try:
                    # Sadece aktif process'leri bul ve sonlandır
                    if self.server_process:
                        subprocess.run(
                            ["taskkill", "/F", "/T", "/PID", str(self.server_process.pid)],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            creationflags=subprocess.CREATE_NO_WINDOW
                        )
                except:
                    pass
                
                self.log_to_app_console("Kaynaklar başarıyla temizlendi", "SUCCESS")
                
            except Exception as e:
                self.log_to_app_console(f"Kaynak temizleme hatası: {str(e)}", "ERROR")
            
            # Uygulamayı kapat
            time.sleep(1)  # Mesajların görünmesi için kısa bekle
            self.root.destroy()
            
        except Exception as e:
            messagebox.showerror("Hata", f"Uygulama kapatılırken hata oluştu: {str(e)}")
            self.root.destroy()
    
    def run(self):
        self.root.mainloop()

    def update_server_list(self):
        """Sunucu listesini günceller"""
        # Listeyi temizle
        for item in self.server_list.get_children():
            self.server_list.delete(item)
        
        # Sunucuları listele
        servers = self.server_manager.get_saved_servers()
        if not servers:
            # Hiç sunucu yoksa bilgi mesajı göster
            self.server_list.insert("", "end", text="Henüz sunucu yok", 
                                  values=("", "Yeni sunucu oluşturun"))
            return
        
        for server in servers:
            self.server_list.insert("", "end", text=server['name'], 
                                  values=(server['version'], server['last_played']),
                                  tags=(server['path'],))

    def show_create_server_frame(self):
        """Yeni sunucu oluşturma frame'ini gösterir"""
        self.server_select_frame.grid_remove()
        self.create_server_frame.grid()
        
        # Konsolları ve çerçevelerini gizle
        self.app_console.master.master.grid_remove()  # Uygulama konsolu ana frame'ini gizle
        self.server_console.master.master.grid_remove()  # Sunucu konsolu ana frame'ini gizle
        self.progress_frame.grid_remove()  # Progress bar frame'ini gizle
        
        # Sağ paneli gizle
        self.right_panel.grid_remove()

    def toggle_token_visibility(self, entry_widget):
        """Token göster/gizle butonunu işler"""
        if entry_widget.cget('show') == '•':
            entry_widget.configure(show='')
        else:
            entry_widget.configure(show='•')

    def update_status(self, message, color="green"):
        """Durum etiketini günceller"""
        self.status_label.config(text=message, foreground=color)

    def show_progress(self, show=True, message=""):
        """Progress bar'ı göster/gizle"""
        try:
            if show:
                self.progress_label.config(text=message)
                self.progress_bar.grid()
                self.progress_bar.start(10)
            else:
                self.progress_bar.stop()
                self.progress_bar.grid_remove()
                self.progress_label.config(text="")
        except Exception as e:
            print(f"Progress bar hatası: {str(e)}") 