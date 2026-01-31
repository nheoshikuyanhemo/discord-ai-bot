import requests
import time
import json
import os
import re
from dotenv import load_dotenv
from datetime import datetime

# ==================== KONFIGURASI ====================
TARGET_CHANNEL_ID = "1462752372831944841"

# AI Configuration
AI_TIMEOUT = 5
MAX_WORDS = 25
BUFFER_SECONDS = 1

# ==================== FIXED COOLDOWN SYSTEM ====================
class FixedCooldownSystem:
    def __init__(self, token, channel_id):
        self.token = token
        self.channel_id = channel_id
        self.current_cooldown = 0
        self.cooldown_until = 0
        self.is_calibrated = False
        self.last_rate_limit = None
        
    def calibrate(self):
        """Kalibrasi dengan double absen"""
        print("=" * 70)
        print("🤖 DISCORD AI - FIXED COOLDOWN SYSTEM")
        print("=" * 70)
        print("🚀 AUTO CALIBRATION...")
        
        # Kirim double absen
        detected = self._detect_cooldown()
        
        # Set cooldown awal
        self.current_cooldown = detected + BUFFER_SECONDS
        self.cooldown_until = time.time() + self.current_cooldown
        self.is_calibrated = True
        
        print(f"\n✅ CALIBRATION COMPLETE")
        print(f"   Detected: {detected:.1f}s")
        print(f"   + Buffer: {BUFFER_SECONDS}s")
        print(f"   Initial Cooldown: {self.current_cooldown:.1f}s")
        
        return self.current_cooldown
    
    def _detect_cooldown(self):
        """Deteksi cooldown dengan double absen"""
        print("\n📡 DETECTING COOLDOWN...")
        
        cooldowns = []
        
        for i in range(2):
            url = f"https://discord.com/api/v9/channels/{self.channel_id}/messages"
            payload = {"content": "absen"}
            headers = {"Authorization": self.token, "Content-Type": "application/json"}
            
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=5)
                
                if response.status_code == 200:
                    # Hapus setelah 0.5s
                    time.sleep(0.5)
                    try:
                        msg_id = response.json().get('id')
                        if msg_id:
                            delete_url = f"{url}/{msg_id}"
                            requests.delete(delete_url, headers=headers, timeout=2)
                    except:
                        pass
                    
                    cooldowns.append(0)
                    print(f"   ABSEN #{i+1}: ✅")
                    
                elif response.status_code == 429:
                    retry = response.json().get('retry_after', 1.0)
                    cooldowns.append(retry)
                    print(f"   ABSEN #{i+1}: ⏳ {retry:.1f}s")
                    
                else:
                    cooldowns.append(0)
                    
            except:
                cooldowns.append(0)
            
            if i == 0:
                time.sleep(0.1)
        
        max_cd = max(cooldowns) if cooldowns else 0
        return max_cd if max_cd > 0 else 2.0
    
    def can_send(self):
        """Cek apakah bisa kirim - FIXED VERSION"""
        now = time.time()
        
        if now < self.cooldown_until:
            remaining = self.cooldown_until - now
            # HANYA tampilkan jika > 1 detik
            if remaining > 1.0:
                mins = int(remaining // 60)
                secs = int(remaining % 60)
                if mins > 0 or secs > 5:
                    next_time = datetime.fromtimestamp(self.cooldown_until).strftime('%H:%M:%S')
                    print(f"⏳ Cooldown: {mins:02d}:{secs:02d} (until {next_time})")
            return False, remaining
        
        return True, 0
    
    def wait_for_cooldown(self):
        """Tunggu cooldown selesai - FIXED"""
        while True:
            can_send, remaining = self.can_send()
            if can_send:
                return True
            
            # Tunggu maksimal 5 detik per check
            sleep_time = min(remaining, 5.0)
            if sleep_time > 0:
                time.sleep(sleep_time)
    
    def record_send(self):
        """Catat pengiriman sukses - PASTIKAN pakai current_cooldown"""
        self.cooldown_until = time.time() + self.current_cooldown
        print(f"📝 Next send in {self.current_cooldown:.1f}s")
    
    def handle_rate_limit(self, retry_after):
        """Handle rate limit - PASTIKAN update benar"""
        print(f"\n🔄 REPOSITIONING COOLDOWN...")
        print(f"   Rate limit: {retry_after:.1f}s")
        
        # UPDATE: Gunakan nilai terbesar antara current dan baru
        new_cooldown = retry_after + BUFFER_SECONDS
        
        # PASTIKAN update current_cooldown
        self.current_cooldown = max(self.current_cooldown, new_cooldown)
        self.cooldown_until = time.time() + self.current_cooldown
        self.last_rate_limit = time.time()
        
        print(f"   New cooldown: {self.current_cooldown:.1f}s")
        print(f"   Next available: {datetime.fromtimestamp(self.cooldown_until).strftime('%H:%M:%S')}")
        
        # TUNGGU cooldown baru
        wait_time = min(retry_after, 30)
        if wait_time > 0:
            print(f"   Waiting {wait_time:.1f}s...")
            time.sleep(wait_time)
        
        return self.current_cooldown

# ==================== AI SYSTEM ====================
def get_ai_response(question):
    """Dapatkan response AI"""
    AI_KEY = os.getenv("AI_ASSIST_KEY")
    
    if not AI_KEY:
        return None
    
    url = "https://api.aiassist.net/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {AI_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        system_prompt = """Bertindaklah sebagai member Discord paling aktif dan lowkey sepuh. Gunakan gaya bahasa anak tongkrongan digital tahun 2026 yang gaul parah, cringe-free, dan super santai.
​Aturan Tambahan:
​Gunakan Mix-Language: Gabungkan bahasa Indonesia dengan istilah slang (contoh: grindset, rizz, cooked, valid, real no cap, mabar, gas-in).
​Gunakan Ketikan 'Manusia': Kadang pakai huruf kecil semua, gunakan singkatan 'yg', 'gw', 'lu', dan tanpa titik di akhir kalimat biar natural.
​Vibe: Supportif tapi tetap cool. Jangan kaku kayak robot customer service.
​Limit: Maksimal 20 kata. perlu di ingat TIDAK LEBIH DARI 20 KATA.
​Topik Fokus: Discord community, grinding, skill development, networking.
​Contoh vibe yang diinginkan: 'Gas terus grind-nya, makin valid skill lu makin gampang networking sama sepuh sini. Real no cap"""
        
        response = requests.post(
            url,
            json={
                "model": "llama-3.1-8b-instant",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question[:250]}
                ],
                "temperature": 0.3,
                "max_tokens": 80
            },
            headers=headers,
            timeout=AI_TIMEOUT
        )
        
        if response.status_code == 200:
            answer = response.json()['choices'][0]['message']['content']
            
            # Clean
            answer = re.sub(r'\s+', ' ', answer).strip()
            answer = re.sub(r'^[""\'`]+|[""\'`]+$', '', answer)
            answer = re.sub(r'^(sebagai|as|ai:|bot:|assistant:)\s*', '', answer, flags=re.IGNORECASE)
            
            words = answer.split()
            if len(words) > MAX_WORDS:
                answer = ' '.join(words[:MAX_WORDS])
            
            return answer.lower()
            
        elif response.status_code == 429:
            print("⚠️ AI rate limit, retry in 3s")
            time.sleep(3)
            return get_ai_response(question)
            
        else:
            return None
            
    except:
        return None

