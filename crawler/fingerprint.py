"""Randomized browser fingerprint generation (split from crawl.py)."""
import time
import random
import logging

logger = logging.getLogger('crawler.fingerprint')


def generate_random_language():
    """
    Generate random European language with 80% French variants
    
    Quality values (q-values) indicate preference order:
    - 1.0 (default, omitted): highest preference
    - 0.9-0.7: secondary preferences
    - 0.6-0.4: tertiary preferences
    
    Randomizing q-values makes fingerprinting harder and mimics natural browser variations.
    """
    
    def randomize_q(base):
        """Add small random variation to quality value (±0.05)"""
        variation = random.uniform(-0.05, 0.05)
        return max(0.1, min(1.0, base + variation))  # Keep between 0.1 and 1.0
    
    def build_lang_string(langs_with_q):
        """Build language string with randomized q-values"""
        parts = []
        for i, (lang, base_q) in enumerate(langs_with_q):
            if i == 0:
                # First language typically has no q-value (implicit 1.0)
                # But sometimes it does - 30% chance
                if random.random() < 0.3:
                    q = randomize_q(0.98)
                    parts.append(f'{lang};q={q:.1f}')
                else:
                    parts.append(lang)
            else:
                q = randomize_q(base_q)
                parts.append(f'{lang};q={q:.1f}')
        return ','.join(parts)
    
    # French variants (80% weight) - defined as (language, base_quality)
    french_language_templates = [
        # France
        [('fr-FR', 1.0), ('fr', 0.9), ('en', 0.8)],
        [('fr-FR', 1.0), ('fr', 0.9), ('en-US', 0.8), ('en', 0.7)],
        [('fr', 1.0), ('fr-FR', 0.95), ('en', 0.8)],
        [('fr-FR', 1.0), ('en', 0.7)],
        # Belgium
        [('fr-BE', 1.0), ('fr', 0.9), ('nl', 0.8), ('en', 0.7)],
        [('fr-BE', 1.0), ('fr', 0.9), ('nl-BE', 0.85), ('nl', 0.8), ('en', 0.7)],
        # Switzerland
        [('fr-CH', 1.0), ('fr', 0.9), ('de', 0.8), ('it', 0.7), ('en', 0.6)],
        [('fr-CH', 1.0), ('fr', 0.95), ('de-CH', 0.85), ('de', 0.8), ('en', 0.6)],
        # Canada
        [('fr-CA', 1.0), ('fr', 0.9), ('en-CA', 0.8), ('en', 0.7)],
        [('fr-CA', 1.0), ('fr', 0.95), ('en', 0.75)],
        [('fr', 1.0), ('fr-CA', 0.95), ('en-CA', 0.8), ('en-US', 0.75), ('en', 0.7)],
        # Luxembourg
        [('fr-LU', 1.0), ('fr', 0.9), ('de', 0.85), ('en', 0.7)],
        [('fr-LU', 1.0), ('fr', 0.95), ('de-LU', 0.9), ('de', 0.85), ('en', 0.7)],
        # Monaco
        [('fr-MC', 1.0), ('fr', 0.9), ('it', 0.8), ('en', 0.7)],
        [('fr-MC', 1.0), ('fr', 0.95), ('en', 0.75)],
    ]
    
    # Other European languages (20% weight)
    other_language_templates = [
        # Germany
        [('de-DE', 1.0), ('de', 0.9), ('en', 0.8)],
        [('de-DE', 1.0), ('de', 0.9), ('en-US', 0.8), ('en', 0.7)],
        [('de', 1.0), ('de-DE', 0.95), ('en', 0.8)],
        # Austria
        [('de-AT', 1.0), ('de', 0.9), ('en', 0.8)],
        [('de-AT', 1.0), ('de', 0.95), ('en-GB', 0.8), ('en', 0.75)],
        # Switzerland (German)
        [('de-CH', 1.0), ('de', 0.9), ('fr', 0.8), ('it', 0.7), ('en', 0.6)],
        [('de-CH', 1.0), ('de', 0.95), ('fr-CH', 0.85), ('fr', 0.8), ('en', 0.6)],
        # Spain
        [('es-ES', 1.0), ('es', 0.9), ('ca', 0.8), ('en', 0.7)],
        [('es-ES', 1.0), ('es', 0.95), ('en', 0.8)],
        [('es', 1.0), ('es-ES', 0.95), ('en-US', 0.8), ('en', 0.75)],
        # Italy
        [('it-IT', 1.0), ('it', 0.9), ('en', 0.8)],
        [('it', 1.0), ('it-IT', 0.95), ('en-US', 0.8), ('en', 0.75)],
        # Switzerland (Italian)
        [('it-CH', 1.0), ('it', 0.9), ('de', 0.8), ('fr', 0.7), ('en', 0.6)],
        # Portugal
        [('pt-PT', 1.0), ('pt', 0.9), ('en', 0.8)],
        [('pt', 1.0), ('pt-PT', 0.95), ('en-GB', 0.8), ('en', 0.75)],
        # Netherlands
        [('nl-NL', 1.0), ('nl', 0.9), ('en', 0.85)],
        [('nl', 1.0), ('nl-NL', 0.95), ('en-US', 0.85), ('en', 0.8)],
        # Belgium (Flemish)
        [('nl-BE', 1.0), ('nl', 0.9), ('fr', 0.8), ('en', 0.7)],
        [('nl-BE', 1.0), ('nl', 0.95), ('fr-BE', 0.85), ('fr', 0.8), ('en', 0.7)],
        # Poland
        [('pl-PL', 1.0), ('pl', 0.9), ('en', 0.8)],
        [('pl', 1.0), ('pl-PL', 0.95), ('en-US', 0.8), ('en', 0.75)],
        # Sweden
        [('sv-SE', 1.0), ('sv', 0.9), ('en', 0.85)],
        [('sv', 1.0), ('sv-SE', 0.95), ('en-GB', 0.85), ('en', 0.8)],
        # Denmark
        [('da-DK', 1.0), ('da', 0.9), ('en', 0.85)],
        [('da', 1.0), ('da-DK', 0.95), ('en-US', 0.85), ('en', 0.8)],
        # Norway
        [('no-NO', 1.0), ('no', 0.9), ('nb', 0.85), ('en', 0.8)],
        [('nb-NO', 1.0), ('nb', 0.95), ('no', 0.9), ('en', 0.8)],
        # Finland
        [('fi-FI', 1.0), ('fi', 0.9), ('sv', 0.8), ('en', 0.75)],
        [('fi', 1.0), ('fi-FI', 0.95), ('sv-FI', 0.85), ('sv', 0.8), ('en', 0.7)],
        # Czech Republic
        [('cs-CZ', 1.0), ('cs', 0.9), ('en', 0.8)],
        [('cs', 1.0), ('cs-CZ', 0.95), ('sk', 0.85), ('en', 0.8)],
        # Hungary
        [('hu-HU', 1.0), ('hu', 0.9), ('en', 0.8)],
        [('hu', 1.0), ('hu-HU', 0.95), ('en-US', 0.8), ('en', 0.75)],
        # Romania
        [('ro-RO', 1.0), ('ro', 0.9), ('en', 0.8)],
        [('ro', 1.0), ('ro-RO', 0.95), ('en-GB', 0.8), ('en', 0.75)],
        # Greece
        [('el-GR', 1.0), ('el', 0.9), ('en', 0.8)],
        [('el', 1.0), ('el-GR', 0.95), ('en-US', 0.8), ('en', 0.75)],
        # Slovakia
        [('sk-SK', 1.0), ('sk', 0.9), ('cs', 0.85), ('en', 0.75)],
        [('sk', 1.0), ('sk-SK', 0.95), ('cs', 0.85), ('en', 0.8)],
        # Bulgaria
        [('bg-BG', 1.0), ('bg', 0.9), ('en', 0.8)],
        # Croatia
        [('hr-HR', 1.0), ('hr', 0.9), ('en', 0.8)],
        # Slovenia
        [('sl-SI', 1.0), ('sl', 0.9), ('en', 0.8)],
        # Estonia
        [('et-EE', 1.0), ('et', 0.9), ('en', 0.85)],
        # Latvia
        [('lv-LV', 1.0), ('lv', 0.9), ('en', 0.85)],
        # Lithuania
        [('lt-LT', 1.0), ('lt', 0.9), ('en', 0.85)],
    ]
    
    # 80% French, 20% other European
    if random.random() < 0.8:
        template = random.choice(french_language_templates)
    else:
        template = random.choice(other_language_templates)
    
    return build_lang_string(template)


def generate_random_hardware():
    """
    Generate random hardware specs (CPU cores, RAM, touch) for anti-fingerprinting
    
    Returns a dict with:
    - hardwareConcurrency: CPU core count
    - deviceMemory: RAM in GB
    - maxTouchPoints: touch capability
    """
    
    # Realistic hardware combinations
    # Format: (cores, ram_gb, touch_points, weight)
    hardware_configs = [
        # Budget laptops
        (2, 4, 0, 10),
        (4, 4, 0, 15),
        (4, 8, 0, 20),
        
        # Mid-range laptops/desktops
        (4, 8, 0, 20),
        (6, 8, 0, 12),
        (8, 8, 0, 15),
        (8, 16, 0, 15),
        
        # High-end desktops
        (12, 16, 0, 8),
        (16, 16, 0, 5),
        (16, 32, 0, 3),
        (24, 32, 0, 2),
        (32, 64, 0, 1),
        
        # Touch-enabled devices (laptops/2-in-1s)
        (4, 8, 10, 5),
        (4, 8, 5, 3),
        (8, 16, 10, 3),
        (8, 16, 5, 2),
        
        # Tablets
        (4, 4, 10, 2),
        (8, 8, 10, 2),
    ]
    
    # Weighted random selection
    total_weight = sum(w for _, _, _, w in hardware_configs)
    rand_val = random.uniform(0, total_weight)
    cumulative = 0
    
    for cores, ram, touch, weight in hardware_configs:
        cumulative += weight
        if rand_val <= cumulative:
            return {
                'hardwareConcurrency': cores,
                'deviceMemory': ram,
                'maxTouchPoints': touch
            }
    
    # Fallback
    return {
        'hardwareConcurrency': 8,
        'deviceMemory': 8,
        'maxTouchPoints': 0
    }


