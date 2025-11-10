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
from urllib.parse import urlparse

# Comprehensive list of websites across China, Europe, and America
# Prioritized list with ad-heavy sites first
sites = [
    # High-ad content sites (news, tabloids, tech blogs)
    "https://dailymail.co.uk", "https://forbes.com", "https://cnet.com", "https://techcrunch.com",
    "https://weather.com", "https://msn.com", "https://yahoo.com", "https://aol.com",
    "https://huffpost.com", "https://buzzfeed.com", "https://tmz.com", "https://ign.com",
    
    # News sites with ads
    "https://cnn.com", "https://foxnews.com", "https://usatoday.com", "https://nypost.com",
    "https://thesun.co.uk", "https://mirror.co.uk", "https://express.co.uk",
    "https://bild.de", "https://20minutes.fr", "https://sport1.de",
    
    # Shopping/E-commerce (typically ad-heavy)
    "https://ebay.com", "https://etsy.com", "https://aliexpress.com", "https://wish.com",
    "https://groupon.com", "https://slickdeals.net", "https://rakuten.com",
    # Chinese E-commerce
    "https://taobao.com", "https://tmall.com", "https://jd.com", "https://pinduoduo.com", "https://vip.com",
    "https://suning.com", "https://dangdang.com", "https://yanxuan.163.com", "https://xiaomiyoupin.com",
    
    # European E-commerce
    "https://amazon.de", "https://amazon.fr", "https://amazon.co.uk", "https://amazon.es", "https://amazon.it",
    "https://ebay.de", "https://ebay.fr", "https://ebay.co.uk", "https://zalando.de", "https://zalando.fr",
    "https://otto.de", "https://cdiscount.com", "https://fnac.com", "https://mediamarkt.de", "https://saturn.de",
    "https://carrefour.fr", "https://tesco.com", "https://sainsburys.co.uk", "https://allegro.pl",
    
    # American E-commerce
    "https://amazon.com", "https://ebay.com", "https://walmart.com", "https://target.com", "https://bestbuy.com",
    "https://homedepot.com", "https://lowes.com", "https://costco.com", "https://macys.com", "https://kohls.com",
    "https://wayfair.com", "https://etsy.com", "https://newegg.com", "https://shein.com", "https://temu.com",
    
    # Search Engines
    "https://google.com", "https://google.de", "https://google.fr", "https://google.co.uk", "https://bing.com",
    "https://yahoo.com", "https://duckduckgo.com", "https://baidu.com", "https://yandex.com",
    
    # Social Media
    "https://facebook.com", "https://instagram.com", "https://twitter.com", "https://linkedin.com", "https://reddit.com",
    "https://pinterest.com", "https://tiktok.com", "https://youtube.com", "https://twitch.tv",
    "https://weibo.com", "https://zhihu.com", "https://xiaohongshu.com", "https://bilibili.com",
    
    # News - European
    "https://bbc.com", "https://theguardian.com", "https://telegraph.co.uk", "https://dailymail.co.uk",
    "https://lemonde.fr", "https://lefigaro.fr", "https://spiegel.de", "https://bild.de", "https://zeit.de",
    "https://elpais.com", "https://corriere.it", "https://repubblica.it",
    
    # News - American
    "https://nytimes.com", "https://washingtonpost.com", "https://wsj.com", "https://usatoday.com", "https://cnn.com",
    "https://foxnews.com", "https://nbcnews.com", "https://reuters.com", "https://bloomberg.com", "https://forbes.com",
    
    # News - Chinese
    "https://sina.com.cn", "https://163.com", "https://sohu.com", "https://people.com.cn", "https://xinhuanet.com",
    
    # Technology
    "https://techcrunch.com", "https://theverge.com", "https://wired.com", "https://arstechnica.com", "https://cnet.com",
    "https://github.com", "https://stackoverflow.com", "https://hackernews.ycombinator.com",
    
    # Streaming
    "https://netflix.com", "https://hulu.com", "https://disneyplus.com", "https://spotify.com", "https://twitch.tv",
    "https://youku.com", "https://iqiyi.com", "https://v.qq.com",
    
    # Travel
    "https://booking.com", "https://expedia.com", "https://airbnb.com", "https://tripadvisor.com", "https://kayak.com",
    "https://skyscanner.com", "https://ctrip.com", "https://qunar.com",
    
    # Finance
    "https://chase.com", "https://wellsfargo.com", "https://bankofamerica.com", "https://paypal.com",
    "https://coinbase.com", "https://robinhood.com", "https://investing.com", "https://finance.yahoo.com",
    "https://alipay.com", "https://eastmoney.com",
    
    # Sports
    "https://espn.com", "https://skysports.com", "https://marca.com", "https://lequipe.fr", "https://gazzetta.it",
    "https://nfl.com", "https://nba.com", "https://mlb.com",
    
    # Food Delivery
    "https://ubereats.com", "https://doordash.com", "https://grubhub.com", "https://deliveroo.com", "https://justeat.com",
    "https://ele.me", "https://meituan.com",
    
    # Job Sites
    "https://indeed.com", "https://linkedin.com", "https://glassdoor.com", "https://monster.com",
    "https://51job.com", "https://zhaopin.com",
    
    # Real Estate
    "https://zillow.com", "https://redfin.com", "https://realtor.com", "https://rightmove.co.uk", "https://immobilienscout24.de",
    "https://fang.com", "https://lianjia.com",
    
    # Gaming
    "https://steam.steampowered.com", "https://epicgames.com", "https://ign.com", "https://gamespot.com",
    "https://17173.com", "https://4399.com",
    
    # Education
    "https://coursera.org", "https://udemy.com", "https://khanacademy.org", "https://edx.org", "https://duolingo.com",
    
    # Government
    "https://usa.gov", "https://gov.uk", "https://gov.cn",
    
    # Automotive
    "https://cars.com", "https://autotrader.com", "https://mobile.de", "https://autohome.com.cn",
    
    # Health
    "https://webmd.com", "https://mayoclinic.org", "https://nhs.uk",
    
    # Wikipedia
    "https://wikipedia.org", "https://en.wikipedia.org", "https://de.wikipedia.org", "https://fr.wikipedia.org",
    
    # Tech Services
    "https://google.com", "https://microsoft.com", "https://apple.com", "https://amazon.com",
    "https://alibaba.com", "https://tencent.com",
    
    # Fashion
    "https://zara.com", "https://hm.com", "https://asos.com", "https://nike.com", "https://adidas.com",
    
    # Crypto
    "https://coinbase.com", "https://binance.com", "https://coinmarketcap.com"
]

