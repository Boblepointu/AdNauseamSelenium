#!/usr/bin/env python3
"""
Browser Chaos Generator
Automates browsing across multiple sites to generate traffic
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import time
import random
import os
from urllib.parse import urlparse

browsers = ['firefox', 'chrome', 'edge']

def load_websites(file_path='/app/websites.txt'):
    """Load websites from a text file, ignoring comments and empty lines"""
    websites = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if line and not line.startswith('#'):
                    websites.append(line)
        
        print(f'✓ Loaded {len(websites)} websites from {file_path}')
        return websites
    except FileNotFoundError:
        print(f'⚠ Warning: {file_path} not found, using fallback websites')
        # Fallback to a minimal list if file not found
        return [
            "https://google.com", "https://bing.com", "https://yahoo.com",
            "https://cnn.com", "https://bbc.com", "https://forbes.com"
        ]
    except Exception as e:
        print(f'⚠ Error loading websites: {e}')
        return [
            "https://google.com", "https://bing.com", "https://yahoo.com"
        ]

# Load websites at startup
sites = load_websites()

def get_domain(url):
    """Extract domain from URL"""
    try:
        parsed = urlparse(url)
        return parsed.netloc.lower()
    except:
        return ''

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
    Get a realistic timezone offset based on the primary language
    
    Returns timezone offset in minutes (e.g., -60 for UTC+1)
    Negative offset means ahead of UTC (e.g., UTC+1 = -60)
    """
    
    # Extract primary language code
    lang_code = language.split(',')[0].split(';')[0].split('-')[0]
    
    # Map languages to typical timezone offsets (in minutes, negative = ahead of UTC)
    timezone_map = {
        'fr': [
            -60,   # France (UTC+1/+2)
            -60,   # Most common
            -120,  # During DST
        ],
        'de': [
            -60,   # Germany (UTC+1/+2)
            -60,
            -120,
        ],
        'es': [
            -60,   # Spain (UTC+1/+2)
            -60,
            -120,
        ],
        'it': [
            -60,   # Italy (UTC+1/+2)
            -60,
            -120,
        ],
        'pt': [
            0,     # Portugal (UTC+0/+1)
            -60,
        ],
        'nl': [
            -60,   # Netherlands (UTC+1/+2)
            -120,
        ],
        'pl': [
            -60,   # Poland (UTC+1/+2)
            -120,
        ],
        'sv': [
            -60,   # Sweden (UTC+1/+2)
            -120,
        ],
        'en': [
            0,     # UK (UTC+0/+1)
            -60,   # UK during DST
            300,   # US East (UTC-5)
            360,   # US Central (UTC-6)
            420,   # US West (UTC-7)
            480,   # US Pacific (UTC-8)
        ],
    }
    
    # Get timezone for language or default to Central European Time
    offsets = timezone_map.get(lang_code, [-60, -120])
    return random.choice(offsets)

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

def generate_random_plugins():
    """
    Generate randomized browser plugins for fingerprinting diversity
    
    Returns a JavaScript-ready string representation of plugins array
    PDF plugins are heavily randomized as they're major fingerprinting vectors
    """
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
    
    # Add 1-2 PDF plugins
    num_pdf = random.choice([1, 1, 1, 2])
    for _ in range(num_pdf):
        plugins.append(random.choice(pdf_plugins))
    
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

