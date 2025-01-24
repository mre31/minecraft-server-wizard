import subprocess
import os
import urllib.request
from urllib.error import URLError
import sys
import time
import platform
import zipfile
import json
import requests
import webbrowser
import shutil

class MinecraftServerManager:
    def __init__(self, base_dir, log_callback=None):
        self.base_dir = base_dir
        self.servers_dir = os.path.join(self.base_dir, "servers")  # Sunucular klasörü
        if not os.path.exists(self.servers_dir):
            os.makedirs(self.servers_dir)
        
        self.resources_dir = os.path.join(self.base_dir, "resources")  # Resources klasörü servers ile aynı yerde
        if not os.path.exists(self.resources_dir):
            os.makedirs(self.resources_dir)
        
        self.current_server_path = None
        self.config = {}
        self.log_callback = log_callback
        
        # Java dizinleri
        self.java_dir = os.path.join(self.resources_dir, "java")
        self.java8_dir = os.path.join(self.java_dir, "java8")
        self.java17_dir = os.path.join(self.java_dir, "java17")
        self.java21_dir = os.path.join(self.java_dir, "java21")
        
        # Ngrok dizini
        self.ngrok_dir = os.path.join(self.resources_dir, "ngrok")
        
        # Desteklenen Minecraft sürümleri
        self.versions = {
            # 1.21.x serisi
            "1.21.4": "https://piston-data.mojang.com/v1/objects/4707d00eb834b446575d89a61a11b5d548d8c001/server.jar",
            "1.21.3": "https://piston-data.mojang.com/v1/objects/45810d238246d90e811d896f87b14695b7fb6839/server.jar",
            "1.21.2": "https://piston-data.mojang.com/v1/objects/7bf95409b0d9b5388bfea3704ec92012d273c14c/server.jar",
            "1.21.1": "https://piston-data.mojang.com/v1/objects/59353fb40c36d304f2035d51e7d6e6baa98dc05c/server.jar",
            "1.21": "https://piston-data.mojang.com/v1/objects/450698d1863ab5180c25d7c804ef0fe6369dd1ba/server.jar",
            
            # 1.20.x serisi
            "1.20.6": "https://piston-data.mojang.com/v1/objects/145ff0858209bcfc164859ba735d4199aafa1eea/server.jar",
            "1.20.5": "https://piston-data.mojang.com/v1/objects/79493072f65e17243fd36a699c9a96b4381feb91/server.jar",
            "1.20.4": "https://piston-data.mojang.com/v1/objects/8dd1a28015f51b1803213892b50b7b4fc76e594d/server.jar",
            "1.20.3": "https://piston-data.mojang.com/v1/objects/4fb536bfd4a83d61cdbaf684b8d311e66e7d4c49/server.jar",
            "1.20.2": "https://piston-data.mojang.com/v1/objects/5b868151bd02b41319f54c8d4061b8cae84e665c/server.jar",
            "1.20.1": "https://piston-data.mojang.com/v1/objects/84194a2f286ef7c14ed7ce0090dba59902951553/server.jar",
            "1.20": "https://piston-data.mojang.com/v1/objects/15c777e2cfe0556eef19aab534b186c0c6f277e1/server.jar",
            
            # 1.19.x serisi
            "1.19.4": "https://piston-data.mojang.com/v1/objects/8f3112a1049751cc472ec13e397eade5336ca7ae/server.jar",
            "1.19.3": "https://piston-data.mojang.com/v1/objects/c9df48efed58511cdd0213c56b9013a7b5c9ac1f/server.jar",
            "1.19.2": "https://piston-data.mojang.com/v1/objects/f69c284232d7c7580bd89a5a4931c3581eae1378/server.jar",
            "1.19.1": "https://piston-data.mojang.com/v1/objects/8399e1211e95faa421c1507b322dbeae86d604df/server.jar",
            "1.19": "https://piston-data.mojang.com/v1/objects/e00c4052dac1d59a1188b2aa9d5a87113aaf1122/server.jar",
            
            # 1.18.x serisi
            "1.18.2": "https://piston-data.mojang.com/v1/objects/c8f83c5655308435b3dcf03c06d9fe8740a77469/server.jar",
            "1.18.1": "https://piston-data.mojang.com/v1/objects/125e5adf40c659fd3bce3e66e67a16bb49ecc1b9/server.jar",
            "1.18": "https://piston-data.mojang.com/v1/objects/3cf24a8694aca6267883b17d934efacc5e44440d/server.jar",
            
            # 1.17.x serisi
            "1.17.1": "https://piston-data.mojang.com/v1/objects/a16d67e5807f57fc4e550299cf20226194497dc2/server.jar",
            "1.17": "https://piston-data.mojang.com/v1/objects/0a269b5f2c5b93b1712d0f5dc43b6182b9ab254e/server.jar",
            
            # 1.16.x serisi
            "1.16.5": "https://piston-data.mojang.com/v1/objects/1b557e7b033b583cd9f66746b7a9ab1ec1673ced/server.jar",
            "1.16.4": "https://piston-data.mojang.com/v1/objects/35139deedbd5182953cf1caa23835da59ca3d7cd/server.jar",
            "1.16.3": "https://piston-data.mojang.com/v1/objects/f02f4473dbf152c23d7d484952121db0b36698cb/server.jar",
            "1.16.2": "https://piston-data.mojang.com/v1/objects/c5f6fb23c3876461d46ec380421e42b289789530/server.jar",
            "1.16.1": "https://piston-data.mojang.com/v1/objects/a412fd69db1f81db3f511c1463fd304675244077/server.jar",
            "1.16": "https://piston-data.mojang.com/v1/objects/a0d03225615ba897619220e256a266cb33a44b6b/server.jar",
            
            # 1.15.x serisi
            "1.15.2": "https://piston-data.mojang.com/v1/objects/bb2b6b1aefcd70dfd1892149ac3a215f6c636b07/server.jar",
            "1.15.1": "https://piston-data.mojang.com/v1/objects/4d1826eebac84847c71a77f9349cc22afd0cf0a1/server.jar",
            "1.15": "https://piston-data.mojang.com/v1/objects/e9f105b3c5c7e85c7b445249a93362a22f62442d/server.jar",
            
            # 1.14.x serisi
            "1.14.4": "https://piston-data.mojang.com/v1/objects/3dc3d84a581f14691199cf6831b71ed1296a9fdf/server.jar",
            "1.14.3": "https://piston-data.mojang.com/v1/objects/d0d0fe2b1dc6ab4c65554cb734270872b72dadd6/server.jar",
            "1.14.2": "https://piston-data.mojang.com/v1/objects/808be3869e2ca6b62378f9f4b33c946621620019/server.jar",
            "1.14.1": "https://piston-data.mojang.com/v1/objects/ed76d597a44c5266be2a7fcd77a8270f1f0bc118/server.jar",
            "1.14": "https://piston-data.mojang.com/v1/objects/f1a0073671057f01aa843443fef34330281333ce/server.jar"
        }
        
        self.server_jar_url = self.versions["1.21.4"]
        self.ngrok_process = None
        self.ngrok_token = None
        
        # DNS yapılandırmasından Ngrok token'ı yükle
        self._load_ngrok_token()
        
        # Fabric versiyonları
        self.fabric_versions = [
            "0.16.10", "0.16.9", "0.16.8", "0.16.7", "0.16.6", "0.16.5", "0.16.4", "0.16.3", "0.16.2", 
            "0.16.1", "0.16.0", "0.15.11", "0.15.10", "0.15.9", "0.15.8", "0.15.7", "0.15.6", "0.15.5", 
            "0.15.4", "0.15.3", "0.15.2", "0.15.1", "0.15.0", "0.14.25", "0.14.24", "0.14.23", "0.14.22", 
            "0.14.21", "0.14.20", "0.14.19", "0.14.18", "0.14.17", "0.14.16", "0.14.15", "0.14.14", 
            "0.14.13", "0.14.12", "0.14.11", "0.14.10", "0.14.9", "0.14.8", "0.14.7", "0.14.6", "0.14.5", 
            "0.14.4", "0.14.3", "0.14.2", "0.14.1", "0.14.0", "0.13.3", "0.13.2", "0.13.1", "0.13.0", 
            "0.12.12", "0.12.11", "0.12.10", "0.12.9", "0.12.8", "0.12.7", "0.12.6", "0.12.5", "0.12.4", 
            "0.12.3", "0.12.2", "0.12.1", "0.12.0"
        ]
        
        self.server_type = "vanilla"  # vanilla veya fabric
        self.fabric_version = "0.16.10"  # varsayılan fabric versiyonu
        self.installer_version = "1.0.1"  # sabit installer versiyonu
    
    def _log(self, message, level="INFO"):
        """Log mesajını callback ile gönderir"""
        if self.log_callback:
            self.log_callback(message, level)
    
    def get_saved_servers(self):
        """Kaydedilmiş sunucuları listeler"""
        servers = []
        for server_dir in os.listdir(self.servers_dir):
            config_file = os.path.join(self.servers_dir, server_dir, "server_config.json")
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    servers.append({
                        'name': server_dir,
                        'version': config.get('version', 'Bilinmiyor'),
                        'last_played': config.get('last_played', 'Hiç'),
                        'path': os.path.join(self.servers_dir, server_dir)
                    })
        return servers

    def load_server(self, server_path):
        """Var olan bir sunucuyu yükler"""
        try:
            config_file = os.path.join(server_path, "server_config.json")
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    self.config = json.load(f)
                self.current_server_path = server_path
                self.server_jar_url = self.versions[self.config['version']]  # Sürümü ayarla
                return True
            return False
        except Exception as e:
            self._log(f"Sunucu yükleme hatası: {str(e)}", "ERROR")
            return False

    def initialize_server(self, server_name, ram, port, gamemode, version, server_type="vanilla", fabric_version=None, properties=None):
        """Yeni bir sunucu oluşturur"""
        try:
            # Sunucu adından geçerli bir klasör adı oluştur
            safe_name = "".join(c for c in server_name if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_name = safe_name.replace(' ', '_')
            
            # Sunucu yolunu ayarla
            self.current_server_path = os.path.join(self.servers_dir, safe_name)
            
            # Eğer aynı isimde sunucu varsa, yeni bir isim oluştur
            counter = 1
            original_path = self.current_server_path
            while os.path.exists(self.current_server_path):
                self.current_server_path = f"{original_path}_{counter}"
                counter += 1
            
            os.makedirs(self.current_server_path)
            
            # Sunucu konfigürasyonunu kaydet
            self.config = {
                'server_name': server_name,
                'ram_allocation': ram,
                'server_port': port,
                'gamemode': gamemode,
                'version': version,
                'server_type': server_type,
                'fabric_version': fabric_version,
                'created_date': time.strftime("%Y-%m-%d %H:%M:%S"),
                'last_played': time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Server type'a göre JAR indir
            if server_type == "fabric":
                self.fabric_version = fabric_version
                if not self._download_fabric_server():
                    return False
            else:
                self.server_jar_url = self.versions[version]
                if not self._download_server_jar():
                    return False
            
            # EULA'yı kabul et
            eula_path = os.path.join(self.current_server_path, "eula.txt")
            with open(eula_path, 'w') as f:
                f.write("eula=true\n")
            
            # Varsayılan server.properties oluştur
            default_properties = {
                "server-port": str(port),
                "gamemode": gamemode,
                "motd": server_name,
                "difficulty": "normal",
                "pvp": "true",
                "online-mode": "true",
                "max-players": "20",
                "enable-command-block": "true",
                "spawn-protection": "16",
                "spawn-monsters": "true",
                "spawn-npcs": "true",
                "spawn-animals": "true",
                "generate-structures": "true",
                "view-distance": "10"
            }
            
            # Kullanıcı tarafından belirtilen özellikleri ekle/güncelle
            if properties:
                default_properties.update(properties)
            
            # server.properties dosyasını oluştur
            props_file = os.path.join(self.current_server_path, "server.properties")
            with open(props_file, 'w', encoding='utf-8') as f:
                for key, value in sorted(default_properties.items()):
                    f.write(f"{key}={value}\n")
            
            # Konfigürasyonu kaydet
            config_file = os.path.join(self.current_server_path, "server_config.json")
            with open(config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
            
            return True
            
        except Exception as e:
            self._log(f"Sunucu hazırlama hatası: {str(e)}", "ERROR")
            return False

    def _download_server_jar(self):
        """Minecraft sunucu JAR dosyasını indirir"""
        jar_path = os.path.join(self.current_server_path, "server.jar")
        
        if os.path.exists(jar_path):
            self._log("Sunucu JAR dosyası zaten mevcut")
            return True
        
        try:
            self._log("Sunucu JAR dosyası indiriliyor...", "INFO")
            urllib.request.urlretrieve(self.server_jar_url, jar_path)
            self._log("JAR indirme tamamlandı!", "SUCCESS")
            return True
        except Exception as e:
            self._log(f"JAR indirme hatası: {str(e)}", "ERROR")
            return False
    
    def _create_eula_file(self):
        """EULA dosyasını oluşturur"""
        with open(os.path.join(self.current_server_path, "eula.txt"), "w") as f:
            f.write("eula=true")
    
    def _create_server_properties(self):
        """server.properties dosyasını oluşturur"""
        properties = [
            f"server-port={self.config['server_port']}",
            f"gamemode={self.config['gamemode']}",
            f"motd={self.config['server_name']}",
            "enable-command-block=true",
            "spawn-protection=16",
            "online-mode=false",
            "difficulty=normal",
            "spawn-monsters=true",
            "spawn-npcs=true",
            "spawn-animals=true",
            "generate-structures=true",
            "view-distance=10",
            "max-players=20"
        ]
        
        with open(os.path.join(self.current_server_path, "server.properties"), "w") as f:
            f.write("\n".join(properties))
    
    def _download_and_setup_ngrok(self):
        """Ngrok'u indirir ve kurar"""
        try:
            if os.path.exists(self.ngrok_dir):  # Zaten kuruluysa tekrar indirme
                ngrok_path = os.path.join(self.ngrok_dir, "ngrok.exe")
                if os.path.exists(ngrok_path):
                    return True, ngrok_path
            
            self._log("Ngrok indiriliyor...", "INFO")
            
            # Ngrok dizinini oluştur/temizle
            if os.path.exists(self.ngrok_dir):
                shutil.rmtree(self.ngrok_dir)
            os.makedirs(self.ngrok_dir)
            
            ngrok_url = "https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-windows-amd64.zip"
            zip_path = os.path.join(self.resources_dir, "ngrok_temp.zip")
            
            # ZIP'i indir
            urllib.request.urlretrieve(ngrok_url, zip_path)
            
            # ZIP'i çıkart
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(self.ngrok_dir)
            
            # ZIP'i sil
            try:
                os.remove(zip_path)
            except:
                pass  # Zip silinmezse önemli değil
            
            ngrok_path = os.path.join(self.ngrok_dir, "ngrok.exe")
            if not os.path.exists(ngrok_path):
                return False, "Ngrok kurulumu başarısız: ngrok.exe bulunamadı"
            
            self._log("Ngrok başarıyla kuruldu", "SUCCESS")
            return True, ngrok_path
            
        except Exception as e:
            self._log(f"Ngrok kurulum hatası: {str(e)}", "ERROR")
            return False, f"Ngrok kurulumu başarısız: {str(e)}"

    def _setup_ngrok_auth(self, auth_token):
        """Ngrok auth token'ı ayarlar"""
        try:
            success, ngrok_path = self._download_and_setup_ngrok()
            if not success:
                return False, ngrok_path
            
            result = subprocess.run(
                [ngrok_path, "config", "add-authtoken", auth_token],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if result.returncode != 0:
                return False, f"Ngrok token hatası: {result.stderr}"
            
            self.ngrok_token = auth_token
            return True, "Ngrok token başarıyla ayarlandı"
            
        except Exception as e:
            return False, f"Ngrok token hatası: {str(e)}"

    def _load_ngrok_token(self):
        """DNS yapılandırma dosyasından Ngrok token'ı yükler"""
        try:
            config_file = os.path.join(self.base_dir, "dns_config.json")
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    token = config.get('ngrok_token')
                    if token:
                        self._setup_ngrok_auth(token)
        except Exception as e:
            self._log(f"Ngrok token yüklenemedi: {str(e)}", "ERROR")

    def start_ngrok(self, port):
        """Ngrok tünelini başlatır"""
        try:
            # Eğer token yoksa hata döndür
            if not self.ngrok_token:
                return False, "NGROK_AUTH_NEEDED"
                
            self._log(f"Ngrok başlatılıyor... Port: {port}", "INFO")
            success, ngrok_path = self._download_and_setup_ngrok()
            if not success:
                return False, ngrok_path
            
            # Önceki Ngrok process'ini temizle
            self._stop_ngrok()
            
            # Yeni Ngrok process'i başlat
            self.ngrok_process = subprocess.Popen(
                [ngrok_path, "tcp", str(port)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            # Ngrok çıktısını kontrol et
            time.sleep(2)  # Ngrok'un başlaması için bekle
            if self.ngrok_process.poll() is not None:
                error = self.ngrok_process.stderr.read()
                if "ERR_NGROK_108" in error:
                    return False, "NGROK_AUTH_NEEDED"
                return False, f"Ngrok başlatılamadı: {error}"
            
            # Tünel URL'sini al
            api_url = "http://localhost:4040/api/tunnels"
            max_retries = 5
            retry_count = 0
            
            while retry_count < max_retries:
                try:
                    response = requests.get(api_url)
                    if response.ok:
                        tunnels = response.json()["tunnels"]
                        if tunnels:
                            url = tunnels[0]["public_url"].replace("tcp://", "")
                            self._log(f"Ngrok tüneli açıldı: {url}", "SUCCESS")
                            return True, url
                except:
                    retry_count += 1
                    time.sleep(1)
            
            return False, "Ngrok tünel bilgisi alınamadı"
            
        except Exception as e:
            self._stop_ngrok()
            return False, f"Ngrok hatası: {str(e)}"
    
    def _stop_ngrok(self):
        """Çalışan Ngrok process'ini durdurur"""
        if self.ngrok_process:
            try:
                self.ngrok_process.terminate()
                self.ngrok_process.wait(timeout=5)
            except:
                try:
                    self.ngrok_process.kill()
                except:
                    pass
            self.ngrok_process = None

    def _check_java(self):
        """Java kurulumunu kontrol eder"""
        if hasattr(self, 'java_path') and os.path.exists(self.java_path):
            return True
        return False

    def _download_and_install_java(self):
        """Portable Java'yı indirir ve ayarlar"""
        try:
            # Minecraft sürümüne göre Java sürümünü belirle
            current_version = self.config.get('version', '1.21.4')
            major_version = float(current_version.split('.')[0] + '.' + current_version.split('.')[1])
            
            # Java sürümünü ve dizinini seç
            if major_version >= 1.21:
                java_url = "https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.2%2B13/OpenJDK21U-jdk_x64_windows_hotspot_21.0.2_13.zip"
                target_dir = self.java21_dir
                java_version = "Java 21"
            elif major_version >= 1.17:
                java_url = "https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.10%2B7/OpenJDK17U-jdk_x64_windows_hotspot_17.0.10_7.zip"
                target_dir = self.java17_dir
                java_version = "Java 17"
            else:
                java_url = "https://github.com/adoptium/temurin8-binaries/releases/download/jdk8u392-b08/OpenJDK8U-jdk_x64_windows_hotspot_8u392b08.zip"
                target_dir = self.java8_dir
                java_version = "Java 8"
            
            # Java dizinini kontrol et
            if os.path.exists(target_dir):
                # Java yolunu bul
                for item in os.listdir(target_dir):
                    if item.startswith("jdk"):
                        self.java_path = os.path.join(target_dir, item, "bin", "java.exe")
                        if os.path.exists(self.java_path):
                            self._log(f"{java_version} zaten kurulu", "INFO")
                            return True, f"{java_version} zaten kurulu"
            
            self._log(f"{java_version} indiriliyor...", "INFO")
            
            # Java dizinlerini oluştur
            os.makedirs(self.java_dir, exist_ok=True)
            os.makedirs(target_dir, exist_ok=True)
            
            # Java'yı indir
            zip_path = os.path.join(self.resources_dir, "java_temp.zip")
            urllib.request.urlretrieve(java_url, zip_path)
            
            self._log(f"{java_version} ayarlanıyor...", "INFO")
            
            # ZIP'i çıkart
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(target_dir)
            
            # ZIP'i sil
            os.remove(zip_path)
            
            # Java dizinini bul
            java_version_dir = None
            for item in os.listdir(target_dir):
                if item.startswith("jdk"):
                    java_version_dir = os.path.join(target_dir, item)
                    break
            
            if not java_version_dir:
                return False, f"{java_version} dizini bulunamadı"
            
            # Java yolunu ayarla
            self.java_path = os.path.join(java_version_dir, "bin", "java.exe")
            
            self._log(f"{java_version} başarıyla ayarlandı", "SUCCESS")
            return True, f"{java_version} başarıyla ayarlandı"
            
        except Exception as e:
            self._log(f"Java kurulum hatası: {str(e)}", "ERROR")
            return False, f"Java kurulum hatası: {str(e)}"

    def start_server(self):
        """Sunucuyu başlatır"""
        try:
            if not self.current_server_path:
                return False, "Sunucu dizini belirtilmemiş"
            
            # Java kontrolü
            if not self._check_java():
                success, message = self._download_and_install_java()
                if not success:
                    return False, message
            
            # Ngrok başlat
            success, message = self.start_ngrok(self.config['server_port'])
            if not success:
                if message == "NGROK_AUTH_NEEDED":
                    return False, "NGROK_AUTH_NEEDED"
                return False, message
            
            # Sunucuyu başlat
            jar_path = os.path.abspath(os.path.join(self.current_server_path, "server.jar"))
            working_dir = os.path.abspath(self.current_server_path)
            
            command_parts = [
                self.java_path,
                f"-Xmx{self.config['ram_allocation']}G",
                "-Xms1G",
                "-jar",
                jar_path,
                "nogui"
            ]
            
            process = subprocess.Popen(
                command_parts,
                cwd=working_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            # Son oynama tarihini güncelle
            self.config['last_played'] = time.strftime("%Y-%m-%d %H:%M:%S")
            config_file = os.path.join(self.current_server_path, "server_config.json")
            with open(config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
            
            return True, process
                
        except Exception as e:
            self._stop_ngrok()  # Hata durumunda Ngrok'u durdur
            return False, f"Hata: {str(e)}"

    def set_version(self, version):
        """Minecraft sürümünü ayarlar"""
        if version in self.versions:
            self.server_jar_url = self.versions[version]
            return True
        return False

    def update_server_properties(self, properties):
        """server.properties dosyasını günceller"""
        try:
            props_file = os.path.join(self.current_server_path, "server.properties")
            if os.path.exists(props_file):
                # Mevcut özellikleri oku
                current_props = {}
                with open(props_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            key, value = line.split('=', 1)
                            current_props[key.strip()] = value.strip()
                
                # Yeni özellikleri ekle/güncelle
                current_props.update(properties)
                
                # Dosyaya geri yaz
                with open(props_file, 'w', encoding='utf-8') as f:
                    for key, value in sorted(current_props.items()):
                        f.write(f"{key}={value}\n")
                
                return True
            return False
        except Exception as e:
            self._log(f"Sunucu ayarları güncellenirken hata: {str(e)}", "ERROR")
            return False

    def _download_fabric_server(self):
        """Fabric sunucu JAR dosyasını indirir"""
        try:
            mc_version = self.config['version']
            jar_name = f"fabric-server-mc.{mc_version}-loader.{self.fabric_version}-launcher.{self.installer_version}.jar"
            jar_path = os.path.join(self.current_server_path, "server.jar")
            
            url = f"https://meta.fabricmc.net/v2/versions/loader/{mc_version}/{self.fabric_version}/{self.installer_version}/server/jar"
            
            self._log("Fabric sunucu JAR dosyası indiriliyor...", "INFO")
            urllib.request.urlretrieve(url, jar_path)
            self._log("Fabric JAR indirme tamamlandı!", "SUCCESS")
            return True
            
        except Exception as e:
            self._log(f"Fabric JAR indirme hatası: {str(e)}", "ERROR")
            return False 