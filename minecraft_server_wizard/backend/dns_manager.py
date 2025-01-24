import requests
import json
import socket
import time
import os

class DNSManager:
    def __init__(self, base_dir, server_manager):
        self.base_dir = base_dir
        self.server_manager = server_manager
        self.cloudflare_token = None
        self.zone_id = None
        self.dns_record_id = None
        self.dns_record_name = None
        self.domain_name = None
        self.ngrok_token = None
        self.operation_mode = "ngrok"  # Varsayılan mod
        
        self.config_file = os.path.join(self.base_dir, "dns_config.json")
        self.load_config()
    
    def load_config(self):
        """Kayıtlı DNS yapılandırmasını yükler"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.cloudflare_token = config.get('cloudflare_token')
                    self.zone_id = config.get('zone_id')
                    self.dns_record_id = config.get('dns_record_id')
                    self.dns_record_name = config.get('dns_record_name')
                    self.domain_name = config.get('domain_name')
                    self.ngrok_token = config.get('ngrok_token')
                    self.operation_mode = config.get('operation_mode', 'ngrok')
        except Exception as e:
            print(f"Yapılandırma yüklenemedi: {str(e)}")

    def save_config(self):
        """DNS yapılandırmasını kaydeder"""
        try:
            config = {
                'cloudflare_token': self.cloudflare_token,
                'zone_id': self.zone_id,
                'dns_record_id': self.dns_record_id,
                'dns_record_name': self.dns_record_name,
                'domain_name': self.domain_name,
                'ngrok_token': self.ngrok_token,
                'operation_mode': self.operation_mode
            }
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            raise Exception(f"Yapılandırma kaydedilemedi: {str(e)}")

    def setup_credentials(self, cloudflare_token, zone_id, dns_record_id, 
                         dns_record_name="_minecraft._tcp.mc",
                         domain_name="", ngrok_token="", operation_mode="ngrok"):
        """DNS ve Ngrok bilgilerini ayarlar ve kaydeder"""
        self.cloudflare_token = cloudflare_token
        self.zone_id = zone_id
        self.dns_record_id = dns_record_id
        self.dns_record_name = dns_record_name
        self.domain_name = domain_name
        self.ngrok_token = ngrok_token
        self.operation_mode = operation_mode
        
        self.save_config()
    
    def get_ngrok_url(self):
        """Ngrok URL'sini alır"""
        try:
            response = requests.get("http://localhost:4040/api/tunnels")
            tunnels = response.json()["tunnels"]
            
            for tunnel in tunnels:
                if tunnel["proto"] == "tcp":
                    url = tunnel["public_url"].replace("tcp://", "")
                    host, port = url.split(":")
                    return host, int(port)
                    
            return None, None
        except Exception as e:
            raise Exception(f"Ngrok URL alınamadı: {str(e)}")
    
    def get_ip_from_host(self, hostname):
        """Hostname'den IP adresini alır"""
        try:
            return socket.gethostbyname(hostname)
        except Exception as e:
            raise Exception(f"IP adresi alınamadı: {str(e)}")
    
    def update_cloudflare_dns(self, ngrok_host, port):
        """Cloudflare DNS kaydını günceller"""
        try:
            url = f"https://api.cloudflare.com/client/v4/zones/{self.zone_id}/dns_records/{self.dns_record_id}"
            headers = {
                "Authorization": f"Bearer {self.cloudflare_token}",
                "Content-Type": "application/json"
            }
            data = {
                "type": "SRV",
                "name": self.dns_record_name,
                "data": {
                    "service": "_minecraft",
                    "proto": "_tcp",
                    "name": self.domain_name,
                    "priority": 0,
                    "weight": 5,
                    "port": port,
                    "target": ngrok_host  # Ngrok host'unu doğrudan kullan
                }
            }
            
            response = requests.put(url, headers=headers, json=data)
            result = response.json()
            
            if result.get("success"):
                return True, "Cloudflare DNS kaydı güncellendi"
            else:
                errors = result.get("errors", [])
                error_msg = errors[0].get("message") if errors else "Bilinmeyen hata"
                return False, f"Cloudflare hatası: {error_msg}"
                
        except Exception as e:
            return False, f"Cloudflare hatası: {str(e)}"
    
    def update_all(self):
        """DNS kayıtlarını günceller"""
        try:
            # Ngrok bilgilerini al
            ngrok_host, ngrok_port = self.get_ngrok_url()
            if not ngrok_host:
                return False, "Ngrok URL'si alınamadı"
            
            if self.operation_mode == "ngrok":
                # Sadece IP:Port göster
                try:
                    ip = self.get_ip_from_host(ngrok_host)
                    connection_info = (
                        f"Sunucu başarıyla başlatıldı\n"
                        f"IP: {ip}\n"
                        f"Port: {ngrok_port}\n\n"
                        f"Minecraft'tan şu adres ile bağlanabilirsiniz:\n"
                        f"{ip}:{ngrok_port}"
                    )
                    return True, connection_info
                except Exception as e:
                    return False, f"IP adresi alınamadı: {str(e)}"
            else:
                # Cloudflare modu
                cf_success, cf_message = self.update_cloudflare_dns(ngrok_host, ngrok_port)
                if not cf_success:
                    return False, cf_message
                
                connection_info = (
                    f"DNS kaydı güncellendi\n"
                    f"Sunucu: {ngrok_host}\n"
                    f"Port: {ngrok_port}\n\n"
                    f"Minecraft'tan şu adres ile bağlanabilirsiniz:\n"
                    f"mc.{self.domain_name}"
                )
                return True, connection_info
            
        except Exception as e:
            return False, f"Güncelleme hatası: {str(e)}" 