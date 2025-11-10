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

def auto_accept_cookies(driver, browser_type):
    """Automatically detect and click cookie consent buttons"""
    try:
        # Common cookie consent button selectors and text patterns
        cookie_selectors = [
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
            
            # Generic buttons (will match by text)
            'button', 'a.button', '.btn', '[role="button"]', 'div[onclick]'
        ]
        
        # Common text patterns for accept buttons (case insensitive)
        accept_text_patterns = [
            'accept all', 'accept cookies', 'i accept', 'allow all', 'allow cookies',
            'agree', 'got it', 'ok', 'continue', 'agree and close', 'accept & close',
            'accept and continue', 'accepter', 'aceptar', 'akzeptieren', 'accetto',
            'aceitar', 'acceptera', 'ja, accepteren', 'zgadzam się', 'souhlasím',
            'συμφωνώ', 'принимаю', 'kabul ediyorum', 'موافق'
        ]
        
        # Try specific selectors first (faster and more reliable)
        for selector in cookie_selectors[:15]:  # Try the most specific ones first
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
        
        # Try finding buttons by text content
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
        
        # Try iframe-based cookie consent (some use iframes)
        try:
            iframes = driver.find_elements(By.TAG_NAME, 'iframe')
            for iframe in iframes:
                try:
                    iframe_name = iframe.get_attribute('name') or iframe.get_attribute('id') or ''
                    if any(keyword in iframe_name.lower() for keyword in ['cookie', 'consent', 'gdpr', 'privacy']):
                        driver.switch_to.frame(iframe)
                        
                        # Try to find accept button in iframe
                        for selector in cookie_selectors[:10]:
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
        
        return False
        
    except Exception as e:
        # Don't let cookie handling break the automation
        return False

def detect_and_click_ads(driver, browser_type, click_chance=0.6):
    """Detect ads on page and optionally click them (60% chance by default)"""
    try:
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
            
            # If a new tab/window opened, close it and return to original
            if len(driver.window_handles) > 1:
                driver.switch_to.window(driver.window_handles[-1])
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
                print(f'  [{browser_type}] 🔄 Closed ad tab, returned to main window')
            
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
                        
                        # Close any new windows
                        if len(driver.window_handles) > 1:
                            driver.switch_to.window(driver.window_handles[-1])
                            driver.close()
                            driver.switch_to.window(driver.window_handles[0])
                        
                        return True
                    driver.switch_to.default_content()
            except:
                try:
                    driver.switch_to.default_content()
                except:
                    pass
            
            return False
            
    except Exception as e:
        # Don't let ad clicking break the automation
        return False