def generate_random_connection():
    """
    Generate random network connection properties for Network Information API
    
    Returns a dict with:
    - effectiveType: connection type (slow-2g, 2g, 3g, 4g, 5g)
    - rtt: round-trip time in ms
    - downlink: download speed in Mbps
    - saveData: data saver mode
    """
    
    # Realistic connection types with typical characteristics
    # Format: (type, rtt_range, downlink_range, weight)
    connection_configs = [
        # 4G (most common)
        ('4g', (50, 150), (5, 20), 45),
        ('4g', (40, 100), (10, 30), 25),
        
        # WiFi (fast)
        ('4g', (20, 50), (20, 100), 15),
        
        # 3G (older networks)
        ('3g', (200, 400), (1, 5), 5),
        
        # 5G (newer devices)
        ('4g', (10, 40), (30, 150), 8),
        
        # Slow connections
        ('3g', (300, 600), (0.5, 2), 2),
    ]
    
    # Weighted random selection
    total_weight = sum(w for _, _, _, w in connection_configs)
    rand_val = random.uniform(0, total_weight)
    cumulative = 0
    
    for conn_type, rtt_range, downlink_range, weight in connection_configs:
        cumulative += weight
        if rand_val <= cumulative:
            rtt = random.randint(rtt_range[0], rtt_range[1])
            downlink = round(random.uniform(downlink_range[0], downlink_range[1]), 1)
            save_data = random.random() < 0.1  # 10% enable data saver
            
            return {
                'effectiveType': conn_type,
                'rtt': rtt,
                'downlink': downlink,
                'saveData': save_data
            }
    
    # Fallback
    return {
        'effectiveType': '4g',
        'rtt': 100,
        'downlink': 10.0,
        'saveData': False
    }


def get_timezone_for_language(language):
    """
    Map language/region to realistic timezone offset
    French-heavy biased but with realistic distribution
    
    Returns timezone offset in minutes (negative is west of UTC)
    """
    # Parse language code (e.g., "fr-FR" -> "fr")
    lang_code = language.split('-')[0].split(',')[0].lower()
    
    # Map languages to common timezone offsets (in minutes)
    # European timezones (-60 to +180 minutes)
    timezone_map = {
        'fr': [-60, 60, 120],  # France (CET/CEST)
        'de': [60, 120],  # Germany (CET/CEST)
        'it': [60, 120],  # Italy
        'es': [60, 120],  # Spain
        'pt': [0, 60],  # Portugal
        'nl': [60, 120],  # Netherlands
        'be': [60, 120],  # Belgium
        'pl': [60, 120],  # Poland
        'en': [0, 60, -300, -360, -480, 600],  # UK, US East, US Central, US West, Australia
        'ru': [180, 240, 300],  # Russia (multiple zones)
        'ar': [180],  # Arabic countries
        'zh': [480],  # China
        'ja': [540],  # Japan
        'ko': [540],  # Korea
    }
    
    if lang_code in timezone_map:
        return random.choice(timezone_map[lang_code])
    
    # Default to Central European Time
    return random.choice([60, 120])


def generate_random_battery():
    """
    Generate random battery status for realistic fingerprinting
    
    Returns a dict with realistic battery properties
    """
    # Realistic battery scenarios
    charging = random.choice([True, False, False, False])  # 25% charging
    
    if charging:
        level = random.uniform(0.2, 0.95)  # Charging devices typically not full
        chargingTime = random.randint(1800, 14400)  # 30 min to 4 hours
        dischargingTime = float('inf')
    else:
        level = random.uniform(0.3, 1.0)  # Not charging, various levels
        chargingTime = float('inf')
        dischargingTime = random.randint(3600, 36000)  # 1 to 10 hours
    
    return {
        'charging': charging,
        'chargingTime': chargingTime,
        'dischargingTime': dischargingTime,
        'level': round(level, 2)
    }


def generate_random_media_devices():
    """
    Generate random media devices list for realistic fingerprinting
    
    Returns a list of realistic media device configurations
    """
    devices = []
    
    # Massively expanded camera configurations
    cameras = [
        # Webcams
        {'kind': 'videoinput', 'label': 'HD WebCam (05ac:8514)', 'deviceId': ''},
        {'kind': 'videoinput', 'label': 'FaceTime HD Camera', 'deviceId': ''},
        {'kind': 'videoinput', 'label': 'Integrated Camera (04f2:b604)', 'deviceId': ''},
        {'kind': 'videoinput', 'label': 'USB2.0 HD UVC WebCam', 'deviceId': ''},
        {'kind': 'videoinput', 'label': 'Logitech HD Webcam C525', 'deviceId': ''},
        {'kind': 'videoinput', 'label': 'Logitech HD Pro Webcam C920', 'deviceId': ''},
        {'kind': 'videoinput', 'label': 'Logitech Webcam C930e', 'deviceId': ''},
        {'kind': 'videoinput', 'label': 'Logitech BRIO Ultra HD', 'deviceId': ''},
        {'kind': 'videoinput', 'label': 'Logitech StreamCam', 'deviceId': ''},
        {'kind': 'videoinput', 'label': 'Microsoft LifeCam HD-3000', 'deviceId': ''},
        {'kind': 'videoinput', 'label': 'Microsoft LifeCam Studio', 'deviceId': ''},
        {'kind': 'videoinput', 'label': 'Microsoft LifeCam Cinema', 'deviceId': ''},
        {'kind': 'videoinput', 'label': 'Razer Kiyo', 'deviceId': ''},
        {'kind': 'videoinput', 'label': 'Razer Kiyo Pro', 'deviceId': ''},
        {'kind': 'videoinput', 'label': 'Creative Live! Cam Sync HD', 'deviceId': ''},
        {'kind': 'videoinput', 'label': 'HD Pro Webcam C920', 'deviceId': ''},
        {'kind': 'videoinput', 'label': 'HD Webcam C615', 'deviceId': ''},
        {'kind': 'videoinput', 'label': 'USB Camera (046d:0825)', 'deviceId': ''},
        {'kind': 'videoinput', 'label': 'HP HD Camera', 'deviceId': ''},
        {'kind': 'videoinput', 'label': 'HP Wide Vision HD Camera', 'deviceId': ''},
        {'kind': 'videoinput', 'label': 'HP TrueVision HD Camera', 'deviceId': ''},
        {'kind': 'videoinput', 'label': 'Dell UltraSharp Webcam', 'deviceId': ''},
        {'kind': 'videoinput', 'label': 'Lenovo Integrated Camera', 'deviceId': ''},
        {'kind': 'videoinput', 'label': 'ThinkPad Integrated Camera', 'deviceId': ''},
        {'kind': 'videoinput', 'label': 'ASUS USB2.0 WebCam', 'deviceId': ''},
        {'kind': 'videoinput', 'label': 'Acer Crystal Eye webcam', 'deviceId': ''},
        {'kind': 'videoinput', 'label': 'Sony Visual Communication Camera', 'deviceId': ''},
        {'kind': 'videoinput', 'label': 'Elgato Facecam', 'deviceId': ''},
        {'kind': 'videoinput', 'label': 'AVerMedia Live Streamer CAM 313', 'deviceId': ''},
        {'kind': 'videoinput', 'label': 'Canon EOS Webcam Utility', 'deviceId': ''},
        {'kind': 'videoinput', 'label': 'Panasonic HD Camera', 'deviceId': ''},
    ]
    
    # Massively expanded microphone configurations
    microphones = [
        {'kind': 'audioinput', 'label': 'Microphone (Realtek High Definition Audio)', 'deviceId': ''},
        {'kind': 'audioinput', 'label': 'Microphone (Realtek(R) Audio)', 'deviceId': ''},
        {'kind': 'audioinput', 'label': 'Built-in Microphone', 'deviceId': ''},
        {'kind': 'audioinput', 'label': 'Internal Microphone (Built-in)', 'deviceId': ''},
        {'kind': 'audioinput', 'label': 'Microphone Array (Intel Smart Sound Technology)', 'deviceId': ''},
        {'kind': 'audioinput', 'label': 'Microphone Array (Intel SST)', 'deviceId': ''},
        {'kind': 'audioinput', 'label': 'Microphone Array (Realtek Audio)', 'deviceId': ''},
        {'kind': 'audioinput', 'label': 'Microphone (NVIDIA High Definition Audio)', 'deviceId': ''},
        {'kind': 'audioinput', 'label': 'Microphone (USB Audio Device)', 'deviceId': ''},
        {'kind': 'audioinput', 'label': 'Blue Yeti Microphone', 'deviceId': ''},
        {'kind': 'audioinput', 'label': 'Blue Snowball', 'deviceId': ''},
        {'kind': 'audioinput', 'label': 'HyperX QuadCast', 'deviceId': ''},
        {'kind': 'audioinput', 'label': 'Razer Seiren Mini', 'deviceId': ''},
        {'kind': 'audioinput', 'label': 'Audio-Technica AT2020USB+', 'deviceId': ''},
        {'kind': 'audioinput', 'label': 'Rode NT-USB Mini', 'deviceId': ''},
        {'kind': 'audioinput', 'label': 'Shure MV7', 'deviceId': ''},
        {'kind': 'audioinput', 'label': 'Elgato Wave:3', 'deviceId': ''},
        {'kind': 'audioinput', 'label': 'SteelSeries Arctis Pro', 'deviceId': ''},
        {'kind': 'audioinput', 'label': 'Logitech USB Headset', 'deviceId': ''},
        {'kind': 'audioinput', 'label': 'Jabra Evolve 75', 'deviceId': ''},
        {'kind': 'audioinput', 'label': 'Plantronics Blackwire 5220', 'deviceId': ''},
        {'kind': 'audioinput', 'label': 'Sennheiser SC 60', 'deviceId': ''},
        {'kind': 'audioinput', 'label': 'AirPods Pro', 'deviceId': ''},
        {'kind': 'audioinput', 'label': 'AirPods (2nd generation)', 'deviceId': ''},
        {'kind': 'audioinput', 'label': 'Sony WH-1000XM4', 'deviceId': ''},
        {'kind': 'audioinput', 'label': 'Bose QuietComfort 35', 'deviceId': ''},
        {'kind': 'audioinput', 'label': 'Default - Microphone (Conexant ISST Audio)', 'deviceId': ''},
        {'kind': 'audioinput', 'label': 'Front Microphone (IDT High Definition Audio CODEC)', 'deviceId': ''},
    ]
    
    # Massively expanded speaker configurations  
    speakers = [
        {'kind': 'audiooutput', 'label': 'Speakers (Realtek High Definition Audio)', 'deviceId': ''},
        {'kind': 'audiooutput', 'label': 'Speakers (Realtek(R) Audio)', 'deviceId': ''},
        {'kind': 'audiooutput', 'label': 'Built-in Output', 'deviceId': ''},
        {'kind': 'audiooutput', 'label': 'Built-in Speakers', 'deviceId': ''},
        {'kind': 'audiooutput', 'label': 'Speakers / Headphones (Realtek Audio)', 'deviceId': ''},
        {'kind': 'audiooutput', 'label': 'Speakers (NVIDIA High Definition Audio)', 'deviceId': ''},
        {'kind': 'audiooutput', 'label': 'Speakers (Intel Display Audio)', 'deviceId': ''},
        {'kind': 'audiooutput', 'label': 'Speakers (AMD High Definition Audio)', 'deviceId': ''},
        {'kind': 'audiooutput', 'label': 'Headphones (USB Audio Device)', 'deviceId': ''},
        {'kind': 'audiooutput', 'label': 'Logitech G Pro X Gaming Headset', 'deviceId': ''},
        {'kind': 'audiooutput', 'label': 'SteelSeries Arctis 7', 'deviceId': ''},
        {'kind': 'audiooutput', 'label': 'HyperX Cloud II', 'deviceId': ''},
        {'kind': 'audiooutput', 'label': 'Razer Kraken', 'deviceId': ''},
        {'kind': 'audiooutput', 'label': 'Corsair VOID RGB Elite', 'deviceId': ''},
        {'kind': 'audiooutput', 'label': 'Sennheiser GSP 600', 'deviceId': ''},
        {'kind': 'audiooutput', 'label': 'Audio-Technica ATH-M50x', 'deviceId': ''},
        {'kind': 'audiooutput', 'label': 'Sony WH-1000XM4', 'deviceId': ''},
        {'kind': 'audiooutput', 'label': 'Bose QuietComfort 35 II', 'deviceId': ''},
        {'kind': 'audiooutput', 'label': 'AirPods Pro', 'deviceId': ''},
        {'kind': 'audiooutput', 'label': 'AirPods Max', 'deviceId': ''},
        {'kind': 'audiooutput', 'label': 'Beats Studio3 Wireless', 'deviceId': ''},
        {'kind': 'audiooutput', 'label': 'JBL Quantum 800', 'deviceId': ''},
        {'kind': 'audiooutput', 'label': 'Astro A50', 'deviceId': ''},
        {'kind': 'audiooutput', 'label': 'Turtle Beach Stealth 700', 'deviceId': ''},
        {'kind': 'audiooutput', 'label': 'Samsung Galaxy Buds Pro', 'deviceId': ''},
        {'kind': 'audiooutput', 'label': 'Jabra Elite 85h', 'deviceId': ''},
        {'kind': 'audiooutput', 'label': 'LG TONE Free', 'deviceId': ''},
        {'kind': 'audiooutput', 'label': 'Default - Speakers (IDT High Definition Audio CODEC)', 'deviceId': ''},
        {'kind': 'audiooutput', 'label': 'Speakers (Conexant ISST Audio)', 'deviceId': ''},
    ]
    
    # Most devices have at least 1 camera, 1 mic, 1 speaker
    # Some have multiple, some laptops without camera
    has_camera = random.random() > 0.1  # 90% have camera
    num_mics = random.choice([1, 1, 1, 1, 2, 2, 3])  # Mostly 1, sometimes 2-3
    num_speakers = random.choice([1, 1, 1, 2, 2, 3])  # Mostly 1, sometimes 2-3
    
    if has_camera:
        num_cameras = random.choice([1, 1, 1, 1, 1, 2])  # Mostly 1, rarely 2
        for _ in range(num_cameras):
            camera = random.choice(cameras).copy()
            camera['deviceId'] = ''.join(random.choices('0123456789abcdef', k=64))
            devices.append(camera)
    
    for _ in range(num_mics):
        mic = random.choice(microphones).copy()
        mic['deviceId'] = ''.join(random.choices('0123456789abcdef', k=64))
        devices.append(mic)
    
    for _ in range(num_speakers):
        speaker = random.choice(speakers).copy()
        speaker['deviceId'] = ''.join(random.choices('0123456789abcdef', k=64))
        devices.append(speaker)
    
    return devices