def prepare_input(content):
    """Siapkan input untuk AI"""
    if not content or len(content.strip()) < 2:
        return None
    
    clean = content.strip()
    clean = re.sub(r'<@!?\d+>', '', clean)
    clean = re.sub(r'http\S+', '', clean)
    clean = re.sub(r'[#*_~|>`]', '', clean)
    clean = re.sub(r'\s+', ' ', clean).strip()
    
    if len(clean) < 2:
        return None
    
    import random
    contexts = [
        "di discord, ",
        "tentang komunitas discord, ",
        "dalam grinding discord, ",
        "ngobrol discord nih, ",
    ]
    
    context = random.choice(contexts)
    
    if len(clean) < 50:
        return f"{context}'{clean}'. komentar singkat dong (max 20 kata)"
    else:
        truncated = clean[:50] + "..."
        return f"{context}'{truncated}'. tanggapan singkat (max 20 kata)"

# ==================== DISCORD HANDLER ====================
def send_message(token, channel_id, message_id, content):
    """Kirim message"""
    url = f"https://discord.com/api/v9/channels/{channel_id}/messages"
    payload = {
        "content": content,
        "message_reference": {
            "message_id": message_id,
            "channel_id": channel_id,
            "guild_id": None
        }
    }
    headers = {
        "Authorization": token,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if response.status_code == 200:
            word_count = len(content.split())
            print(f"[{timestamp}] ✅ SENT ({word_count}w): {content[:40]}...")
            return True, None
            
        elif response.status_code == 429:
            retry_after = response.json().get('retry_after', 1.0)
            print(f"[{timestamp}] 🔴 RATE LIMIT: {retry_after:.1f}s")
            return False, retry_after
            
        else:
            print(f"[{timestamp}] ❌ Error: {response.status_code}")
            return False, None
            
    except Exception as e:
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] ❌ Network: {e}")
        return False, None

