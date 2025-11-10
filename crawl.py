#!/usr/bin/env python3
"""
Browser Chaos Generator with Advanced Anti-Fingerprinting
Automates browsing across multiple sites with persistent persona management
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, WebDriverException, MoveTargetOutOfBoundsException
import time
import random
import os
import math
import numpy as np
from datetime import datetime
from urllib.parse import urlparse
from faker import Faker

# Import persona manager for persistent fingerprint rotation
try:
    from persona_manager import PersonaManager, fingerprint_to_dict
    PERSONA_MANAGER_AVAILABLE = True
except ImportError:
    print('⚠️  PersonaManager not available, running without persistence')
    PERSONA_MANAGER_AVAILABLE = False

# ============================================
# HUMAN-LIKE MOUSE MOVEMENT FUNCTIONS
# ============================================

def bezier_curve(start, end, control_points, steps=50):
    """
    Generate points along a Bézier curve for natural mouse movement
    
    Args:
        start: (x, y) starting position
        end: (x, y) ending position
        control_points: List of (x, y) control points for curve shape
        steps: Number of points to generate along curve
    
    Returns:
        List of (x, y) coordinates along the curve
    """
    points = [start] + control_points + [end]
    n = len(points) - 1
    curve_points = []
    
    for step in range(steps + 1):
        t = step / steps
        x = 0
        y = 0
        
        # Bernstein polynomial calculation
        for i, (px, py) in enumerate(points):
            # Binomial coefficient
            binom = 1
            for j in range(1, i + 1):
                binom = binom * (n - j + 1) // j
            
            # Bernstein basis
            basis = binom * (t ** i) * ((1 - t) ** (n - i))
            x += px * basis
            y += py * basis
        
        curve_points.append((int(x), int(y)))
    
    return curve_points


def human_mouse_movement(driver, target_element, overshoot_chance=0.3):
    """
    Move mouse to target element along natural Bézier curve with human-like characteristics
    
    Features:
    - Random control points for curve variation
    - Variable speed with acceleration/deceleration
    - Occasional overshooting and correction
    - Micro-movements for realism
    
    Args:
        driver: Selenium WebDriver instance
        target_element: Target element to move to
        overshoot_chance: Probability of overshooting (0.0-1.0)
    """
    try:
        actions = ActionChains(driver)
        
        # Get element location and size
        location = target_element.location
        size = target_element.size
        
        # Target center of element (with slight randomness)
        target_x = location['x'] + size['width'] // 2 + random.randint(-10, 10)
        target_y = location['y'] + size['height'] // 2 + random.randint(-5, 5)
        
        # Current position (assume starting from viewport origin + random offset)
        current_x = random.randint(100, 400)
        current_y = random.randint(100, 300)
        
        # Generate 1-3 random control points for Bézier curve
        num_controls = random.randint(1, 3)
        control_points = []
        
        for _ in range(num_controls):
            # Control points create the curve shape
            ctrl_x = current_x + (target_x - current_x) * random.uniform(0.2, 0.8) + random.randint(-50, 50)
            ctrl_y = current_y + (target_y - current_y) * random.uniform(0.2, 0.8) + random.randint(-50, 50)
            control_points.append((ctrl_x, ctrl_y))
        
        # Generate curve points
        steps = random.randint(30, 60)  # More steps = smoother movement
        curve = bezier_curve((current_x, current_y), (target_x, target_y), control_points, steps)
        
        # Overshoot occasionally (human-like)
        if random.random() < overshoot_chance:
            overshoot_x = target_x + random.randint(10, 30) * (1 if random.random() > 0.5 else -1)
            overshoot_y = target_y + random.randint(5, 15) * (1 if random.random() > 0.5 else -1)
            overshoot_curve = bezier_curve((target_x, target_y), (overshoot_x, overshoot_y), [], steps=10)
            correction_curve = bezier_curve((overshoot_x, overshoot_y), (target_x, target_y), [], steps=8)
            curve = curve + overshoot_curve + correction_curve
        
        # Move along curve with variable speed (acceleration/deceleration)
        prev_x, prev_y = curve[0]
        
        for i, (x, y) in enumerate(curve[1:], 1):
            # Calculate relative movement
            dx = x - prev_x
            dy = y - prev_y
            
            # Variable speed: slower at start/end, faster in middle
            progress = i / len(curve)
            if progress < 0.2:  # Acceleration
                speed_factor = progress / 0.2
            elif progress > 0.8:  # Deceleration
                speed_factor = (1.0 - progress) / 0.2
            else:  # Full speed
                speed_factor = 1.0
            
            # Move by offset with slight delay
            try:
                actions.move_by_offset(dx, dy)
                
                # Variable pause based on speed (faster = shorter pause)
                pause = random.uniform(0.001, 0.005) * (1.0 / max(speed_factor, 0.1))
                actions.pause(pause)
                
            except MoveTargetOutOfBoundsException:
                # Element out of bounds, skip this movement
                break
            
            prev_x, prev_y = x, y
        
        # Final micro-adjustment (jitter)
        if random.random() < 0.5:
            actions.move_by_offset(random.randint(-2, 2), random.randint(-2, 2))
            actions.pause(random.uniform(0.01, 0.03))
        
        # Perform all movements
        actions.perform()
        
    except Exception as e:
        # Fallback to simple move_to_element if Bézier fails
        try:
            ActionChains(driver).move_to_element(target_element).perform()
        except:
            pass


def hover_before_click(driver, element, hover_time=None):
    """
    Hover over element before clicking (human-like behavior)
    
    Args:
        driver: Selenium WebDriver instance
        element: Element to hover over and click
        hover_time: Time to hover in seconds (randomized if None)
    """
    try:
        # Move mouse to element with human-like curve
        human_mouse_movement(driver, element)
        
        # Hover for realistic duration
        if hover_time is None:
            hover_time = random.uniform(0.2, 0.8)
        
        time.sleep(hover_time)
        
        # 10% chance to move away without clicking (changed mind)
        if random.random() < 0.1:
            # Small movement away
            try:
                ActionChains(driver).move_by_offset(
                    random.randint(20, 50),
                    random.randint(10, 30)
                ).perform()
            except:
                pass
            return False  # Didn't click
        
        # Click the element
        element.click()
        return True  # Clicked successfully
        
    except Exception as e:
        # Fallback to direct click
        try:
            element.click()
            return True
        except:
            return False


def fidget_mouse(driver, duration=None, movements=None):
    """
    Perform random mouse movements while "reading" page (human fidgeting)
    
    Args:
        driver: Selenium WebDriver instance
        duration: How long to fidget (seconds), randomized if None
        movements: Number of movements, randomized if None
    """
    if duration is None:
        duration = random.uniform(1.0, 3.0)
    
    if movements is None:
        movements = random.randint(3, 8)
    
    start_time = time.time()
    actions = ActionChains(driver)
    
    try:
        for _ in range(movements):
            # Break if duration exceeded
            if time.time() - start_time > duration:
                break
            
            # Small random movements (10-50px)
            dx = random.randint(-50, 50)
            dy = random.randint(-50, 50)
            
            # Occasionally larger movements (looking around)
            if random.random() < 0.2:
                dx *= 2
                dy *= 2
            
            try:
                actions.move_by_offset(dx, dy)
                actions.pause(random.uniform(0.1, 0.4))
            except MoveTargetOutOfBoundsException:
                # Hit viewport boundary, move in opposite direction
                actions.move_by_offset(-dx // 2, -dy // 2)
                actions.pause(random.uniform(0.1, 0.3))
        
        # Perform all fidget movements
        actions.perform()
        
    except Exception:
        # Silently fail - fidgeting is optional
        pass


def smooth_scroll(driver, amount, duration=None):
    """
    Smooth scroll using ActionChains (more realistic than JavaScript)
    
    Args:
        driver: Selenium WebDriver instance
        amount: Scroll amount in pixels (positive = down, negative = up)
        duration: Time to complete scroll (seconds), randomized if None
    """
    if duration is None:
        duration = random.uniform(0.3, 0.8)
    
    try:
        # Get a random element to scroll from (more realistic)
        body = driver.find_element(By.TAG_NAME, 'body')
        
        # Break scroll into chunks for smoothness
        chunks = random.randint(5, 12)
        chunk_size = amount // chunks
        chunk_delay = duration / chunks
        
        actions = ActionChains(driver)
        
        for i in range(chunks):
            # Variable chunk size for natural scrolling
            if i == chunks - 1:
                # Last chunk gets remainder
                current_chunk = amount - (chunk_size * (chunks - 1))
            else:
                # Add small variation to chunk size
                current_chunk = chunk_size + random.randint(-5, 5)
            
            # Use scroll_by_amount for realistic wheel events
            actions.scroll_by_amount(0, current_chunk)
            actions.pause(chunk_delay + random.uniform(-0.02, 0.02))
        
        actions.perform()
        
    except Exception:
        # Fallback to JavaScript scroll
        driver.execute_script(f"window.scrollBy(0, {amount})")


def reading_behavior(driver, duration=None):
    """
    Simulate realistic reading behavior with mouse fidgeting and occasional scrolling
    
    Args:
        driver: Selenium WebDriver instance
        duration: Reading duration in seconds, randomized if None
    """
    if duration is None:
        duration = random.uniform(2.0, 5.0)
    
    start_time = time.time()
    
    while time.time() - start_time < duration:
        action_choice = random.random()
        
        if action_choice < 0.4:
            # Fidget mouse (40% chance)
            fidget_mouse(driver, duration=random.uniform(0.5, 1.5), movements=random.randint(2, 5))
            
        elif action_choice < 0.7:
            # Small scroll (30% chance)
            scroll_amount = random.randint(50, 200)
            smooth_scroll(driver, scroll_amount, duration=random.uniform(0.2, 0.5))
            
        else:
            # Just pause/read (30% chance)
            time.sleep(random.uniform(0.5, 1.5))
        
        # Brief pause between actions
        time.sleep(random.uniform(0.3, 0.8))


# ============================================
# HUMAN-LIKE TIMING FUNCTIONS
# ============================================

class SessionFatigueModel:
    """
    Model human fatigue during browsing sessions
    - Humans slow down over time
    - Action count affects fatigue
    """
    def __init__(self):
        self.start_time = time.time()
        self.actions_count = 0
    
    def get_fatigue_multiplier(self):
        """
        Returns delay multiplier based on session duration
        - 0-10 min: 1.0x (fresh)
        - 10-20 min: 1.1x (slight slowdown)
        - 20-30 min: 1.2x (tired)
        - 30+ min: 1.4x (very tired)
        - Also increases slightly with action count
        """
        elapsed_min = (time.time() - self.start_time) / 60
        self.actions_count += 1
        
        # Base fatigue from elapsed time
        if elapsed_min < 10:
            time_fatigue = 1.0
        elif elapsed_min < 20:
            time_fatigue = 1.1
        elif elapsed_min < 30:
            time_fatigue = 1.2
        elif elapsed_min < 45:
            time_fatigue = 1.3
        else:
            time_fatigue = 1.4
        
        # Additional fatigue from action count (every 100 actions adds 2%)
        action_fatigue = 1.0 + (self.actions_count // 100) * 0.02
        
        return min(time_fatigue * action_fatigue, 2.0)  # Cap at 2x slowdown


def get_time_of_day_multiplier():
    """
    Humans are slower at certain hours (circadian rhythm)
    - 2-6 AM: 1.5x slower (very tired)
    - 6-9 AM: 1.2x slower (morning grogginess)
    - 9 AM-5 PM: 1.0x (normal work hours)
    - 5-11 PM: 1.05x (slightly slower, evening)
    - 11 PM-2 AM: 1.3x (late night)
    """
    hour = datetime.now().hour
    
    if 2 <= hour < 6:
        return 1.5  # Very tired
    elif 6 <= hour < 9:
        return 1.2  # Morning grogginess
    elif 9 <= hour < 17:
        return 1.0  # Normal work hours
    elif 17 <= hour < 23:
        return 1.05  # Evening, slightly slower
    else:  # 23-2 (11 PM to 2 AM)
        return 1.3  # Late night


def human_delay(base_seconds, variance=0.3):
    """
    Generate human-like delays using normal distribution
    - 68% of values within ±variance of base
    - Occasional long pauses (distractions)
    - Never less than 0.3 seconds
    
    Args:
        base_seconds: Target delay in seconds
        variance: Standard deviation as fraction of base (0.0-1.0)
    
    Returns:
        Delay in seconds with human-like variation
    """
    # Use normal distribution (more realistic than uniform)
    std_dev = base_seconds * variance
    delay = np.random.normal(base_seconds, std_dev)
    
    # 5% chance of distraction (2x-5x longer delay)
    if random.random() < 0.05:
        delay *= random.uniform(2.0, 5.0)
    
    # 2% chance of very quick action (impatient)
    elif random.random() < 0.02:
        delay *= random.uniform(0.3, 0.6)
    
    # Never less than 0.3s (too fast = bot-like)
    return max(0.3, delay)


def realistic_delay(base_seconds, variance=0.3, apply_fatigue=True):
    """
    Generate realistic delay combining all human factors:
    - Normal distribution (not uniform)
    - Session fatigue
    - Circadian rhythm
    - Random distractions
    
    Args:
        base_seconds: Base delay duration
        variance: Variation factor (0.0-1.0)
        apply_fatigue: Whether to apply fatigue multiplier
    
    Returns:
        Final delay duration in seconds
    """
    # Get base human delay with normal distribution
    delay = human_delay(base_seconds, variance)
    
    # Apply circadian rhythm (time of day)
    circadian = get_time_of_day_multiplier()
    delay *= circadian
    
    # Apply fatigue if enabled and fatigue model exists
    if apply_fatigue and 'fatigue_model' in globals():
        fatigue = fatigue_model.get_fatigue_multiplier()
        delay *= fatigue
    
    return delay


# ============================================
# REALISTIC USER BEHAVIORS
# ============================================

def inject_realistic_errors(driver):
    """
    Inject realistic console errors and warnings with high variability
    Real users see JS errors occasionally - too clean = suspicious
    """
    if random.random() < 0.12:  # 12% of page loads
        try:
            # Common error types with realistic URLs and line numbers
            error_templates = [
                # Cookie/Consent errors
                "console.warn('[Cookie] Consent not provided for {domain}');",
                "console.error('[GDPR] Failed to load consent framework from {cdn}');",
                "console.warn('[Privacy] Third-party cookie blocked: {cookie_name}');",
                
                # Analytics/Tracking errors
                "console.error('[Analytics] Failed to load script from {analytics_domain}');",
                "console.warn('[Tracking] Google Analytics: gtag is not defined');",
                "console.error('[GTM] Failed to initialize Google Tag Manager');",
                "console.log('[FB Pixel] Facebook pixel failed to load - connection timeout');",
                "console.warn('[Hotjar] Recording script blocked by ad blocker');",
                
                # Ad-related errors
                "console.warn('[Ads] Unable to load advertisement from {ad_network}');",
                "console.error('[AdBlock] Failed to display ad unit: {ad_id}');",
                "console.log('[AdSense] adsbygoogle.js load timeout after {timeout}ms');",
                "console.warn('[Prebid] Bid adapter failed: {adapter_name}');",
                
                # Service Worker errors
                "console.log('[SW] ServiceWorker registration failed: SecurityError');",
                "console.error('[SW] Failed to update service worker: NetworkError');",
                "console.warn('[SW] Service worker: fetch event handler error');",
                
                # Resource loading errors
                "console.error('[Resource] Failed to load resource: {resource_url}');",
                "console.warn('[CSS] Failed to load stylesheet from {cdn}');",
                "console.error('[Font] Failed to load font: {font_name}');",
                "console.log('[Image] Image failed to load: {image_url}');",
                
                # CORS errors
                "console.error('[CORS] Cross-origin request blocked: {origin}');",
                "console.warn('[Security] Mixed content blocked: {url}');",
                "console.error('[XHR] XMLHttpRequest error: CORS policy');",
                
                # JavaScript errors
                "console.error('[JS] Uncaught TypeError: Cannot read property \\'{prop}\\' of undefined');",
                "console.error('[JS] Uncaught ReferenceError: {var_name} is not defined');",
                "console.warn('[Deprecation] {api_name} is deprecated and will be removed');",
                
                # Network errors
                "console.error('[Network] Failed to fetch: NetworkError when attempting to fetch resource');",
                "console.warn('[API] Request timeout after {timeout}ms: {api_endpoint}');",
                "console.error('[WebSocket] WebSocket connection failed: {ws_url}');",
                
                # Browser warnings
                "console.warn('[Performance] Long task detected: {duration}ms');",
                "console.warn('[Memory] Heap snapshot size exceeds threshold');",
                "console.log('[Browser] Slow network detected, reducing quality');",
            ]
            
            # Random data for templates
            domains = ['example.com', 'analytics.google.com', 'doubleclick.net', 'facebook.com', 
                      'ads.yahoo.com', 'googlesyndication.com', 'adnxs.com', 'criteo.com']
            cdns = ['cdn.cookielaw.org', 'cdn.jsdelivr.net', 'unpkg.com', 'cdnjs.cloudflare.com']
            cookie_names = ['_ga', '_gid', '_fbp', '__utma', '__utmz', 'fr', 'datr', 'sb']
            analytics_domains = ['www.google-analytics.com', 'analytics.google.com', 'stats.g.doubleclick.net']
            ad_networks = ['googlesyndication.com', 'doubleclick.net', 'adnxs.com', 'casalemedia.com']
            ad_ids = [f'ad-{random.randint(1000, 9999)}', f'banner-{random.randint(100, 999)}', 
                     f'slot-{random.randint(1, 20)}']
            adapters = ['rubicon', 'appnexus', 'pubmatic', 'openx', 'sovrn']
            resources = ['/assets/main.js', '/static/bundle.js', '/dist/vendor.js', '/js/app.min.js']
            fonts = ['Roboto', 'Open Sans', 'Lato', 'Montserrat', 'Source Sans Pro']
            images = ['/images/banner.jpg', '/assets/hero.png', '/media/thumbnail.webp']
            props = ['innerHTML', 'classList', 'parentNode', 'addEventListener', 'dataset']
            var_names = ['jQuery', '$', 'ga', 'gtag', 'fbq', 'dataLayer']
            apis = ['document.write', 'synchronous XMLHttpRequest', 'unload event', 'webkitRequestAnimationFrame']
            api_endpoints = ['/api/v1/user', '/graphql', '/rest/data', '/api/products']
            ws_urls = ['wss://live.example.com', 'ws://stream.example.com:8080']
            
            # Select random error and fill in template
            error_template = random.choice(error_templates)
            error = error_template.format(
                domain=random.choice(domains),
                cdn=random.choice(cdns),
                cookie_name=random.choice(cookie_names),
                analytics_domain=random.choice(analytics_domains),
                ad_network=random.choice(ad_networks),
                ad_id=random.choice(ad_ids),
                timeout=random.choice([3000, 5000, 10000, 15000]),
                adapter_name=random.choice(adapters),
                resource_url=random.choice(resources),
                font_name=random.choice(fonts),
                image_url=random.choice(images),
                origin=random.choice(domains),
                url=f'https://{random.choice(domains)}{random.choice(resources)}',
                prop=random.choice(props),
                var_name=random.choice(var_names),
                api_name=random.choice(apis),
                api_endpoint=random.choice(api_endpoints),
                ws_url=random.choice(ws_urls),
                duration=random.randint(200, 2000)
            )
            
            # Add line numbers and file references occasionally
            if random.random() < 0.4:
                file_name = random.choice(['bundle.js', 'app.js', 'vendor.js', 'main.js', 'analytics.js'])
                line_num = random.randint(1, 9999)
                col_num = random.randint(1, 120)
                error = f"{error} at {file_name}:{line_num}:{col_num}"
            
            driver.execute_script(error)
            
            # Sometimes inject multiple errors (2-3 errors in a row)
            if random.random() < 0.15:
                time.sleep(random.uniform(0.05, 0.2))
                driver.execute_script(random.choice(error_templates).format(
                    domain=random.choice(domains),
                    cdn=random.choice(cdns),
                    cookie_name=random.choice(cookie_names),
                    analytics_domain=random.choice(analytics_domains),
                    ad_network=random.choice(ad_networks),
                    ad_id=random.choice(ad_ids),
                    timeout=random.choice([3000, 5000, 10000]),
                    adapter_name=random.choice(adapters),
                    resource_url=random.choice(resources),
                    font_name=random.choice(fonts),
                    image_url=random.choice(images),
                    origin=random.choice(domains),
                    url=f'https://{random.choice(domains)}',
                    prop=random.choice(props),
                    var_name=random.choice(var_names),
                    api_name=random.choice(apis),
                    api_endpoint=random.choice(api_endpoints),
                    ws_url=random.choice(ws_urls),
                    duration=random.randint(200, 2000)
                ))
        except:
            pass


def simulate_copy_paste(driver):
    """
    Simulate occasional copy/paste behavior
    Real users copy text from pages - clipboard API should be accessed
    """
    if random.random() < 0.05:  # 5% chance per page
        try:
            driver.execute_script('''
                try {
                    const elements = document.querySelectorAll('p, h1, h2, h3, span, a, div');
                    if (elements.length > 0) {
                        const randomElement = elements[Math.floor(Math.random() * Math.min(elements.length, 50))];
                        const text = randomElement.innerText || randomElement.textContent;
                        
                        if (text && text.trim().length > 10) {
                            // Select the text
                            const range = document.createRange();
                            range.selectNodeContents(randomElement);
                            const selection = window.getSelection();
                            selection.removeAllRanges();
                            selection.addRange(range);
                            
                            // Copy to clipboard
                            document.execCommand('copy');
                            
                            // Clear selection after a moment
                            setTimeout(() => {
                                selection.removeAllRanges();
                            }, 100);
                        }
                    }
                } catch (e) {
                    // Silently fail
                }
            ''')
        except:
            pass


def simulate_right_click(driver, browser_type):
    """
    Simulate right-click (context menu) behavior
    Real users occasionally right-click on links/images
    """
    if random.random() < 0.03:  # Reduced to 3% to minimize errors
        try:
            # Set a short timeout for this operation
            driver.set_page_load_timeout(5)
            
            # Find clickable elements (links, images)
            elements = driver.find_elements(By.CSS_SELECTOR, 'a, img, button')
            if not elements:
                return
            
            # Pick a random visible element
            visible_elements = []
            for e in elements[:30]:
                try:
                    if e.is_displayed() and e.is_enabled():
                        visible_elements.append(e)
                except:
                    continue
            
            if not visible_elements:
                return
            
            element = random.choice(visible_elements)
            
            # Right-click with ActionChains (with explicit error handling)
            try:
                actions = ActionChains(driver)
                actions.context_click(element).perform()
                
                print(f'  [{browser_type}] 🖱️  Right-clicked element')
                
                # Wait briefly (user reading context menu)
                time.sleep(random.uniform(0.3, 0.8))
                
                # Close context menu with Escape
                try:
                    actions = ActionChains(driver)
                    actions.send_keys(Keys.ESCAPE).perform()
                except:
                    # If escape fails, just continue
                    pass
                
                time.sleep(random.uniform(0.1, 0.3))
            except Exception as e:
                # Element became stale or context menu didn't work - just continue
                pass
        except:
            pass
        finally:
            # Restore normal timeout
            try:
                driver.set_page_load_timeout(30)
            except:
                pass


def simulate_keyboard_shortcuts(driver, browser_type):
    """
    Simulate keyboard shortcuts that real users use
    """
    if random.random() < 0.05:  # Reduced to 5% (was 8%)
        try:
            shortcuts = [
                (Keys.SPACE, 'Scroll with Space'),
                (Keys.PAGE_DOWN, 'Page Down'),
                (Keys.HOME, 'Home key'),
                (Keys.END, 'End key'),
            ]
            
            # Select random shortcut
            key, description = random.choice(shortcuts)
            
            actions = ActionChains(driver)
            actions.send_keys(key).perform()
            
            print(f'  [{browser_type}] ⌨️  Pressed keyboard shortcut: {description}')
            time.sleep(random.uniform(0.2, 0.5))
        except:
            pass


def generate_fake_data():
    """Generate realistic fake data for form fields using Faker"""
    # Initialize Faker with random locale for diversity
    locales = ['en_US', 'en_GB', 'en_CA', 'fr_FR', 'de_DE', 'es_ES', 'it_IT']
    fake = Faker(random.choice(locales))
    
    # Generate realistic data
    first_name = fake.first_name()
    last_name = fake.last_name()
    
    # Email variations
    email_formats = [
        f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 999)}@{fake.free_email_domain()}",
        f"{first_name.lower()}{last_name.lower()}@{fake.free_email_domain()}",
        f"{first_name[0].lower()}{last_name.lower()}{random.randint(1, 99)}@{fake.free_email_domain()}",
        f"{first_name.lower()}_{last_name.lower()}@{fake.free_email_domain()}",
        f"{first_name.lower()}{random.randint(100, 999)}@{fake.free_email_domain()}",
    ]
    
    # Search query variations (much more diverse)
    search_queries = [
        fake.catch_phrase(),  # Random business phrases
        fake.bs(),  # Random business speak
        fake.word(),  # Random word
        f"how to {fake.word()}",
        f"{fake.word()} {fake.word()}",
        f"{fake.city()} {random.choice(['weather', 'news', 'restaurants', 'hotels'])}",
        f"best {fake.word()}",
        random.choice(['news', 'weather', 'sports', 'recipes', 'movies', 'music', 'games', 'shopping']),
        '',  # Empty search sometimes
    ]
    
    # Message variations
    messages = [
        fake.sentence(nb_words=random.randint(3, 10)),
        fake.text(max_nb_chars=random.randint(20, 100)),
        random.choice(['Hello', 'Hi', 'Thanks', 'Great site', 'Interesting', 'Love it', 'Nice', '']),
    ]
    
    return {
        'email': random.choice(email_formats),
        'name': f"{first_name} {last_name}",
        'first_name': first_name,
        'last_name': last_name,
        'phone': fake.phone_number(),
        'zipcode': fake.postcode(),
        'address': fake.street_address(),
        'city': fake.city(),
        'state': fake.state_abbr() if random.random() < 0.5 else fake.state(),
        'country': fake.country(),
        'age': str(random.randint(18, 75)),
        'number': str(random.randint(1, 100)),
        'date': fake.date(),
        'username': fake.user_name(),
        'company': fake.company(),
        'job_title': fake.job(),
        'search': random.choice(search_queries),
        'message': random.choice(messages),
        'url': fake.url(),
    }


def simulate_typing_and_forms(driver, browser_type):
    """
    Simulate typing in forms with proper data validation
    - Detects email, name, phone, etc. fields
    - Types realistic data
    - Handles frontend validation
    - Occasionally submits forms (carefully)
    """
    if random.random() > 0.10:  # Reduced to 10% (was 15%) to avoid timeouts
        return False
    
    try:
        # Set a shorter timeout for this operation
        original_timeout = 30
        try:
            driver.set_page_load_timeout(10)
        except:
            pass
        
        # Find all input fields (visible and not password)
        inputs = driver.find_elements(By.CSS_SELECTOR, 
            'input[type="text"], input[type="email"], input[type="tel"], input[type="search"], '
            'input[type="number"], input:not([type]), textarea')
        
        # Filter to visible, enabled inputs
        visible_inputs = [inp for inp in inputs if inp.is_displayed() and inp.is_enabled()]
        
        if not visible_inputs:
            return False
        
        # Limit to first 3 inputs (was 5) to avoid overwhelming
        visible_inputs = visible_inputs[:3]
        
        # Generate fake data for this session
        fake_data = generate_fake_data()
        
        filled_count = 0
        
        for input_field in visible_inputs:
            try:
                # Initialize search field flag
                is_search_field = False
                
                # Get field attributes to determine type
                field_type = input_field.get_attribute('type') or 'text'
                field_name = (input_field.get_attribute('name') or '').lower()
                field_id = (input_field.get_attribute('id') or '').lower()
                field_placeholder = (input_field.get_attribute('placeholder') or '').lower()
                field_aria_label = (input_field.get_attribute('aria-label') or '').lower()
                
                # Combine all attributes to detect field purpose
                field_text = f"{field_name} {field_id} {field_placeholder} {field_aria_label}"
                
                # Determine what data to type based on field indicators
                value_to_type = None
                
                if field_type == 'email' or any(word in field_text for word in ['email', 'e-mail', 'mail']):
                    value_to_type = fake_data['email']
                
                elif field_type == 'tel' or any(word in field_text for word in ['phone', 'tel', 'mobile', 'cellular']):
                    value_to_type = fake_data['phone']
                
                elif any(word in field_text for word in ['firstname', 'first_name', 'first name', 'fname', 'prenom']):
                    value_to_type = fake_data['first_name']
                
                elif any(word in field_text for word in ['lastname', 'last_name', 'last name', 'lname', 'nom', 'surname']):
                    value_to_type = fake_data['last_name']
                
                elif any(word in field_text for word in ['name', 'fullname', 'full_name', 'your name']):
                    value_to_type = fake_data['name']
                
                elif field_type == 'number' or any(word in field_text for word in ['age', 'quantity', 'amount']):
                    value_to_type = fake_data['number']
                
                elif any(word in field_text for word in ['zip', 'postal', 'postcode', 'zipcode']):
                    value_to_type = fake_data['zipcode']
                
                elif field_type == 'search' or any(word in field_text for word in ['search', 'query', 'find', 'recherche', 'buscar', 'q']):
                    value_to_type = fake_data['search']
                    # Mark this as a search field for later submission
                    is_search_field = True
                
                elif any(word in field_text for word in ['address', 'street', 'addr']):
                    value_to_type = fake_data['address']
                
                elif any(word in field_text for word in ['city', 'ville']):
                    value_to_type = fake_data['city']
                
                elif any(word in field_text for word in ['state', 'province', 'region']):
                    value_to_type = fake_data['state']
                
                elif any(word in field_text for word in ['country', 'pays']):
                    value_to_type = fake_data['country']
                
                elif any(word in field_text for word in ['username', 'user', 'login']):
                    value_to_type = fake_data['username']
                
                elif any(word in field_text for word in ['company', 'organization', 'organisation']):
                    value_to_type = fake_data['company']
                
                elif any(word in field_text for word in ['job', 'title', 'position']):
                    value_to_type = fake_data['job_title']
                
                elif any(word in field_text for word in ['url', 'website', 'link']):
                    value_to_type = fake_data['url']
                
                elif any(word in field_text for word in ['date', 'birthday', 'dob']):
                    value_to_type = fake_data['date']
                
                elif input_field.tag_name == 'textarea' or any(word in field_text for word in ['message', 'comment', 'feedback']):
                    value_to_type = fake_data['message']
                
                else:
                    # Generic text field - use search term or skip
                    if random.random() < 0.5:
                        value_to_type = fake_data['search']
                
                # Type the value if we determined what it should be
                if value_to_type:
                    # Clear field first
                    input_field.clear()
                    time.sleep(random.uniform(0.1, 0.3))
                    
                    # Type with realistic timing
                    for char in value_to_type:
                        input_field.send_keys(char)
                        time.sleep(random.uniform(0.08, 0.25))
                    
                    # Occasional typo and correction
                    if random.random() < 0.15 and len(value_to_type) > 3:
                        time.sleep(random.uniform(0.2, 0.5))
                        input_field.send_keys(Keys.BACK_SPACE)
                        time.sleep(random.uniform(0.1, 0.3))
                        input_field.send_keys(value_to_type[-1])
                    
                    filled_count += 1
                    
                    # If this is a search field, submit search immediately (50% chance)
                    if 'is_search_field' in locals() and is_search_field and random.random() < 0.5:
                        time.sleep(random.uniform(0.3, 0.8))
                        try:
                            # Try pressing Enter
                            input_field.send_keys(Keys.ENTER)
                            print(f'  [{browser_type}] 🔍 Performed search: "{value_to_type[:40]}"')
                            time.sleep(random.uniform(1.5, 3.0))
                            return True  # Search performed, exit function
                        except:
                            pass
                    
                    # Pause between fields
                    time.sleep(random.uniform(0.5, 1.5))
                    
                    # Reset search field flag
                    is_search_field = False
            
            except Exception:
                continue
        
        if filled_count > 0:
            print(f'  [{browser_type}] ⌨️  Typed in {filled_count} form field(s)')
            
            # Small chance to submit form (10% of forms filled)
            if random.random() < 0.1:
                try:
                    # Look for submit button
                    submit_buttons = driver.find_elements(By.CSS_SELECTOR, 
                        'button[type="submit"], input[type="submit"], '
                        'button:not([type="button"]):not([type="reset"])')
                    
                    for button in submit_buttons:
                        if button.is_displayed() and button.is_enabled():
                            button_text = button.text.lower() if button.text else ''
                            
                            # Only click safe submit buttons (avoid logout, delete, etc.)
                            safe_keywords = ['search', 'find', 'go', 'submit', 'send', 'subscribe', 
                                           'sign up', 'newsletter', 'rechercher', 'envoyer']
                            unsafe_keywords = ['delete', 'remove', 'logout', 'log out', 'signout', 
                                             'unsubscribe', 'cancel', 'supprimer', 'deconnecter']
                            
                            is_safe = any(keyword in button_text for keyword in safe_keywords)
                            is_unsafe = any(keyword in button_text for keyword in unsafe_keywords)
                            
                            if is_safe and not is_unsafe:
                                time.sleep(random.uniform(0.5, 1.5))
                                button.click()
                                print(f'  [{browser_type}] 📨 Submitted form')
                                time.sleep(random.uniform(1.0, 2.0))
                                break
                except Exception:
                    pass
            
            return True
        
        return False
        
    except Exception:
        return False
    finally:
        # Restore normal timeout
        try:
            driver.set_page_load_timeout(30)
        except:
            pass


# ============================================
# BROWSER CONFIGURATION
# ============================================

# All browser types available in Selenium Grid
# We run multiple versions of each browser type for maximum TLS/HTTP/CSS diversity
# Selenium Grid automatically load-balances requests across available nodes
# 
# Available browser nodes (26 total versions):
# 
# CHROME (8 versions):
#   - chrome-95, chrome-110, chrome-120, chrome-125, chrome-130
#   - chrome-latest (v131+), chrome-beta, chrome-dev
# 
# FIREFOX (8 versions):
#   - firefox-98, firefox-110, firefox-120, firefox-130, firefox-140
#   - firefox-latest (v144), firefox-beta, firefox-dev
# 
# EDGE (7 versions):
#   - edge-114, edge-120, edge-125, edge-130
#   - edge-latest, edge-beta, edge-dev
# 
# CHROMIUM (3 versions):
#   - chromium-latest, chromium-beta, chromium-dev
#
# Each browser version has unique characteristics:
# - TLS/SSL fingerprints (JA3/JA4 - cipher order, extensions, curves)
# - HTTP/2 stream prioritization and header compression
# - CSS feature support (implementation differences across versions)
# - JavaScript engine variations and performance characteristics
# - WebGL implementation differences
# - Default fonts and rendering engine versions
# 
# Combined with extensive fingerprint randomization:
# - 150+ GPU configurations (multi-GPU support)
# - 180+ platform/OS combinations
# - 400+ fonts (Windows/macOS/Linux)
# - 30+ media devices (cameras/mics/speakers)
# - 50+ WebKit versions
# - 80+ browser build numbers
# - Canvas/Audio noise injection
# - WebRTC randomization
# - Battery API randomization
#
# = BILLIONS OF UNIQUE BROWSER FINGERPRINTS =

# Weighted browser selection for realistic distribution
browsers = (
    ['chrome'] * 40 +      # 40% - Most popular browser
    ['firefox'] * 30 +     # 30% - Second most popular
    ['edge'] * 20 +        # 20% - Growing market share
    ['chromium'] * 10      # 10% - Open-source variant for extra diversity
)

# Persona rotation configuration from environment
PERSONA_ROTATION_STRATEGY = os.getenv('PERSONA_ROTATION_STRATEGY', 'weighted')
PERSONA_MAX_AGE_DAYS = int(os.getenv('PERSONA_MAX_AGE_DAYS', '30'))
PERSONA_MAX_USES = int(os.getenv('PERSONA_MAX_USES', '100'))

# Global persona manager instance
persona_manager = PersonaManager() if PERSONA_MANAGER_AVAILABLE else None

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


def get_coords_for_timezone(timezone_offset):
    """
    Map timezone offset to realistic geographic coordinates
    Used for geolocation API consistency
    
    Args:
        timezone_offset: Timezone offset in minutes
    
    Returns:
        tuple: (latitude, longitude) with slight randomization
    """
    # Major cities by timezone offset (minutes from UTC)
    timezone_to_city_coords = {
        -480: (37.7749, -122.4194),   # San Francisco (PST)
        -420: (33.4484, -112.0740),   # Phoenix (MST)
        -360: (41.8781, -87.6298),    # Chicago (CST)
        -300: (40.7128, -74.0060),    # New York (EST)
        -240: (10.4806, -66.9036),    # Caracas
        -180: (-23.5505, -46.6333),   # São Paulo
        0: (51.5074, -0.1278),        # London (GMT)
        60: (48.8566, 2.3522),        # Paris (CET)
        120: (52.5200, 13.4050),      # Berlin (CEST)
        180: (55.7558, 37.6173),      # Moscow
        240: (25.2048, 55.2708),      # Dubai
        300: (28.6139, 77.2090),      # Delhi
        330: (19.0760, 72.8777),      # Mumbai
        360: (23.8103, 90.4125),      # Dhaka
        420: (13.7563, 100.5018),     # Bangkok
        480: (39.9042, 116.4074),     # Beijing
        540: (35.6762, 139.6503),     # Tokyo
        600: (37.5665, 126.9780),     # Seoul / Sydney area
        660: (-33.8688, 151.2093),    # Sydney
        720: (-36.8485, 174.7633),    # Auckland
    }
    
    # Get closest timezone
    if timezone_offset in timezone_to_city_coords:
        base_lat, base_lng = timezone_to_city_coords[timezone_offset]
    else:
        # Find nearest timezone
        nearest_offset = min(timezone_to_city_coords.keys(), 
                           key=lambda x: abs(x - timezone_offset))
        base_lat, base_lng = timezone_to_city_coords[nearest_offset]
    
    # Add ±0.5km noise to coordinates
    lat_noise = (random.random() - 0.5) * 0.01  # ~0.5km
    lng_noise = (random.random() - 0.5) * 0.01
    
    return (round(base_lat + lat_noise, 4), round(base_lng + lng_noise, 4))


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

def generate_random_user_agent():
    """Generate a random realistic user agent by combining different components"""
    
    # MASSIVELY EXPANDED Platform/OS options - Desktop, Mobile, Tablet, Legacy
    platforms = [
        # Modern Windows (heavily weighted)
        "Windows NT 10.0; Win64; x64",
        "Windows NT 10.0; Win64; x64",
        "Windows NT 10.0; Win64; x64",
        "Windows NT 11.0; Win64; x64",
        "Windows NT 11.0; Win64; x64",
        "Windows NT 10.0; WOW64",
        "Windows NT 10.0; Win64; x64; rv:109.0",
        "Windows NT 10.0; Win64; x64; rv:115.0",
        "Windows NT 6.1; Win64; x64",  # Windows 7
        "Windows NT 6.3; Win64; x64",  # Windows 8.1
        "Windows NT 6.2; Win64; x64",  # Windows 8
        "Windows NT 6.1; WOW64",  # Windows 7 32-bit on 64-bit
        "Windows NT 6.3; WOW64",
        "Windows NT 5.1",  # Windows XP
        "Windows NT 6.0",  # Windows Vista
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
        "X11; Linux x86_64; rv:109.0",
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
    
    # MASSIVELY EXPANDED Chrome versions (major versions and builds)
    chrome_major_versions = [
        109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130
    ]
    chrome_builds = [
        "0.0.0", "0.0.0", "0.0.0",  # Common default
        "0.5414.74", "0.5414.87", "0.5414.119", "0.5414.129",
        "0.5481.77", "0.5481.100", "0.5481.177", "0.5481.192",
        "0.5615.49", "0.5615.86", "0.5615.121", "0.5615.137", "0.5615.165",
        "0.5735.90", "0.5735.106", "0.5735.134", "0.5735.198", "0.5735.248",
        "0.5845.96", "0.5845.110", "0.5845.140", "0.5845.179", "0.5845.228",
        "0.5993.70", "0.5993.88", "0.5993.117", "0.5993.159",
        "0.6045.105", "0.6045.124", "0.6045.159", "0.6045.199",
        "0.6099.56", "0.6099.71", "0.6099.109", "0.6099.129", "0.6099.216",
        "0.6100.42", "0.6100.67", "0.6100.88", "0.6100.99",
        "0.6261.57", "0.6261.69", "0.6261.94", "0.6261.111", "0.6261.128",
        "0.6312.58", "0.6312.86", "0.6312.105", "0.6312.122", "0.6312.145",
        "0.6367.60", "0.6367.78", "0.6367.91", "0.6367.118", "0.6367.155", "0.6367.201",
        "0.6478.61", "0.6478.114", "0.6478.126", "0.6478.182",
        "0.6563.64", "0.6563.110", "0.6563.156", "0.6563.187",
        "0.6613.84", "0.6613.119", "0.6613.137", "0.6613.162",
        "0.6723.58", "0.6723.91", "0.6723.116", "0.6723.132",
        "0.6820.51", "0.6820.82", "0.6820.106", "0.6820.128",
    ]
    
    # MASSIVELY EXPANDED Firefox versions
    firefox_versions = [
        110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128
    ]
    
    # MASSIVELY EXPANDED Edge versions
    edge_versions = [
        109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125
    ]
    
    # MASSIVELY EXPANDED Safari versions
    safari_versions = [
        "15.0", "15.1", "15.2", "15.3", "15.4", "15.5", "15.6",
        "16.0", "16.1", "16.2", "16.3", "16.4", "16.5", "16.6",
        "17.0", "17.1", "17.2", "17.3", "17.4", "17.5"
    ]
    
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

def play_youtube_video(driver, browser_type):
    """
    Detect and play YouTube videos when encountered
    
    Args:
        driver: WebDriver instance
        browser_type: Browser name for logging
    
    Returns:
        bool: True if a video was played
    """
    try:
        current_url = driver.current_url
        
        # Check if we're on YouTube
        if 'youtube.com' not in current_url and 'youtu.be' not in current_url:
            return False
        
        print(f'  [{browser_type}] 🎥 Detected YouTube page, attempting to play video...')
        
        # Wait a moment for page to load
        time.sleep(random.uniform(1, 2))
        
        # Try multiple methods to play the video
        play_selectors = [
            'button.ytp-large-play-button',  # Big play button overlay
            'button.ytp-play-button',  # Small play button in controls
            '.ytp-play-button',
            'button[aria-label*="Play"]',
            'button[title*="Play"]',
            '.html5-video-player',  # Click anywhere on video player
            'video.html5-main-video',  # The actual video element
        ]
        
        video_played = False
        
        # Method 1: Try clicking play button selectors
        for selector in play_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if element.is_displayed():
                        try:
                            element.click()
                            print(f'  [{browser_type}] ▶️  Clicked play button!')
                            video_played = True
                            time.sleep(random.uniform(0.5, 1))
                            break
                        except:
                            continue
                if video_played:
                    break
            except:
                continue
        
        # Method 2: Use JavaScript to play the video directly
        if not video_played:
            try:
                driver.execute_script('''
                    var videos = document.querySelectorAll('video');
                    if (videos.length > 0) {
                        videos[0].play();
                        return true;
                    }
                    return false;
                ''')
                print(f'  [{browser_type}] ▶️  Started video via JavaScript!')
                video_played = True
            except:
                pass
        
        if video_played:
            # Let video play for a realistic amount of time (5-30 seconds)
            watch_time = random.uniform(5, 30)
            print(f'  [{browser_type}] 📺 Watching video for {watch_time:.1f}s...')
            time.sleep(watch_time)
            
            # Occasionally scroll down to comments (30% chance)
            if random.random() < 0.3:
                try:
                    scroll_amount = random.randint(500, 1500)
                    driver.execute_script(f'window.scrollBy(0, {scroll_amount});')
                    print(f'  [{browser_type}] 💬 Scrolled to comments section')
                    time.sleep(random.uniform(1, 3))
                except:
                    pass
            
            # Occasionally interact with video controls (pause, seek, volume)
            if random.random() < 0.2:  # 20% chance
                try:
                    # Click pause button
                    pause_button = driver.find_element(By.CSS_SELECTOR, 'button.ytp-play-button')
                    if pause_button.is_displayed():
                        pause_button.click()
                        print(f'  [{browser_type}] ⏸️  Paused video')
                        time.sleep(random.uniform(1, 3))
                        # Play again
                        pause_button.click()
                        print(f'  [{browser_type}] ▶️  Resumed video')
                        time.sleep(random.uniform(2, 5))
                except:
                    pass
            
            return True
        else:
            print(f'  [{browser_type}] ⚠️  Could not find play button')
            return False
            
    except Exception as e:
        print(f'  [{browser_type}] ⚠️  YouTube play error: {str(e)[:50]}')
        return False

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
            
            # Step 2: Google & YouTube-specific consent handling (must be before generic)
            try:
                # Try XPath for Google consent buttons (more reliable for exact text matching)
                google_consent_xpaths = [
                    # French (primary for the user's case)
                    "//button[contains(text(), 'Tout accepter')]",
                    "//button[contains(., 'Tout accepter')]",
                    "//button[normalize-space()='Tout accepter']",
                    "//form//button[contains(text(), 'Tout accepter')]",
                    "//form//button[contains(text(), 'accepter')]",
                    "//div[@role='dialog']//button[contains(text(), 'Tout accepter')]",
                    # English
                    "//button[contains(text(), 'Accept all')]",
                    "//button[contains(., 'Accept all')]",
                    "//button[normalize-space()='Accept all']",
                    "//form//button[contains(text(), 'Accept all')]",
                    "//div[@role='dialog']//button[contains(text(), 'Accept all')]",
                    # German
                    "//button[contains(text(), 'Alle akzeptieren')]",
                    "//form//button[contains(text(), 'Alle akzeptieren')]",
                    # Spanish
                    "//button[contains(text(), 'Aceptar todo')]",
                    "//form//button[contains(text(), 'Aceptar todo')]",
                    # Italian
                    "//button[contains(text(), 'Accetta tutto')]",
                    # Portuguese
                    "//button[contains(text(), 'Aceitar tudo')]",
                    # Dutch
                    "//button[contains(text(), 'Alles accepteren')]",
                    # Swedish
                    "//button[contains(text(), 'Godkänn alla')]",
                    # Danish
                    "//button[contains(text(), 'Accepter alle')]",
                    # Finnish
                    "//button[contains(text(), 'Hyväksy kaikki')]",
                ]
                
                # First try XPath selectors (more reliable for exact text matching)
                for xpath in google_consent_xpaths:
                    try:
                        elements = driver.find_elements(By.XPATH, xpath)
                        for element in elements:
                            try:
                                if element.is_displayed() and element.is_enabled():
                                    element.click()
                                    print(f'  [{browser_type}] 🍪 Accepted Google/YouTube consent (XPath)')
                                    time.sleep(1)
                                    return True
                            except:
                                continue
                    except:
                        continue
                
                # Then try CSS selectors for Google consent
                google_consent_selectors = [
                    # Google consent form specific selectors
                    'form[action*="consent.google"] button[type="submit"]',
                    'form[action*="consent"] button[type="submit"]',
                    
                    # YouTube-specific consent handling
                    'button[aria-label*="Accept all"]',
                    'button[aria-label*="accept all"]',
                    'button[aria-label*="Accepter tout"]',
                    'button[aria-label*="Tout accepter"]',
                    'ytd-button-renderer button[aria-label*="Accept"]',
                    'tp-yt-paper-dialog button[aria-label*="Accept all"]',
                    'c3-consent-bump button[aria-label*="Accept"]',
                    '[aria-label="Accept all"]',
                    '[aria-label="Tout accepter"]',
                    '[aria-label="Accept the use of cookies"]',
                    'ytd-consent-bump-v2-lightbox button[aria-label*="Accept"]',
                    
                    # Additional Google consent patterns
                    'button[jsname*="accept"]',
                    'button[jsaction*="accept"]',
                    
                    # Generic dialog buttons (try first button in Google consent dialogs)
                    'div[role="dialog"] button[type="button"]',
                ]
                
                # Try CSS selectors
                for selector in google_consent_selectors:
                    try:
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        for element in elements:
                            try:
                                if element.is_displayed() and element.is_enabled():
                                    # Check button text to ensure it's the accept button
                                    button_text = element.text.lower()
                                    accept_keywords = ['accept', 'accepter', 'tout', 'all', 'alle', 'aceptar', 'accetta', 'aceitar', 'godkänn', 'hyväksy']
                                    reject_keywords = ['reject', 'refus', 'refuse', 'deny', 'decline', 'opt out', 'options', 'settings', 'parameters', 'param']
                                    
                                    # Only click if it has accept keywords and no reject keywords
                                    has_accept = any(keyword in button_text for keyword in accept_keywords)
                                    has_reject = any(keyword in button_text for keyword in reject_keywords)
                                    
                                    if has_accept and not has_reject:
                                        element.click()
                                        print(f'  [{browser_type}] 🍪 Accepted Google/YouTube consent (CSS)')
                                        time.sleep(1)
                                        return True
                            except:
                                continue
                    except:
                        continue
            except:
                pass
            
            # Step 3: Toggle cookie category switches (Usercentrics, accessiBe, etc.)
            try:
                # Find toggle switches/checkboxes for cookie categories
                toggle_selectors = [
                    # Usercentrics / accessiBe toggles
                    'input[type="checkbox"][role="switch"]',
                    '.switch input[type="checkbox"]',
                    'input[aria-label*="Cookies"]',
                    'input[aria-label*="cookie"]',
                    # Generic toggles with cookie-related parents
                    '[class*="cookie"] input[type="checkbox"]',
                    '[id*="cookie"] input[type="checkbox"]',
                    '[class*="consent"] input[type="checkbox"]',
                    '[id*="consent"] input[type="checkbox"]',
                    # Toggle switches (not just checkboxes)
                    '[role="switch"]',
                    '.toggle-switch input',
                ]
                
                toggled_count = 0
                for selector in toggle_selectors:
                    try:
                        toggles = driver.find_elements(By.CSS_SELECTOR, selector)
                        for toggle in toggles:
                            try:
                                # Check if toggle is visible and not already checked
                                if toggle.is_displayed() and toggle.is_enabled():
                                    # Get labels to avoid toggling "Essential" (always on)
                                    parent_text = ''
                                    try:
                                        parent = toggle.find_element(By.XPATH, './ancestor::*[1]')
                                        parent_text = parent.text.lower() if parent else ''
                                    except:
                                        pass
                                    
                                    # Skip "Essential" toggles (they're always on and read-only)
                                    if 'essential' not in parent_text and 'essent' not in parent_text:
                                        # Check if already checked
                                        is_checked = toggle.is_selected() or toggle.get_attribute('checked') == 'true' or toggle.get_attribute('aria-checked') == 'true'
                                        
                                        if not is_checked:
                                            # Click to enable this cookie category
                                            try:
                                                # Try clicking the toggle itself
                                                toggle.click()
                                                toggled_count += 1
                                                time.sleep(random.uniform(0.2, 0.4))
                                            except:
                                                # If direct click fails, try clicking parent label
                                                try:
                                                    parent = toggle.find_element(By.XPATH, './ancestor::label[1]')
                                                    parent.click()
                                                    toggled_count += 1
                                                    time.sleep(random.uniform(0.2, 0.4))
                                                except:
                                                    pass
                            except:
                                continue
                    except:
                        continue
                
                if toggled_count > 0:
                    print(f'  [{browser_type}] 🍪 Toggled {toggled_count} cookie category switch(es)')
                    time.sleep(random.uniform(0.3, 0.6))
            except:
                pass
            
            # Step 4: Common "Accept All" / "Agree to all" buttons (Comprehensive Multi-Language, Multi-Provider)
            accept_all_selectors = [
                # ============================================
                # MAJOR CONSENT PLATFORMS
                # ============================================
                
                # OneTrust
                '#onetrust-accept-btn-handler',
                '.onetrust-close-btn-handler',
                'button[aria-label="Accept All Cookies"]',
                '#accept-recommended-btn-handler',
                '.ot-pc-refuse-all-handler',
                
                # Cookiebot
                '#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll',
                '#CybotCookiebotDialogBodyButtonAccept',
                '.CybotCookiebotDialogBodyButton',
                'a[id*="CybotCookiebot"]',
                
                # DIDOMI
                'button[aria-label="Agree to all"]',
                'button.didomi-button-highlight',
                '#didomi-notice-agree-button',
                '.didomi-consent-popup-actions button:first-child',
                
                # Quantcast Choice (TCF)
                'button[aria-label="AGREE"]',
                'button[aria-label="ACCEPTER"]',
                'button[mode="primary"]',
                '.qc-cmp2-summary-buttons button:first-child',
                
                # Usercentrics
                '[data-testid="uc-accept-all-button"]',
                '#uc-btn-accept-banner',
                'button[data-testid="uc-accept-all-button"]',
                '[aria-label="Accept All"]',
                
                # TrustArc
                '#truste-consent-button',
                '.truste-button1',
                '.trustarc-agree-btn',
                
                # Osano
                '.osano-cm-accept-all',
                '.osano-cm-dialog__close',
                
                # Cookie Information
                '#cookie-information-template-wrapper button',
                
                # Termly
                '#termly-code-snippet-support button',
                
                # Sourcepoint
                'button[title="Accept all"]',
                'button[title="Accepter tout"]',
                
                # Consentmanager.net
                '#cmpwelcomebtnyes',
                '.cmpboxbtnyes',
                
                # ============================================
                # TCF VENDOR DIALOGS (Multi-Language)
                # ============================================
                
                # English
                'button:has-text("Consent")',
                'button:has-text("Accept")',
                'button:has-text("I Accept")',
                'button:has-text("I Agree")',
                'button[title*="Consent"]',
                'button[aria-label*="Consent"]',
                'button[aria-label*="Accept"]',
                
                # French
                'button:has-text("Accepter")',
                'button:has-text("J\'accepte")',
                'button:has-text("Je consens")',
                'button[aria-label*="Accepter"]',
                'button[title*="Accepter"]',
                
                # German
                'button:has-text("Akzeptieren")',
                'button:has-text("Alle akzeptieren")',
                'button:has-text("Zustimmen")',
                'button[aria-label*="Akzeptieren"]',
                
                # Spanish
                'button:has-text("Aceptar")',
                'button:has-text("Acepto")',
                'button:has-text("Aceptar todo")',
                'button[aria-label*="Aceptar"]',
                
                # Italian
                'button:has-text("Accetta")',
                'button:has-text("Accetto")',
                'button:has-text("Accetta tutto")',
                'button[aria-label*="Accetta"]',
                
                # Portuguese
                'button:has-text("Aceitar")',
                'button:has-text("Aceito")',
                'button:has-text("Aceitar tudo")',
                'button[aria-label*="Aceitar"]',
                
                # Dutch
                'button:has-text("Accepteren")',
                'button:has-text("Alles accepteren")',
                'button[aria-label*="Accepteren"]',
                
                # Polish
                'button:has-text("Akceptuję")',
                'button:has-text("Zgadzam się")',
                'button[aria-label*="Akceptuj"]',
                
                # Swedish
                'button:has-text("Acceptera")',
                'button:has-text("Godkänn")',
                'button[aria-label*="Acceptera"]',
                
                # Danish
                'button:has-text("Accepter")',
                'button:has-text("Godkend")',
                
                # Norwegian
                'button:has-text("Godta")',
                'button:has-text("Aksepter")',
                
                # Finnish
                'button:has-text("Hyväksy")',
                
                # ============================================
                # COMMON CLASS PATTERNS
                # ============================================
                
                '[class*="accept-all"]',
                '[class*="acceptAll"]',
                '[class*="accept_all"]',
                '[class*="consent-accept"]',
                '[class*="consent-btn"]',
                '[class*="consent-button"]',
                '[class*="cookie-accept"]',
                '[class*="cookie-btn-accept"]',
                '[class*="cookies-accept"]',
                '[class*="cmp-accept"]',
                '[class*="gdpr-accept"]',
                '[class*="banner-accept"]',
                '[class*="consent-agree"]',
                '[class*="agree-button"]',
                '.accept-cookies',
                '.accept-button',
                '.cookie-accept-button',
                '.js-accept-cookies',
                '.cookie-banner-accept',
                '.consent-banner-button-accept',
                
                # ============================================
                # COMMON ID PATTERNS
                # ============================================
                
                '#accept-cookies',
                '#acceptCookies',
                '#accept_cookies',
                '#cookie-accept',
                '#cookieAccept',
                '#cookie_accept',
                '#accept-all',
                '#acceptAll',
                '#accept_all',
                '#acceptAllButton',
                '#accept-all-cookies',
                '#accept_all_cookies',
                '#btn-accept',
                '#btn-accept-all',
                '#btnAcceptAll',
                '#cookie-consent-accept',
                '#consent-accept-all',
                '#gdpr-accept',
                '#privacy-accept',
                
                # ============================================
                # DATA ATTRIBUTES (Provider-Specific)
                # ============================================
                
                '[data-action="accept"]',
                '[data-action="accept-all"]',
                '[data-action="acceptAll"]',
                '[data-cookie="accept"]',
                '[data-consent="accept"]',
                '[data-consent="accept-all"]',
                '[data-testid="cookie-accept"]',
                '[data-testid="accept-all"]',
                '[data-testid="accept-all-cookies"]',
                '[data-testid="consent-banner-accept-button"]',
                '[data-choice="accept"]',
                '[data-choice="accept-all"]',
                '[data-gdpr="accept"]',
                '[data-cookie-consent="accept"]',
                '[data-cc="accept"]',
                '[data-consent-action="accept"]',
                
                # ============================================
                # BUTTON NAMES & TITLES
                # ============================================
                
                'button[name="accept"]',
                'button[name="accept-all"]',
                'button[name="agree"]',
                'button[name="consent"]',
                'button[title="Accept"]',
                'button[title="Accept all"]',
                'button[title="Accept All Cookies"]',
                'button[title="Accepter"]',
                'button[title="Accepter tout"]',
                'button[title="Akzeptieren"]',
                'button[title="Aceptar"]',
                
                # ============================================
                # SPECIFIC SITE IMPLEMENTATIONS
                # ============================================
                
                # IAB TCF Framework
                '[class*="tcf"] button:first-child',
                '[id*="tcf"] button[mode="primary"]',
                
                # Utiq / ConsentHub / Reworld Media
                'button:contains("Accepter"):not(:contains("Rejeter"))',
                '[class*="consenthub"] button:contains("Accepter")',
                '[id*="utiq"] button:contains("Accepter")',
                
                # Generic fallbacks
                'button[class*="accept"]:not([class*="reject"]):not([class*="refuse"])',
                'button[id*="accept"]:not([id*="reject"])',
                '.cookie-banner button:first-child',
                '.cookie-notice button:first-child',
                '[class*="cookie"] button:has-text("Accept")',
                '[class*="consent"] button:has-text("Accept")',
                '[class*="gdpr"] button:has-text("Accept")',
                '[class*="privacy"] button:has-text("Accept")',
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
            
            # Step 5: Find buttons by text content (Multi-Language)
            accept_text_patterns = [
                # ============================================
                # ENGLISH
                # ============================================
                'accept all cookies', 'accept all', 'accept cookies', 'i accept', 'allow all', 'allow cookies',
                'agree', 'agree to all', 'agree and continue', 'got it', 'ok', 'continue', 'consent',
                'agree and close', 'accept & close', 'accept and continue', 'accept & continue',
                'allow all cookies', 'yes, i accept', 'i understand', 'understood',
                
                # ============================================
                # FRENCH
                # ============================================
                'accepter et continuer', 'accepter tout', 'accepter', 'tout accepter', 
                'j\'accepte', 'j accepte', 'accepter et fermer', 'consentir', 'je consens',
                'accepter les cookies', 'accepter tous les cookies', 'd\'accord',
                'autoriser', 'autoriser tout',
                
                # ============================================
                # GERMAN
                # ============================================
                'alle akzeptieren', 'akzeptieren', 'einverstanden', 'akzeptieren und fortfahren',
                'alle cookies akzeptieren', 'verstanden', 'zustimmen', 'ich stimme zu',
                'annehmen', 'alle annehmen', 'ok, verstanden',
                
                # ============================================
                # SPANISH
                # ============================================
                'aceptar todo', 'aceptar', 'acepto', 'aceptar y continuar', 'consentimiento',
                'aceptar todas', 'aceptar cookies', 'permitir', 'permitir todo',
                'de acuerdo', 'entendido', 'estoy de acuerdo',
                
                # ============================================
                # ITALIAN
                # ============================================
                'accetta tutto', 'accetto', 'accetta', 'accetta e continua', 'consenso',
                'accetta tutti', 'accetta i cookie', 'acconsento', 'sono d\'accordo',
                'd\'accordo', 'ho capito', 'autorizza',
                
                # ============================================
                # PORTUGUESE
                # ============================================
                'aceitar tudo', 'aceitar', 'aceitar e continuar', 'consentir', 'aceito',
                'aceitar cookies', 'aceitar todos', 'permitir', 'permitir tudo',
                'concordo', 'eu aceito', 'entendi',
                
                # ============================================
                # DUTCH
                # ============================================
                'accepteer alles', 'accepteren', 'ja, accepteren', 'accepteren en doorgaan',
                'alle cookies accepteren', 'toestaan', 'akkoord', 'ik ga akkoord',
                'begrepen', 'ik accepteer',
                
                # ============================================
                # POLISH
                # ============================================
                'akceptuję', 'zgadzam się', 'zaakceptuj wszystko', 'akceptuj',
                'akceptuj wszystkie', 'zgoda', 'rozumiem', 'potwierdzam',
                
                # ============================================
                # SWEDISH
                # ============================================
                'acceptera', 'godkänn', 'acceptera alla', 'jag accepterar',
                'acceptera allt', 'jag godkänner', 'ok, jag förstår', 'tillåt',
                
                # ============================================
                # DANISH
                # ============================================
                'accepter', 'godkend', 'accepter alle', 'jeg accepterer',
                'tillad', 'forstået', 'jeg forstår',
                
                # ============================================
                # NORWEGIAN
                # ============================================
                'godta', 'aksepter', 'godta alle', 'jeg godtar',
                'jeg aksepterer', 'tillat', 'forstått',
                
                # ============================================
                # FINNISH
                # ============================================
                'hyväksy', 'hyväksy kaikki', 'hyväksyn', 'ymmärrän',
                'salli', 'suostumus',
                
                # ============================================
                # OTHER EUROPEAN LANGUAGES
                # ============================================
                'souhlasím', 'přijmout vše', 'přijmout', 'rozumím',  # Czech
                'accept toate', 'sunt de acord', 'înțeleg',  # Romanian
                
                # ============================================
                # NON-LATIN SCRIPTS
                # ============================================
                'συμφωνώ', 'αποδοχή', 'αποδοχή όλων', 'κατανοώ',  # Greek
                'принимаю', 'согласен', 'принять все', 'понятно',  # Russian
                'kabul ediyorum', 'kabul et', 'tümünü kabul et', 'anladım',  # Turkish
                'موافق', 'قبول', 'قبول الكل', 'أوافق',  # Arabic
                '同意する', '同意', 'すべて許可', '了解',  # Japanese
                '동의', '모두 동의', '확인', '동의합니다',  # Korean
                '接受', '全部接受', '同意', '我同意', '确定', '接受全部', '允许', '明白了',  # Chinese
            ]
            
            try:
                all_buttons = driver.find_elements(By.TAG_NAME, 'button')
                all_buttons += driver.find_elements(By.CSS_SELECTOR, 'a.button, .btn, [role="button"]')
                
                # First pass: prioritize "accept all" / "accepter tout" type buttons
                priority_patterns = [
                    # English
                    'accept all cookies', 'accept all', 'allow all', 'agree to all', 'consent',
                    # French
                    'accepter tout', 'tout accepter', 'accepter et continuer', 'accepter tous les cookies',
                    # German
                    'alle akzeptieren', 'alle cookies akzeptieren',
                    # Spanish
                    'aceptar todo', 'aceptar todas',
                    # Italian
                    'accetta tutto', 'accetta tutti',
                    # Portuguese
                    'aceitar tudo', 'aceitar todos',
                    # Dutch
                    'accepteer alles', 'alle cookies accepteren',
                    # Polish
                    'zaakceptuj wszystko', 'akceptuj wszystkie',
                    # Swedish, Danish, Norwegian
                    'acceptera alla', 'acceptera allt', 'godta alle', 'accepter alle',
                    # Finnish, Czech
                    'hyväksy kaikki', 'přijmout vše',
                ]
                
                for button in all_buttons:
                    try:
                        if not button.is_displayed():
                            continue
                        
                        button_text = button.text.lower().strip()
                        
                        # Skip reject buttons
                        reject_keywords = ['reject', 'refuse', 'rejeter', 'refuser', 'deny', 'decline', 'manage options']
                        if any(keyword in button_text for keyword in reject_keywords):
                            continue
                        
                        # Check priority patterns first
                        for pattern in priority_patterns:
                            if pattern in button_text:
                                button.click()
                                print(f'  [{browser_type}] 🍪 Accepted cookies via text: "{button.text[:40]}"')
                                time.sleep(0.5)
                                return True
                    except:
                        continue
                
                # Second pass: accept other accept buttons
                for button in all_buttons:
                    try:
                        if not button.is_displayed():
                            continue
                        
                        button_text = button.text.lower().strip()
                        
                        # Skip reject buttons (check before anything else)
                        reject_keywords = ['reject', 'refuse', 'rejeter', 'refuser', 'deny', 'decline', 'preferences', 'manage', 'gérer']
                        if any(keyword in button_text for keyword in reject_keywords):
                            continue
                        
                        # Skip empty buttons
                        if not button_text:
                            continue
                        
                        # Check for exact simple matches first (for buttons with just "Accepter", "Accept", etc.)
                        simple_accept_words = ['accepter', 'accept', 'agree', 'ok', 'aceptar', 'akzeptieren', 'accetta', 'aceitar']
                        if button_text in simple_accept_words:
                            button.click()
                            print(f'  [{browser_type}] 🍪 Accepted cookies via exact match: "{button.text[:40]}"')
                            time.sleep(0.5)
                            return True
                        
                        # Check if button text matches any accept pattern
                        for pattern in accept_text_patterns:
                            if pattern in button_text or button_text == pattern.replace(' ', ''):
                                button.click()
                                print(f'  [{browser_type}] 🍪 Accepted cookies via text: "{button.text[:40]}"')
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
    
    # Generate random GPU info for WebGL fingerprinting (with multi-GPU support)
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
    
    # Generate random plugins with browser-specific logic
    plugins_js = generate_random_plugins(browser_type)
    
    # Generate random WebRTC local IPs
    webrtc = generate_random_webrtc()
    
    # Save persona to disk for rotation across sessions
    if persona_manager:
        try:
            fingerprint_data = fingerprint_to_dict(
                browser_type, user_agent, accept_language, screen, gpu, hardware,
                connection, timezone_offset, battery, media_devices, fonts, webrtc, plugins_js
            )
            persona_id = persona_manager.create_persona(fingerprint_data)
            print(f'[{browser_type}] 💾 Saved persona: {persona_id}')
        except Exception as e:
            print(f'[{browser_type}] ⚠️  Failed to save persona: {str(e)[:50]}')
    
    print(f'[{browser_type}] Generated UA: {user_agent[:80]}...')
    print(f'[{browser_type}] Language: {accept_language.split(",")[0]}')
    print(f'[{browser_type}] Screen: {screen["width"]}x{screen["height"]} @ {screen["devicePixelRatio"]}x DPR')
    print(f'[{browser_type}] GPU: {gpu["vendor"]} / {gpu["renderer"][:50]}{"... [Multi-GPU]" if gpu["isMultiGPU"] else ""}')
    print(f'[{browser_type}] Hardware: {hardware["hardwareConcurrency"]} cores, {hardware["deviceMemory"]}GB RAM, {hardware["maxTouchPoints"]} touch')
    print(f'[{browser_type}] Connection: {connection["effectiveType"]}, {connection["rtt"]}ms RTT, {connection["downlink"]}Mbps')
    print(f'[{browser_type}] Timezone: UTC{timezone_offset/60:+.0f}')
    print(f'[{browser_type}] Battery: {"Charging" if battery["charging"] else "Discharging"} at {int(battery["level"]*100)}%')
    print(f'[{browser_type}] WebRTC: {len(webrtc["localIPs"])} local IPs')
    print(f'[{browser_type}] Media: {len(media_devices)} devices, Fonts: {len(fonts)} installed, Plugins: randomized')
    
    if browser_type == 'chrome' or browser_type == 'chromium':
        options = webdriver.ChromeOptions()
        
        # Set browser name for Selenium Grid to pick the right nodes
        options.set_capability('browserName', browser_type)
        
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
    
    # Apply comprehensive CDP stealth for Chrome and Chromium (RemoteWebDriver compatible)
    if browser_type == 'chrome' or browser_type == 'chromium':
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
                    // ============================================
                    // ADVANCED WEBDRIVER ARTIFACT REMOVAL
                    // ============================================
                    
                    // Remove all ChromeDriver-specific artifacts
                    delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
                    delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
                    delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
                    delete window.cdc_adoQpoasnfa76pfcZLmcfl_Object;
                    delete window.cdc_adoQpoasnfa76pfcZLmcfl_Proxy;
                    delete window.cdc_adoQpoasnfa76pfcZLmcfl_JSON;
                    
                    // Remove all variations using regex (cdc_, $cdc_, $wdc_, etc.)
                    Object.keys(window).forEach(key => {{
                        if (key.match(/^(cdc_|\\$cdc_|\\$wdc_|\\$chrome_|__webdriver|__selenium|__fxdriver|__driver)/)) {{
                            try {{
                                delete window[key];
                            }} catch (e) {{}}
                        }}
                    }});
                    
                    // Remove document-level script caches
                    delete document.__webdriver_script_fn;
                    delete document.__selenium_unwrapped;
                    delete document.__webdriver_unwrapped;
                    delete document.__driver_evaluate;
                    delete document.__webdriver_evaluate;
                    delete document.__fxdriver_evaluate;
                    delete document.__driver_unwrapped;
                    delete document.__fxdriver_unwrapped;
                    delete document.__webdriver_script_func;
                    delete document.$cdc_asdjflasutopfhvcZLmcfl_;
                    delete document.$chrome_asyncScriptInfo;
                    
                    // Override Function.prototype.toString to hide proxy behavior
                    const originalToString = Function.prototype.toString;
                    const originalFunctionToString = originalToString;
                    const newToString = function() {{
                        if (this === navigator.webdriver || 
                            this === Navigator.prototype.webdriver) {{
                            return 'function webdriver() {{ [native code] }}';
                        }}
                        // Hide proxy/bound function indicators
                        const str = originalFunctionToString.call(this);
                        if (str.includes('native')) {{
                            return str;
                        }}
                        return str;
                    }};
                    
                    // Make the override itself look native
                    Object.defineProperty(Function.prototype, 'toString', {{
                        value: newToString,
                        writable: true,
                        configurable: true,
                        enumerable: false
                    }});
                    
                    // Prevent new cdc_ properties from being added
                    const cdcProps = [
                        'cdc_adoQpoasnfa76pfcZLmcfl_Array',
                        'cdc_adoQpoasnfa76pfcZLmcfl_Promise',
                        'cdc_adoQpoasnfa76pfcZLmcfl_Symbol'
                    ];
                    
                    cdcProps.forEach(prop => {{
                        Object.defineProperty(window, prop, {{
                            get: () => undefined,
                            set: () => {{}},
                            configurable: false,
                            enumerable: false
                        }});
                    }});
                    
                    // ============================================
                    // NAVIGATOR PROPERTY OVERRIDES
                    // ============================================
                    
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
                    
                    // Mock Geolocation API (consistent with timezone)
                    if (navigator.geolocation) {{
                        const geoCoords = {str(get_coords_for_timezone(timezone_offset))};
                        const mockPosition = {{
                            coords: {{
                                latitude: geoCoords[0],
                                longitude: geoCoords[1],
                                accuracy: 10 + Math.random() * 50,
                                altitude: null,
                                altitudeAccuracy: null,
                                heading: null,
                                speed: null
                            }},
                            timestamp: Date.now()
                        }};
                        
                        navigator.geolocation.getCurrentPosition = function(success, error, options) {{
                            if (success) {{
                                setTimeout(() => success(mockPosition), 50 + Math.random() * 100);
                            }}
                        }};
                        
                        navigator.geolocation.watchPosition = function(success, error, options) {{
                            if (success) {{
                                setTimeout(() => success(mockPosition), 50 + Math.random() * 100);
                            }}
                            return Math.floor(Math.random() * 1000);
                        }};
                        
                        navigator.geolocation.clearWatch = function(id) {{}};
                    }}
                    
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
                    
                    // WebRTC IP randomization (enable but with random local IPs per session)
                    const randomLocalIPs = {str(webrtc["localIPs"])};
                    const OriginalRTCPeerConnection = window.RTCPeerConnection || window.webkitRTCPeerConnection;
                    if (OriginalRTCPeerConnection) {{
                        window.RTCPeerConnection = function(...args) {{
                            const pc = new OriginalRTCPeerConnection(...args);
                            const originalCreateOffer = pc.createOffer;
                            const originalCreateAnswer = pc.createAnswer;
                            
                            // Inject random IPs into SDP
                            const injectRandomIPs = (sdp) => {{
                                if (sdp && sdp.sdp && randomLocalIPs.length > 0) {{
                                    const randomIP = randomLocalIPs[Math.floor(Math.random() * randomLocalIPs.length)];
                                    // Replace candidate IPs with our random ones
                                    sdp.sdp = sdp.sdp.replace(/([0-9]{{1,3}}\\.){{3}}[0-9]{{1,3}}/g, randomIP);
                                }}
                                return sdp;
                            }};
                            
                            pc.createOffer = function(...args2) {{
                                return originalCreateOffer.apply(this, args2).then(injectRandomIPs);
                            }};
                            
                            pc.createAnswer = function(...args2) {{
                                return originalCreateAnswer.apply(this, args2).then(injectRandomIPs);
                            }};
                            
                            return pc;
                        }};
                        window.RTCPeerConnection.prototype = OriginalRTCPeerConnection.prototype;
                    }}
                    
                    // ============================================
                    // PERFORMANCE API NOISE INJECTION
                    // ============================================
                    
                    // Add noise to performance.memory
                    if (performance.memory) {{
                        const originalMemory = Object.getOwnPropertyDescriptor(Performance.prototype, 'memory') ||
                                             Object.getOwnPropertyDescriptor(performance, 'memory');
                        Object.defineProperty(performance, 'memory', {{
                            get: function() {{
                                const base = originalMemory && originalMemory.get ? 
                                           originalMemory.get.call(this) : {{
                                    totalJSHeapSize: {random.randint(8000000, 15000000)},
                                    usedJSHeapSize: {random.randint(4000000, 9000000)},
                                    jsHeapSizeLimit: {random.randint(1900000000, 2200000000)}
                                }};
                                // Add 5-10% noise to memory values
                                const noise = 1 + (Math.random() * 0.10 - 0.05);
                                return {{
                                    totalJSHeapSize: Math.floor(base.totalJSHeapSize * noise),
                                    usedJSHeapSize: Math.floor(base.usedJSHeapSize * noise),
                                    jsHeapSizeLimit: base.jsHeapSizeLimit
                                }};
                            }},
                            configurable: true,
                            enumerable: true
                        }});
                    }}
                    
                    // Add slight noise to performance.now()
                    const originalNow = performance.now;
                    const timeOffset = (Math.random() * 2 - 1);  // ±1ms offset
                    performance.now = function() {{
                        return originalNow.call(this) + timeOffset + (Math.random() * 0.1 - 0.05);
                    }};
                    
                    // ============================================
                    // OCCASIONAL CLIPBOARD/ERROR SIMULATION  
                    // ============================================
                    
                    // Occasionally inject realistic errors (5% chance)
                    if (Math.random() < 0.05) {{
                        setTimeout(() => {{
                            console.warn('Third-party cookie blocked');
                            console.warn('Tracking protection may affect functionality');
                        }}, Math.random() * 1000 + 500);
                    }}
                    
                    // Simulate occasional clipboard access (3% chance)
                    if (Math.random() < 0.03) {{
                        setTimeout(() => {{
                            try {{
                                const selection = window.getSelection();
                                if (document.body.querySelector('p, h1, h2, span, div')) {{
                                    const el = document.body.querySelector('p, h1, h2, span, div');
                                    const range = document.createRange();
                                    if (el && el.childNodes[0]) {{
                                        range.selectNode(el.childNodes[0]);
                                        selection.removeAllRanges();
                                        selection.addRange(range);
                                        // Simulate copy
                                        document.execCommand('copy');
                                        selection.removeAllRanges();
                                    }}
                                }}
                            }} catch(e) {{}}
                        }}, Math.random() * 2000 + 1000);
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
                    // ============================================
                    // ADVANCED WEBDRIVER ARTIFACT REMOVAL
                    // ============================================
                    
                    // Remove all ChromeDriver/EdgeDriver-specific artifacts
                    delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
                    delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
                    delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
                    delete window.cdc_adoQpoasnfa76pfcZLmcfl_Object;
                    delete window.cdc_adoQpoasnfa76pfcZLmcfl_Proxy;
                    delete window.cdc_adoQpoasnfa76pfcZLmcfl_JSON;
                    
                    // Remove all variations using regex
                    Object.keys(window).forEach(key => {{
                        if (key.match(/^(cdc_|\\$cdc_|\\$wdc_|\\$chrome_|\\$edge_|__webdriver|__selenium|__fxdriver|__driver)/)) {{
                            try {{
                                delete window[key];
                            }} catch (e) {{}}
                        }}
                    }});
                    
                    // Remove document-level script caches
                    delete document.__webdriver_script_fn;
                    delete document.__selenium_unwrapped;
                    delete document.__webdriver_unwrapped;
                    delete document.__driver_evaluate;
                    delete document.__webdriver_evaluate;
                    delete document.__fxdriver_evaluate;
                    delete document.__driver_unwrapped;
                    delete document.__fxdriver_unwrapped;
                    delete document.__webdriver_script_func;
                    delete document.$cdc_asdjflasutopfhvcZLmcfl_;
                    delete document.$chrome_asyncScriptInfo;
                    
                    // Override Function.prototype.toString to hide proxy behavior
                    const originalToString = Function.prototype.toString;
                    const newToString = function() {{
                        if (this === navigator.webdriver || 
                            this === Navigator.prototype.webdriver) {{
                            return 'function webdriver() {{ [native code] }}';
                        }}
                        const str = originalToString.call(this);
                        return str;
                    }};
                    
                    Object.defineProperty(Function.prototype, 'toString', {{
                        value: newToString,
                        writable: true,
                        configurable: true,
                        enumerable: false
                    }});
                    
                    // Prevent new cdc_ properties from being added
                    ['cdc_adoQpoasnfa76pfcZLmcfl_Array', 'cdc_adoQpoasnfa76pfcZLmcfl_Promise', 'cdc_adoQpoasnfa76pfcZLmcfl_Symbol'].forEach(prop => {{
                        Object.defineProperty(window, prop, {{
                            get: () => undefined,
                            set: () => {{}},
                            configurable: false,
                            enumerable: false
                        }});
                    }});
                    
                    // ============================================
                    // NAVIGATOR PROPERTY OVERRIDES
                    // ============================================
                    
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
                    
                    // Mock Geolocation API (consistent with timezone)
                    if (navigator.geolocation) {{
                        const geoCoords = {str(get_coords_for_timezone(timezone_offset))};
                        const mockPosition = {{
                            coords: {{
                                latitude: geoCoords[0],
                                longitude: geoCoords[1],
                                accuracy: 10 + Math.random() * 50,
                                altitude: null,
                                altitudeAccuracy: null,
                                heading: null,
                                speed: null
                            }},
                            timestamp: Date.now()
                        }};
                        
                        navigator.geolocation.getCurrentPosition = function(success, error, options) {{
                            if (success) {{
                                setTimeout(() => success(mockPosition), 50 + Math.random() * 100);
                            }}
                        }};
                        
                        navigator.geolocation.watchPosition = function(success, error, options) {{
                            if (success) {{
                                setTimeout(() => success(mockPosition), 50 + Math.random() * 100);
                            }}
                            return Math.floor(Math.random() * 1000);
                        }};
                        
                        navigator.geolocation.clearWatch = function(id) {{}};
                    }}
                    
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
                    
                    // WebRTC IP randomization (enable but with random local IPs per session)
                    const randomLocalIPsEdge = {str(webrtc["localIPs"])};
                    const OriginalRTCPeerConnectionEdge = window.RTCPeerConnection || window.webkitRTCPeerConnection;
                    if (OriginalRTCPeerConnectionEdge) {{
                        window.RTCPeerConnection = function(...args) {{
                            const pc = new OriginalRTCPeerConnectionEdge(...args);
                            const originalCreateOffer = pc.createOffer;
                            const originalCreateAnswer = pc.createAnswer;
                            
                            // Inject random IPs into SDP
                            const injectRandomIPs = (sdp) => {{
                                if (sdp && sdp.sdp && randomLocalIPsEdge.length > 0) {{
                                    const randomIP = randomLocalIPsEdge[Math.floor(Math.random() * randomLocalIPsEdge.length)];
                                    // Replace candidate IPs with our random ones
                                    sdp.sdp = sdp.sdp.replace(/([0-9]{{1,3}}\\.){{3}}[0-9]{{1,3}}/g, randomIP);
                                }}
                                return sdp;
                            }};
                            
                            pc.createOffer = function(...args2) {{
                                return originalCreateOffer.apply(this, args2).then(injectRandomIPs);
                            }};
                            
                            pc.createAnswer = function(...args2) {{
                                return originalCreateAnswer.apply(this, args2).then(injectRandomIPs);
                            }};
                            
                            return pc;
                        }};
                        window.RTCPeerConnection.prototype = OriginalRTCPeerConnectionEdge.prototype;
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
            // ============================================
            // ADVANCED WEBDRIVER ARTIFACT REMOVAL
            // ============================================
            
            // Remove all Gecko/Firefox driver artifacts
            delete window.__webdriver_evaluate;
            delete window.__selenium_evaluate;
            delete window.__webdriver_script_func;
            delete window.__webdriver_script_fn;
            delete window.__fxdriver_evaluate;
            delete window.__driver_unwrapped;
            delete window.__webdriver_unwrapped;
            delete window.__fxdriver_unwrapped;
            
            // Remove document-level script caches
            delete document.__webdriver_script_fn;
            delete document.__selenium_unwrapped;
            delete document.__webdriver_unwrapped;
            delete document.__driver_evaluate;
            delete document.__webdriver_evaluate;
            delete document.__fxdriver_evaluate;
            delete document.__driver_unwrapped;
            delete document.__fxdriver_unwrapped;
            delete document.__webdriver_script_func;
            
            // Remove all variations using regex
            Object.keys(window).forEach(key => {{
                if (key.match(/^(__webdriver|__selenium|__fxdriver|__driver|__gecko)/)) {{
                    try {{
                        delete window[key];
                    }} catch (e) {{}}
                }}
            }});
            
            // Override Function.prototype.toString to hide proxy behavior
            const originalToString = Function.prototype.toString;
            const newToString = function() {{
                if (this === navigator.webdriver || 
                    this === Navigator.prototype.webdriver) {{
                    return 'function webdriver() {{ [native code] }}';
                }}
                const str = originalToString.call(this);
                return str;
            }};
            
            Object.defineProperty(Function.prototype, 'toString', {{
                value: newToString,
                writable: true,
                configurable: true,
                enumerable: false
            }});
            
            // ============================================
            // NAVIGATOR PROPERTY OVERRIDES
            // ============================================
            
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
            
            // WebRTC IP randomization (enable but with random local IPs per session)
            const randomLocalIPsFF = {str(webrtc["localIPs"])};
            const OriginalRTCPeerConnectionFF = window.RTCPeerConnection || window.webkitRTCPeerConnection || window.mozRTCPeerConnection;
            if (OriginalRTCPeerConnectionFF) {{
                window.RTCPeerConnection = function(...args) {{
                    const pc = new OriginalRTCPeerConnectionFF(...args);
                    const originalCreateOffer = pc.createOffer;
                    const originalCreateAnswer = pc.createAnswer;
                    
                    // Inject random IPs into SDP
                    const injectRandomIPs = (sdp) => {{
                        if (sdp && sdp.sdp && randomLocalIPsFF.length > 0) {{
                            const randomIP = randomLocalIPsFF[Math.floor(Math.random() * randomLocalIPsFF.length)];
                            // Replace candidate IPs with our random ones
                            sdp.sdp = sdp.sdp.replace(/([0-9]{{1,3}}\\.){{3}}[0-9]{{1,3}}/g, randomIP);
                        }}
                        return sdp;
                    }};
                    
                    pc.createOffer = function(...args2) {{
                        return originalCreateOffer.apply(this, args2).then(injectRandomIPs);
                    }};
                    
                    pc.createAnswer = function(...args2) {{
                        return originalCreateAnswer.apply(this, args2).then(injectRandomIPs);
                    }};
                    
                    return pc;
                }};
                window.RTCPeerConnection.prototype = OriginalRTCPeerConnectionFF.prototype;
                if (window.mozRTCPeerConnection) {{
                    window.mozRTCPeerConnection = window.RTCPeerConnection;
                }}
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
        error_msg = str(e)
        print(f'  [{browser_type}] ⚠ Tab management error: {error_msg[:50]}')
        
        # Check if session is lost - re-raise to trigger session recreation in main loop
        if 'Cannot find session' in error_msg or 'invalid session id' in error_msg.lower():
            print(f'  [{browser_type}] 💥 Session lost in tab management - propagating error...')
            raise  # Re-raise to be caught by main loop's WebDriverException handler
        
        # Try to recover from other errors
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

def detect_and_bypass_bot_challenge(driver, browser_type, max_attempts=3):
    """
    Detect and attempt to bypass bot detection challenges (Cloudflare, etc.)
    
    Args:
        driver: WebDriver instance
        browser_type: Browser name for logging
        max_attempts: Maximum number of challenge attempts (default 3)
    
    Returns:
        bool: True if challenge was bypassed or not present, False if failed
    """
    try:
        for attempt in range(max_attempts):
            time.sleep(random.uniform(1.5, 3.0))  # Wait for page to load
            
            # Get page source and title to detect challenges
            try:
                page_title = driver.title.lower()
                page_source = driver.page_source.lower()
            except:
                return True  # If we can't get page info, assume we're good
            
            # Detection patterns for various bot challenges
            challenge_indicators = [
                'cloudflare' in page_source,
                'just a moment' in page_title or 'just a moment' in page_source,
                'checking your browser' in page_source,
                'verify you are human' in page_source or 'vérifiez que vous êtes' in page_source,
                'confirmez que vous êtes un humain' in page_source,
                'challenge-form' in page_source,
                'cf-challenge' in page_source,
                'ray id' in page_source and 'cloudflare' in page_source,
                'ddos-guard' in page_source,
                'sucuri' in page_source and 'security check' in page_source,
                'perimeterx' in page_source or 'px-captcha' in page_source,
                'datadome' in page_source,
                'are you a robot' in page_source,
                'human verification' in page_source,
            ]
            
            if not any(challenge_indicators):
                # No challenge detected
                if attempt == 0:
                    return True  # Clean page load
                else:
                    print(f'  [{browser_type}] ✅ Bot challenge passed! (attempt {attempt + 1})')
                    return True
            
            print(f'  [{browser_type}] 🤖 Bot challenge detected (attempt {attempt + 1}/{max_attempts})...')
            
            # Check for CAPTCHA (if present, we skip)
            captcha_indicators = [
                'captcha' in page_source,
                'recaptcha' in page_source,
                'hcaptcha' in page_source,
                'g-recaptcha' in page_source,
                'h-captcha' in page_source,
            ]
            
            if any(captcha_indicators):
                print(f'  [{browser_type}] 🧩 CAPTCHA detected - skipping (as requested)')
                return False
            
            # Look for challenge buttons/checkboxes to click
            # Try multiple selectors for different challenge types
            challenge_selectors = [
                # Cloudflare
                'input[type="checkbox"]',
                'input#challenge-form',
                '.cf-turnstile',
                'iframe[src*="challenges.cloudflare.com"]',
                'input[name="cf_captcha_kind"]',
                # Generic challenge buttons
                'button[type="submit"]',
                'input[type="submit"]',
                'button:contains("Verify")',
                'button:contains("Continue")',
                'button:contains("I\'m not a robot")',
                'button:contains("Je ne suis pas un robot")',
                # Checkboxes
                'input[type="checkbox"][name*="human"]',
                'input[type="checkbox"][id*="verify"]',
                'input[type="checkbox"][id*="challenge"]',
            ]
            
            clicked_something = False
            
            # First try to find and click checkboxes
            try:
                checkboxes = driver.find_elements(By.CSS_SELECTOR, 'input[type="checkbox"]')
                for checkbox in checkboxes:
                    try:
                        if checkbox.is_displayed() and checkbox.is_enabled():
                            # Human-like delay before clicking
                            time.sleep(random.uniform(0.8, 1.5))
                            
                            # Move mouse to checkbox realistically
                            try:
                                actions = ActionChains(driver)
                                actions.move_to_element(checkbox)
                                actions.pause(random.uniform(0.2, 0.5))
                                actions.click()
                                actions.perform()
                            except:
                                # Fallback to direct click
                                checkbox.click()
                            
                            print(f'  [{browser_type}] ✓ Clicked challenge checkbox')
                            clicked_something = True
                            time.sleep(random.uniform(1.5, 3.0))  # Wait for processing
                            break
                    except:
                        continue
            except:
                pass
            
            # Try clicking buttons if checkbox didn't work
            if not clicked_something:
                try:
                    buttons = driver.find_elements(By.TAG_NAME, 'button')
                    buttons.extend(driver.find_elements(By.CSS_SELECTOR, 'input[type="submit"]'))
                    
                    for button in buttons:
                        try:
                            if button.is_displayed() and button.is_enabled():
                                button_text = button.text.lower() if button.text else ''
                                button_value = button.get_attribute('value')
                                if button_value:
                                    button_text += ' ' + button_value.lower()
                                
                                # Look for verify/continue buttons
                                if any(word in button_text for word in ['verify', 'continue', 'submit', 'proceed', 'confirm', 'vérifier', 'continuer']):
                                    time.sleep(random.uniform(0.8, 1.5))
                                    
                                    try:
                                        actions = ActionChains(driver)
                                        actions.move_to_element(button)
                                        actions.pause(random.uniform(0.2, 0.5))
                                        actions.click()
                                        actions.perform()
                                    except:
                                        button.click()
                                    
                                    print(f'  [{browser_type}] ✓ Clicked challenge button: "{button_text[:30]}"')
                                    clicked_something = True
                                    time.sleep(random.uniform(1.5, 3.0))
                                    break
                        except:
                            continue
                except:
                    pass
            
            # Try iframe-based challenges (like Cloudflare Turnstile)
            if not clicked_something:
                try:
                    iframes = driver.find_elements(By.TAG_NAME, 'iframe')
                    for iframe in iframes:
                        try:
                            src = iframe.get_attribute('src')
                            if src and ('challenge' in src.lower() or 'turnstile' in src.lower() or 'cloudflare' in src.lower()):
                                print(f'  [{browser_type}] 🔄 Found challenge iframe, switching to it...')
                                driver.switch_to.frame(iframe)
                                time.sleep(random.uniform(0.5, 1.0))
                                
                                # Look for checkbox inside iframe
                                try:
                                    iframe_checkbox = driver.find_element(By.CSS_SELECTOR, 'input[type="checkbox"]')
                                    if iframe_checkbox.is_displayed():
                                        time.sleep(random.uniform(0.8, 1.5))
                                        
                                        try:
                                            actions = ActionChains(driver)
                                            actions.move_to_element(iframe_checkbox)
                                            actions.pause(random.uniform(0.2, 0.5))
                                            actions.click()
                                            actions.perform()
                                        except:
                                            iframe_checkbox.click()
                                        
                                        print(f'  [{browser_type}] ✓ Clicked checkbox in iframe')
                                        clicked_something = True
                                        time.sleep(random.uniform(1.5, 3.0))
                                except:
                                    pass
                                
                                # Switch back to main content
                                driver.switch_to.default_content()
                                
                                if clicked_something:
                                    break
                        except:
                            try:
                                driver.switch_to.default_content()
                            except:
                                pass
                            continue
                except:
                    try:
                        driver.switch_to.default_content()
                    except:
                        pass
            
            # If we didn't find anything to click, the challenge might be automatic
            if not clicked_something:
                print(f'  [{browser_type}] ⏳ Waiting for automatic challenge resolution...')
                time.sleep(random.uniform(3.0, 5.0))
            
            # Check if we're still on a challenge page
            # If yes, loop will continue to next attempt
            
        # After all attempts, check one more time if we passed
        try:
            time.sleep(random.uniform(1.0, 2.0))
            page_source = driver.page_source.lower()
            final_check = not any([
                'cloudflare' in page_source and 'checking' in page_source,
                'verify you are human' in page_source,
                'confirmez que vous êtes un humain' in page_source,
            ])
            
            if final_check:
                print(f'  [{browser_type}] ✅ Bot challenge passed!')
                return True
            else:
                print(f'  [{browser_type}] ❌ Failed to bypass bot challenge after {max_attempts} attempts')
                return False
        except:
            return False
            
    except Exception as e:
        print(f'  [{browser_type}] ⚠ Error in bot challenge bypass: {str(e)[:60]}')
        return True  # Assume we're okay if error occurred

def browse():
    """Main browsing function - creates chaos by clicking through random links"""
    # Initialize global fatigue model for this session
    global fatigue_model
    fatigue_model = SessionFatigueModel()
    
    browser_type = random.choice(browsers)
    print(f'\n{"="*60}')
    print(f'Starting {browser_type} browser')
    print(f'{"="*60}')
    print(f'⏰ Current time: {datetime.now().strftime("%H:%M")} (circadian factor: {get_time_of_day_multiplier()}x)')
    
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
                time.sleep(realistic_delay(2.0, variance=0.4))
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
            
            # Detect and bypass bot challenges (Cloudflare, etc.)
            challenge_passed = detect_and_bypass_bot_challenge(driver, browser_type, max_attempts=3)
            if not challenge_passed:
                print(f'  [{browser_type}] ⚠ Could not bypass bot challenge, skipping to next website')
                continue  # Skip to next website
            
            # Random human-like delay with fidgeting
            reading_behavior(driver, duration=random.uniform(2, 4))
            
            # Auto-accept cookies
            auto_accept_cookies(driver, browser_type)
            
            # Inject realistic console errors (10% chance)
            inject_realistic_errors(driver)
            
            # Play YouTube videos if detected
            play_youtube_video(driver, browser_type)
            
            # Simulate copy/paste behavior (5% chance)
            simulate_copy_paste(driver)
            
            # Simulate right-click behavior (5% chance)
            simulate_right_click(driver, browser_type)
            
            # Simulate keyboard shortcuts (5% chance)
            # simulate_keyboard_shortcuts(driver, browser_type)  # TEMPORARILY DISABLED - causing timeouts
            
            # Try typing in forms with proper data (10% chance)
            # simulate_typing_and_forms(driver, browser_type)  # TEMPORARILY DISABLED - causing timeouts
            
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
                    
                    # Check for bot challenges on the new ad tab
                    challenge_passed = detect_and_bypass_bot_challenge(driver, browser_type, max_attempts=3)
                    if not challenge_passed:
                        print(f'  [{browser_type}] ⚠ Ad tab has bot challenge, closing it')
                        try:
                            driver.close()
                            # Switch back to original browsing tab
                            if current_browsing_tab in driver.window_handles:
                                driver.switch_to.window(current_browsing_tab)
                            elif driver.window_handles:
                                current_browsing_tab = driver.window_handles[0]
                                driver.switch_to.window(current_browsing_tab)
                        except:
                            pass
                    
                    time.sleep(realistic_delay(1.5, variance=0.3))
            
            # Simulate human reading/scrolling behavior on first page with realistic mouse movement
            for _ in range(random.randint(1, 2)):
                scroll_amount = random.randint(200, 500)
                smooth_scroll(driver, scroll_amount, duration=random.uniform(0.4, 0.9))
                
                # Fidget mouse while "reading"
                if random.random() < 0.6:  # 60% chance to fidget
                    fidget_mouse(driver, duration=random.uniform(0.5, 1.5))
                
                time.sleep(realistic_delay(1.4, variance=0.4))
            
            time.sleep(realistic_delay(2.0, variance=0.4))
            
            # Navigate through links on this website
            max_depth = random.randint(3, 8)  # Reduced depth per site to visit more sites
            current_depth = 0
            
            while current_depth < max_depth:
                try:
                    # Manage tabs at each iteration (might switch tabs randomly)
                    current_browsing_tab, tab_switched = manage_tabs(driver, browser_type, current_browsing_tab, max_tabs)
                    
                    if tab_switched:
                        # We switched to a different tab, continue browsing it
                        time.sleep(realistic_delay(1.5, variance=0.3))
                    
                    current_url = driver.current_url
                    current_domain = get_domain(current_url)
                    
                    # Scroll the page with more human-like behavior using smooth scrolling
                    scroll_count = random.randint(1, 3)
                    for i in range(scroll_count):
                        # Variable scroll amounts
                        scroll_position = random.randint(100, 1000)
                        smooth_scroll(driver, scroll_position, duration=random.uniform(0.3, 0.8))
                        
                        # Fidget mouse while scrolling (50% chance)
                        if random.random() < 0.5:
                            fidget_mouse(driver, duration=random.uniform(0.5, 1.2), movements=random.randint(2, 4))
                        
                        # Human-like pauses (sometimes longer, sometimes shorter)
                        if random.random() < 0.3:  # 30% chance of longer pause
                            time.sleep(realistic_delay(3.0, variance=0.4))
                        else:
                            time.sleep(realistic_delay(1.0, variance=0.4))
                        
                        # Occasionally scroll back up a bit
                        if random.random() < 0.2:  # 20% chance
                            smooth_scroll(driver, -random.randint(50, 200), duration=random.uniform(0.2, 0.5))
                            time.sleep(realistic_delay(0.5, variance=0.3))
                    
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
                            
                            # Try human-like hover and click (80% chance)
                            click_success = False
                            
                            if random.random() < 0.8:
                                # Use hover_before_click for realistic behavior
                                try:
                                    click_success = hover_before_click(driver, chosen_link, hover_time=random.uniform(0.3, 0.9))
                                    if click_success:
                                        print(f'  [{browser_type}] ✓ Used hover-and-click')
                                except Exception as e:
                                    print(f'  [{browser_type}] Hover-click failed: {str(e)[:40]}')
                            
                            # Fallback methods if hover-click didn't work or wasn't attempted
                            if not click_success:
                                # Human-like delay before clicking (with fatigue)
                                time.sleep(realistic_delay(1.0, variance=0.4))
                                
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
                                            except Exception as e2:
                                                print(f'  [{browser_type}] ✗ All click methods failed: {str(e2)[:40]}')
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
                            
                            # Variable delay after click (humans don't click instantly, includes fatigue)
                            time.sleep(realistic_delay(3.5, variance=0.4))
                            
                            # Check if link opened new tabs
                            if len(driver.window_handles) > len(driver.window_handles):
                                current_browsing_tab, switched_to_new = handle_new_tab_from_ad(driver, browser_type, current_browsing_tab)
                            
                            # Try to accept cookies on new page (but don't wait too long)
                            try:
                                auto_accept_cookies(driver, browser_type)
                            except:
                                pass
                            
                            # Play YouTube videos if detected
                            try:
                                play_youtube_video(driver, browser_type)
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
            time.sleep(realistic_delay(2.0, variance=0.4))
            
        except TimeoutException:
            print(f'[{browser_type}] ⏱ Timeout, moving to next website')
            websites_visited += 1
        except WebDriverException as e:
            error_msg = str(e)
            print(f'[{browser_type}] ⚠ WebDriver error: {error_msg[:80]}')
            
            # Check if session is lost - needs recreation
            if 'Cannot find session' in error_msg or 'invalid session id' in error_msg.lower():
                print(f'[{browser_type}] 🔄 Session lost! Creating new session...')
                try:
                    driver.quit()
                except:
                    pass
                
                # Create new driver and reset state
                try:
                    driver = create_driver(browser_type)
                    current_browsing_tab = driver.current_window_handle
                    max_tabs = random.randint(5, 10)
                    print(f'[{browser_type}] ✅ New session created successfully')
                    print(f'[{browser_type}] 📍 New tab: {current_browsing_tab[:8]}... (max {max_tabs} tabs)')
                except Exception as create_error:
                    print(f'[{browser_type}] ❌ Failed to create new session: {str(create_error)[:80]}')
                    print(f'[{browser_type}] Exiting to restart container...')
                    break
            else:
                # Other WebDriver errors - try to continue
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