def generate_random_fonts():
    """
    Generate a random subset of fonts for font fingerprinting
    
    Returns a list of font names
    """
    # Massively expanded font list with hundreds of options
    all_fonts = [
        # Windows common
        'Arial', 'Arial Black', 'Arial Narrow', 'Calibri', 'Cambria', 'Cambria Math',
        'Candara', 'Comic Sans MS', 'Consolas', 'Constantia', 'Corbel', 'Courier New',
        'Ebrima', 'Franklin Gothic Medium', 'Georgia', 'Impact', 'Lucida Console', 
        'Lucida Sans Unicode', 'Microsoft Sans Serif', 'MS Gothic', 'MS PGothic', 
        'MS UI Gothic', 'Palatino Linotype', 'Segoe Print', 'Segoe Script', 'Segoe UI', 
        'Segoe UI Black', 'Segoe UI Historic', 'Segoe UI Emoji', 'Segoe UI Symbol',
        'Tahoma', 'Times New Roman', 'Trebuchet MS', 'Verdana', 'Webdings', 'Wingdings',
        'Sylfaen', 'Symbol', 'Marlett', 'Microsoft YaHei', 'Microsoft JhengHei',
        'Malgun Gothic', 'Leelawadee UI', 'Javanese Text', 'Myanmar Text', 'Nirmala UI',
        'Gadugi', 'MV Boli', 'Mongolian Baiti', 'Microsoft PhagsPa', 'Microsoft Tai Le',
        'Microsoft Himalaya', 'Microsoft New Tai Lue', 'Microsoft Yi Baiti', 'Sitka',
        'Bahnschrift', 'Yu Gothic', 'Yu Gothic UI', 'Yu Mincho', 'HoloLens MDL2 Assets',
        'Ink Free', 'Gabriola', 'Centaur', 'Century', 'Rockwell', 'Bookman Old Style',
        'Bradley Hand ITC', 'Californian FB', 'Castellar', 'Chiller', 'Colonna MT',
        'Cooper Black', 'Copperplate Gothic', 'Curlz MT', 'Edwardian Script ITC',
        'Engravers MT', 'Felix Titling', 'Forte', 'French Script MT', 'Freestyle Script',
        'Garamond', 'Gigi', 'Gill Sans MT', 'Gloucester MT', 'Goudy Old Style',
        'Goudy Stout', 'Haettenschweiler', 'Harlow Solid Italic', 'Harrington',
        'High Tower Text', 'Imprint MT Shadow', 'Jokerman', 'Juice ITC', 'Kristen ITC',
        'Kunstler Script', 'Wide Latin', 'Lucida Bright', 'Lucida Calligraphy',
        'Lucida Fax', 'Lucida Handwriting', 'Lucida Sans', 'Lucida Sans Typewriter',
        'Magneto', 'Maiandra GD', 'Matura MT Script Capitals', 'Mistral', 'Modern No. 20',
        'Monotype Corsiva', 'Niagara Engraved', 'Niagara Solid', 'OCR A Extended',
        'Old English Text MT', 'Onyx', 'Palace Script MT', 'Papyrus', 'Parchment',
        'Perpetua', 'Perpetua Titling MT', 'Playbill', 'Poor Richard', 'Pristina',
        'Rage Italic', 'Ravie', 'Rockwell Extra Bold', 'Script MT Bold', 'Showcard Gothic',
        'Snap ITC', 'Stencil', 'Tempus Sans ITC', 'Tw Cen MT', 'Viner Hand ITC',
        'Vivaldi', 'Vladimir Script',
        
        # macOS common
        'American Typewriter', 'Andale Mono', 'Apple Chancery', 'Apple Color Emoji',
        'Apple SD Gothic Neo', 'Apple Symbols', 'AppleGothic', 'AppleMyungjo',
        'Arial Hebrew', 'Arial Rounded MT Bold', 'Arial Unicode MS', 'Avenir', 
        'Avenir Next', 'Avenir Next Condensed', 'Baskerville', 'Big Caslon', 
        'Bodoni 72', 'Bodoni 72 Oldstyle', 'Bodoni 72 Smallcaps', 'Bodoni Ornaments',
        'Bradley Hand', 'Brush Script MT', 'Chalkboard', 'Chalkboard SE', 'Chalkduster',
        'Charter', 'Cochin', 'Comic Sans MS', 'Copperplate', 'Courier', 'Courier New',
        'Damascus', 'Devanagari MT', 'Devanagari Sangam MN', 'Didot', 'DIN Alternate',
        'DIN Condensed', 'Euphemia UCAS', 'Futura', 'Galvji', 'Geeza Pro', 'Geneva',
        'Georgia', 'Gill Sans', 'Gujarati MT', 'Gujarati Sangam MN', 'Gurmukhi MN',
        'Gurmukhi MT', 'Gurmukhi Sangam MN', 'Heiti SC', 'Heiti TC', 'Helvetica',
        'Helvetica Neue', 'Herculanum', 'Hiragino Maru Gothic Pro', 'Hiragino Mincho ProN',
        'Hiragino Sans', 'Hiragino Sans GB', 'Hoefler Text', 'Impact', 'Iowan Old Style',
        'Kailasa', 'Kannada MN', 'Kannada Sangam MN', 'Kefa', 'Khmer MN', 'Khmer Sangam MN',
        'Kohinoor Bangla', 'Kohinoor Devanagari', 'Kohinoor Gujarati', 'Kohinoor Telugu',
        'Kokonor', 'Krungthep', 'KufiStandardGK', 'Lao MN', 'Lao Sangam MN', 'Lucida Grande',
        'Luminari', 'Malayalam MN', 'Malayalam Sangam MN', 'Marion', 'Marker Felt',
        'Menlo', 'Microsoft Sans Serif', 'Mishafi', 'Monaco', 'Mshtakan', 'Muna',
        'Myanmar MN', 'Myanmar Sangam MN', 'Nadeem', 'New Peninim MT', 'Noteworthy',
        'Noto Nastaliq Urdu', 'Optima', 'Oriya MN', 'Oriya Sangam MN', 'Palatino',
        'Papyrus', 'Party LET', 'Phosphate', 'PingFang HK', 'PingFang SC', 'PingFang TC',
        'Plantagenet Cherokee', 'PT Mono', 'PT Sans', 'PT Sans Caption', 'PT Sans Narrow',
        'PT Serif', 'PT Serif Caption', 'Raanana', 'Rockwell', 'Sana', 'Sathu', 'Savoye LET',
        'Seravek', 'Shree Devanagari 714', 'SignPainter', 'Silom', 'Sinhala MN',
        'Sinhala Sangam MN', 'Skia', 'Snell Roundhand', 'Songti SC', 'Songti TC',
        'STFangsong', 'STHeiti', 'STIX Two Math', 'STIX Two Text', 'STIXGeneral',
        'STIXIntegralsD', 'STIXIntegralsSm', 'STIXIntegralsUp', 'STIXIntegralsUpD',
        'STIXIntegralsUpSm', 'STIXNonUnicode', 'STIXSizeFiveSym', 'STIXSizeFourSym',
        'STIXSizeOneSym', 'STIXSizeThreeSym', 'STIXSizeTwoSym', 'STIXVariants', 'STKaiti',
        'STSong', 'Sukhumvit Set', 'Superclarendon', 'Symbol', 'Tahoma', 'Tamil MN',
        'Tamil Sangam MN', 'Telugu MN', 'Telugu Sangam MN', 'Thonburi', 'Times',
        'Times New Roman', 'Trattatello', 'Trebuchet MS', 'Verdana', 'Waseem', 'Webdings',
        'Wingdings', 'Wingdings 2', 'Wingdings 3', 'Zapf Dingbats', 'Zapfino',
        'SF Pro Display', 'SF Pro Text', 'SF Pro Rounded', 'SF Mono', 'SF Compact Display',
        'SF Compact Text', 'SF Compact Rounded', 'New York', 'New York Small', 'New York Medium',
        'New York Large', 'New York Extra Large', '.AppleSystemUIFont',
        
        # Linux common
        'DejaVu Sans', 'DejaVu Sans Mono', 'DejaVu Serif', 'DejaVu Sans Condensed',
        'DejaVu Serif Condensed', 'DejaVu Math TeX Gyre', 'Droid Sans', 'Droid Sans Mono',
        'Droid Serif', 'FreeSans', 'FreeSerif', 'FreeMono', 'Liberation Sans', 
        'Liberation Sans Narrow', 'Liberation Serif', 'Liberation Mono', 'Nimbus Mono PS',
        'Nimbus Roman', 'Nimbus Sans', 'Nimbus Sans Narrow', 'Noto Sans', 'Noto Sans CJK',
        'Noto Sans Mono', 'Noto Serif', 'Noto Serif CJK', 'Noto Color Emoji', 'Noto Emoji',
        'Noto Sans Arabic', 'Noto Sans Armenian', 'Noto Sans Bengali', 'Noto Sans Cherokee',
        'Noto Sans Devanagari', 'Noto Sans Ethiopic', 'Noto Sans Georgian', 'Noto Sans Gujarati',
        'Noto Sans Gurmukhi', 'Noto Sans Hebrew', 'Noto Sans JP', 'Noto Sans KR',
        'Noto Sans Kannada', 'Noto Sans Khmer', 'Noto Sans Lao', 'Noto Sans Malayalam',
        'Noto Sans Myanmar', 'Noto Sans Oriya', 'Noto Sans SC', 'Noto Sans Sinhala',
        'Noto Sans Symbols', 'Noto Sans Tamil', 'Noto Sans TC', 'Noto Sans Telugu',
        'Noto Sans Thai', 'Noto Sans Tibetan', 'Ubuntu', 'Ubuntu Condensed', 'Ubuntu Mono',
        'Cantarell', 'C059', 'P052', 'Z003', 'URW Gothic', 'URW Bookman', 'URW Palladio',
        'Standard Symbols PS', 'D050000L', 'Lohit Devanagari', 'Lohit Gujarati',
        'Lohit Tamil', 'Gargi', 'Lohit Bengali', 'Tlwg Mono', 'Waree', 'Sawasdee',
        'Kacst', 'Umpush', 'Norasi', 'Purisa', 'Saab', 'OpenSymbol', 'Bitstream Charter',
        'Century Schoolbook L', 'Courier 10 Pitch', 'Dingbats', 'Carlito', 'Caladea',
        'Chilanka', 'Dyuthi', 'Karumbi', 'Keraleeyam', 'Manjari', 'Meera', 'Rachana',
        'Suruma', 'Uroob', 'Abyssinica SIL', 'Padauk', 'Pothana2000', 'Vemana2000',
        'Gubbi', 'Navilu', 'Sahadeva', 'Tibetan Machine Uni', 'Khmer OS', 'Phetsarath OT',
        'Saysettha OT', 'Loma', 'Tlwg Typewriter', 'Tlwg Typist', 'Tlwg Typo',
        
        # Google Fonts (commonly embedded)
        'Roboto', 'Roboto Condensed', 'Roboto Mono', 'Roboto Slab', 'Open Sans',
        'Open Sans Condensed', 'Lato', 'Montserrat', 'Source Sans Pro', 'Raleway',
        'PT Sans', 'PT Serif', 'Ubuntu', 'Merriweather', 'Playfair Display', 'Nunito',
        'Noto Sans', 'Noto Serif', 'Poppins', 'Oswald', 'Slabo 27px', 'Slabo 13px',
        'Fira Sans', 'Fira Sans Condensed', 'Crimson Text', 'Mukta', 'Titillium Web',
        'Hind', 'Rubik', 'Work Sans', 'Karla', 'Oxygen', 'Inconsolata', 'Nunito Sans',
        'Quicksand', 'Yanone Kaffeesatz', 'Arimo', 'Cabin', 'Varela Round', 'Bitter',
        'Heebo', 'Source Code Pro', 'Fjalla One', 'Dosis', 'Dancing Script', 'Lobster',
        'Anton', 'Barlow', 'Barlow Condensed', 'Prompt', 'Comfortaa', 'Abel', 'Archivo',
        'Play', 'Exo 2', 'Josefin Sans', 'Questrial', 'Abril Fatface', 'Cairo', 'Signika',
        'Maven Pro', 'Libre Franklin', 'Arvo', 'Catamaran', 'Zilla Slab', 'IBM Plex Sans',
        'IBM Plex Serif', 'IBM Plex Mono', 'Shadows Into Light', 'Pacifico', 'Amatic SC',
        'Indie Flower', 'Permanent Marker', 'Righteous', 'Fredoka One', 'Bebas Neue',
        'Alfa Slab One', 'Archivo Black', 'Cinzel', 'Satisfy', 'Cookie', 'Great Vibes',
        'Architects Daughter', 'Sacramento', 'Courgette', 'Kaushan Script', 'Caveat',
    ]
    
    # Randomly include 55-98% of fonts (simulating different OS/installations/embeddings)
    num_fonts = random.randint(int(len(all_fonts) * 0.55), int(len(all_fonts) * 0.98))
    return random.sample(all_fonts, num_fonts)