browsers = ['firefox', 'chrome', 'edge']

def get_domain(url):
    """Extract domain from URL"""
    try:
        parsed = urlparse(url)
        return parsed.netloc.lower()
    except:
        return ''

def generate_random_user_agent():
    """Generate a random realistic user agent by combining different components"""
    
    # Platform/OS options
    platforms = [
        "Windows NT 10.0; Win64; x64",
        "Windows NT 11.0; Win64; x64",
        "Windows NT 10.0; WOW64",
        "Macintosh; Intel Mac OS X 10_15_7",
        "Macintosh; Intel Mac OS X 11_6_0",
        "Macintosh; Intel Mac OS X 12_0_1",
        "Macintosh; Intel Mac OS X 13_1",
        "Macintosh; Intel Mac OS X 14_0",
        "X11; Linux x86_64",
        "X11; Ubuntu; Linux x86_64",
        "X11; Fedora; Linux x86_64",
        "X11; Linux i686",
    ]
    
    # WebKit/AppleWebKit versions
    webkit_versions = [
        "537.36",
        "537.35",
        "537.34",
        "605.1.15",
        "605.1.16",
        "604.1.38",
    ]
    
    # Chrome versions (major.0.0.0 or major.0.build.0)
    chrome_major_versions = [115, 116, 117, 118, 119, 120, 121, 122]
    chrome_builds = [
        "0.0.0",
        "0.6045.199",
        "0.6045.105",
        "0.6099.109",
        "0.6100.88",
        "0.0.6312.122",
        "0.0.6367.91",
    ]
    
    # Firefox versions
    firefox_versions = [118, 119, 120, 121, 122, 123]
    
    # Edge versions
    edge_versions = [115, 116, 117, 118, 119, 120, 121]
    
    # Safari versions
    safari_versions = ["16.1", "16.2", "16.3", "16.4", "16.5", "17.0", "17.1", "17.2"]
    
    # Choose browser type
    browser_type = random.choice(['chrome', 'firefox', 'safari', 'edge'])
    platform = random.choice(platforms)
    
    if browser_type == 'chrome':
        webkit = random.choice(webkit_versions)
        chrome_major = random.choice(chrome_major_versions)
        chrome_build = random.choice(chrome_builds)
        chrome_version = f"{chrome_major}.{chrome_build}"
        
        ua = f"Mozilla/5.0 ({platform}) AppleWebKit/{webkit} (KHTML, like Gecko) Chrome/{chrome_version} Safari/{webkit}"
        
    elif browser_type == 'firefox':
        firefox_ver = random.choice(firefox_versions)
        # Firefox uses Gecko
        ua = f"Mozilla/5.0 ({platform}; rv:{firefox_ver}.0) Gecko/20100101 Firefox/{firefox_ver}.0"
        
    elif browser_type == 'safari':
        # Safari only on macOS
        mac_platforms = [p for p in platforms if 'Mac' in p]
        if mac_platforms:
            platform = random.choice(mac_platforms)
        webkit = random.choice(webkit_versions)
        safari_ver = random.choice(safari_versions)
        
        ua = f"Mozilla/5.0 ({platform}) AppleWebKit/{webkit} (KHTML, like Gecko) Version/{safari_ver} Safari/{webkit}"
        
    elif browser_type == 'edge':
        webkit = random.choice(webkit_versions)
        edge_ver = random.choice(edge_versions)
        chrome_major = random.choice(chrome_major_versions)  # Edge is Chromium-based
        chrome_build = random.choice(chrome_builds)
        chrome_version = f"{chrome_major}.{chrome_build}"
        
        ua = f"Mozilla/5.0 ({platform}) AppleWebKit/{webkit} (KHTML, like Gecko) Chrome/{chrome_version} Safari/{webkit} Edg/{edge_ver}.0.{random.randint(1000, 9999)}.{random.randint(10, 99)}"
    
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
