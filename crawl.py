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
from selenium_stealth import stealth
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

def create_driver(browser_type):
    """Create a Selenium WebDriver for automated browsing with anti-detection"""
    
    # Realistic user agents (updated for 2025)
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    ]
    user_agent = random.choice(user_agents)
    
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
        options.set_preference("general.useragent.override", user_agent)
        # Firefox anti-detection preferences
        options.set_preference("dom.webdriver.enabled", False)
        options.set_preference("useAutomationExtension", False)
        options.set_preference("marionette", True)
        options.set_preference("privacy.trackingprotection.enabled", False)
        
    elif browser_type == 'edge':
        options = webdriver.EdgeOptions()
        options.add_argument(f'user-agent={user_agent}')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Same additional arguments as Chrome
        options.add_argument('--disable-popup-blocking')
        options.add_argument('--start-maximized')
        options.add_argument('--disable-extensions')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
    else:
        raise ValueError(f"Unsupported browser: {browser_type}")
    
    print(f'[{browser_type}] Creating browser session with stealth mode...')
    driver = webdriver.Remote(
        command_executor='http://selenium-hub:4444/wd/hub',
        options=options
    )
    
    # Apply Selenium Stealth for Chrome/Edge (most effective)
    if browser_type in ['chrome', 'edge']:
        # Set user agent via CDP
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": user_agent,
            "platform": "Win32",
            "acceptLanguage": "en-US,en;q=0.9"
        })
        
        # Apply selenium-stealth
        stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
        )
        
        # Additional CDP commands for stealth
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                // Mock plugins
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
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
                    app: {}
                };
                
                // Mock permissions
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: 'denied' }) :
                        originalQuery(parameters)
                );
            '''
        })
    elif browser_type == 'firefox':
        # For Firefox, inject stealth script after page load
        driver._stealth_js = '''
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
                configurable: true
            });
            
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
                configurable: true
            });
            
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
                configurable: true
            });
        '''
    
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
    
    while True:
        try:
            start_url = random.choice(sites)
            start_domain = get_domain(start_url)
            print(f'\n[{browser_type}] 🌐 Starting journey from: {start_url}')
            
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
            
            # Simulate human reading/scrolling behavior on first page
            for _ in range(random.randint(1, 2)):
                scroll_amount = random.randint(200, 500)
                driver.execute_script(f'window.scrollBy(0, {scroll_amount});')
                time.sleep(random.uniform(0.8, 2.0))
            
            time.sleep(random.uniform(1, 3))
            
            max_depth = random.randint(30, 50)
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
                    
                    # Find clickable links
                    links = driver.find_elements(By.TAG_NAME, 'a')
                    if not links:
                        print(f'  [{browser_type}] No links found at depth {current_depth}, restarting journey')
                        break
                    
                    clickable = [l for l in links[:50] if l.is_displayed()]
                    if not clickable:
                        print(f'  [{browser_type}] No clickable links at depth {current_depth}, restarting journey')
                        break
                    
                    # Separate internal and external links
                    internal_links = []
                    external_links = []
                    
                    for link in clickable:
                        try:
                            href = link.get_attribute('href')
                            if href and href.startswith('http'):
                                link_domain = get_domain(href)
                                if link_domain == start_domain:
                                    internal_links.append(link)
                                else:
                                    external_links.append(link)
                        except:
                            continue
                    
                    # Choose link strategy
                    chosen_link = None
                    if current_depth == 0:
                        # Stay internal on first click
                        if internal_links:
                            chosen_link = random.choice(internal_links)
                    elif current_depth >= 1:
                        # Prefer external links (70% chance)
                        if external_links and random.random() < 0.7:
                            chosen_link = random.choice(external_links)
                            print(f'  [{browser_type}] Depth {current_depth}: → External link')
                        elif internal_links:
                            chosen_link = random.choice(internal_links)
                            print(f'  [{browser_type}] Depth {current_depth}: → Internal link')
                        elif external_links:
                            chosen_link = random.choice(external_links)
                    
                    if chosen_link:
                        try:
                            href = chosen_link.get_attribute('href')
                            link_domain = get_domain(href)
                            print(f'  [{browser_type}] Depth {current_depth}: {href[:80]}')
                            
                            # Human-like delay before clicking
                            time.sleep(random.uniform(0.5, 1.5))
                            
                            chosen_link.click()
                            
                            # Variable delay after click (humans don't click instantly)
                            time.sleep(random.uniform(2, 5))
                            
                            # Try to accept cookies on new page (but don't wait too long)
                            try:
                                auto_accept_cookies(driver, browser_type)
                            except:
                                pass
                            
                            current_depth += 1
                            
                            if link_domain != start_domain:
                                start_domain = link_domain
                                print(f'  [{browser_type}] 🔄 Now exploring: {start_domain}')
                                
                        except Exception as click_error:
                            print(f'  [{browser_type}] Click failed: {str(click_error)[:50]}')
                            break
                    else:
                        print(f'  [{browser_type}] No suitable link found at depth {current_depth}')
                        break
                        
                except Exception as nav_error:
                    print(f'  [{browser_type}] Navigation error: {str(nav_error)[:50]}')
                    break
            
            print(f'[{browser_type}] ✓ Journey complete. Depth: {current_depth}/{max_depth}')
            time.sleep(random.uniform(2, 5))
            
        except TimeoutException:
            print(f'[{browser_type}] ⏱ Timeout, starting new journey')
        except WebDriverException as e:
            print(f'[{browser_type}] ⚠ WebDriver error: {str(e)[:80]}')
            print(f'[{browser_type}] Recreating driver...')
            try:
                driver.quit()
            except:
                pass
            driver = create_driver(browser_type)
        except Exception as e:
            print(f'[{browser_type}] ⚠ Error: {str(e)[:80]}')

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
