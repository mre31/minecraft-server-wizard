import tkinter as tk
from tkinter import ttk, messagebox

class DNSConfigDialog:
    def __init__(self, parent, dns_manager):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("DNS Yapılandırması")
        self.dialog.geometry("600x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.dns_manager = dns_manager
        self.setup_gui()
        self.load_saved_values()  # Kayıtlı değerleri yükle
    
    def setup_gui(self):
        # Ana frame
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Çalışma modu seçimi
        mode_frame = ttk.LabelFrame(main_frame, text="Çalışma Modu", padding="5")
        mode_frame.pack(fill=tk.X, pady=5)
        
        self.operation_mode = ttk.Combobox(mode_frame, values=["Değişken IP Kullan", "Cloudflare Domain Kullan"])
        self.operation_mode.grid(row=0, column=0, sticky=tk.W, pady=2)
        self.operation_mode.bind('<<ComboboxSelected>>', self.on_mode_change)
        
        # Cloudflare ayarları
        self.cf_frame = ttk.LabelFrame(main_frame, text="Cloudflare Ayarları", padding="5")
        self.cf_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(self.cf_frame, text="Domain Adı:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.domain_name = ttk.Entry(self.cf_frame, width=40)
        self.domain_name.grid(row=0, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(self.cf_frame, text="API Token:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.cf_token = ttk.Entry(self.cf_frame, width=40, show="•")
        self.cf_token.grid(row=1, column=1, sticky=tk.W, pady=2)
        
        # Token göster/gizle butonu
        self.cf_token_visible = False
        self.cf_token_btn = ttk.Button(self.cf_frame, text="👁", width=3,
                                      command=lambda: self.toggle_token_visibility(self.cf_token))
        self.cf_token_btn.grid(row=1, column=2, padx=5)
        
        ttk.Label(self.cf_frame, text="Zone ID:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.zone_id = ttk.Entry(self.cf_frame, width=40, show="•")
        self.zone_id.grid(row=2, column=1, sticky=tk.W, pady=2)
        
        # Zone ID göster/gizle butonu
        self.zone_id_btn = ttk.Button(self.cf_frame, text="👁", width=3,
                                     command=lambda: self.toggle_token_visibility(self.zone_id))
        self.zone_id_btn.grid(row=2, column=2, padx=5)
        
        ttk.Label(self.cf_frame, text="DNS Record ID:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.record_id = ttk.Entry(self.cf_frame, width=40, show="•")
        self.record_id.grid(row=3, column=1, sticky=tk.W, pady=2)
        
        # Record ID göster/gizle butonu
        self.record_id_btn = ttk.Button(self.cf_frame, text="👁", width=3,
                                       command=lambda: self.toggle_token_visibility(self.record_id))
        self.record_id_btn.grid(row=3, column=2, padx=5)
        
        ttk.Label(self.cf_frame, text="Subdomain:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.record_name = ttk.Entry(self.cf_frame, width=40)
        self.record_name.grid(row=4, column=1, sticky=tk.W, pady=2)
        
        # Subdomain için yardım etiketi
        ttk.Label(self.cf_frame, text="Örnek: minecraft").grid(row=4, column=2, sticky=tk.W, padx=5)
        
        # Ngrok ayarları
        ngrok_frame = ttk.LabelFrame(main_frame, text="Ngrok Ayarları", padding="5")
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
        
        # Kaydet butonu
        ttk.Button(main_frame, text="Kaydet", command=self.save_config).pack(pady=10)
    
    def on_mode_change(self, event):
        # Seçilen moda göre Cloudflare ayarlarını göster/gizle
        if self.operation_mode.get() == "Cloudflare Domain Kullan":
            self.cf_frame.pack(fill=tk.X, pady=5)
        else:
            self.cf_frame.pack_forget()
    
    def toggle_token_visibility(self, entry_widget):
        """Token'ın görünürlüğünü değiştirir"""
        current_text = entry_widget.get()
        if entry_widget.cget('show') == '•':
            entry_widget.configure(show='')
        else:
            entry_widget.configure(show='•')
    
    def load_saved_values(self):
        """Kayıtlı DNS ayarlarını form alanlarına yükler ve ilk 5 karakteri gösterir"""
        def set_masked_value(entry_widget, value):
            if value:
                visible_part = value[:5]  # İlk 5 karakter
                hidden_part = "•" * (len(value) - 5)  # Geri kalanı nokta
                entry_widget.delete(0, tk.END)
                entry_widget.insert(0, value)  # Tam değeri kaydet
                entry_widget.configure(show="•")  # Tümünü gizle
        
        if self.dns_manager.domain_name:
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
        self.on_mode_change(None)
    
    def save_config(self):
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
                record_name,  # Formatlı record name'i gönder
                domain_name,
                ngrok_token,
                operation_mode
            )
            
            messagebox.showinfo("Başarılı", "Yapılandırma kaydedildi")
            self.dialog.destroy()
            
        except Exception as e:
            messagebox.showerror("Hata", f"Yapılandırma kaydedilemedi: {str(e)}") 