def generate_random_plugins(browser_type='chrome'):
    """
    Generate randomized browser-specific plugins for fingerprinting diversity
    
    Args:
        browser_type: Browser type (chrome/firefox/edge/chromium) for realistic plugin lists
    
    Returns a JavaScript-ready string representation of plugins array
    PDF plugins are heavily randomized as they're major fingerprinting vectors
    
    30% chance of no plugins (privacy-conscious users)
    50% chance of partial plugins
    20% chance of full plugin list
    """
    
    # 30% chance of no plugins (increasing privacy awareness)
    if random.random() < 0.3:
        return '[]'
    
    plugins = []
    
    # PDF Plugin variations (CRITICAL fingerprinting vector - always present but highly varied)
    pdf_plugins = [
        # Chrome variations
        {
            'name': 'Chrome PDF Plugin',
            'filename': 'internal-pdf-viewer',
            'description': 'Portable Document Format',
            'version': random.choice(['1.0', '1.1', '1.15', '2.0', '2.1']),
            'mimeTypes': [{'type': 'application/x-google-chrome-pdf', 'suffixes': 'pdf'}]
        },
        {
            'name': 'Chrome PDF Viewer',
            'filename': f'mhjfbmdgcfjbbpaeojofohoefgiehjai',
            'description': random.choice(['', 'Portable Document Format', 'PDF Viewer']),
            'version': random.choice(['1.0', '1.2', '1.5', '2.0']),
            'mimeTypes': [{'type': 'application/pdf', 'suffixes': 'pdf'}]
        },
        {
            'name': 'Chromium PDF Viewer',
            'filename': 'internal-pdf-viewer',
            'description': 'Portable Document Format',
            'version': random.choice(['1.0', '1.1', '2.0']),
            'mimeTypes': [{'type': 'application/pdf', 'suffixes': 'pdf'}]
        },
        # Edge variations  
        {
            'name': 'Microsoft Edge PDF Viewer',
            'filename': 'edge-pdf-viewer',
            'description': 'Portable Document Format',
            'version': random.choice(['1.0', '1.1', '1.2']),
            'mimeTypes': [{'type': 'application/pdf', 'suffixes': 'pdf'}]
        },
        # Firefox variations
        {
            'name': 'PDF.js',
            'filename': 'pdf.js',
            'description': 'Portable Document Format',
            'version': random.choice(['2.14.305', '2.16.105', '3.0.279', '3.1.81', '3.2.146', '3.3.122', '3.4.120']),
            'mimeTypes': [{'type': 'application/pdf', 'suffixes': 'pdf'}]
        },
    ]
    
    # Browser-specific PDF plugin selection
    if browser_type == 'firefox':
        # Firefox primarily uses PDF.js
        pdf_candidates = [p for p in pdf_plugins if 'PDF.js' in p['name'] or 'Firefox' in p['name']]
        if not pdf_candidates:
            pdf_candidates = [pdf_plugins[4]]  # PDF.js
    elif browser_type == 'edge':
        # Edge has its own PDF viewer and Chrome-based ones
        pdf_candidates = [p for p in pdf_plugins if 'Edge' in p['name'] or 'Chrome' in p['name']]
    elif browser_type == 'chromium':
        # Chromium uses open-source PDF viewers
        pdf_candidates = [p for p in pdf_plugins if 'Chromium' in p['name'] or 'Chrome PDF Plugin' in p['name']]
    else:  # chrome
        # Chrome has various PDF plugins
        pdf_candidates = [p for p in pdf_plugins if 'Chrome' in p['name']]
    
    # Add 1-2 PDF plugins (or 0 if 50% partial plugin mode)
    pdf_chance = random.random()
    if pdf_chance < 0.2:  # 20% - full plugins
        num_pdf = random.choice([1, 2])
    elif pdf_chance < 0.7:  # 50% - partial plugins (1 or 0)
        num_pdf = random.choice([0, 1, 1])
    else:  # 30% already handled above (no plugins at all)
        num_pdf = 1
    
    for _ in range(num_pdf):
        if pdf_candidates:
            plugins.append(random.choice(pdf_candidates))
    
    # Additional plugin types (present on some systems)
    optional_plugins = [
        # Native Client (Chrome)
        {
            'name': 'Native Client',
            'filename': 'internal-nacl-plugin',
            'description': 'Native Client Executable',
            'version': random.choice(['1.0', '1.0.0', '']),
            'mimeTypes': [
                {'type': 'application/x-nacl', 'suffixes': ''},
                {'type': 'application/x-pnacl', 'suffixes': ''}
            ]
        },
        # Widevine (DRM - very common)
        {
            'name': 'Widevine Content Decryption Module',
            'filename': random.choice(['widevinecdmadapter.dll', 'widevinecdm', 'libwidevinecdm.so']),
            'description': 'Enables Widevine licenses for playback of HTML audio/video content.',
            'version': random.choice(['4.10.2209.1', '4.10.2391.0', '4.10.2440.0', '4.10.2449.0', '4.10.2557.0']),
            'mimeTypes': [{'type': 'application/x-ppapi-widevine-cdm', 'suffixes': ''}]
        },
        # Shockwave Flash (legacy, but still on some systems)
        {
            'name': 'Shockwave Flash',
            'filename': random.choice(['pepflashplayer.dll', 'libpepflashplayer.so', 'PepperFlashPlayer.plugin']),
            'description': 'Shockwave Flash',
            'version': random.choice(['32.0.0.465', '32.0.0.453', '32.0.0.445', '32.0.0.438', '32.0.0.371']),
            'mimeTypes': [{'type': 'application/x-shockwave-flash', 'suffixes': 'swf'}]
        },
        # Java (legacy)
        {
            'name': 'Java Deployment Toolkit',
            'filename': random.choice(['npdeployJava1.dll', 'libnpjp2.so']),
            'description': random.choice(['Java Deployment Toolkit', 'NPRuntime Script Plug-in Library for Java']),
            'version': random.choice(['11.0.1', '11.0.2', '11.0.11', '1.8.0_311', '1.8.0_301']),
            'mimeTypes': [{'type': 'application/java-deployment-toolkit', 'suffixes': ''}]
        },
        # Chrome Remote Desktop
        {
            'name': 'Chrome Remote Desktop Viewer',
            'filename': 'remoting-host',
            'description': 'Chrome Remote Desktop',
            'version': random.choice(['1.0', '2.0', '']),
            'mimeTypes': [{'type': 'application/vnd.chromium.remoting-viewer', 'suffixes': ''}]
        },
        # Microsoft Silverlight (legacy)
        {
            'name': 'Silverlight Plug-In',
            'filename': random.choice(['npctrl.dll', 'libSilverlight.so']),
            'description': 'Silverlight Plug-In',
            'version': random.choice(['5.1.50918.0', '5.1.50907.0', '5.1.50901.0']),
            'mimeTypes': [{'type': 'application/x-silverlight', 'suffixes': 'xap'}]
        },
    ]
    
    # Randomly add 0-3 optional plugins
    num_optional = random.choice([0, 0, 0, 1, 1, 2, 3])
    if num_optional > 0:
        selected = random.sample(optional_plugins, min(num_optional, len(optional_plugins)))
        plugins.extend(selected)
    
    # Build JavaScript array representation
    js_plugins = []
    for i, plugin in enumerate(plugins):
        mime_objs = []
        for j, mime in enumerate(plugin['mimeTypes']):
            mime_objs.append(f"{j}: {{type: '{mime['type']}', suffixes: '{mime['suffixes']}', description: '{plugin['description']}'}}") 
        
        mime_str = ', '.join(mime_objs)
        
        js_plugin = f'''{{
            {mime_str},
            description: '{plugin['description']}',
            filename: '{plugin['filename']}',
            length: {len(plugin['mimeTypes'])},
            name: '{plugin['name']}'
        }}'''
        js_plugins.append(js_plugin)
    
    return '[' + ','.join(js_plugins) + ']'


