#!/usr/bin/env python3
"""
Browser Chaos Generator with AdNauseam Extension
Automates browsing across multiple sites with ad-clicking extension
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import time
import random
from urllib.parse import urlparse
import os

# Comprehensive list of websites across China, Europe, and America
sites = [
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

# Extension paths - must be mounted in Docker
EXTENSION_PATHS = {
    'chrome': '/extensions/adnauseam-chrome',
    'firefox': '/extensions/adnauseam.xpi',
    'edge': '/extensions/adnauseam-chrome'
}

browsers = ['chrome', 'firefox', 'edge']

def get_domain(url):
    """Extract domain from URL"""
    try:
        parsed = urlparse(url)
        return parsed.netloc.lower()
    except:
        return ''

def setup_adnauseam(driver, browser_type):
    """Configure AdNauseam extension on first run - enable all three options"""
    try:
        print(f"  [{browser_type}] Setting up AdNauseam...")
        time.sleep(3)
        
        # Try to find AdNauseam first-run page
        windows = driver.window_handles
        for window in windows:
            driver.switch_to.window(window)
            current_url = driver.current_url
            
            if 'adnauseam' in current_url.lower() or 'firstrun' in current_url.lower():
                print(f"  [{browser_type}] Found AdNauseam setup page: {current_url[:50]}")
                time.sleep(2)
                
                try:
                    # Enable all three toggles: HIDE ADS, CLICK ADS, BLOCK MALWARE
                    driver.execute_script("""
                        var toggles = document.querySelectorAll('input[type="checkbox"]');
                        var count = 0;
                        toggles.forEach(function(toggle) {
                            if (!toggle.checked) {
                                toggle.click();
                                count++;
                            }
                        });
                        return count;
                    """)
                    time.sleep(1)
                    print(f"  [{browser_type}] ✓ AdNauseam configured: HIDE ADS, CLICK ADS, BLOCK MALWARE enabled")
                except Exception as e:
                    print(f"  [{browser_type}] Could not auto-configure: {str(e)[:50]}")
                
                break
        
        # Return to normal browsing
        if len(driver.window_handles) > 0:
            driver.switch_to.window(driver.window_handles[0])
            
    except Exception as e:
        print(f"  [{browser_type}] AdNauseam setup error: {str(e)[:50]}")

def create_driver(browser_type):
    """Create a Selenium WebDriver with AdNauseam extension loaded"""
    options = None
    
    if browser_type == 'chrome':
        options = webdriver.ChromeOptions()
        if os.path.exists(EXTENSION_PATHS['chrome']):
            options.add_argument(f'--load-extension={EXTENSION_PATHS["chrome"]}')
            print(f'[{browser_type}] ✓ Loading AdNauseam extension')
        else:
            print(f'[{browser_type}] ⚠ AdNauseam extension not found at {EXTENSION_PATHS["chrome"]}')
            
    elif browser_type == 'firefox':
        options = webdriver.FirefoxOptions()
        # Set preferences to allow unsigned extensions
        options.set_preference("xpinstall.signatures.required", False)
        options.set_preference("extensions.langpacks.signatures.required", False)
        options.set_preference("extensions.webextensions.uuids", '{"adnauseam@rednoise.org": "{12345678-1234-1234-1234-123456789012}"}')
        if os.path.exists(EXTENSION_PATHS['firefox']):
            print(f'[{browser_type}] ✓ Will install AdNauseam extension after driver creation')
        else:
            print(f'[{browser_type}] ⚠ AdNauseam extension not found at {EXTENSION_PATHS["firefox"]}')
        
    elif browser_type == 'edge':
        options = webdriver.EdgeOptions()
        if os.path.exists(EXTENSION_PATHS['edge']):
            options.add_argument(f'--load-extension={EXTENSION_PATHS["edge"]}')
            print(f'[{browser_type}] ✓ Loading AdNauseam extension')
        else:
            print(f'[{browser_type}] ⚠ AdNauseam extension not found at {EXTENSION_PATHS["edge"]}')
    
    # Common options
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-blink-features=AutomationControlled')
    
    # Make browser look more human
    if browser_type in ['chrome', 'edge']:
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Remote(
        command_executor='http://selenium-hub:4444/wd/hub',
        options=options
    )
    
    # For Firefox, install extension after driver creation
    if browser_type == 'firefox' and os.path.exists(EXTENSION_PATHS['firefox']):
        try:
            driver.install_addon(EXTENSION_PATHS['firefox'], temporary=False)
            print(f'[{browser_type}] ✓ Installed AdNauseam extension (permanent)')
            time.sleep(2)  # Give extension time to initialize
        except Exception as e:
            print(f'[{browser_type}] Failed to install extension: {str(e)[:100]}')
    
    driver.set_page_load_timeout(30)
    
    # Configure AdNauseam
    setup_adnauseam(driver, browser_type)
    
    return driver

def browse():
    """Main browsing function - creates chaos by clicking through random links"""
    browser_type = random.choice(browsers)
    print(f'\n{"="*60}')
    print(f'Starting {browser_type} browser with AdNauseam')
    print(f'{"="*60}')
    
    driver = create_driver(browser_type)
    
    while True:
        try:
            start_url = random.choice(sites)
            start_domain = get_domain(start_url)
            print(f'\n[{browser_type}] 🌐 Starting journey from: {start_url}')
            
            driver.get(start_url)
            time.sleep(random.uniform(3, 8))
            
            max_depth = random.randint(30, 50)
            current_depth = 0
            
            while current_depth < max_depth:
                try:
                    current_url = driver.current_url
                    current_domain = get_domain(current_url)
                    
                    # Scroll to trigger ad loading (AdNauseam will handle clicking)
                    for _ in range(random.randint(1, 3)):
                        scroll_position = random.randint(100, 1000)
                        driver.execute_script(f'window.scrollTo(0, {scroll_position});')
                        time.sleep(random.uniform(1, 2))
                    
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
                            
                            chosen_link.click()
                            time.sleep(random.uniform(3, 6))
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
    ║   Browser Chaos Generator with AdNauseam                   ║
    ║   Automated browsing with ad-clicking extension            ║
    ╚════════════════════════════════════════════════════════════╝
    """)
    
    print("Extension paths:")
    for browser, path in EXTENSION_PATHS.items():
        exists = '✓' if os.path.exists(path) else '✗'
        print(f"  {exists} {browser}: {path}")
    
    print("\nStarting in 5 seconds...")
    time.sleep(5)
    
    while True:
        try:
            browse()
        except Exception as e:
            print(f'\n⚠ Fatal error: {e}')
            print('Restarting in 5 seconds...')
            time.sleep(5)