def create_driver(browser_type):
    """Create a Selenium WebDriver for automated browsing with anti-detection"""
    
    # Generate a random realistic user agent (thousands of combinations possible)
    user_agent = generate_random_user_agent()
    print(f'[{browser_type}] Generated UA: {user_agent[:80]}...')
    
    if browser_type == 'chrome':
        options = webdriver.ChromeOptions()
        
        # Selenium Stealth recommended options
        options.add_argument(f'user-agent={user_agent}')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Additional stealth arguments from the article
        options.add_argument('--disable-popup-blocking')
        options.add_argument('--start-maximized')
        options.add_argument('--disable-extensions')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-setuid-sandbox')
        options.add_argument('--disable-infobars')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-web-security')
        options.add_argument('--disable-features=IsolateOrigins,site-per-process')
        options.add_argument('--lang=en-US,en;q=0.9')
        
        # Additional stealth preferences
        prefs = {
            "profile.default_content_setting_values.notifications": 2,
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
            "webrtc.ip_handling_policy": "disable_non_proxied_udp",
            "webrtc.multiple_routes_enabled": False,
            "webrtc.nonproxied_udp_enabled": False
        }
        options.add_experimental_option("prefs", prefs)
        
    elif browser_type == 'firefox':
        options = webdriver.FirefoxOptions()
        
        # Comprehensive Firefox stealth preferences
        options.set_preference("general.useragent.override", user_agent)
        options.set_preference("dom.webdriver.enabled", False)
        options.set_preference("useAutomationExtension", False)
        options.set_preference("marionette", True)
        
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
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-web-security')
        options.add_argument('--disable-features=IsolateOrigins,site-per-process,VizDisplayCompositor')
        options.add_argument('--lang=en-US,en;q=0.9')
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
            "profile.default_content_setting_values.geolocation": 2
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
                "acceptLanguage": "en-US,en;q=0.9"
            })
            
            print(f'[{browser_type}] ✓ Applied CDP user agent override')
        except Exception as e:
            print(f'[{browser_type}] ⚠ CDP user agent not applied: {str(e)[:50]}')
        
        # Comprehensive CDP stealth commands
        try:
            driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    // Remove webdriver property
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                    
                    // Mock plugins (realistic Chrome plugins)
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [
                            {
                                0: {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format", enabledPlugin: Plugin},
                                description: "Portable Document Format",
                                filename: "internal-pdf-viewer",
                                length: 1,
                                name: "Chrome PDF Plugin"
                            },
                            {
                                0: {type: "application/pdf", suffixes: "pdf", description: "", enabledPlugin: Plugin},
                                description: "",
                                filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai",
                                length: 1,
                                name: "Chrome PDF Viewer"
                            },
                            {
                                description: "Native Client Executable",
                                filename: "internal-nacl-plugin",
                                length: 2,
                                name: "Native Client"
                            }
                        ]
                    });
                    
                    // Mock mimeTypes
                    Object.defineProperty(navigator, 'mimeTypes', {
                        get: () => [
                            {type: "application/pdf", suffixes: "pdf", description: "", enabledPlugin: Plugin},
                            {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format", enabledPlugin: Plugin}
                        ]
                    });
                    
                    // Mock languages
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['en-US', 'en']
                    });
                    
                    // Chrome runtime with full objects
                    window.chrome = {
                        runtime: {},
                        loadTimes: function() {},
                        csi: function() {},
                        app: {
                            isInstalled: false,
                            InstallState: {
                                DISABLED: 'disabled',
                                INSTALLED: 'installed',
                                NOT_INSTALLED: 'not_installed'
                            },
                            RunningState: {
                                CANNOT_RUN: 'cannot_run',
                                READY_TO_RUN: 'ready_to_run',
                                RUNNING: 'running'
                            }
                        }
                    };
                    
                    // Mock permissions
                    const originalQuery = window.navigator.permissions.query;
                    window.navigator.permissions.query = (parameters) => (
                        parameters.name === 'notifications' ?
                            Promise.resolve({ state: 'denied' }) :
                            originalQuery(parameters)
                    );
                    
                    // Mock connection (for Network Information API)
                    Object.defineProperty(navigator, 'connection', {
                        get: () => ({
                            effectiveType: '4g',
                            rtt: 100,
                            downlink: 10,
                            saveData: false
                        })
                    });
                    
                    // Override toString to hide modifications
                    const newProto = navigator.__proto__;
                    delete newProto.webdriver;
                    navigator.__proto__ = newProto;
                '''
            })
            
            # Additional stealth headers
            driver.execute_cdp_cmd('Network.enable', {})
            driver.execute_cdp_cmd('Network.setExtraHTTPHeaders', {
                'headers': {
                    'Accept-Language': 'en-US,en;q=0.9',
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
                "acceptLanguage": "en-US,en;q=0.9"
            })
            
            # Comprehensive CDP stealth for Edge
            driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    // Remove webdriver property
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                    
                    // Mock plugins
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [
                            {
                                0: {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format", enabledPlugin: Plugin},
                                description: "Portable Document Format",
                                filename: "internal-pdf-viewer",
                                length: 1,
                                name: "Chrome PDF Plugin"
                            },
                            {
                                0: {type: "application/pdf", suffixes: "pdf", description: "", enabledPlugin: Plugin},
                                description: "",
                                filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai",
                                length: 1,
                                name: "Chrome PDF Viewer"
                            },
                            {
                                description: "Native Client Executable",
                                filename: "internal-nacl-plugin",
                                length: 2,
                                name: "Native Client"
                            }
                        ]
                    });
                    
                    // Mock mimeTypes
                    Object.defineProperty(navigator, 'mimeTypes', {
                        get: () => [
                            {type: "application/pdf", suffixes: "pdf", description: "", enabledPlugin: Plugin},
                            {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format", enabledPlugin: Plugin}
                        ]
                    });
                    
                    // Mock languages
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['en-US', 'en']
                    });
                    
                    // Chrome runtime
                    window.chrome = {
                        runtime: {},
                        loadTimes: function() {},
                        csi: function() {},
                        app: {
                            isInstalled: false,
                            InstallState: {
                                DISABLED: 'disabled',
                                INSTALLED: 'installed',
                                NOT_INSTALLED: 'not_installed'
                            },
                            RunningState: {
                                CANNOT_RUN: 'cannot_run',
                                READY_TO_RUN: 'ready_to_run',
                                RUNNING: 'running'
                            }
                        }
                    };
                    
                    // Mock permissions
                    const originalQuery = window.navigator.permissions.query;
                    window.navigator.permissions.query = (parameters) => (
                        parameters.name === 'notifications' ?
                            Promise.resolve({ state: 'denied' }) :
                            originalQuery(parameters)
                    );
                    
                    // Override toString
                    const newProto = navigator.__proto__;
                    delete newProto.webdriver;
                    navigator.__proto__ = newProto;
                '''
            })
            
            # Additional Edge-specific stealth
            driver.execute_cdp_cmd('Network.enable', {})
            driver.execute_cdp_cmd('Network.setExtraHTTPHeaders', {
                'headers': {
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
                }
            })
            
            print(f'[{browser_type}] ✓ Applied comprehensive CDP stealth (Edge)')
        except Exception as e:
            print(f'[{browser_type}] ⚠ CDP stealth partially applied: {str(e)[:50]}')
            
    elif browser_type == 'firefox':
        # For Firefox, inject comprehensive stealth script after page load
        driver._stealth_js = '''
            // Remove webdriver property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
                configurable: true
            });
            
            // Mock plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [
                    {
                        0: {type: "application/x-test", suffixes: "test", description: "Test Plugin"},
                        description: "Test Plugin",
                        filename: "test-plugin",
                        length: 1,
                        name: "Test Plugin"
                    }
                ],
                configurable: true
            });
            
            // Mock mimeTypes  
            Object.defineProperty(navigator, 'mimeTypes', {
                get: () => [
                    {type: "application/pdf", suffixes: "pdf", description: "Portable Document Format"}
                ],
                configurable: true
            });
            
            // Mock languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
                configurable: true
            });
            
            // Mock hardwareConcurrency
            Object.defineProperty(navigator, 'hardwareConcurrency', {
                get: () => 8,
                configurable: true
            });
            
            // Mock deviceMemory
            Object.defineProperty(navigator, 'deviceMemory', {
                get: () => 8,
                configurable: true
            });
            
            // Mock permissions
            if (navigator.permissions) {
                const originalQuery = navigator.permissions.query;
                navigator.permissions.query = function(parameters) {
                    if (parameters.name === 'notifications') {
                        return Promise.resolve({ state: 'denied' });
                    }
                    return originalQuery(parameters);
                };
            }
        '''
        print(f'[{browser_type}] ✓ Prepared comprehensive stealth script (will inject on page load)')
    
    driver.set_page_load_timeout(30)
    driver.set_window_size(1920, 1080)
    
    print(f'[{browser_type}] ✓ Browser ready with advanced stealth mode')
    
    return driver

def browse():
    """Main browsing function - creates chaos by clicking through random links"""
    browser_type = random.choice(browsers)
    print(f'\n{"="*60}')
    print(f'Starting {browser_type} browser')
    print(f'{"="*60}')
    
    driver = create_driver(browser_type)
    
    # Keep track of websites visited in this session
    websites_visited = 0
    max_websites_per_session = random.randint(80, 120)  # 80-120 sites per session
    
    print(f'[{browser_type}] 🎯 Session goal: Visit {max_websites_per_session} websites')
    
    while websites_visited < max_websites_per_session:
        try:
            start_url = random.choice(sites)
            start_domain = get_domain(start_url)
            websites_visited += 1
            
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
            detect_and_click_ads(driver, browser_type, click_chance=0.6)
            
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
                            
                            # Try to accept cookies on new page (but don't wait too long)
                            try:
                                auto_accept_cookies(driver, browser_type)
                            except:
                                pass
                            
                            # Occasionally try to click ads (60% chance)
                            if random.random() < 0.4:  # 40% of the time, try to click ads
                                try:
                                    detect_and_click_ads(driver, browser_type, click_chance=0.6)
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