def generate_random_webrtc():
    """
    Generate randomized WebRTC local IP addresses for fingerprinting diversity
    
    Returns a dict with realistic local IPs
    """
    # Common private IP ranges
    ip_patterns = [
        # 192.168.x.x (most common home networks)
        lambda: f"192.168.{random.randint(0, 255)}.{random.randint(2, 254)}",
        lambda: f"192.168.1.{random.randint(2, 254)}",
        lambda: f"192.168.0.{random.randint(2, 254)}",
        # 10.x.x.x (large networks, VPNs)
        lambda: f"10.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(2, 254)}",
        lambda: f"10.0.{random.randint(0, 255)}.{random.randint(2, 254)}",
        # 172.16-31.x.x (corporate networks)
        lambda: f"172.{random.randint(16, 31)}.{random.randint(0, 255)}.{random.randint(2, 254)}",
    ]
    
    # Generate 1-3 local IPs (most devices have 1-2)
    num_ips = random.choice([1, 1, 1, 2, 2, 3])
    local_ips = []
    for _ in range(num_ips):
        ip_gen = random.choice(ip_patterns)
        local_ips.append(ip_gen())
    
    # IPv6 addresses (some systems have these)
    has_ipv6 = random.random() < 0.3  # 30% have IPv6
    if has_ipv6:
        # Generate realistic link-local IPv6 (fe80::)
        ipv6_parts = [f"{random.randint(0, 65535):04x}" for _ in range(4)]
        local_ips.append(f"fe80::{':'.join(ipv6_parts)}")
    
    return {
        'localIPs': local_ips,
        'publicIP': f"{random.randint(1, 223)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"
    }