def generate_random_gpu():
    """
    Generate random GPU vendor and renderer strings for WebGL fingerprinting
    
    Returns a dict with:
    - vendor: GPU vendor string (parameter 37445)
    - renderer: GPU renderer string (parameter 37446)
    """
    
    # Common real GPU configurations (vendor, renderer)
    gpu_configs = [
        # Intel integrated graphics (most common)
        ("Intel Inc.", "Intel Iris OpenGL Engine"),
        ("Intel Inc.", "Intel(R) UHD Graphics 630"),
        ("Intel Inc.", "Intel(R) HD Graphics 620"),
        ("Intel Inc.", "Intel(R) HD Graphics 530"),
        ("Intel Inc.", "Intel(R) Iris(R) Plus Graphics 640"),
        ("Intel Inc.", "Intel(R) Iris(R) Plus Graphics 655"),
        ("Intel Inc.", "Intel(R) Iris(R) Xe Graphics"),
        ("Intel Inc.", "Mesa Intel(R) UHD Graphics 620 (KBL GT2)"),
        ("Intel Inc.", "Mesa Intel(R) HD Graphics 630 (KBL GT2)"),
        ("Intel", "Intel(R) HD Graphics 4000"),
        ("Intel", "Intel(R) HD Graphics 5500"),
        
        # NVIDIA (gaming/professional)
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 1050/PCIe/SSE2"),
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 1060/PCIe/SSE2"),
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 1650/PCIe/SSE2"),
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 1660 Ti/PCIe/SSE2"),
        ("NVIDIA Corporation", "NVIDIA GeForce RTX 2060/PCIe/SSE2"),
        ("NVIDIA Corporation", "NVIDIA GeForce RTX 2070/PCIe/SSE2"),
        ("NVIDIA Corporation", "NVIDIA GeForce RTX 3060/PCIe/SSE2"),
        ("NVIDIA Corporation", "NVIDIA GeForce RTX 3070/PCIe/SSE2"),
        ("NVIDIA Corporation", "NVIDIA GeForce RTX 4060/PCIe/SSE2"),
        ("NVIDIA Corporation", "GeForce GTX 960/PCIe/SSE2"),
        ("NVIDIA Corporation", "GeForce GTX 970/PCIe/SSE2"),
        ("NVIDIA Corporation", "GeForce MX150/PCIe/SSE2"),
        ("NVIDIA Corporation", "GeForce MX250/PCIe/SSE2"),
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 1080/PCIe/SSE2"),
        
        # AMD
        ("AMD", "AMD Radeon(TM) Graphics"),
        ("AMD", "AMD Radeon RX 580 Series"),
        ("AMD", "AMD Radeon RX 5700"),
        ("AMD", "AMD Radeon RX 6700 XT"),
        ("AMD", "AMD Radeon(TM) Vega 8 Graphics"),
        ("AMD", "AMD Radeon(TM) RX Vega 10 Graphics"),
        ("ATI Technologies Inc.", "AMD Radeon HD 7900 Series"),
        ("ATI Technologies Inc.", "AMD Radeon R9 200 Series"),
        
        # Apple (Mac)
        ("Apple", "Apple M1"),
        ("Apple", "Apple M2"),
        ("Apple", "Apple M1 Pro"),
        ("Apple", "Apple M1 Max"),
        ("Apple", "AMD Radeon Pro 5500M"),
        ("Apple", "AMD Radeon Pro 560X"),
        
        # Generic/Angle (Chrome on Windows)
        ("Google Inc. (Intel)", "ANGLE (Intel, Intel(R) UHD Graphics 630 Direct3D11 vs_5_0 ps_5_0)"),
        ("Google Inc. (Intel)", "ANGLE (Intel, Intel(R) HD Graphics 620 Direct3D11 vs_5_0 ps_5_0)"),
        ("Google Inc. (NVIDIA)", "ANGLE (NVIDIA, NVIDIA GeForce GTX 1660 Ti Direct3D11 vs_5_0 ps_5_0)"),
        ("Google Inc. (NVIDIA)", "ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0)"),
        ("Google Inc. (AMD)", "ANGLE (AMD, AMD Radeon(TM) Graphics Direct3D11 vs_5_0 ps_5_0)"),
        
        # Mesa (Linux)
        ("Mesa/X.org", "Mesa DRI Intel(R) HD Graphics 620 (KBL GT2)"),
        ("Mesa/X.org", "Mesa DRI Intel(R) UHD Graphics 630 (KBL GT2)"),
        ("X.Org", "AMD Radeon RX 580 Series (polaris10, LLVM 15.0.0, DRM 3.42, 5.15.0)"),
        
        # Qualcomm (mobile/ARM laptops)
        ("Qualcomm", "Adreno (TM) 640"),
        ("Qualcomm", "Adreno (TM) 650"),
        ("Qualcomm", "Adreno (TM) 730"),
    ]
    
    vendor, renderer = random.choice(gpu_configs)
    
    return {
        'vendor': vendor,
        'renderer': renderer
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

def generate_random_user_agent():
    """Generate a random realistic user agent by combining different components"""
    
    # Platform/OS options - Desktop, Mobile, Tablet, Legacy
    platforms = [
        # Modern Windows
        "Windows NT 10.0; Win64; x64",
        "Windows NT 11.0; Win64; x64",
        "Windows NT 10.0; WOW64",
        "Windows NT 6.1; Win64; x64",  # Windows 7
        "Windows NT 6.3; Win64; x64",  # Windows 8.1
        "Windows NT 6.2; Win64; x64",  # Windows 8
        "Windows NT 5.1",  # Windows XP
        "Windows NT 6.0",  # Windows Vista
        
        # macOS
        "Macintosh; Intel Mac OS X 10_15_7",
        "Macintosh; Intel Mac OS X 11_6_0",
        "Macintosh; Intel Mac OS X 12_0_1",
        "Macintosh; Intel Mac OS X 12_6_0",
        "Macintosh; Intel Mac OS X 13_0_0",
        "Macintosh; Intel Mac OS X 13_1",
        "Macintosh; Intel Mac OS X 13_2_1",
        "Macintosh; Intel Mac OS X 13_4_1",
        "Macintosh; Intel Mac OS X 14_0",
        "Macintosh; Intel Mac OS X 14_1_1",
        "Macintosh; Intel Mac OS X 14_2_1",
        "Macintosh; Intel Mac OS X 10_14_6",
        "Macintosh; Intel Mac OS X 10_13_6",
        
        # Linux
        "X11; Linux x86_64",
        "X11; Ubuntu; Linux x86_64",
        "X11; Fedora; Linux x86_64",
        "X11; Linux i686",
        "X11; CrOS x86_64 14541.0.0",  # ChromeOS
        
        # Android smartphones
        "Linux; Android 13; SM-S918B",  # Samsung Galaxy S23 Ultra
        "Linux; Android 13; SM-G998B",  # Samsung Galaxy S21 Ultra
        "Linux; Android 12; SM-G991B",  # Samsung Galaxy S21
        "Linux; Android 13; Pixel 7 Pro",
        "Linux; Android 13; Pixel 7",
        "Linux; Android 12; Pixel 6 Pro",
        "Linux; Android 12; Pixel 6",
        "Linux; Android 11; Pixel 5",
        "Linux; Android 13; SM-A536B",  # Samsung Galaxy A53
        "Linux; Android 12; SM-A525F",  # Samsung Galaxy A52
        "Linux; Android 11; SM-G973F",  # Samsung Galaxy S10
        "Linux; Android 10; SM-G960F",  # Samsung Galaxy S9
        "Linux; Android 13; OnePlus KB2003",  # OnePlus 11
        "Linux; Android 12; OnePlus LE2123",  # OnePlus 9 Pro
        "Linux; Android 11; ONEPLUS A6013",  # OnePlus 6T
        "Linux; Android 13; 2201123G",  # Xiaomi 12
        "Linux; Android 12; M2102J20SG",  # Xiaomi Mi 11
        "Linux; Android 11; Mi 10T Pro",
        "Linux; Android 10; Mi 9",
        
        # Android tablets
        "Linux; Android 13; SM-X906B",  # Samsung Galaxy Tab S9 Ultra
        "Linux; Android 12; SM-X906C",  # Samsung Galaxy Tab S8 Ultra
        "Linux; Android 11; SM-T870",  # Samsung Galaxy Tab S7
        "Linux; Android 13; Lenovo TB-X606F",  # Lenovo Tab P11
        "Linux; Android 12; Lenovo TB-J606F",  # Lenovo Tab M10
        
        # iOS (iPhone)
        "iPhone; CPU iPhone OS 17_1 like Mac OS X",
        "iPhone; CPU iPhone OS 17_0 like Mac OS X",
        "iPhone; CPU iPhone OS 16_6 like Mac OS X",
        "iPhone; CPU iPhone OS 16_5 like Mac OS X",
        "iPhone; CPU iPhone OS 16_4 like Mac OS X",
        "iPhone; CPU iPhone OS 16_3 like Mac OS X",
        "iPhone; CPU iPhone OS 15_7 like Mac OS X",
        "iPhone; CPU iPhone OS 15_6 like Mac OS X",
        "iPhone; CPU iPhone OS 14_8 like Mac OS X",
        
        # iOS (iPad)
        "iPad; CPU OS 17_1 like Mac OS X",
        "iPad; CPU OS 16_6 like Mac OS X",
        "iPad; CPU OS 16_5 like Mac OS X",
        "iPad; CPU OS 15_7 like Mac OS X",
        "iPad; CPU OS 14_8 like Mac OS X",
    ]
    
    # WebKit/AppleWebKit versions
    webkit_versions = [
        "537.36",
        "537.35",
        "537.34",
        "537.33",
        "537.32",
        "537.31",
        "605.1.15",
        "605.1.16",
        "604.1.38",
        "604.5.6",
        "605.1.33",
        "606.1.36",
        "607.1.40",
        "608.1.49",
        "609.1.20",
    ]
    
    # Chrome versions (major.0.0.0 or major.0.build.0)
    chrome_major_versions = [110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126]
    chrome_builds = [
        "0.0.0",
        "0.5414.119",
        "0.5481.177",
        "0.5615.137",
        "0.5735.198",
        "0.5845.179",
        "0.5993.117",
        "0.6045.105",
        "0.6045.199",
        "0.6099.109",
        "0.6100.88",
        "0.6261.94",
        "0.6312.122",
        "0.6367.91",
        "0.6367.201",
        "0.6478.126",
        "0.6563.110",
        "0.6613.119",
    ]
    
    # Firefox versions
    firefox_versions = [115, 116, 117, 118, 119, 120, 121, 122, 123, 124]
    
    # Edge versions
    edge_versions = [115, 116, 117, 118, 119, 120, 121, 122]
    
    # Safari versions
    safari_versions = ["16.1", "16.2", "16.3", "16.4", "16.5", "16.6", "17.0", "17.1", "17.2"]
    
    # Legacy browser versions
    opera_versions = ["12.16", "12.17", "11.64", "11.62", "10.63"]
    ie_versions = ["11.0", "10.0", "9.0", "8.0", "7.0"]
    trident_versions = ["7.0", "6.0", "5.0", "4.0"]
    
    # Choose browser type - weighted towards modern browsers
    browser_choices = (
        ['chrome'] * 35 + ['firefox'] * 25 + ['safari'] * 15 + 
        ['edge'] * 15 + ['opera'] * 5 + ['ie'] * 5
    )
    browser_type = random.choice(browser_choices)
    platform = random.choice(platforms)
    
    if browser_type == 'chrome':
        webkit = random.choice(webkit_versions)
        chrome_major = random.choice(chrome_major_versions)
        chrome_build = random.choice(chrome_builds)
        chrome_version = f"{chrome_major}.{chrome_build}"
        
        # Filter platform for mobile Chrome
        if 'Android' in platform or 'iPhone' in platform:
            # Mobile Chrome
            mobile_suffix = "Mobile Safari" if 'Android' in platform else ""
            ua = f"Mozilla/5.0 ({platform}) AppleWebKit/{webkit} (KHTML, like Gecko) Chrome/{chrome_version} {mobile_suffix} Safari/{webkit}"
        else:
            # Desktop Chrome
            ua = f"Mozilla/5.0 ({platform}) AppleWebKit/{webkit} (KHTML, like Gecko) Chrome/{chrome_version} Safari/{webkit}"
        
    elif browser_type == 'firefox':
        firefox_ver = random.choice(firefox_versions)
        # Firefox uses Gecko
        if 'Android' in platform:
            # Mobile Firefox
            ua = f"Mozilla/5.0 ({platform}) Gecko/{firefox_ver}.0 Firefox/{firefox_ver}.0"
        else:
            # Desktop Firefox
            ua = f"Mozilla/5.0 ({platform}; rv:{firefox_ver}.0) Gecko/20100101 Firefox/{firefox_ver}.0"
        
    elif browser_type == 'safari':
        # Safari on macOS and iOS
        webkit = random.choice(webkit_versions)
        safari_ver = random.choice(safari_versions)
        
        if 'iPhone' in platform or 'iPad' in platform:
            # iOS Safari
            ua = f"Mozilla/5.0 ({platform}) AppleWebKit/{webkit} (KHTML, like Gecko) Version/{safari_ver} Mobile/15E148 Safari/{webkit}"
        else:
            # macOS Safari
            mac_platforms = [p for p in platforms if 'Mac' in p and 'iPhone' not in p and 'iPad' not in p]
            if mac_platforms:
                platform = random.choice(mac_platforms)
            ua = f"Mozilla/5.0 ({platform}) AppleWebKit/{webkit} (KHTML, like Gecko) Version/{safari_ver} Safari/{webkit}"
        
    elif browser_type == 'edge':
        webkit = random.choice(webkit_versions)
        edge_ver = random.choice(edge_versions)
        chrome_major = random.choice(chrome_major_versions)  # Edge is Chromium-based
        chrome_build = random.choice(chrome_builds)
        chrome_version = f"{chrome_major}.{chrome_build}"
        
        # Edge is primarily Windows
        win_platforms = [p for p in platforms if 'Windows' in p]
        if win_platforms:
            platform = random.choice(win_platforms)
        
        ua = f"Mozilla/5.0 ({platform}) AppleWebKit/{webkit} (KHTML, like Gecko) Chrome/{chrome_version} Safari/{webkit} Edg/{edge_ver}.0.{random.randint(1000, 9999)}.{random.randint(10, 99)}"
    
    elif browser_type == 'opera':
        # Opera (legacy Presto and modern Chromium-based)
        opera_ver = random.choice(opera_versions)
        if float(opera_ver) < 15:
            # Old Presto Opera
            ua = f"Opera/9.80 ({platform}) Presto/2.12.388 Version/{opera_ver}"
        else:
            # Modern Chromium-based Opera
            webkit = random.choice(webkit_versions)
            chrome_major = random.choice(chrome_major_versions)
            chrome_build = random.choice(chrome_builds)
            chrome_version = f"{chrome_major}.{chrome_build}"
            opera_major = random.randint(85, 105)
            ua = f"Mozilla/5.0 ({platform}) AppleWebKit/{webkit} (KHTML, like Gecko) Chrome/{chrome_version} Safari/{webkit} OPR/{opera_major}.0.{random.randint(1000, 9999)}.{random.randint(10, 99)}"
    
    elif browser_type == 'ie':
        # Internet Explorer (legacy)
        ie_ver = random.choice(ie_versions)
        trident_ver = random.choice(trident_versions)
        
        # IE only on Windows
        win_platforms = [p for p in platforms if 'Windows' in p]
        if win_platforms:
            platform = random.choice(win_platforms)
        
        if float(ie_ver) >= 11:
            ua = f"Mozilla/5.0 ({platform}; Trident/{trident_ver}; rv:{ie_ver}) like Gecko"
        else:
            ua = f"Mozilla/5.0 (compatible; MSIE {ie_ver}; {platform}; Trident/{trident_ver})"
    
    return ua

def auto_accept_cookies(driver, browser_type, max_attempts=3):
    """Automatically detect and click cookie consent buttons - with retries and multi-step handling"""
    
    for attempt in range(max_attempts):
        try:
            if attempt > 0:
                print(f'  [{browser_type}] 🍪 Cookie consent attempt {attempt + 1}/{max_attempts}')
                time.sleep(1)
            
            # Step 1: Click individual "Agree" buttons if they exist (e.g., DIDOMI consent platform)
            # This handles cases where you need to agree to individual categories before the main button
            individual_agree_selectors = [
                # DIDOMI and similar platforms with individual toggles
                'button[aria-label="Agree"]',
                'button[aria-label*="Agree"]:not([aria-label*="all"])',
                '.didomi-components-button[aria-label*="Agree"]',
                'button.didomi-button:not(.didomi-button-highlight)',
                'button:has-text("Agree"):not(:has-text("all"))',
                # Generic agree buttons (not "Agree to all")
                'button:not([aria-label*="all"]):not([class*="all"])',
            ]
            
            individual_agreed = False
            for selector in individual_agree_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        try:
                            if element.is_displayed() and 'agree' in element.text.lower():
                                # Filter out "Disagree" buttons and "Agree to all" buttons
                                if 'disagree' not in element.text.lower() and 'all' not in element.text.lower():
                                    element.click()
                                    individual_agreed = True
                                    time.sleep(0.3)  # Small delay between individual clicks
                        except:
                            continue
                except:
                    continue
            
            if individual_agreed:
                print(f'  [{browser_type}] 🍪 Clicked individual agree buttons')
                time.sleep(0.5)
            
            # Step 2: YouTube-specific consent handling (must be before generic)
            try:
                youtube_accept_selectors = [
                    'button[aria-label*="Accept all"]',
                    'button[aria-label*="accept all"]',
                    'ytd-button-renderer button[aria-label*="Accept"]',
                    'tp-yt-paper-dialog button[aria-label*="Accept all"]',
                    'c3-consent-bump button[aria-label*="Accept"]',
                    '[aria-label="Accept all"]',
                    '[aria-label="Accept the use of cookies"]',
                    'button:has-text("Accept all")',
                    'ytd-consent-bump-v2-lightbox button[aria-label*="Accept"]'
                ]
                
                for selector in youtube_accept_selectors:
                    try:
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        for element in elements:
                            if element.is_displayed():
                                element.click()
                                print(f'  [{browser_type}] 🍪 Accepted YouTube consent')
                                time.sleep(1)
                                return True
                    except:
                        continue
            except:
                pass
            
            # Step 3: Common "Accept All" / "Agree to all" buttons
            accept_all_selectors = [
                # DIDOMI "Agree to all" button
                'button[aria-label="Agree to all"]',
                'button.didomi-button-highlight',
                '#didomi-notice-agree-button',
                
                # Common IDs
                '#accept-cookies', '#acceptCookies', '#cookie-accept', '#cookieAccept',
                '#accept-all', '#acceptAll', '#cookie-consent-accept', '#onetrust-accept-btn-handler',
                '#acceptAllButton', '#accept_all_cookies', '#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll',
                
                # Common Classes
                '.accept-cookies', '.acceptCookies', '.cookie-accept', '.cookieAccept',
                '.accept-all', '.acceptAll', '.cookie-consent-accept', '.accept-button',
                '.cookie-accept-button', '.js-accept-cookies', '.cookie-banner-accept',
                
                # Data attributes
                '[data-action="accept"]', '[data-cookie="accept"]', '[data-consent="accept"]',
                '[data-testid="cookie-accept"]', '[data-testid="accept-all"]',
                
                # Common button names
                'button[name="accept"]', 'button[name="accept-all"]', 'button[name="agree"]',
            ]
            
            # Try specific selectors first (faster and more reliable)
            for selector in accept_all_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed():
                            element.click()
                            print(f'  [{browser_type}] 🍪 Accepted cookies via selector: {selector}')
                            time.sleep(0.5)
                            return True
                except:
                    continue
            
            # Step 4: Find buttons by text content
            accept_text_patterns = [
                'accept all', 'accept cookies', 'i accept', 'allow all', 'allow cookies',
                'agree', 'agree to all', 'got it', 'ok', 'continue', 'agree and close', 'accept & close',
                'accept and continue', 'accepter', 'tout accepter', 'aceptar', 'akzeptieren', 'accetto',
                'aceitar', 'acceptera', 'ja, accepteren', 'zgadzam się', 'souhlasím',
                'συμφωνώ', 'принимаю', 'kabul ediyorum', 'موافق'
            ]
            
            try:
                all_buttons = driver.find_elements(By.TAG_NAME, 'button')
                all_buttons += driver.find_elements(By.CSS_SELECTOR, 'a.button, .btn, [role="button"]')
                
                for button in all_buttons:
                    try:
                        if not button.is_displayed():
                            continue
                        
                        button_text = button.text.lower().strip()
                        
                        # Check if button text matches any accept pattern
                        for pattern in accept_text_patterns:
                            if pattern in button_text or button_text == pattern.replace(' ', ''):
                                button.click()
                                print(f'  [{browser_type}] 🍪 Accepted cookies via text: "{button.text[:30]}"')
                                time.sleep(0.5)
                                return True
                    except:
                        continue
            except:
                pass
            
            # Step 5: Try iframe-based cookie consent (some use iframes)
            try:
                iframes = driver.find_elements(By.TAG_NAME, 'iframe')
                for iframe in iframes:
                    try:
                        iframe_name = iframe.get_attribute('name') or iframe.get_attribute('id') or ''
                        if any(keyword in iframe_name.lower() for keyword in ['cookie', 'consent', 'gdpr', 'privacy', 'didomi']):
                            driver.switch_to.frame(iframe)
                            
                            # Try to find accept button in iframe
                            for selector in accept_all_selectors[:10]:
                                try:
                                    element = driver.find_element(By.CSS_SELECTOR, selector)
                                    if element.is_displayed():
                                        element.click()
                                        driver.switch_to.default_content()
                                        print(f'  [{browser_type}] 🍪 Accepted cookies in iframe')
                                        time.sleep(0.5)
                                        return True
                                except:
                                    continue
                            
                            driver.switch_to.default_content()
                    except:
                        driver.switch_to.default_content()
                        continue
            except:
                pass
            
            # If we got here, no cookie banner was found or clicked
            if attempt == 0:
                # Only break if first attempt found nothing
                break
            
        except Exception as e:
            # Don't let cookie handling break the automation
            try:
                driver.switch_to.default_content()
            except:
                pass
            
    return False

def detect_and_click_ads(driver, browser_type, click_chance=0.6):
    """Detect ads on page and optionally click them (60% chance by default)"""
    try:
        # Store initial window handle (but don't manage tabs - let caller handle that)
        initial_window = driver.current_window_handle
        
        # Common ad selectors (Google Ads, display ads, etc.)
        ad_selectors = [
            # Google Ads
            'iframe[id*="google_ads"]',
            'iframe[id*="aswift"]',
            'div[id*="google_ads"]',
            'ins.adsbygoogle',
            
            # Generic ad containers
            '[class*="advertisement"]',
            '[class*="ad-container"]',
            '[class*="ad-banner"]',
            '[class*="ad-slot"]',
            '[id*="ad-container"]',
            '[id*="advertisement"]',
            'div[class*="ads"]',
            'div[id*="ads"]',
            
            # Common ad networks
            '[class*="doubleclick"]',
            '[id*="doubleclick"]',
            'iframe[src*="doubleclick"]',
            'iframe[src*="googlesyndication"]',
            'iframe[src*="advertising"]',
            
            # Ad links
            'a[href*="ad.doubleclick"]',
            'a[href*="googleadservices"]',
            'a[rel="sponsored"]',
            'a[data-ad]',
            
            # Taboola, Outbrain, etc.
            '[class*="taboola"]',
            '[class*="outbrain"]',
            '[id*="taboola"]',
            '[id*="outbrain"]'
        ]
        
        ads_found = []
        
        # Find all potential ads
        for selector in ad_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    try:
                        if element.is_displayed() and element.is_enabled():
                            ads_found.append(element)
                    except:
                        continue
            except:
                continue
        
        if not ads_found:
            return False
        
        print(f'  [{browser_type}] 📢 Detected {len(ads_found)} ad(s) on page')
        
        # Decide whether to click (60% chance)
        if random.random() > click_chance:
            print(f'  [{browser_type}] 🎲 Decided not to click ads this time')
            return False
        
        # Try to click a random ad
        ad_to_click = random.choice(ads_found)
        
        try:
            # Scroll ad into view
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", ad_to_click)
            time.sleep(random.uniform(0.5, 1.0))
            
            # Try to click the ad
            ad_to_click.click()
            print(f'  [{browser_type}] 💰 Clicked on ad!')
            time.sleep(random.uniform(1, 3))
            
            # Note: We don't close tabs here - let the caller handle tab management
            # This allows for more realistic browsing behavior
            
            return True
            
        except Exception as e:
            # Ad might be in iframe, try to find and click link inside
            try:
                if ad_to_click.tag_name == 'iframe':
                    driver.switch_to.frame(ad_to_click)
                    links = driver.find_elements(By.TAG_NAME, 'a')
                    if links:
                        links[0].click()
                        driver.switch_to.default_content()
                        print(f'  [{browser_type}] 💰 Clicked ad link in iframe!')
                        time.sleep(random.uniform(1, 3))
                        return True
                    driver.switch_to.default_content()
            except:
                try:
                    driver.switch_to.default_content()
                except:
                    pass
                try:
                    # Make sure we're back on the initial window
                    if initial_window in driver.window_handles:
                        driver.switch_to.window(initial_window)
                    elif driver.window_handles:
                        driver.switch_to.window(driver.window_handles[0])
                except:
                    pass
            
            return False
            
    except Exception as e:
        # Don't let ad clicking break the automation
        # Try to ensure we're on a valid window
        try:
            if driver.window_handles:
                driver.switch_to.window(driver.window_handles[0])
        except:
            pass
        return False

def create_driver(browser_type):
    """Create a Selenium WebDriver for automated browsing with anti-detection"""
    
    # Generate a random realistic user agent (thousands of combinations possible)
    user_agent = generate_random_user_agent()
    
    # Generate random European language (80% French)
    accept_language = generate_random_language()
    
    # Generate random screen properties
    screen = generate_random_screen()
    
    # Generate random GPU info for WebGL fingerprinting
    gpu = generate_random_gpu()
    
    # Generate random hardware specs (CPU, RAM, touch)
    hardware = generate_random_hardware()
    
    # Generate random network connection properties
    connection = generate_random_connection()
    
    # Get timezone based on language
    timezone_offset = get_timezone_for_language(accept_language)
    
    # Generate random battery status
    battery = generate_random_battery()
    
    # Generate random media devices
    media_devices = generate_random_media_devices()
    
    # Generate random fonts list
    fonts = generate_random_fonts()
    
    # Generate random plugins with heavy PDF randomization
    plugins_js = generate_random_plugins()
    
    print(f'[{browser_type}] Generated UA: {user_agent[:80]}...')
    print(f'[{browser_type}] Language: {accept_language.split(",")[0]}')
    print(f'[{browser_type}] Screen: {screen["width"]}x{screen["height"]} @ {screen["devicePixelRatio"]}x DPR')
    print(f'[{browser_type}] GPU: {gpu["vendor"]} / {gpu["renderer"][:50]}...')
    print(f'[{browser_type}] Hardware: {hardware["hardwareConcurrency"]} cores, {hardware["deviceMemory"]}GB RAM, {hardware["maxTouchPoints"]} touch')
    print(f'[{browser_type}] Connection: {connection["effectiveType"]}, {connection["rtt"]}ms RTT, {connection["downlink"]}Mbps')
    print(f'[{browser_type}] Timezone: UTC{timezone_offset/60:+.0f}')
    print(f'[{browser_type}] Battery: {"Charging" if battery["charging"] else "Discharging"} at {int(battery["level"]*100)}%')
    print(f'[{browser_type}] Media: {len(media_devices)} devices, Fonts: {len(fonts)} installed, Plugins: randomized')
    
    if browser_type == 'chrome':
        options = webdriver.ChromeOptions()
        
        # Selenium Stealth recommended options
        options.add_argument(f'user-agent={user_agent}')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Additional Facebook/anti-bot detection prevention
        options.add_argument('--disable-features=IsolateOrigins,site-per-process,SitePerProcess')
        options.add_argument('--disable-site-isolation-trials')
        
        # Additional stealth arguments from the article
        options.add_argument('--disable-popup-blocking')
        options.add_argument('--start-maximized')
        options.add_argument('--disable-extensions')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-setuid-sandbox')
        options.add_argument('--disable-infobars')
        options.add_argument(f'--window-size={screen["width"]},{screen["height"]}')
        options.add_argument(f'--lang={accept_language.split(",")[0].split(";")[0]}')
        
        # Additional anti-detection for Facebook and modern sites
        options.add_argument('--enable-features=NetworkService,NetworkServiceInProcess')
        options.add_argument('--disable-features=VizDisplayCompositor')
        options.add_argument('--force-color-profile=srgb')
        options.add_argument('--metrics-recording-only')
        options.add_argument('--use-mock-keychain')
        
        # Additional stealth preferences
        prefs = {
            "profile.default_content_setting_values.notifications": 2,
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
            "webrtc.ip_handling_policy": "disable_non_proxied_udp",
            "webrtc.multiple_routes_enabled": False,
            "webrtc.nonproxied_udp_enabled": False,
            # Disable external protocol handler prompts
            "profile.default_content_setting_values.protocol_handlers": 2,
            "profile.content_settings.exceptions.protocol_handlers": {}
        }
        options.add_experimental_option("prefs", prefs)
        
    elif browser_type == 'firefox':
        options = webdriver.FirefoxOptions()
        
        # Comprehensive Firefox stealth preferences
        options.set_preference("general.useragent.override", user_agent)
        options.set_preference("dom.webdriver.enabled", False)
        options.set_preference("useAutomationExtension", False)
        options.set_preference("marionette", True)
        
        # Language preferences
        options.set_preference("intl.accept_languages", accept_language)
        options.set_preference("intl.locale.requested", accept_language.split(",")[0].split(";")[0])
        
        # Privacy & tracking preferences
        options.set_preference("privacy.trackingprotection.enabled", False)
        options.set_preference("geo.enabled", False)
        options.set_preference("geo.provider.use_corelocation", False)
        options.set_preference("geo.prompt.testing", False)
        options.set_preference("geo.prompt.testing.allow", False)
        
        # Media preferences (disable WebRTC leaks)
        options.set_preference("media.peerconnection.enabled", False)
        options.set_preference("media.navigator.enabled", False)
        
        # Disable leak detection
        options.set_preference("network.http.sendRefererHeader", 0)
        options.set_preference("network.http.sendSecureXSiteReferrer", False)
        
        # Canvas fingerprinting protection
        options.set_preference("privacy.resistFingerprinting", True)
        options.set_preference("privacy.trackingprotection.fingerprinting.enabled", True)
        
        # WebGL fingerprinting
        options.set_preference("webgl.disabled", False)
        options.set_preference("privacy.resistFingerprinting.block_mozAddonManager", True)
        
        # Notifications
        options.set_preference("dom.webnotifications.enabled", False)
        options.set_preference("dom.push.enabled", False)
        
        # Additional anti-detection
        options.set_preference("browser.startup.page", 0)
        options.set_preference("browser.cache.disk.enable", False)
        options.set_preference("browser.cache.memory.enable", False)
        options.set_preference("browser.cache.offline.enable", False)
        options.set_preference("network.http.use-cache", False)
        
        # Disable external protocol handler prompts (xdg-open, etc.)
        options.set_preference("network.protocol-handler.external-default", False)
        options.set_preference("network.protocol-handler.warn-external-default", False)
        options.set_preference("network.protocol-handler.expose-all", False)
        options.set_preference("network.protocol-handler.expose.http", True)
        options.set_preference("network.protocol-handler.expose.https", True)
        options.set_preference("network.protocol-handler.expose.ftp", True)
        # Disable specific protocol handlers that trigger popups
        options.set_preference("network.protocol-handler.external.mailto", False)
        options.set_preference("network.protocol-handler.external.news", False)
        options.set_preference("network.protocol-handler.external.nntp", False)
        options.set_preference("network.protocol-handler.external.snews", False)
        options.set_preference("network.protocol-handler.external.tel", False)
        options.set_preference("network.protocol-handler.external.webcal", False)
        options.set_preference("network.protocol-handler.external.ms-windows-store", False)
        
    elif browser_type == 'edge':
        options = webdriver.EdgeOptions()
        
        # Comprehensive Edge stealth configuration
        options.add_argument(f'user-agent={user_agent}')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Additional Edge-specific stealth arguments
        options.add_argument('--disable-popup-blocking')
        options.add_argument('--start-maximized')
        options.add_argument('--disable-extensions')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-setuid-sandbox')
        options.add_argument('--disable-infobars')
        options.add_argument(f'--window-size={screen["width"]},{screen["height"]}')
        options.add_argument('--disable-web-security')
        options.add_argument('--disable-features=IsolateOrigins,site-per-process,VizDisplayCompositor')
        options.add_argument(f'--lang={accept_language.split(",")[0].split(";")[0]}')
        options.add_argument('--disable-background-timer-throttling')
        options.add_argument('--disable-backgrounding-occluded-windows')
        options.add_argument('--disable-renderer-backgrounding')
        
        # Edge preferences (similar to Chrome)
        prefs = {
            "profile.default_content_setting_values.notifications": 2,
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
            "webrtc.ip_handling_policy": "disable_non_proxied_udp",
            "webrtc.multiple_routes_enabled": False,
            "webrtc.nonproxied_udp_enabled": False,
            "profile.default_content_setting_values.media_stream_mic": 2,
            "profile.default_content_setting_values.media_stream_camera": 2,
            "profile.default_content_setting_values.geolocation": 2,
            # Disable external protocol handler prompts
            "profile.default_content_setting_values.protocol_handlers": 2,
            "profile.content_settings.exceptions.protocol_handlers": {}
        }
        options.add_experimental_option("prefs", prefs)
    else:
        raise ValueError(f"Unsupported browser: {browser_type}")
    
    print(f'[{browser_type}] Creating browser session with stealth mode...')
    driver = webdriver.Remote(
        command_executor='http://selenium-hub:4444/wd/hub',
        options=options
    )
    
    # Apply comprehensive CDP stealth for Chrome (RemoteWebDriver compatible)
    if browser_type == 'chrome':
        try:
            # Set user agent via CDP
            driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": user_agent,
                "platform": "Win32",
                "acceptLanguage": accept_language
            })
            
            print(f'[{browser_type}] ✓ Applied CDP user agent override')
        except Exception as e:
            print(f'[{browser_type}] ⚠ CDP user agent not applied: {str(e)[:50]}')
        
        # Comprehensive CDP stealth commands
        try:
            driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': f'''
                    // Remove webdriver property completely
                    Object.defineProperty(navigator, 'webdriver', {{
                        get: () => undefined,
                        configurable: true
                    }});
                    
                    // Override Automation-related properties
                    delete navigator.__proto__.webdriver;
                    
                    // Override screen properties with randomized values
                    Object.defineProperty(screen, 'width', {{
                        get: () => {screen["width"]}
                    }});
                    Object.defineProperty(screen, 'height', {{
                        get: () => {screen["height"]}
                    }});
                    Object.defineProperty(screen, 'availWidth', {{
                        get: () => {screen["availWidth"]}
                    }});
                    Object.defineProperty(screen, 'availHeight', {{
                        get: () => {screen["availHeight"]}
                    }});
                    Object.defineProperty(screen, 'colorDepth', {{
                        get: () => {screen["colorDepth"]}
                    }});
                    Object.defineProperty(screen, 'pixelDepth', {{
                        get: () => {screen["pixelDepth"]}
                    }});
                    Object.defineProperty(window, 'devicePixelRatio', {{
                        get: () => {screen["devicePixelRatio"]}
                    }});
                    Object.defineProperty(screen.orientation, 'type', {{
                        get: () => '{screen["orientation"]}'
                    }});
                    
                    // Also override window.innerWidth/Height to match screen
                    Object.defineProperty(window, 'innerWidth', {{
                        get: () => {screen["width"]}
                    }});
                    Object.defineProperty(window, 'innerHeight', {{
                        get: () => {screen["availHeight"]}
                    }});
                    Object.defineProperty(window, 'outerWidth', {{
                        get: () => {screen["width"]}
                    }});
                    Object.defineProperty(window, 'outerHeight', {{
                        get: () => {screen["height"]}
                    }});
                    
                    // Mock plugins (randomized per session, PDF plugins heavily varied)
                    Object.defineProperty(navigator, 'plugins', {{
                        get: () => {plugins_js}
                    }});
                    
                    // Mock mimeTypes
                    Object.defineProperty(navigator, 'mimeTypes', {{
                        get: () => [
                            {{type: "application/pdf", suffixes: "pdf", description: "", enabledPlugin: Plugin}},
                            {{type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format", enabledPlugin: Plugin}}
                        ]
                    }});
                    
                    // Mock languages
                    Object.defineProperty(navigator, 'languages', {{
                        get: () => ['en-US', 'en']
                    }});
                    
                    // Chrome runtime with full objects
                    if (!window.chrome) {{
                        window.chrome = {{}};
                    }}
                    window.chrome.runtime = {{
                        OnInstalledReason: {{
                            CHROME_UPDATE: "chrome_update",
                            INSTALL: "install",
                            SHARED_MODULE_UPDATE: "shared_module_update",
                            UPDATE: "update"
                        }},
                        OnRestartRequiredReason: {{
                            APP_UPDATE: "app_update",
                            OS_UPDATE: "os_update",
                            PERIODIC: "periodic"
                        }},
                        PlatformArch: {{
                            ARM: "arm",
                            ARM64: "arm64",
                            MIPS: "mips",
                            MIPS64: "mips64",
                            X86_32: "x86-32",
                            X86_64: "x86-64"
                        }},
                        PlatformNaclArch: {{
                            ARM: "arm",
                            MIPS: "mips",
                            MIPS64: "mips64",
                            X86_32: "x86-32",
                            X86_64: "x86-64"
                        }},
                        PlatformOs: {{
                            ANDROID: "android",
                            CROS: "cros",
                            LINUX: "linux",
                            MAC: "mac",
                            OPENBSD: "openbsd",
                            WIN: "win"
                        }},
                        RequestUpdateCheckStatus: {{
                            NO_UPDATE: "no_update",
                            THROTTLED: "throttled",
                            UPDATE_AVAILABLE: "update_available"
                        }}
                    }};
                    
                    window.chrome.loadTimes = function() {{
                        return {{
                            commitLoadTime: performance.timing.responseStart / 1000,
                            connectionInfo: "http/1.1",
                            finishDocumentLoadTime: performance.timing.domContentLoadedEventEnd / 1000,
                            finishLoadTime: performance.timing.loadEventEnd / 1000,
                            firstPaintAfterLoadTime: 0,
                            firstPaintTime: performance.timing.responseStart / 1000,
                            navigationType: "Other",
                            npnNegotiatedProtocol: "unknown",
                            requestTime: performance.timing.navigationStart / 1000,
                            startLoadTime: performance.timing.navigationStart / 1000,
                            wasAlternateProtocolAvailable: false,
                            wasFetchedViaSpdy: false,
                            wasNpnNegotiated: false
                        }};
                    }};
                    
                    window.chrome.csi = function() {{
                        return {{
                            onloadT: performance.timing.loadEventEnd,
                            pageT: Date.now() - performance.timing.navigationStart,
                            startE: performance.timing.navigationStart,
                            tran: 15
                        }};
                    }};
                    
                    window.chrome.app = {{
                        isInstalled: false,
                        InstallState: {{
                            DISABLED: 'disabled',
                            INSTALLED: 'installed',
                            NOT_INSTALLED: 'not_installed'
                        }},
                        RunningState: {{
                            CANNOT_RUN: 'cannot_run',
                            READY_TO_RUN: 'ready_to_run',
                            RUNNING: 'running'
                        }}
                    }};
                    
                    // Mock permissions
                    const originalQuery = window.navigator.permissions.query;
                    window.navigator.permissions.query = (parameters) => (
                        parameters.name === 'notifications' ?
                            Promise.resolve({{ state: 'denied' }}) :
                            originalQuery(parameters)
                    );
                    
                    // Mock connection (for Network Information API)
                    Object.defineProperty(navigator, 'connection', {{
                        get: () => ({{
                            effectiveType: '{connection["effectiveType"]}',
                            rtt: {connection["rtt"]},
                            downlink: {connection["downlink"]},
                            saveData: {str(connection["saveData"]).lower()},
                            onchange: null
                        }})
                    }});
                    
                    // Mock hardwareConcurrency (randomized)
                    Object.defineProperty(navigator, 'hardwareConcurrency', {{
                        get: () => {hardware["hardwareConcurrency"]}
                    }});
                    
                    // Mock deviceMemory (randomized)
                    Object.defineProperty(navigator, 'deviceMemory', {{
                        get: () => {hardware["deviceMemory"]}
                    }});
                    
                    // Mock maxTouchPoints (randomized based on device)
                    Object.defineProperty(navigator, 'maxTouchPoints', {{
                        get: () => {hardware["maxTouchPoints"]}
                    }});
                    
                    // Override timezone offset
                    Date.prototype.getTimezoneOffset = function() {{
                        return {timezone_offset};
                    }};
                    
                    // Mock Battery API with randomized realistic values
                    if (navigator.getBattery) {{
                        const batteryInfo = {{
                            charging: {str(battery["charging"]).lower()},
                            chargingTime: {battery["chargingTime"]},
                            dischargingTime: {battery["dischargingTime"]},
                            level: {battery["level"]},
                            addEventListener: function() {{}},
                            removeEventListener: function() {{}},
                            onchargingchange: null,
                            onchargingtimechange: null,
                            ondischargingtimechange: null,
                            onlevelchange: null
                        }};
                        navigator.getBattery = () => Promise.resolve(batteryInfo);
                    }}
                    
                    // Mock media device enumeration with randomized realistic devices
                    if (navigator.mediaDevices && navigator.mediaDevices.enumerateDevices) {{
                        const devices = {str(media_devices).replace("'", '"')};
                        navigator.mediaDevices.enumerateDevices = () => {{
                            return Promise.resolve(devices);
                        }};
                    }}
                    
                    // Canvas fingerprinting protection - add noise injection
                    const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
                    const originalToBlob = HTMLCanvasElement.prototype.toBlob;
                    const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;
                    
                    // Generate consistent noise seed per session
                    const noiseSeed = {random.random()};
                    
                    // Simple hash function for consistent noise
                    function simpleHash(str) {{
                        let hash = 0;
                        for (let i = 0; i < str.length; i++) {{
                            hash = ((hash << 5) - hash) + str.charCodeAt(i);
                            hash = hash & hash;
                        }}
                        return Math.abs(hash);
                    }}
                    
                    // Add minimal noise to canvas data
                    HTMLCanvasElement.prototype.toDataURL = function(...args) {{
                        const context = this.getContext('2d');
                        if (context) {{
                            const imageData = context.getImageData(0, 0, this.width, this.height);
                            for (let i = 0; i < imageData.data.length; i += 4) {{
                                const noise = (simpleHash(i.toString() + noiseSeed) % 5) - 2;
                                imageData.data[i] += noise;     // R
                                imageData.data[i+1] += noise;   // G
                                imageData.data[i+2] += noise;   // B
                            }}
                            context.putImageData(imageData, 0, 0);
                        }}
                        return originalToDataURL.apply(this, args);
                    }};
                    
                    CanvasRenderingContext2D.prototype.getImageData = function(...args) {{
                        const imageData = originalGetImageData.apply(this, args);
                        for (let i = 0; i < imageData.data.length; i += 4) {{
                            const noise = (simpleHash(i.toString() + noiseSeed) % 5) - 2;
                            imageData.data[i] += noise;     // R
                            imageData.data[i+1] += noise;   // G
                            imageData.data[i+2] += noise;   // B
                        }}
                        return imageData;
                    }};
                    
                    // AudioContext fingerprinting - add randomized noise per session
                    const AudioContext = window.AudioContext || window.webkitAudioContext;
                    if (AudioContext) {{
                        const audioNoise = Math.random() * 0.0002 - 0.0001;
                        const originalGetChannelData = AudioBuffer.prototype.getChannelData;
                        AudioBuffer.prototype.getChannelData = function(channel) {{
                            const originalData = originalGetChannelData.call(this, channel);
                            // Add randomized noise per session
                            for (let i = 0; i < originalData.length; i++) {{
                                originalData[i] += audioNoise + (Math.random() - 0.5) * 0.00005;
                            }}
                            return originalData;
                        }};
                        
                        const OriginalAnalyser = window.AnalyserNode || window.webkitAnalyserNode;
                        if (OriginalAnalyser) {{
                            const originalGetFloatFrequencyData = OriginalAnalyser.prototype.getFloatFrequencyData;
                            OriginalAnalyser.prototype.getFloatFrequencyData = function(array) {{
                                originalGetFloatFrequencyData.call(this, array);
                                for (let i = 0; i < array.length; i++) {{
                                    array[i] += (Math.random() - 0.5) * 0.1;
                                }}
                            }};
                        }}
                    }}
                    
                    // Font fingerprinting - wildly randomized per session
                    const availableFonts = {str(fonts)};
                    const originalMeasureText = CanvasRenderingContext2D.prototype.measureText;
                    CanvasRenderingContext2D.prototype.measureText = function(text) {{
                        const metrics = originalMeasureText.call(this, text);
                        // Add noise to font metrics
                        const noise = (Math.random() - 0.5) * 0.0002;
                        Object.defineProperty(metrics, 'width', {{
                            value: metrics.width + noise,
                            writable: false
                        }});
                        return metrics;
                    }};
                    
                    // Mock vendor
                    Object.defineProperty(navigator, 'vendor', {{
                        get: () => 'Google Inc.'
                    }});
                    
                    // Mock platform
                    Object.defineProperty(navigator, 'platform', {{
                        get: () => 'Win32'
                    }});
                    
                    // Fix chrome detection by making sure chrome object is properly defined
                    Object.defineProperty(window, 'chrome', {{
                        get: () => ({{
                            runtime: window.chrome.runtime,
                            loadTimes: window.chrome.loadTimes,
                            csi: window.chrome.csi,
                            app: window.chrome.app
                        }}),
                        configurable: true
                    }});
                    
                    // Make sure toString doesn't reveal native code wrapping
                    const getParameter = WebGLRenderingContext.prototype.getParameter;
                    WebGLRenderingContext.prototype.getParameter = function(parameter) {{
                        // parameter 37445 = UNMASKED_VENDOR_WEBGL
                        if (parameter === 37445) {{
                            return '{gpu["vendor"]}';
                        }}
                        // parameter 37446 = UNMASKED_RENDERER_WEBGL
                        if (parameter === 37446) {{
                            return '{gpu["renderer"]}';
                        }}
                        return getParameter.call(this, parameter);
                    }};
                    
                    // Also override for WebGL2
                    if (typeof WebGL2RenderingContext !== 'undefined') {{
                        const getParameter2 = WebGL2RenderingContext.prototype.getParameter;
                        WebGL2RenderingContext.prototype.getParameter = function(parameter) {{
                            if (parameter === 37445) {{
                                return '{gpu["vendor"]}';
                            }}
                            if (parameter === 37446) {{
                                return '{gpu["renderer"]}';
                            }}
                            return getParameter2.call(this, parameter);
                        }};
                    }}
                '''
            })
            
            # Additional stealth headers
            driver.execute_cdp_cmd('Network.enable', {})
            driver.execute_cdp_cmd('Network.setExtraHTTPHeaders', {
                'headers': {
                    'Accept-Language': accept_language,
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'
                }
            })
            
            print(f'[{browser_type}] ✓ Applied comprehensive CDP stealth')
        except Exception as e:
            print(f'[{browser_type}] ⚠ CDP commands not applied: {str(e)[:50]}')
            
    elif browser_type == 'edge':
        # Edge uses CDP and is Chromium-based, apply comprehensive stealth
        try:
            driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": user_agent,
                "platform": "Win32",
                "acceptLanguage": accept_language
            })
            
            # Comprehensive CDP stealth for Edge
            driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': f'''
                    // Remove webdriver property
                    Object.defineProperty(navigator, 'webdriver', {{
                        get: () => undefined
                    }});
                    
                    // Mock connection (for Network Information API)
                    Object.defineProperty(navigator, 'connection', {{
                        get: () => ({{
                            effectiveType: '{connection["effectiveType"]}',
                            rtt: {connection["rtt"]},
                            downlink: {connection["downlink"]},
                            saveData: {str(connection["saveData"]).lower()},
                            onchange: null
                        }})
                    }});
                    
                    // Mock hardwareConcurrency (randomized)
                    Object.defineProperty(navigator, 'hardwareConcurrency', {{
                        get: () => {hardware["hardwareConcurrency"]}
                    }});
                    
                    // Mock deviceMemory (randomized)
                    Object.defineProperty(navigator, 'deviceMemory', {{
                        get: () => {hardware["deviceMemory"]}
                    }});
                    
                    // Mock maxTouchPoints (randomized based on device)
                    Object.defineProperty(navigator, 'maxTouchPoints', {{
                        get: () => {hardware["maxTouchPoints"]}
                    }});
                    
                    // Override timezone offset
                    Date.prototype.getTimezoneOffset = function() {{
                        return {timezone_offset};
                    }};
                    
                    // Mock Battery API with randomized realistic values
                    if (navigator.getBattery) {{
                        const batteryInfo = {{
                            charging: {str(battery["charging"]).lower()},
                            chargingTime: {battery["chargingTime"]},
                            dischargingTime: {battery["dischargingTime"]},
                            level: {battery["level"]},
                            addEventListener: function() {{}},
                            removeEventListener: function() {{}},
                            onchargingchange: null,
                            onchargingtimechange: null,
                            ondischargingtimechange: null,
                            onlevelchange: null
                        }};
                        navigator.getBattery = () => Promise.resolve(batteryInfo);
                    }}
                    
                    // Mock media device enumeration with randomized realistic devices
                    if (navigator.mediaDevices && navigator.mediaDevices.enumerateDevices) {{
                        const devices = {str(media_devices).replace("'", '"')};
                        navigator.mediaDevices.enumerateDevices = () => {{
                            return Promise.resolve(devices);
                        }};
                    }}
                    
                    // Canvas fingerprinting protection - add noise injection
                    const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
                    const originalToBlob = HTMLCanvasElement.prototype.toBlob;
                    const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;
                    
                    // Generate consistent noise seed per session
                    const noiseSeed = {random.random()};
                    
                    // Simple hash function for consistent noise
                    function simpleHash(str) {{
                        let hash = 0;
                        for (let i = 0; i < str.length; i++) {{
                            hash = ((hash << 5) - hash) + str.charCodeAt(i);
                            hash = hash & hash;
                        }}
                        return Math.abs(hash);
                    }}
                    
                    // Add minimal noise to canvas data
                    HTMLCanvasElement.prototype.toDataURL = function(...args) {{
                        const context = this.getContext('2d');
                        if (context) {{
                            const imageData = context.getImageData(0, 0, this.width, this.height);
                            for (let i = 0; i < imageData.data.length; i += 4) {{
                                const noise = (simpleHash(i.toString() + noiseSeed) % 5) - 2;
                                imageData.data[i] += noise;     // R
                                imageData.data[i+1] += noise;   // G
                                imageData.data[i+2] += noise;   // B
                            }}
                            context.putImageData(imageData, 0, 0);
                        }}
                        return originalToDataURL.apply(this, args);
                    }};
                    
                    CanvasRenderingContext2D.prototype.getImageData = function(...args) {{
                        const imageData = originalGetImageData.apply(this, args);
                        for (let i = 0; i < imageData.data.length; i += 4) {{
                            const noise = (simpleHash(i.toString() + noiseSeed) % 5) - 2;
                            imageData.data[i] += noise;     // R
                            imageData.data[i+1] += noise;   // G
                            imageData.data[i+2] += noise;   // B
                        }}
                        return imageData;
                    }};
                    
                    // AudioContext fingerprinting - add randomized noise per session
                    const AudioContext = window.AudioContext || window.webkitAudioContext;
                    if (AudioContext) {{
                        const audioNoise = Math.random() * 0.0002 - 0.0001;
                        const originalGetChannelData = AudioBuffer.prototype.getChannelData;
                        AudioBuffer.prototype.getChannelData = function(channel) {{
                            const originalData = originalGetChannelData.call(this, channel);
                            // Add randomized noise per session
                            for (let i = 0; i < originalData.length; i++) {{
                                originalData[i] += audioNoise + (Math.random() - 0.5) * 0.00005;
                            }}
                            return originalData;
                        }};
                        
                        const OriginalAnalyser = window.AnalyserNode || window.webkitAnalyserNode;
                        if (OriginalAnalyser) {{
                            const originalGetFloatFrequencyData = OriginalAnalyser.prototype.getFloatFrequencyData;
                            OriginalAnalyser.prototype.getFloatFrequencyData = function(array) {{
                                originalGetFloatFrequencyData.call(this, array);
                                for (let i = 0; i < array.length; i++) {{
                                    array[i] += (Math.random() - 0.5) * 0.1;
                                }}
                            }};
                        }}
                    }}
                    
                    // Font fingerprinting - wildly randomized per session
                    const availableFonts = {str(fonts)};
                    const originalMeasureText = CanvasRenderingContext2D.prototype.measureText;
                    CanvasRenderingContext2D.prototype.measureText = function(text) {{
                        const metrics = originalMeasureText.call(this, text);
                        // Add noise to font metrics
                        const noise = (Math.random() - 0.5) * 0.0002;
                        Object.defineProperty(metrics, 'width', {{
                            value: metrics.width + noise,
                            writable: false
                        }});
                        return metrics;
                    }};
                    
                    // Mock plugins (randomized per session, PDF plugins heavily varied)
                    Object.defineProperty(navigator, 'plugins', {{
                        get: () => {plugins_js}
                    }});
                    
                    // Mock mimeTypes
                    Object.defineProperty(navigator, 'mimeTypes', {{
                        get: () => [
                            {{type: "application/pdf", suffixes: "pdf", description: "", enabledPlugin: Plugin}},
                            {{type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format", enabledPlugin: Plugin}}
                        ]
                    }});
                    
                    // Mock languages
                    Object.defineProperty(navigator, 'languages', {{
                        get: () => ['en-US', 'en']
                    }});
                    
                    // Chrome runtime
                    window.chrome = {{
                        runtime: {{}},
                        loadTimes: function() {{}},
                        csi: function() {{}},
                        app: {{
                            isInstalled: false,
                            InstallState: {{
                                DISABLED: 'disabled',
                                INSTALLED: 'installed',
                                NOT_INSTALLED: 'not_installed'
                            }},
                            RunningState: {{
                                CANNOT_RUN: 'cannot_run',
                                READY_TO_RUN: 'ready_to_run',
                                RUNNING: 'running'
                            }}
                        }}
                    }};
                    
                    // Mock permissions
                    const originalQuery = window.navigator.permissions.query;
                    window.navigator.permissions.query = (parameters) => (
                        parameters.name === 'notifications' ?
                            Promise.resolve({{ state: 'denied' }}) :
                            originalQuery(parameters)
                    );
                    
                    // Override toString
                    const newProto = navigator.__proto__;
                    delete newProto.webdriver;
                    navigator.__proto__ = newProto;
                    
                    // WebGL fingerprinting protection
                    const getParameter = WebGLRenderingContext.prototype.getParameter;
                    WebGLRenderingContext.prototype.getParameter = function(parameter) {{
                        // parameter 37445 = UNMASKED_VENDOR_WEBGL
                        if (parameter === 37445) {{
                            return '{gpu["vendor"]}';
                        }}
                        // parameter 37446 = UNMASKED_RENDERER_WEBGL
                        if (parameter === 37446) {{
                            return '{gpu["renderer"]}';
                        }}
                        return getParameter.call(this, parameter);
                    }};
                    
                    // Also override for WebGL2
                    if (typeof WebGL2RenderingContext !== 'undefined') {{
                        const getParameter2 = WebGL2RenderingContext.prototype.getParameter;
                        WebGL2RenderingContext.prototype.getParameter = function(parameter) {{
                            if (parameter === 37445) {{
                                return '{gpu["vendor"]}';
                            }}
                            if (parameter === 37446) {{
                                return '{gpu["renderer"]}';
                            }}
                            return getParameter2.call(this, parameter);
                        }};
                    }}
                '''
            })
            
            # Additional Edge-specific stealth
            driver.execute_cdp_cmd('Network.enable', {})
            driver.execute_cdp_cmd('Network.setExtraHTTPHeaders', {
                'headers': {
                    'Accept-Language': accept_language,
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
                }
            })
            
            print(f'[{browser_type}] ✓ Applied comprehensive CDP stealth (Edge)')
        except Exception as e:
            print(f'[{browser_type}] ⚠ CDP stealth partially applied: {str(e)[:50]}')
            
    elif browser_type == 'firefox':
        # For Firefox, inject comprehensive stealth script after page load
        driver._stealth_js = f'''
            // Remove webdriver property
            Object.defineProperty(navigator, 'webdriver', {{
                get: () => undefined,
                configurable: true
            }});
            
            // Override screen properties with randomized values
            Object.defineProperty(screen, 'width', {{
                get: () => {screen["width"]},
                configurable: true
            }});
            Object.defineProperty(screen, 'height', {{
                get: () => {screen["height"]},
                configurable: true
            }});
            Object.defineProperty(screen, 'availWidth', {{
                get: () => {screen["availWidth"]},
                configurable: true
            }});
            Object.defineProperty(screen, 'availHeight', {{
                get: () => {screen["availHeight"]},
                configurable: true
            }});
            Object.defineProperty(screen, 'colorDepth', {{
                get: () => {screen["colorDepth"]},
                configurable: true
            }});
            Object.defineProperty(screen, 'pixelDepth', {{
                get: () => {screen["pixelDepth"]},
                configurable: true
            }});
            Object.defineProperty(window, 'devicePixelRatio', {{
                get: () => {screen["devicePixelRatio"]},
                configurable: true
            }});
            
            // Also override window.innerWidth/Height to match screen
            Object.defineProperty(window, 'innerWidth', {{
                get: () => {screen["width"]},
                configurable: true
            }});
            Object.defineProperty(window, 'innerHeight', {{
                get: () => {screen["availHeight"]},
                configurable: true
            }});
            Object.defineProperty(window, 'outerWidth', {{
                get: () => {screen["width"]},
                configurable: true
            }});
            Object.defineProperty(window, 'outerHeight', {{
                get: () => {screen["height"]},
                configurable: true
            }});
            
            // Mock plugins (randomized per session, PDF plugins heavily varied)
            Object.defineProperty(navigator, 'plugins', {{
                get: () => {plugins_js},
                configurable: true
            }});
            
            // Mock mimeTypes  
            Object.defineProperty(navigator, 'mimeTypes', {{
                get: () => [
                    {{type: "application/pdf", suffixes: "pdf", description: "Portable Document Format"}}
                ],
                configurable: true
            }});
            
            // Mock languages
            Object.defineProperty(navigator, 'languages', {{
                get: () => ['en-US', 'en'],
                configurable: true
            }});
            
            // Mock connection (for Network Information API)
            Object.defineProperty(navigator, 'connection', {{
                get: () => ({{
                    effectiveType: '{connection["effectiveType"]}',
                    rtt: {connection["rtt"]},
                    downlink: {connection["downlink"]},
                    saveData: {str(connection["saveData"]).lower()},
                    onchange: null
                }}),
                configurable: true
            }});
            
            // Mock hardwareConcurrency (randomized)
            Object.defineProperty(navigator, 'hardwareConcurrency', {{
                get: () => {hardware["hardwareConcurrency"]},
                configurable: true
            }});
            
            // Mock deviceMemory (randomized)
            Object.defineProperty(navigator, 'deviceMemory', {{
                get: () => {hardware["deviceMemory"]},
                configurable: true
            }});
            
            // Mock maxTouchPoints (randomized based on device)
            Object.defineProperty(navigator, 'maxTouchPoints', {{
                get: () => {hardware["maxTouchPoints"]},
                configurable: true
            }});
            
            // Override timezone offset
            Date.prototype.getTimezoneOffset = function() {{
                return {timezone_offset};
            }};
            
            // Mock Battery API with randomized realistic values
            if (navigator.getBattery) {{
                const batteryInfo = {{
                    charging: {str(battery["charging"]).lower()},
                    chargingTime: {battery["chargingTime"]},
                    dischargingTime: {battery["dischargingTime"]},
                    level: {battery["level"]},
                    addEventListener: function() {{}},
                    removeEventListener: function() {{}},
                    onchargingchange: null,
                    onchargingtimechange: null,
                    ondischargingtimechange: null,
                    onlevelchange: null
                }};
                navigator.getBattery = () => Promise.resolve(batteryInfo);
            }}
            
            // Mock media device enumeration with randomized realistic devices
            if (navigator.mediaDevices && navigator.mediaDevices.enumerateDevices) {{
                const devices = {str(media_devices).replace("'", '"')};
                navigator.mediaDevices.enumerateDevices = () => {{
                    return Promise.resolve(devices);
                }};
            }}
            
            // Canvas fingerprinting protection - add noise injection
            const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
            const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;
            
            // Generate consistent noise seed per session
            const noiseSeed = {random.random()};
            
            // Simple hash function for consistent noise
            function simpleHash(str) {{
                let hash = 0;
                for (let i = 0; i < str.length; i++) {{
                    hash = ((hash << 5) - hash) + str.charCodeAt(i);
                    hash = hash & hash;
                }}
                return Math.abs(hash);
            }}
            
            // Add minimal noise to canvas data
            HTMLCanvasElement.prototype.toDataURL = function(...args) {{
                const context = this.getContext('2d');
                if (context) {{
                    const imageData = context.getImageData(0, 0, this.width, this.height);
                    for (let i = 0; i < imageData.data.length; i += 4) {{
                        const noise = (simpleHash(i.toString() + noiseSeed) % 5) - 2;
                        imageData.data[i] += noise;     // R
                        imageData.data[i+1] += noise;   // G
                        imageData.data[i+2] += noise;   // B
                    }}
                    context.putImageData(imageData, 0, 0);
                }}
                return originalToDataURL.apply(this, args);
            }};
            
            CanvasRenderingContext2D.prototype.getImageData = function(...args) {{
                const imageData = originalGetImageData.apply(this, args);
                for (let i = 0; i < imageData.data.length; i += 4) {{
                    const noise = (simpleHash(i.toString() + noiseSeed) % 5) - 2;
                    imageData.data[i] += noise;     // R
                    imageData.data[i+1] += noise;   // G
                    imageData.data[i+2] += noise;   // B
                }}
                return imageData;
            }};
            
            // AudioContext fingerprinting - add randomized noise per session
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            if (AudioContext) {{
                const audioNoise = Math.random() * 0.0002 - 0.0001;
                const originalGetChannelData = AudioBuffer.prototype.getChannelData;
                AudioBuffer.prototype.getChannelData = function(channel) {{
                    const originalData = originalGetChannelData.call(this, channel);
                    // Add randomized noise per session
                    for (let i = 0; i < originalData.length; i++) {{
                        originalData[i] += audioNoise + (Math.random() - 0.5) * 0.00005;
                    }}
                    return originalData;
                }};
                
                const OriginalAnalyser = window.AnalyserNode || window.webkitAnalyserNode;
                if (OriginalAnalyser) {{
                    const originalGetFloatFrequencyData = OriginalAnalyser.prototype.getFloatFrequencyData;
                    OriginalAnalyser.prototype.getFloatFrequencyData = function(array) {{
                        originalGetFloatFrequencyData.call(this, array);
                        for (let i = 0; i < array.length; i++) {{
                            array[i] += (Math.random() - 0.5) * 0.1;
                        }}
                    }};
                }}
            }}
            
            // Font fingerprinting - wildly randomized per session
            const availableFonts = {str(fonts)};
            const originalMeasureText = CanvasRenderingContext2D.prototype.measureText;
            CanvasRenderingContext2D.prototype.measureText = function(text) {{
                const metrics = originalMeasureText.call(this, text);
                // Add noise to font metrics
                const noise = (Math.random() - 0.5) * 0.0002;
                Object.defineProperty(metrics, 'width', {{
                    value: metrics.width + noise,
                    writable: false
                }});
                return metrics;
            }};
            
            // WebGL fingerprinting protection
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {{
                // parameter 37445 = UNMASKED_VENDOR_WEBGL
                if (parameter === 37445) {{
                    return '{gpu["vendor"]}';
                }}
                // parameter 37446 = UNMASKED_RENDERER_WEBGL
                if (parameter === 37446) {{
                    return '{gpu["renderer"]}';
                }}
                return getParameter.call(this, parameter);
            }};
            
            // Also override for WebGL2
            if (typeof WebGL2RenderingContext !== 'undefined') {{
                const getParameter2 = WebGL2RenderingContext.prototype.getParameter;
                WebGL2RenderingContext.prototype.getParameter = function(parameter) {{
                    if (parameter === 37445) {{
                        return '{gpu["vendor"]}';
                    }}
                    if (parameter === 37446) {{
                        return '{gpu["renderer"]}';
                    }}
                    return getParameter2.call(this, parameter);
                }};
            }}
            
            // Mock permissions
            if (navigator.permissions) {{
                const originalQuery = navigator.permissions.query;
                navigator.permissions.query = function(parameters) {{
                    if (parameters.name === 'notifications') {{
                        return Promise.resolve({{ state: 'denied' }});
                    }}
                    return originalQuery(parameters);
                }};
            }}
        '''
        print(f'[{browser_type}] ✓ Prepared comprehensive stealth script (will inject on page load)')
    
    driver.set_page_load_timeout(30)
    driver.set_window_size(screen["width"], screen["height"])
    
    print(f'[{browser_type}] ✓ Browser ready with advanced stealth mode')
    
    return driver

def manage_tabs(driver, browser_type, current_browsing_tab, max_tabs=8):
    """
    Manage open tabs realistically - keep some open, close others randomly
    
    Args:
        driver: WebDriver instance
        browser_type: Browser name for logging
        current_browsing_tab: The tab we're currently browsing
        max_tabs: Maximum number of tabs to keep open (default 8)
    
    Returns:
        tuple: (current_browsing_tab, switched_tab)
               switched_tab is True if we switched to a different tab
    """
    try:
        all_handles = driver.window_handles
        
        # If only one tab, nothing to do
        if len(all_handles) <= 1:
            return current_browsing_tab, False
        
        # If we have too many tabs, close some randomly
        if len(all_handles) > max_tabs:
            num_to_close = len(all_handles) - max_tabs
            print(f'  [{browser_type}] 🗂️ Too many tabs ({len(all_handles)}), closing {num_to_close}...')
            
            # Never close the current browsing tab
            closeable_handles = [h for h in all_handles if h != current_browsing_tab]
            
            # Randomly select tabs to close
            tabs_to_close = random.sample(closeable_handles, min(num_to_close, len(closeable_handles)))
            
            for handle in tabs_to_close:
                try:
                    driver.switch_to.window(handle)
                    driver.close()
                except:
                    pass
            
            # Switch back to current browsing tab
            try:
                driver.switch_to.window(current_browsing_tab)
            except:
                # Current tab was somehow closed, use first available
                if driver.window_handles:
                    current_browsing_tab = driver.window_handles[0]
                    driver.switch_to.window(current_browsing_tab)
        
        # Randomly decide if we should switch tabs (30% chance if multiple tabs exist)
        all_handles = driver.window_handles
        if len(all_handles) > 1 and random.random() < 0.3:
            # Switch to a random different tab
            other_handles = [h for h in all_handles if h != current_browsing_tab]
            if other_handles:
                new_tab = random.choice(other_handles)
                driver.switch_to.window(new_tab)
                print(f'  [{browser_type}] 🔄 Switched to different tab ({len(all_handles)} tabs open)')
                return new_tab, True
        
        # Make sure we're on the current browsing tab
        if driver.current_window_handle != current_browsing_tab:
            try:
                driver.switch_to.window(current_browsing_tab)
            except:
                # Tab no longer exists, use first available
                if driver.window_handles:
                    current_browsing_tab = driver.window_handles[0]
                    driver.switch_to.window(current_browsing_tab)
        
        return current_browsing_tab, False
        
    except Exception as e:
        print(f'  [{browser_type}] ⚠ Tab management error: {str(e)[:50]}')
        # Try to recover
        try:
            if driver.window_handles:
                if current_browsing_tab in driver.window_handles:
                    driver.switch_to.window(current_browsing_tab)
                else:
                    current_browsing_tab = driver.window_handles[0]
                    driver.switch_to.window(current_browsing_tab)
        except:
            pass
        return current_browsing_tab, False

def handle_new_tab_from_ad(driver, browser_type, current_browsing_tab):
    """
    Handle new tabs opened by ads - randomly decide to browse it or close it
    
    Returns:
        tuple: (current_browsing_tab, browsing_new_tab)
               browsing_new_tab is True if we switched to browse the new ad tab
    """
    try:
        all_handles = driver.window_handles
        
        # Find new tabs (any tab that's not the current one)
        new_tabs = [h for h in all_handles if h != current_browsing_tab]
        
        if not new_tabs:
            return current_browsing_tab, False
        
        # 40% chance to browse the ad's new tab
        if random.random() < 0.4:
            new_tab = random.choice(new_tabs)
            driver.switch_to.window(new_tab)
            print(f'  [{browser_type}] 🆕 Switched to browse ad tab! ({len(all_handles)} tabs open)')
            return new_tab, True
        else:
            # Stay on current tab, but keep the new tabs open (will be managed later)
            driver.switch_to.window(current_browsing_tab)
            print(f'  [{browser_type}] 📌 Keeping current tab, {len(new_tabs)} new tab(s) in background')
            return current_browsing_tab, False
            
    except Exception as e:
        # On error, return to current tab
        try:
            if current_browsing_tab in driver.window_handles:
                driver.switch_to.window(current_browsing_tab)
            elif driver.window_handles:
                current_browsing_tab = driver.window_handles[0]
                driver.switch_to.window(current_browsing_tab)
        except:
            pass
        return current_browsing_tab, False

def browse():
    """Main browsing function - creates chaos by clicking through random links"""
    browser_type = random.choice(browsers)
    print(f'\n{"="*60}')
    print(f'Starting {browser_type} browser')
    print(f'{"="*60}')
    
    driver = create_driver(browser_type)
    
    # Store the current browsing tab (starts as main window)
    current_browsing_tab = driver.current_window_handle
    max_tabs = random.randint(5, 10)  # Random max tabs between 5-10
    
    # Keep track of websites visited in this session
    websites_visited = 0
    max_websites_per_session = random.randint(80, 120)  # 80-120 sites per session
    
    print(f'[{browser_type}] 🎯 Session goal: Visit {max_websites_per_session} websites')
    print(f'[{browser_type}] 📍 Initial tab: {current_browsing_tab[:8]}... (max {max_tabs} tabs)')
    
    while websites_visited < max_websites_per_session:
        try:
            start_url = random.choice(sites)
            start_domain = get_domain(start_url)
            websites_visited += 1
            
            # Manage tabs before navigating
            current_browsing_tab, tab_switched = manage_tabs(driver, browser_type, current_browsing_tab, max_tabs)
            
            if tab_switched:
                # If we switched tabs, continue browsing the new tab
                print(f'\n[{browser_type}] 🌐 Continuing on switched tab...')
                time.sleep(random.uniform(1, 3))
            else:
                # Navigate to new URL
                print(f'\n[{browser_type}] 🌐 Website {websites_visited}/{max_websites_per_session}: {start_url}')
                driver.get(start_url)
            
            # Inject stealth script for Firefox
            if hasattr(driver, '_stealth_js'):
                try:
                    driver.execute_script(driver._stealth_js)
                except:
                    pass
            
            # Random human-like delay
            time.sleep(random.uniform(2, 5))
            
            # Auto-accept cookies
            auto_accept_cookies(driver, browser_type)
            
            # Try to detect and click ads (60% chance)
            initial_tab_count = len(driver.window_handles)
            detect_and_click_ads(driver, browser_type, click_chance=0.6)
            
            # Handle new tabs from ads (40% chance to switch to ad tab)
            if len(driver.window_handles) > initial_tab_count:
                current_browsing_tab, switched_to_ad = handle_new_tab_from_ad(driver, browser_type, current_browsing_tab)
                if switched_to_ad:
                    # We're now browsing the ad tab, inject stealth and continue
                    if hasattr(driver, '_stealth_js'):
                        try:
                            driver.execute_script(driver._stealth_js)
                        except:
                            pass
                    time.sleep(random.uniform(1, 2))
            
            # Simulate human reading/scrolling behavior on first page
            for _ in range(random.randint(1, 2)):
                scroll_amount = random.randint(200, 500)
                driver.execute_script(f'window.scrollBy(0, {scroll_amount});')
                time.sleep(random.uniform(0.8, 2.0))
            
            time.sleep(random.uniform(1, 3))
            
            # Navigate through links on this website
            max_depth = random.randint(3, 8)  # Reduced depth per site to visit more sites
            current_depth = 0
            
            while current_depth < max_depth:
                try:
                    # Manage tabs at each iteration (might switch tabs randomly)
                    current_browsing_tab, tab_switched = manage_tabs(driver, browser_type, current_browsing_tab, max_tabs)
                    
                    if tab_switched:
                        # We switched to a different tab, continue browsing it
                        time.sleep(random.uniform(1, 2))
                    
                    current_url = driver.current_url
                    current_domain = get_domain(current_url)
                    
                    # Scroll the page with more human-like behavior
                    scroll_count = random.randint(1, 3)
                    for i in range(scroll_count):
                        # Variable scroll amounts
                        scroll_position = random.randint(100, 1000)
                        driver.execute_script(f'window.scrollBy(0, {scroll_position});')
                        
                        # Human-like pauses (sometimes longer, sometimes shorter)
                        if random.random() < 0.3:  # 30% chance of longer pause
                            time.sleep(random.uniform(2, 4))
                        else:
                            time.sleep(random.uniform(0.5, 1.5))
                        
                        # Occasionally scroll back up a bit
                        if random.random() < 0.2:  # 20% chance
                            driver.execute_script(f'window.scrollBy(0, -{random.randint(50, 200)});')
                            time.sleep(random.uniform(0.3, 0.8))
                    
                    # Find clickable links - be more lenient
                    links = driver.find_elements(By.TAG_NAME, 'a')
                    if not links:
                        print(f'  [{browser_type}] No links found at depth {current_depth}, moving to next website')
                        break
                    
                    # Get more links and filter less strictly
                    clickable = []
                    for link in links[:200]:  # Check more links
                        try:
                            if link.is_displayed() and link.is_enabled():
                                href = link.get_attribute('href')
                                if href and (href.startswith('http://') or href.startswith('https://')):
                                    clickable.append(link)
                        except:
                            continue
                    
                    if not clickable:
                        print(f'  [{browser_type}] No clickable links at depth {current_depth}, moving to next website')
                        break
                    
                    print(f'  [{browser_type}] Found {len(clickable)} clickable links')
                    
                    # Separate internal and external links
                    internal_links = []
                    external_links = []
                    
                    for link in clickable:
                        try:
                            href = link.get_attribute('href')
                            if href:
                                link_domain = get_domain(href)
                                # More lenient domain matching (including subdomains)
                                if link_domain == start_domain or start_domain in link_domain or link_domain in start_domain:
                                    internal_links.append(link)
                                else:
                                    external_links.append(link)
                        except:
                            continue
                    
                    print(f'  [{browser_type}] Internal: {len(internal_links)}, External: {len(external_links)}')
                    
                    # Choose link strategy - prefer internal to stay on site longer
                    chosen_link = None
                    if internal_links and random.random() < 0.8:  # 80% prefer internal
                        chosen_link = random.choice(internal_links)
                        print(f'  [{browser_type}] Depth {current_depth}: Choosing internal link')
                    elif external_links:
                        chosen_link = random.choice(external_links)
                        print(f'  [{browser_type}] Depth {current_depth}: Choosing external link (will move to next website)')
                        # If we go external, break after this click to count as new website
                    elif internal_links:
                        chosen_link = random.choice(internal_links)
                    elif clickable:
                        chosen_link = random.choice(clickable)
                    
                    if chosen_link:
                        try:
                            href = chosen_link.get_attribute('href')
                            link_domain = get_domain(href)
                            print(f'  [{browser_type}] Depth {current_depth}: {href[:80]}')
                            
                            # Human-like delay before clicking
                            time.sleep(random.uniform(0.5, 1.5))
                            
                            # Try multiple click methods (handle intercepted clicks)
                            click_success = False
                            
                            # Method 1: Regular click
                            try:
                                chosen_link.click()
                                click_success = True
                            except Exception as e:
                                if 'intercepted' in str(e).lower():
                                    print(f'  [{browser_type}] Click intercepted, trying alternative methods...')
                                    
                                    # Method 2: Scroll into view and click
                                    try:
                                        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", chosen_link)
                                        time.sleep(0.5)
                                        chosen_link.click()
                                        click_success = True
                                    except:
                                        # Method 3: JavaScript click (most reliable)
                                        try:
                                            driver.execute_script("arguments[0].click();", chosen_link)
                                            click_success = True
                                            print(f'  [{browser_type}] ✓ Used JavaScript click')
                                        except:
                                            # Method 4: Navigate directly
                                            try:
                                                driver.get(href)
                                                click_success = True
                                                print(f'  [{browser_type}] ✓ Navigated directly to URL')
                                            except:
                                                pass
                                else:
                                    # Some other error, try JavaScript click
                                    try:
                                        driver.execute_script("arguments[0].click();", chosen_link)
                                        click_success = True
                                    except:
                                        pass
                            
                            if not click_success:
                                print(f'  [{browser_type}] ⚠ Could not click link, skipping')
                                continue
                            
                            # Variable delay after click (humans don't click instantly)
                            time.sleep(random.uniform(2, 5))
                            
                            # Check if link opened new tabs
                            if len(driver.window_handles) > len(driver.window_handles):
                                current_browsing_tab, switched_to_new = handle_new_tab_from_ad(driver, browser_type, current_browsing_tab)
                            
                            # Try to accept cookies on new page (but don't wait too long)
                            try:
                                auto_accept_cookies(driver, browser_type)
                            except:
                                pass
                            
                            # Occasionally try to click ads (60% chance)
                            if random.random() < 0.4:  # 40% of the time, try to click ads
                                try:
                                    initial_tabs = len(driver.window_handles)
                                    detect_and_click_ads(driver, browser_type, click_chance=0.6)
                                    
                                    # Handle new tabs from ads
                                    if len(driver.window_handles) > initial_tabs:
                                        current_browsing_tab, _ = handle_new_tab_from_ad(driver, browser_type, current_browsing_tab)
                                except:
                                    pass
                            
                            current_depth += 1
                            
                            # If we went to external site, break to count as new website
                            if link_domain != start_domain:
                                print(f'  [{browser_type}] 🔄 Moved to external site, counting as next website')
                                websites_visited += 1
                                start_domain = link_domain
                                break
                                
                        except Exception as click_error:
                            print(f'  [{browser_type}] Navigation failed: {str(click_error)[:50]}')
                            continue
                    else:
                        print(f'  [{browser_type}] No suitable link found at depth {current_depth}')
                        break
                        
                except Exception as nav_error:
                    print(f'  [{browser_type}] Navigation error: {str(nav_error)[:50]}')
                    break
            
            print(f'[{browser_type}] ✓ Finished exploring website. Depth: {current_depth}/{max_depth}')
            time.sleep(random.uniform(1, 3))
            
        except TimeoutException:
            print(f'[{browser_type}] ⏱ Timeout, moving to next website')
            websites_visited += 1
        except WebDriverException as e:
            print(f'[{browser_type}] ⚠ WebDriver error: {str(e)[:80]}')
            print(f'[{browser_type}] Trying to continue with same session...')
            time.sleep(2)
        except Exception as e:
            print(f'[{browser_type}] ⚠ Error: {str(e)[:80]}')
    
    # Session complete, close browser
    print(f'\n[{browser_type}] ✅ Session complete! Visited {websites_visited} websites.')
    print(f'[{browser_type}] Closing browser and starting new session...')
    try:
        driver.quit()
    except:
        pass

if __name__ == '__main__':
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║   Browser Chaos Generator                                  ║
    ║   Automated browsing to generate web traffic               ║
    ╚════════════════════════════════════════════════════════════╝
    """)
    
    print(f"Available browsers: {', '.join(browsers)}")
    print("\nStarting in 5 seconds...")
    time.sleep(5)
    
    while True:
        try:
            browse()
        except Exception as e:
            print(f'\n⚠ Fatal error: {e}')
            print('Restarting in 5 seconds...')
            time.sleep(5)