def get_messages(token, channel_id, limit=10):
    """Ambil pesan"""
    url = f"https://discord.com/api/v9/channels/{channel_id}/messages?limit={limit}"
    headers = {"Authorization": token}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

# ==================== MAIN - FIXED VERSION ====================
def main():
    load_dotenv()
    TOKEN = os.getenv("DISCORD_TOKEN")
    AI_KEY = os.getenv("AI_ASSIST_KEY")
    
    if not TOKEN or not AI_KEY:
        print("❌ Missing credentials")
        return
    
    # Initialize system
    cd_system = FixedCooldownSystem(TOKEN, TARGET_CHANNEL_ID)
    
    # Calibrate
    try:
        initial_cd = cd_system.calibrate()
    except Exception as e:
        print(f"❌ Calibration failed: {e}")
        return
    
    # Tunggu cooldown awal
    print(f"\n⏳ Waiting initial cooldown ({initial_cd:.1f}s)...")
    time.sleep(initial_cd)
    
    # Get user info
    MY_USER_ID = None
    try:
        url = "https://discord.com/api/v9/users/@me"
        response = requests.get(url, headers={"Authorization": TOKEN}, timeout=5)
        if response.status_code == 200:
            user_info = response.json()
            MY_USER_ID = user_info['id']
            print(f"✅ User ID: {MY_USER_ID}")
    except:
        pass
    
    # Load history
    replied = []
    HISTORY_FILE = "replied_ai_messages.json"
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r') as f:
                replied = json.load(f)
        except:
            pass
    
    print(f"📊 History: {len(replied)} messages")
    
    print("\n" + "="*50)
    print("🚀 FIXED SYSTEM: RUNNING")
    print(f"⏳ Cooldown: {cd_system.current_cooldown:.1f}s")
    print("🔄 Real-time repositioning")
    print("="*50 + "\n")
    
    stats = {
        'cycles': 0,
        'checked': 0,
        'ai_calls': 0,
        'sent': 0,
        'rate_limits': 0,
        'start_time': time.time()
    }
    
    try:
        while True:
            stats['cycles'] += 1
            
            # WAIT FOR COOLDOWN - FIXED
            cd_system.wait_for_cooldown()
            
            # Get messages
            messages = get_messages(TOKEN, TARGET_CHANNEL_ID, limit=12)
            stats['checked'] += 1
            
            if not messages:
                time.sleep(2)
                continue
            
            # Process messages
            processed = False
            
            for message in reversed(messages):
                message_id = message['id']
                
                if message_id in replied:
                    continue
                
                author = message['author']
                if author.get('bot', False):
                    continue
                
                if MY_USER_ID and author.get('id') == MY_USER_ID:
                    continue
                
                content = message.get('content', '').strip()
                if len(content) < 2:
                    continue
                
                if content.startswith(('!', '/', '.', '$', '?', '-', '\\')):
                    continue
                
                # Check priority
                is_priority = False
                if MY_USER_ID:
                    if message.get('referenced_message'):
                        ref = message['referenced_message']
                        if ref and ref.get('author', {}).get('id') == MY_USER_ID:
                            is_priority = True
                    
                    mentions = message.get('mentions', [])
                    for mention in mentions:
                        if mention.get('id') == MY_USER_ID:
                            is_priority = True
                            break
                
                # Process semua pesan
                author_name = author['username']
                print(f"📩 @{author_name}: {content[:50]}...")
                
                # AI
                ai_input = prepare_input(content)
                if not ai_input:
                    continue
                
                print("   🤖 Generating AI...")
                ai_response = get_ai_response(ai_input)
                stats['ai_calls'] += 1
                
                if not ai_response:
                    print("   ❌ AI failed")
                    time.sleep(1)
                    continue
                
                # Send
                success, retry_time = send_message(TOKEN, TARGET_CHANNEL_ID, message_id, ai_response)
                
                if success:
                    # RECORD SEND - PASTIKAN pakai current_cooldown
                    cd_system.record_send()
                    stats['sent'] += 1
                    replied.append(message_id)
                    processed = True
                    
                    # Save
                    if len(replied) % 5 == 0:
                        with open(HISTORY_FILE, 'w') as f:
                            json.dump(replied[-2000:], f)
                    
                    # Small pause
                    time.sleep(0.3)
                    break
                    
                elif retry_time is not None:
                    # HANDLE RATE LIMIT - PASTIKAN reposition
                    cd_system.handle_rate_limit(retry_time)
                    stats['rate_limits'] += 1
                    processed = True
                    break
                
                else:
                    print("   ❌ Send failed")
                    time.sleep(2)
                    processed = True
                    break
            
            if not processed:
                time.sleep(3)
            
            # Stats
            if stats['sent'] > 0 and stats['sent'] % 3 == 0:
                elapsed = time.time() - stats['start_time']
                rate = (stats['sent'] / elapsed) * 60 if elapsed > 0 else 0
                efficiency = (stats['sent'] / stats['ai_calls'] * 100) if stats['ai_calls'] > 0 else 0
                
                print(f"\n📊 FIXED STATS")
                print(f"   ✅ Sent: {stats['sent']}")
                print(f"   🤖 AI Calls: {stats['ai_calls']}")
                print(f"   💯 Efficiency: {efficiency:.1f}%")
                print(f"   🔴 Rate Limits: {stats['rate_limits']}")
                print(f"   ⏳ Current Cooldown: {cd_system.current_cooldown:.1f}s")
                print(f"   ⚡ Rate: {rate:.1f}/min")
                print("-" * 40)
                
    except KeyboardInterrupt:
        print("\n\n🛑 STOPPED")
        
    finally:
        # Save
        with open(HISTORY_FILE, 'w') as f:
            json.dump(replied[-2000:], f)
        
        # Final stats
        elapsed = time.time() - stats['start_time']
        rate = (stats['sent'] / elapsed) * 60 if elapsed > 0 else 0
        efficiency = (stats['sent'] / stats['ai_calls'] * 100) if stats['ai_calls'] > 0 else 0
        
        print(f"\n📈 FINAL REPORT")
        print(f"✅ Sent: {stats['sent']}")
        print(f"🤖 AI Calls: {stats['ai_calls']}")
        print(f"💯 Efficiency: {efficiency:.1f}%")
        print(f"🔴 Rate Limits: {stats['rate_limits']}")
        print(f"⏳ Final Cooldown: {cd_system.current_cooldown:.1f}s")
        print(f"⚡ Rate: {rate:.1f}/min")

if __name__ == "__main__":
    main()