def generate_random_gpu():
    """
    Generate random GPU vendor and renderer strings for WebGL fingerprinting
    Supports multi-GPU configurations (integrated + discrete)
    
    Returns a dict with:
    - vendor: GPU vendor string (parameter 37445)
    - renderer: GPU renderer string (parameter 37446)
    - isMultiGPU: whether this is a multi-GPU system
    """
    
    # Massively expanded GPU configurations (vendor, renderer, is_discrete, weight)
    gpu_configs = [
        # Intel integrated graphics (most common) - HIGH WEIGHT
        ("Intel Inc.", "Intel Iris OpenGL Engine", False, 15),
        ("Intel Inc.", "Intel(R) UHD Graphics 630", False, 20),
        ("Intel Inc.", "Intel(R) UHD Graphics 620", False, 18),
        ("Intel Inc.", "Intel(R) HD Graphics 620", False, 15),
        ("Intel Inc.", "Intel(R) HD Graphics 630", False, 12),
        ("Intel Inc.", "Intel(R) HD Graphics 530", False, 10),
        ("Intel Inc.", "Intel(R) HD Graphics 520", False, 8),
        ("Intel Inc.", "Intel(R) Iris(R) Plus Graphics 640", False, 8),
        ("Intel Inc.", "Intel(R) Iris(R) Plus Graphics 655", False, 8),
        ("Intel Inc.", "Intel(R) Iris(R) Xe Graphics", False, 12),
        ("Intel Inc.", "Intel(R) UHD Graphics 770", False, 10),
        ("Intel Inc.", "Intel(R) UHD Graphics 730", False, 8),
        ("Intel Inc.", "Intel(R) Arc(TM) A770 Graphics", False, 3),
        ("Intel Inc.", "Intel(R) Arc(TM) A750 Graphics", False, 2),
        ("Intel Inc.", "Mesa Intel(R) UHD Graphics 620 (KBL GT2)", False, 8),
        ("Intel Inc.", "Mesa Intel(R) HD Graphics 630 (KBL GT2)", False, 8),
        ("Intel Inc.", "Mesa Intel(R) UHD Graphics (CML GT2)", False, 6),
        ("Intel", "Intel(R) HD Graphics 4000", False, 5),
        ("Intel", "Intel(R) HD Graphics 5500", False, 6),
        ("Intel", "Intel(R) HD Graphics 4600", False, 5),
        ("Intel", "Intel(R) HD Graphics 3000", False, 3),
        ("Intel", "Intel(R) Iris(TM) Graphics 5100", False, 4),
        ("Intel", "Intel(R) Iris(TM) Graphics 6100", False, 4),
        
        # NVIDIA (gaming/professional) - MEDIUM-HIGH WEIGHT
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 1650/PCIe/SSE2", True, 12),
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 1050/PCIe/SSE2", True, 10),
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 1050 Ti/PCIe/SSE2", True, 10),
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 1060/PCIe/SSE2", True, 12),
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 1660/PCIe/SSE2", True, 10),
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 1660 Ti/PCIe/SSE2", True, 12),
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 1660 SUPER/PCIe/SSE2", True, 8),
        ("NVIDIA Corporation", "NVIDIA GeForce RTX 2060/PCIe/SSE2", True, 10),
        ("NVIDIA Corporation", "NVIDIA GeForce RTX 2070/PCIe/SSE2", True, 8),
        ("NVIDIA Corporation", "NVIDIA GeForce RTX 2080/PCIe/SSE2", True, 6),
        ("NVIDIA Corporation", "NVIDIA GeForce RTX 3050/PCIe/SSE2", True, 10),
        ("NVIDIA Corporation", "NVIDIA GeForce RTX 3060/PCIe/SSE2", True, 12),
        ("NVIDIA Corporation", "NVIDIA GeForce RTX 3060 Ti/PCIe/SSE2", True, 10),
        ("NVIDIA Corporation", "NVIDIA GeForce RTX 3070/PCIe/SSE2", True, 10),
        ("NVIDIA Corporation", "NVIDIA GeForce RTX 3070 Ti/PCIe/SSE2", True, 6),
        ("NVIDIA Corporation", "NVIDIA GeForce RTX 3080/PCIe/SSE2", True, 6),
        ("NVIDIA Corporation", "NVIDIA GeForce RTX 4060/PCIe/SSE2", True, 8),
        ("NVIDIA Corporation", "NVIDIA GeForce RTX 4060 Ti/PCIe/SSE2", True, 6),
        ("NVIDIA Corporation", "NVIDIA GeForce RTX 4070/PCIe/SSE2", True, 6),
        ("NVIDIA Corporation", "NVIDIA GeForce RTX 4080/PCIe/SSE2", True, 4),
        ("NVIDIA Corporation", "NVIDIA GeForce RTX 4090/PCIe/SSE2", True, 3),
        ("NVIDIA Corporation", "GeForce GTX 960/PCIe/SSE2", True, 6),
        ("NVIDIA Corporation", "GeForce GTX 970/PCIe/SSE2", True, 6),
        ("NVIDIA Corporation", "GeForce GTX 980/PCIe/SSE2", True, 4),
        ("NVIDIA Corporation", "GeForce GTX 1070/PCIe/SSE2", True, 8),
        ("NVIDIA Corporation", "GeForce GTX 1080/PCIe/SSE2", True, 6),
        ("NVIDIA Corporation", "GeForce GTX 1080 Ti/PCIe/SSE2", True, 5),
        ("NVIDIA Corporation", "GeForce MX150/PCIe/SSE2", True, 8),
        ("NVIDIA Corporation", "GeForce MX250/PCIe/SSE2", True, 8),
        ("NVIDIA Corporation", "GeForce MX350/PCIe/SSE2", True, 6),
        ("NVIDIA Corporation", "GeForce MX450/PCIe/SSE2", True, 6),
        ("NVIDIA Corporation", "GeForce GT 1030/PCIe/SSE2", True, 5),
        ("NVIDIA Corporation", "GeForce GT 730/PCIe/SSE2", True, 4),
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 750 Ti/PCIe/SSE2", True, 4),
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 950/PCIe/SSE2", True, 4),
        ("NVIDIA Corporation", "NVIDIA T400/PCIe/SSE2", True, 3),
        ("NVIDIA Corporation", "NVIDIA T1000/PCIe/SSE2", True, 3),
        ("NVIDIA Corporation", "Quadro P1000/PCIe/SSE2", True, 3),
        ("NVIDIA Corporation", "Quadro P2000/PCIe/SSE2", True, 2),
        
        # AMD Radeon - MEDIUM WEIGHT
        ("AMD", "AMD Radeon(TM) Graphics", False, 15),
        ("AMD", "AMD Radeon(TM) Vega 8 Graphics", False, 12),
        ("AMD", "AMD Radeon(TM) Vega 10 Graphics", False, 10),
        ("AMD", "AMD Radeon(TM) Vega 11 Graphics", False, 8),
        ("AMD", "AMD Radeon(TM) RX Vega 10 Graphics", False, 8),
        ("AMD", "AMD Radeon RX 580 Series", True, 10),
        ("AMD", "AMD Radeon RX 570 Series", True, 8),
        ("AMD", "AMD Radeon RX 5500 XT", True, 8),
        ("AMD", "AMD Radeon RX 5600 XT", True, 8),
        ("AMD", "AMD Radeon RX 5700", True, 8),
        ("AMD", "AMD Radeon RX 5700 XT", True, 8),
        ("AMD", "AMD Radeon RX 6600", True, 8),
        ("AMD", "AMD Radeon RX 6600 XT", True, 8),
        ("AMD", "AMD Radeon RX 6700 XT", True, 8),
        ("AMD", "AMD Radeon RX 6800", True, 6),
        ("AMD", "AMD Radeon RX 6800 XT", True, 5),
        ("AMD", "AMD Radeon RX 6900 XT", True, 4),
        ("AMD", "AMD Radeon RX 7600", True, 6),
        ("AMD", "AMD Radeon RX 7700 XT", True, 5),
        ("AMD", "AMD Radeon RX 7800 XT", True, 4),
        ("AMD", "AMD Radeon RX 7900 XT", True, 3),
        ("AMD", "AMD Radeon RX 7900 XTX", True, 3),
        ("AMD", "AMD Radeon RX 480", True, 6),
        ("AMD", "AMD Radeon RX 470", True, 5),
        ("AMD", "AMD Radeon(TM) 780M", False, 6),
        ("AMD", "AMD Radeon(TM) 680M", False, 5),
        ("AMD", "AMD Radeon(TM) 660M", False, 5),
        ("ATI Technologies Inc.", "AMD Radeon HD 7900 Series", True, 3),
        ("ATI Technologies Inc.", "AMD Radeon R9 200 Series", True, 3),
        ("ATI Technologies Inc.", "AMD Radeon R9 380 Series", True, 3),
        ("ATI Technologies Inc.", "AMD Radeon HD 7700 Series", True, 2),
        
        # Apple Silicon (Mac) - MEDIUM WEIGHT
        ("Apple", "Apple M1", False, 12),
        ("Apple", "Apple M2", False, 10),
        ("Apple", "Apple M3", False, 8),
        ("Apple", "Apple M1 Pro", False, 8),
        ("Apple", "Apple M1 Max", False, 6),
        ("Apple", "Apple M1 Ultra", False, 3),
        ("Apple", "Apple M2 Pro", False, 6),
        ("Apple", "Apple M2 Max", False, 5),
        ("Apple", "Apple M2 Ultra", False, 2),
        ("Apple", "Apple M3 Pro", False, 5),
        ("Apple", "Apple M3 Max", False, 4),
        ("Apple", "AMD Radeon Pro 5500M", True, 4),
        ("Apple", "AMD Radeon Pro 560X", True, 3),
        ("Apple", "AMD Radeon Pro 5300M", True, 3),
        ("Apple", "AMD Radeon Pro 5600M", True, 3),
        ("Apple", "AMD Radeon Pro Vega 20", True, 2),
        
        # Generic/ANGLE (Chrome on Windows) - HIGH WEIGHT
        ("Google Inc. (Intel)", "ANGLE (Intel, Intel(R) UHD Graphics 630 Direct3D11 vs_5_0 ps_5_0)", False, 15),
        ("Google Inc. (Intel)", "ANGLE (Intel, Intel(R) HD Graphics 620 Direct3D11 vs_5_0 ps_5_0)", False, 12),
        ("Google Inc. (Intel)", "ANGLE (Intel, Intel(R) UHD Graphics 620 Direct3D11 vs_5_0 ps_5_0)", False, 12),
        ("Google Inc. (Intel)", "ANGLE (Intel, Intel(R) Iris(R) Xe Graphics Direct3D11 vs_5_0 ps_5_0)", False, 10),
        ("Google Inc. (NVIDIA)", "ANGLE (NVIDIA, NVIDIA GeForce GTX 1660 Ti Direct3D11 vs_5_0 ps_5_0)", True, 10),
        ("Google Inc. (NVIDIA)", "ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0)", True, 10),
        ("Google Inc. (NVIDIA)", "ANGLE (NVIDIA, NVIDIA GeForce RTX 3070 Direct3D11 vs_5_0 ps_5_0)", True, 8),
        ("Google Inc. (NVIDIA)", "ANGLE (NVIDIA, NVIDIA GeForce GTX 1650 Direct3D11 vs_5_0 ps_5_0)", True, 10),
        ("Google Inc. (NVIDIA)", "ANGLE (NVIDIA, NVIDIA GeForce GTX 1050 Ti Direct3D11 vs_5_0 ps_5_0)", True, 8),
        ("Google Inc. (AMD)", "ANGLE (AMD, AMD Radeon(TM) Graphics Direct3D11 vs_5_0 ps_5_0)", False, 12),
        ("Google Inc. (AMD)", "ANGLE (AMD, AMD Radeon RX 580 Series Direct3D11 vs_5_0 ps_5_0)", True, 8),
        ("Google Inc. (AMD)", "ANGLE (AMD, AMD Radeon RX 6700 XT Direct3D11 vs_5_0 ps_5_0)", True, 6),
        
        # Mesa (Linux) - MEDIUM WEIGHT
        ("Mesa/X.org", "Mesa DRI Intel(R) HD Graphics 620 (KBL GT2)", False, 8),
        ("Mesa/X.org", "Mesa DRI Intel(R) UHD Graphics 630 (KBL GT2)", False, 8),
        ("Mesa/X.org", "Mesa DRI Intel(R) Iris(R) Xe Graphics (TGL GT2)", False, 6),
        ("X.Org", "AMD Radeon RX 580 Series (polaris10, LLVM 15.0.0, DRM 3.42, 5.15.0)", True, 6),
        ("X.Org", "AMD Radeon RX 5700 (navi10, LLVM 15.0.0, DRM 3.42, 5.15.0)", True, 5),
        ("X.Org", "AMD Radeon RX 6700 XT (navi22, LLVM 15.0.0, DRM 3.42, 5.15.0)", True, 4),
        ("Mesa", "Mesa Intel(R) UHD Graphics (CML GT2)", False, 6),
        ("Mesa", "Mesa Intel(R) Graphics (RPL-S)", False, 5),
        ("nouveau", "NV138", True, 3),
        ("nouveau", "NV137", True, 2),
        
        # Qualcomm (mobile/ARM laptops) - LOW WEIGHT
        ("Qualcomm", "Adreno (TM) 640", False, 3),
        ("Qualcomm", "Adreno (TM) 650", False, 3),
        ("Qualcomm", "Adreno (TM) 730", False, 4),
        ("Qualcomm", "Adreno (TM) 740", False, 3),
        ("Qualcomm", "Adreno (TM) 680", False, 3),
    ]
    
    # Weighted random selection for primary GPU
    total_weight = sum(w for _, _, _, w in gpu_configs)
    rand_val = random.uniform(0, total_weight)
    cumulative = 0
    
    for vendor, renderer, is_discrete, weight in gpu_configs:
        cumulative += weight
        if rand_val <= cumulative:
            primary_vendor = vendor
            primary_renderer = renderer
            primary_is_discrete = is_discrete
            break
    
    # Multi-GPU: If discrete GPU selected, maybe add integrated GPU (30% chance)
    # This simulates laptop/desktop with both integrated + discrete graphics
    is_multi_gpu = False
    if primary_is_discrete and random.random() < 0.3:
        is_multi_gpu = True
        # Add an integrated GPU to the mix
        integrated_gpus = [gpu for gpu in gpu_configs if not gpu[2]]  # Filter integrated only
        if integrated_gpus:
            total_int_weight = sum(w for _, _, _, w in integrated_gpus)
            rand_int = random.uniform(0, total_int_weight)
            cumulative = 0
            for vendor, renderer, _, weight in integrated_gpus:
                cumulative += weight
                if rand_int <= cumulative:
                    # Return the discrete as primary (what WebGL typically reports)
                    # but note it's multi-GPU in metadata
                    break
    
    return {
        'vendor': primary_vendor,
        'renderer': primary_renderer,
        'isMultiGPU': is_multi_gpu
    }


