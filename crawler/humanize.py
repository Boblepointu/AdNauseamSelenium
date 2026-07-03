"""Human-like behavior simulation helpers (split from crawl.py)."""
import time
import random
import logging
import numpy as np
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import MoveTargetOutOfBoundsException

from crawler import config

logger = logging.getLogger('crawler.humanize')


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
        except Exception:
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
            except Exception:
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
        except Exception:
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
        
        return min(time_fatigue * action_fatigue, 2.0)


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
        return 1.3


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
    if apply_fatigue and config.fatigue_model is not None:
        fatigue = config.fatigue_model.get_fatigue_multiplier()
        delay *= fatigue
    
    return delay


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
        except Exception:
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
        except Exception:
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
                except Exception:
                    continue
            
            if not visible_elements:
                return
            
            element = random.choice(visible_elements)
            
            # Right-click with ActionChains (with explicit error handling)
            try:
                actions = ActionChains(driver)
                actions.context_click(element).perform()
                
                logger.info(f'  [{browser_type}] 🖱️  Right-clicked element')
                
                # Wait briefly (user reading context menu)
                time.sleep(random.uniform(0.3, 0.8))
                
                # Close context menu with Escape
                try:
                    actions = ActionChains(driver)
                    actions.send_keys(Keys.ESCAPE).perform()
                except Exception:
                    # If escape fails, just continue
                    pass
                
                time.sleep(random.uniform(0.1, 0.3))
            except Exception as e:
                # Element became stale or context menu didn't work - just continue
                pass
        except Exception:
            pass
        finally:
            # Restore normal timeout
            try:
                driver.set_page_load_timeout(30)
            except Exception:
                pass