def generate_random_screen():
    """
    Generate random screen resolution and properties for anti-fingerprinting
    
    Returns a dict with:
    - width, height: total screen dimensions
    - availWidth, availHeight: available space (minus taskbar)
    - colorDepth: bits per pixel
    - pixelDepth: same as colorDepth usually
    - devicePixelRatio: scaling factor for high-DPI displays
    """
    
    # Common real-world screen resolutions
    # Format: (width, height, devicePixelRatio, weight)
    resolutions = [
        # Standard HD monitors (most common)
        (1920, 1080, 1, 25),     # Full HD - very common
        (1366, 768, 1, 15),      # Laptop standard
        (1536, 864, 1, 10),      # 16:9 laptop
        (1440, 900, 1, 8),       # 16:10 laptop
        (1600, 900, 1, 7),       # HD+ laptop
        (1280, 1024, 1, 5),      # Old 5:4 monitor
        (1280, 800, 1, 5),       # Old laptop
        (1680, 1050, 1, 5),      # WSXGA+
        
        # 2K/QHD monitors
        (2560, 1440, 1, 8),      # 2K monitor
        (2560, 1080, 1, 3),      # Ultrawide
        (3440, 1440, 1, 2),      # Ultrawide QHD
        
        # 4K monitors
        (3840, 2160, 1, 4),      # 4K monitor
        (3840, 2160, 1.5, 2),    # 4K with scaling
        
        # High-DPI laptops (Mac-style retina)
        (1920, 1080, 1.25, 3),   # Small high-DPI
        (1920, 1080, 1.5, 3),    # Medium high-DPI
        (2560, 1440, 1.5, 2),    # Retina-style
        (2560, 1600, 2, 2),      # MacBook Pro 13"
        (2880, 1800, 2, 2),      # MacBook Pro 15"
        (3024, 1964, 2, 1),      # MacBook Pro 14" (M1)
        (3456, 2234, 2, 1),      # MacBook Pro 16" (M1)
        
        # Less common but real
        (1280, 720, 1, 3),       # HD Ready
        (2048, 1152, 1, 2),      # Uncommon but exists
        (2560, 1600, 1, 2),      # 16:10 2K
        (1920, 1200, 1, 4),      # WUXGA (16:10)
    ]
    
    # Weighted random selection
    total_weight = sum(w for _, _, _, w in resolutions)
    rand_val = random.uniform(0, total_weight)
    cumulative = 0
    
    for width, height, dpr, weight in resolutions:
        cumulative += weight
        if rand_val <= cumulative:
            chosen_width = width
            chosen_height = height
            device_pixel_ratio = dpr
            break
    
    # Add small random variations to make each session unique
    # ±2% variation in resolution
    width_variation = random.randint(-int(chosen_width * 0.02), int(chosen_width * 0.02))
    height_variation = random.randint(-int(chosen_height * 0.02), int(chosen_height * 0.02))
    
    screen_width = chosen_width + width_variation
    screen_height = chosen_height + height_variation
    
    # Ensure minimum size
    screen_width = max(screen_width, 1024)
    screen_height = max(screen_height, 768)
    
    # Calculate available dimensions (minus taskbar/dock)
    # Taskbar typically takes 40-72 pixels on Windows, 25-50 on Mac
    taskbar_height = random.choice([0, 30, 40, 48, 50, 60, 72])  # Sometimes fullscreen (0)
    avail_width = screen_width
    avail_height = screen_height - taskbar_height
    
    # Color depth - most common values
    color_depth = random.choice([24, 24, 24, 24, 32, 32, 30])  # 24 is most common
    pixel_depth = color_depth  # Usually the same
    
    # Randomize devicePixelRatio slightly for high-DPI displays
    if device_pixel_ratio > 1:
        # Add small variation (±0.05)
        dpr_variation = random.uniform(-0.05, 0.05)
        device_pixel_ratio = round(device_pixel_ratio + dpr_variation, 2)
        device_pixel_ratio = max(1.0, min(3.0, device_pixel_ratio))
    
    return {
        'width': screen_width,
        'height': screen_height,
        'availWidth': avail_width,
        'availHeight': avail_height,
        'colorDepth': color_depth,
        'pixelDepth': pixel_depth,
        'devicePixelRatio': device_pixel_ratio,
        'orientation': 'landscape-primary'  # Most common
    }


def generate_random_user_agent(browser_type):
    """Generate a random realistic user agent coherent with the real browser family.

    Args:
        browser_type: The actual browser being launched (chrome/chromium/firefox/edge).
                      The returned UA's engine token is forced to match this family so
                      that a Chromium session never advertises a Gecko/Safari UA, etc.
    """
    
    # MASSIVELY EXPANDED Platform/OS options - Desktop, Mobile, Tablet, Legacy
    platforms = [
        # Modern Windows -- Windows 10 AND 11 both report "Windows NT 10.0".
        # There is no "Windows NT 11.0". No "rv:" token here: that is a Gecko field
        # added only when building a Firefox UA, never inside a Chromium UA string.
        "Windows NT 10.0; Win64; x64",
        "Windows NT 10.0; Win64; x64",
        "Windows NT 10.0; Win64; x64",
        "Windows NT 10.0; Win64; x64",
        "Windows NT 10.0; Win64; x64",
        "Windows NT 10.0; WOW64",
        "Windows NT 6.1; Win64; x64",  # Windows 7 (small remaining share)
        "Windows NT 6.3; Win64; x64",  # Windows 8.1
        "Windows NT 10.0; ARM64",
        
        # macOS (massively expanded)
        "Macintosh; Intel Mac OS X 10_15_7",
        "Macintosh; Intel Mac OS X 10_15_7",
        "Macintosh; Intel Mac OS X 11_6_0",
        "Macintosh; Intel Mac OS X 11_7_0",
        "Macintosh; Intel Mac OS X 12_0_1",
        "Macintosh; Intel Mac OS X 12_1_0",
        "Macintosh; Intel Mac OS X 12_2_1",
        "Macintosh; Intel Mac OS X 12_3_1",
        "Macintosh; Intel Mac OS X 12_4",
        "Macintosh; Intel Mac OS X 12_5_1",
        "Macintosh; Intel Mac OS X 12_6_0",
        "Macintosh; Intel Mac OS X 12_6_7",
        "Macintosh; Intel Mac OS X 13_0_0",
        "Macintosh; Intel Mac OS X 13_0_1",
        "Macintosh; Intel Mac OS X 13_1",
        "Macintosh; Intel Mac OS X 13_2_1",
        "Macintosh; Intel Mac OS X 13_3_1",
        "Macintosh; Intel Mac OS X 13_4_1",
        "Macintosh; Intel Mac OS X 13_5_2",
        "Macintosh; Intel Mac OS X 13_6_0",
        "Macintosh; Intel Mac OS X 14_0",
        "Macintosh; Intel Mac OS X 14_1_1",
        "Macintosh; Intel Mac OS X 14_2_1",
        "Macintosh; Intel Mac OS X 14_3_0",
        "Macintosh; Intel Mac OS X 14_4_0",
        "Macintosh; Intel Mac OS X 10_14_6",  # Mojave
        "Macintosh; Intel Mac OS X 10_13_6",  # High Sierra
        "Macintosh; Intel Mac OS X 10_12_6",  # Sierra
        "Macintosh; Apple M1 Mac OS X 13_2_1",  # Apple Silicon
        "Macintosh; Apple M2 Mac OS X 14_1_1",  # Apple Silicon M2
        
        # Linux (massively expanded)
        "X11; Linux x86_64",
        "X11; Linux x86_64",
        "X11; Ubuntu; Linux x86_64",
        "X11; Ubuntu; Linux x86_64",
        "X11; Fedora; Linux x86_64",
        "X11; Debian; Linux x86_64",
        "X11; Arch Linux; Linux x86_64",
        "X11; Manjaro; Linux x86_64",
        "X11; Linux x86_64",
        "X11; Linux i686",
        "X11; CrOS x86_64 14541.0.0",  # ChromeOS
        "X11; CrOS x86_64 15117.0.0",
        "X11; CrOS aarch64 15183.0.0",
        "X11; Linux aarch64",
        
        # Android smartphones (massively expanded)
        "Linux; Android 14; SM-S928B",  # Samsung Galaxy S24 Ultra
        "Linux; Android 14; SM-S926B",  # Samsung Galaxy S24+
        "Linux; Android 14; SM-S921B",  # Samsung Galaxy S24
        "Linux; Android 13; SM-S918B",  # Samsung Galaxy S23 Ultra
        "Linux; Android 13; SM-S916B",  # Samsung Galaxy S23+
        "Linux; Android 13; SM-S911B",  # Samsung Galaxy S23
        "Linux; Android 13; SM-G998B",  # Samsung Galaxy S21 Ultra
        "Linux; Android 12; SM-G991B",  # Samsung Galaxy S21
        "Linux; Android 13; Pixel 8 Pro",
        "Linux; Android 13; Pixel 8",
        "Linux; Android 13; Pixel 7 Pro",
        "Linux; Android 13; Pixel 7",
        "Linux; Android 12; Pixel 6 Pro",
        "Linux; Android 12; Pixel 6",
        "Linux; Android 11; Pixel 5",
        "Linux; Android 11; Pixel 4a",
        "Linux; Android 10; Pixel 3 XL",
        "Linux; Android 13; SM-A536B",  # Samsung Galaxy A53
        "Linux; Android 12; SM-A525F",  # Samsung Galaxy A52
        "Linux; Android 13; SM-A546B",  # Samsung Galaxy A54
        "Linux; Android 13; SM-A146B",  # Samsung Galaxy A14
        "Linux; Android 11; SM-G973F",  # Samsung Galaxy S10
        "Linux; Android 10; SM-G960F",  # Samsung Galaxy S9
        "Linux; Android 13; OnePlus KB2003",  # OnePlus 11
        "Linux; Android 13; OnePlus CPH2449",  # OnePlus 11R
        "Linux; Android 12; OnePlus LE2123",  # OnePlus 9 Pro
        "Linux; Android 11; OnePlus IN2023",  # OnePlus 8T
        "Linux; Android 11; ONEPLUS A6013",  # OnePlus 6T
        "Linux; Android 13; 2201123G",  # Xiaomi 12
        "Linux; Android 13; 2211133G",  # Xiaomi 12T
        "Linux; Android 13; 23049PCD8G",  # Xiaomi 13
        "Linux; Android 12; M2102J20SG",  # Xiaomi Mi 11
        "Linux; Android 11; Mi 10T Pro",
        "Linux; Android 10; Mi 9",
        "Linux; Android 13; Redmi Note 12 Pro",
        "Linux; Android 12; Redmi Note 11 Pro",
        "Linux; Android 13; Moto G Power (2023)",
        "Linux; Android 12; Moto G Stylus 5G",
        "Linux; Android 11; Nokia 8.3 5G",
        "Linux; Android 13; ASUS_AI2302",  # ASUS ROG Phone 7
        "Linux; Android 12; ASUS_I006D",  # ASUS Zenfone 9
        "Linux; Android 13; V2231A",  # Vivo X90 Pro
        "Linux; Android 13; V2227A",  # Vivo Y56 5G
        "Linux; Android 13; RMX3501",  # Realme GT 2 Pro
        "Linux; Android 12; RMX3371",  # Realme 9 Pro+
        "Linux; Android 13; Infinix X6833B",  # Infinix Note 30
        
        # Android tablets (massively expanded)
        "Linux; Android 13; SM-X906B",  # Samsung Galaxy Tab S9 Ultra
        "Linux; Android 13; SM-X916B",  # Samsung Galaxy Tab S9+
        "Linux; Android 13; SM-X916C",  # Samsung Galaxy Tab S9
        "Linux; Android 12; SM-X906C",  # Samsung Galaxy Tab S8 Ultra
        "Linux; Android 12; SM-X906B",  # Samsung Galaxy Tab S8+
        "Linux; Android 11; SM-T870",  # Samsung Galaxy Tab S7
        "Linux; Android 13; Lenovo TB-X606F",  # Lenovo Tab P11
        "Linux; Android 12; Lenovo TB-J606F",  # Lenovo Tab M10
        "Linux; Android 13; Lenovo TB-Q706F",  # Lenovo Tab P12 Pro
        "Linux; Android 13; XiaoMi Pad 6",
        "Linux; Android 12; XiaoMi Pad 5 Pro",
        "Linux; Android 13; Pixel Tablet",
        
        # iOS (iPhone) - massively expanded
        "iPhone; CPU iPhone OS 17_3_1 like Mac OS X",
        "iPhone; CPU iPhone OS 17_2_1 like Mac OS X",
        "iPhone; CPU iPhone OS 17_1_2 like Mac OS X",
        "iPhone; CPU iPhone OS 17_1_1 like Mac OS X",
        "iPhone; CPU iPhone OS 17_1 like Mac OS X",
        "iPhone; CPU iPhone OS 17_0_3 like Mac OS X",
        "iPhone; CPU iPhone OS 17_0_2 like Mac OS X",
        "iPhone; CPU iPhone OS 17_0_1 like Mac OS X",
        "iPhone; CPU iPhone OS 17_0 like Mac OS X",
        "iPhone; CPU iPhone OS 16_7_2 like Mac OS X",
        "iPhone; CPU iPhone OS 16_6_1 like Mac OS X",
        "iPhone; CPU iPhone OS 16_6 like Mac OS X",
        "iPhone; CPU iPhone OS 16_5_1 like Mac OS X",
        "iPhone; CPU iPhone OS 16_5 like Mac OS X",
        "iPhone; CPU iPhone OS 16_4_1 like Mac OS X",
        "iPhone; CPU iPhone OS 16_4 like Mac OS X",
        "iPhone; CPU iPhone OS 16_3_1 like Mac OS X",
        "iPhone; CPU iPhone OS 16_3 like Mac OS X",
        "iPhone; CPU iPhone OS 16_2 like Mac OS X",
        "iPhone; CPU iPhone OS 16_1_2 like Mac OS X",
        "iPhone; CPU iPhone OS 15_7_1 like Mac OS X",
        "iPhone; CPU iPhone OS 15_7 like Mac OS X",
        "iPhone; CPU iPhone OS 15_6_1 like Mac OS X",
        "iPhone; CPU iPhone OS 15_6 like Mac OS X",
        "iPhone; CPU iPhone OS 15_5 like Mac OS X",
        "iPhone; CPU iPhone OS 14_8_1 like Mac OS X",
        "iPhone; CPU iPhone OS 14_8 like Mac OS X",
        
        # iOS (iPad) - massively expanded
        "iPad; CPU OS 17_3_1 like Mac OS X",
        "iPad; CPU OS 17_2_1 like Mac OS X",
        "iPad; CPU OS 17_1_2 like Mac OS X",
        "iPad; CPU OS 17_1_1 like Mac OS X",
        "iPad; CPU OS 17_1 like Mac OS X",
        "iPad; CPU OS 17_0_3 like Mac OS X",
        "iPad; CPU OS 16_7_2 like Mac OS X",
        "iPad; CPU OS 16_6_1 like Mac OS X",
        "iPad; CPU OS 16_6 like Mac OS X",
        "iPad; CPU OS 16_5_1 like Mac OS X",
        "iPad; CPU OS 16_5 like Mac OS X",
        "iPad; CPU OS 16_4_1 like Mac OS X",
        "iPad; CPU OS 15_7_1 like Mac OS X",
        "iPad; CPU OS 15_7 like Mac OS X",
        "iPad; CPU OS 14_8_1 like Mac OS X",
        "iPad; CPU OS 14_8 like Mac OS X",
    ]
    
    # MASSIVELY EXPANDED WebKit/AppleWebKit versions
    webkit_versions = [
        "537.36", "537.36", "537.36",  # Most common
        "537.35", "537.34", "537.33", "537.32", "537.31", "537.30",
        "605.1.15", "605.1.16", "605.1.17", "605.1.18", "605.1.19", "605.1.20",
        "604.1.38", "604.1.39", "604.1.40", "604.1.41", "604.1.42",
        "604.5.6", "604.5.7", "604.5.8", "604.5.9",
        "605.1.33", "605.1.34", "605.1.35",
        "606.1.36", "606.1.37", "606.1.38", "606.1.39",
        "607.1.40", "607.1.41", "607.1.42", "607.1.43",
        "608.1.49", "608.1.50", "608.1.51", "608.1.52",
        "609.1.20", "609.1.21", "609.1.22", "609.1.23",
        "610.1.25", "610.1.26", "610.1.27", "610.1.28",
        "611.1.30", "611.1.31", "611.1.32",
        "612.1.29", "612.1.30", "612.1.31",
        "613.1.17", "613.1.18", "613.1.19",
        "614.1.26", "614.1.27", "614.1.28",
        "615.1.26", "615.1.27", "615.1.28", "615.1.29",
        "616.1.27", "616.1.28", "616.1.29", "616.1.30",
        "617.1.15", "617.1.16", "617.1.17", "617.1.18",
    ]
    
    # Coherent (Chrome major, build-base) pairs. Each build-base actually belongs
    # to that major release, so we never emit an impossible major.build combination.
    # Refreshed to recent releases to avoid an obviously-stale (low-trust) UA.
    chrome_version_pairs = [
        (120, 6099), (121, 6167), (122, 6261), (123, 6312), (124, 6367),
        (125, 6422), (126, 6478), (127, 6533), (128, 6613), (129, 6668),
        (130, 6723), (131, 6778), (132, 6834), (133, 6943),
    ]
    
    # MASSIVELY EXPANDED Firefox versions
    firefox_versions = [
        115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135
    ]
    
    # Edge major tracks the Chrome major it is built on, so it is derived from the
    # chosen chrome_version_pairs entry below rather than picked independently.
    
    # Normalize to the families we actually launch. The pool is
    # chrome / chromium / firefox / edge — Safari/Opera/IE are never launched
    # so we must never advertise those engines (that would be an instant tell).
    bt = (browser_type or 'chrome').lower()

    platform = random.choice(platforms)

    if bt == 'firefox':
        # Firefox uses the Gecko engine (no AppleWebKit token).
        firefox_ver = random.choice(firefox_versions)
        if 'Android' in platform:
            # Mobile Firefox
            ua = f"Mozilla/5.0 ({platform}) Gecko/{firefox_ver}.0 Firefox/{firefox_ver}.0"
        else:
            # Firefox never ships on iOS with a Gecko UA; keep it on desktop/Android.
            if 'iPhone' in platform or 'iPad' in platform:
                platform = random.choice([p for p in platforms if 'iPhone' not in p and 'iPad' not in p])
            ua = f"Mozilla/5.0 ({platform}; rv:{firefox_ver}.0) Gecko/20100101 Firefox/{firefox_ver}.0"

    elif bt == 'edge':
        # Edge is Chromium-based (AppleWebKit/537.36) with an Edg/ token, Windows-first.
        webkit = "537.36"
        chrome_major, chrome_base = random.choice(chrome_version_pairs)
        chrome_version = f"{chrome_major}.0.{chrome_base}.{random.randint(50, 240)}"
        edge_ver = chrome_major  # Edge major tracks the Chrome major it is built on
        win_platforms = [p for p in platforms if 'Windows' in p]
        if win_platforms:
            platform = random.choice(win_platforms)
        ua = (f"Mozilla/5.0 ({platform}) AppleWebKit/{webkit} (KHTML, like Gecko) "
              f"Chrome/{chrome_version} Safari/{webkit} "
              f"Edg/{edge_ver}.0.{random.randint(1000, 3999)}.{random.randint(10, 99)}")

    else:
        # chrome / chromium -> Chromium UA (AppleWebKit/537.36 + Chrome token).
        webkit = "537.36"
        chrome_major, chrome_base = random.choice(chrome_version_pairs)
        chrome_version = f"{chrome_major}.0.{chrome_base}.{random.randint(50, 240)}"
        if 'iPhone' in platform or 'iPad' in platform:
            # Chrome on iOS is CriOS on the WebKit engine, not the Chrome token.
            ua = (f"Mozilla/5.0 ({platform}) AppleWebKit/605.1.15 (KHTML, like Gecko) "
                  f"CriOS/{chrome_major}.0.0.0 Mobile/15E148 Safari/604.1")
        elif 'Android' in platform:
            ua = (f"Mozilla/5.0 ({platform}) AppleWebKit/{webkit} (KHTML, like Gecko) "
                  f"Chrome/{chrome_version} Mobile Safari/{webkit}")
        else:
            ua = (f"Mozilla/5.0 ({platform}) AppleWebKit/{webkit} (KHTML, like Gecko) "
                  f"Chrome/{chrome_version} Safari/{webkit}")

    return ua


def derive_platform_from_ua(user_agent):
    """Derive a navigator.platform value coherent with the chosen user agent.

    Used so the CDP setUserAgentOverride 'platform' field matches the OS advertised
    in the UA string (instead of hardcoding Win32).
    """
    ua = user_agent or ''
    if 'Windows' in ua:
        return 'Win32'
    if 'iPhone' in ua:
        return 'iPhone'
    if 'iPad' in ua:
        return 'iPad'
    if 'Android' in ua:
        return 'Linux armv8l'
    if 'Macintosh' in ua or 'Mac OS X' in ua:
        return 'MacIntel'
    if 'CrOS' in ua:
        return 'Linux x86_64'
    if 'Linux' in ua or 'X11' in ua:
        return 'Linux x86_64'
    return 'Win32'
