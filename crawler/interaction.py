"""Page interaction: cookies, ads, tab management, bot challenges (split from crawl.py)."""
import time
import random
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import WebDriverException

from crawler import config
from crawler.driver import is_driver_alive

logger = logging.getLogger('crawler.interaction')


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
        
        logger.info(f'  [{browser_type}] 🎥 Detected YouTube page, attempting to play video...')
        
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
                            logger.info(f'  [{browser_type}] ▶️  Clicked play button!')
                            video_played = True
                            time.sleep(random.uniform(0.5, 1))
                            break
                        except Exception:
                            continue
                if video_played:
                    break
            except Exception:
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
                logger.info(f'  [{browser_type}] ▶️  Started video via JavaScript!')
                video_played = True
            except Exception:
                pass
        
        if video_played:
            # Let video play for a realistic amount of time (5-30 seconds)
            watch_time = random.uniform(5, 30)
            logger.info(f'  [{browser_type}] 📺 Watching video for {watch_time:.1f}s...')
            time.sleep(watch_time)
            
            # Occasionally scroll down to comments (30% chance)
            if random.random() < 0.3:
                try:
                    scroll_amount = random.randint(500, 1500)
                    driver.execute_script(f'window.scrollBy(0, {scroll_amount});')
                    logger.info(f'  [{browser_type}] 💬 Scrolled to comments section')
                    time.sleep(random.uniform(1, 3))
                except Exception:
                    pass
            
            # Occasionally interact with video controls (pause, seek, volume)
            if random.random() < 0.2:  # 20% chance
                try:
                    # Click pause button
                    pause_button = driver.find_element(By.CSS_SELECTOR, 'button.ytp-play-button')
                    if pause_button.is_displayed():
                        pause_button.click()
                        logger.info(f'  [{browser_type}] ⏸️  Paused video')
                        time.sleep(random.uniform(1, 3))
                        # Play again
                        pause_button.click()
                        logger.info(f'  [{browser_type}] ▶️  Resumed video')
                        time.sleep(random.uniform(2, 5))
                except Exception:
                    pass
            
            return True
        else:
            logger.warning(f'  [{browser_type}] ⚠️  Could not find play button')
            return False
            
    except Exception as e:
        logger.warning(f'  [{browser_type}] ⚠️  YouTube play error: {str(e)[:50]}')
        return False


def auto_accept_cookies(driver, browser_type, max_attempts=3):
    """Automatically detect and click cookie consent buttons - with retries and multi-step handling"""
    
    for attempt in range(max_attempts):
        try:
            if attempt > 0:
                logger.info(f'  [{browser_type}] 🍪 Cookie consent attempt {attempt + 1}/{max_attempts}')
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
                        except Exception:
                            continue
                except Exception:
                    continue
            
            if individual_agreed:
                logger.info(f'  [{browser_type}] 🍪 Clicked individual agree buttons')
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
                                    logger.info(f'  [{browser_type}] 🍪 Accepted Google/YouTube consent (XPath)')
                                    time.sleep(1)
                                    return True
                            except Exception:
                                continue
                    except Exception:
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
                                        logger.info(f'  [{browser_type}] 🍪 Accepted Google/YouTube consent (CSS)')
                                        time.sleep(1)
                                        return True
                            except Exception:
                                continue
                    except Exception:
                        continue
            except Exception:
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
                                    except Exception:
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
                                            except Exception:
                                                # If direct click fails, try clicking parent label
                                                try:
                                                    parent = toggle.find_element(By.XPATH, './ancestor::label[1]')
                                                    parent.click()
                                                    toggled_count += 1
                                                    time.sleep(random.uniform(0.2, 0.4))
                                                except Exception:
                                                    pass
                            except Exception:
                                continue
                    except Exception:
                        continue
                
                if toggled_count > 0:
                    logger.info(f'  [{browser_type}] 🍪 Toggled {toggled_count} cookie category switch(es)')
                    time.sleep(random.uniform(0.3, 0.6))
            except Exception:
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
                            logger.info(f'  [{browser_type}] 🍪 Accepted cookies via selector: {selector}')
                            time.sleep(0.5)
                            return True
                except Exception:
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
                                logger.info(f'  [{browser_type}] 🍪 Accepted cookies via text: "{button.text[:40]}"')
                                time.sleep(0.5)
                                return True
                    except Exception:
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
                            logger.info(f'  [{browser_type}] 🍪 Accepted cookies via exact match: "{button.text[:40]}"')
                            time.sleep(0.5)
                            return True
                        
                        # Check if button text matches any accept pattern
                        for pattern in accept_text_patterns:
                            if pattern in button_text or button_text == pattern.replace(' ', ''):
                                button.click()
                                logger.info(f'  [{browser_type}] 🍪 Accepted cookies via text: "{button.text[:40]}"')
                                time.sleep(0.5)
                                return True
                    except Exception:
                        continue
            except Exception:
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
                                        logger.info(f'  [{browser_type}] 🍪 Accepted cookies in iframe')
                                        time.sleep(0.5)
                                        return True
                                except Exception:
                                    continue
                            
                            driver.switch_to.default_content()
                    except Exception:
                        driver.switch_to.default_content()
                        continue
            except Exception:
                pass
            
            # If we got here, no cookie banner was found or clicked
            if attempt == 0:
                # Only break if first attempt found nothing
                break
            
        except Exception as e:
            # Don't let cookie handling break the automation
            try:
                driver.switch_to.default_content()
            except Exception:
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
                    except Exception:
                        continue
            except Exception:
                continue
        
        if not ads_found:
            return False
        
        logger.info(f'  [{browser_type}] 📢 Detected {len(ads_found)} ad(s) on page')
        config.STATS['pages_with_ads'] += 1

        # Decide whether to click (60% chance)
        if random.random() > click_chance:
            logger.info(f'  [{browser_type}] 🎲 Decided not to click ads this time')
            return False
        
        # Try to click a random ad
        ad_to_click = random.choice(ads_found)
        
        try:
            # Scroll ad into view
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", ad_to_click)
            time.sleep(random.uniform(0.5, 1.0))
            
            # Try to click the ad
            ad_to_click.click()
            config.STATS['ads_clicked'] += 1
            logger.info(f'  [{browser_type}] 💰 Clicked on ad!')
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
                        logger.info(f'  [{browser_type}] 💰 Clicked ad link in iframe!')
                        time.sleep(random.uniform(1, 3))
                        return True
                    driver.switch_to.default_content()
            except Exception:
                try:
                    driver.switch_to.default_content()
                except Exception:
                    pass
                try:
                    # Make sure we're back on the initial window
                    if initial_window in driver.window_handles:
                        driver.switch_to.window(initial_window)
                    elif driver.window_handles:
                        driver.switch_to.window(driver.window_handles[0])
                except Exception:
                    pass
            
            return False
            
    except Exception as e:
        # Don't let ad clicking break the automation
        # Try to ensure we're on a valid window
        try:
            if driver.window_handles:
                driver.switch_to.window(driver.window_handles[0])
        except Exception:
            pass
        return False


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
        # First check if driver is alive
        if not is_driver_alive(driver):
            raise WebDriverException("Driver connection lost")
        
        all_handles = driver.window_handles
        
        # If only one tab, nothing to do
        if len(all_handles) <= 1:
            return current_browsing_tab, False
        
        # If we have too many tabs, close some randomly
        if len(all_handles) > max_tabs:
            num_to_close = len(all_handles) - max_tabs
            logger.info(f'  [{browser_type}] 🗂️ Too many tabs ({len(all_handles)}), closing {num_to_close}...')
            
            # Never close the current browsing tab
            closeable_handles = [h for h in all_handles if h != current_browsing_tab]
            
            # Randomly select tabs to close
            tabs_to_close = random.sample(closeable_handles, min(num_to_close, len(closeable_handles)))
            
            for handle in tabs_to_close:
                try:
                    driver.switch_to.window(handle)
                    driver.close()
                except Exception:
                    pass
            
            # Switch back to current browsing tab
            try:
                driver.switch_to.window(current_browsing_tab)
            except Exception:
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
                logger.info(f'  [{browser_type}] 🔄 Switched to different tab ({len(all_handles)} tabs open)')
                return new_tab, True
        
        # Make sure we're on the current browsing tab
        if driver.current_window_handle != current_browsing_tab:
            try:
                driver.switch_to.window(current_browsing_tab)
            except Exception:
                # Tab no longer exists, use first available
                if driver.window_handles:
                    current_browsing_tab = driver.window_handles[0]
                    driver.switch_to.window(current_browsing_tab)
        
        return current_browsing_tab, False
        
    except Exception as e:
        error_msg = str(e)
        logger.warning(f'  [{browser_type}] ⚠ Tab management error: {error_msg[:100]}')
        
        # Check if session is lost - re-raise to trigger session recreation in main loop
        if not is_driver_alive(driver):
            logger.warning(f'  [{browser_type}] 💥 Session lost in tab management - propagating error...')
            raise WebDriverException("Driver connection lost")  # Re-raise with clear message
        
        # Try to recover from other errors
        try:
            if driver.window_handles:
                if current_browsing_tab in driver.window_handles:
                    driver.switch_to.window(current_browsing_tab)
                else:
                    current_browsing_tab = driver.window_handles[0]
                    driver.switch_to.window(current_browsing_tab)
        except Exception:
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
            logger.info(f'  [{browser_type}] 🆕 Switched to browse ad tab! ({len(all_handles)} tabs open)')
            return new_tab, True
        else:
            # Stay on current tab, but keep the new tabs open (will be managed later)
            driver.switch_to.window(current_browsing_tab)
            logger.info(f'  [{browser_type}] 📌 Keeping current tab, {len(new_tabs)} new tab(s) in background')
            return current_browsing_tab, False
            
    except Exception as e:
        # On error, return to current tab
        try:
            if current_browsing_tab in driver.window_handles:
                driver.switch_to.window(current_browsing_tab)
            elif driver.window_handles:
                current_browsing_tab = driver.window_handles[0]
                driver.switch_to.window(current_browsing_tab)
        except Exception:
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
            except Exception:
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
                    logger.info(f'  [{browser_type}] ✅ Bot challenge passed! (attempt {attempt + 1})')
                    return True
            
            logger.info(f'  [{browser_type}] 🤖 Bot challenge detected (attempt {attempt + 1}/{max_attempts})...')
            
            # Check for CAPTCHA (if present, we skip)
            captcha_indicators = [
                'captcha' in page_source,
                'recaptcha' in page_source,
                'hcaptcha' in page_source,
                'g-recaptcha' in page_source,
                'h-captcha' in page_source,
            ]
            
            if any(captcha_indicators):
                logger.info(f'  [{browser_type}] 🧩 CAPTCHA detected - skipping (as requested)')
                return False
            
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
                            except Exception:
                                # Fallback to direct click
                                checkbox.click()
                            
                            logger.info(f'  [{browser_type}] ✓ Clicked challenge checkbox')
                            clicked_something = True
                            time.sleep(random.uniform(1.5, 3.0))  # Wait for processing
                            break
                    except Exception:
                        continue
            except Exception:
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
                                    except Exception:
                                        button.click()
                                    
                                    logger.info(f'  [{browser_type}] ✓ Clicked challenge button: "{button_text[:30]}"')
                                    clicked_something = True
                                    time.sleep(random.uniform(1.5, 3.0))
                                    break
                        except Exception:
                            continue
                except Exception:
                    pass
            
            # Try iframe-based challenges (like Cloudflare Turnstile)
            if not clicked_something:
                try:
                    iframes = driver.find_elements(By.TAG_NAME, 'iframe')
                    for iframe in iframes:
                        try:
                            src = iframe.get_attribute('src')
                            if src and ('challenge' in src.lower() or 'turnstile' in src.lower() or 'cloudflare' in src.lower()):
                                logger.info(f'  [{browser_type}] 🔄 Found challenge iframe, switching to it...')
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
                                        except Exception:
                                            iframe_checkbox.click()
                                        
                                        logger.info(f'  [{browser_type}] ✓ Clicked checkbox in iframe')
                                        clicked_something = True
                                        time.sleep(random.uniform(1.5, 3.0))
                                except Exception:
                                    pass
                                
                                # Switch back to main content
                                driver.switch_to.default_content()
                                
                                if clicked_something:
                                    break
                        except Exception:
                            try:
                                driver.switch_to.default_content()
                            except Exception:
                                pass
                            continue
                except Exception:
                    try:
                        driver.switch_to.default_content()
                    except Exception:
                        pass
            
            # If we didn't find anything to click, the challenge might be automatic
            if not clicked_something:
                logger.info(f'  [{browser_type}] ⏳ Waiting for automatic challenge resolution...')
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
                logger.info(f'  [{browser_type}] ✅ Bot challenge passed!')
                return True
            else:
                logger.warning(f'  [{browser_type}] ❌ Failed to bypass bot challenge after {max_attempts} attempts')
                return False
        except Exception:
            return False
            
    except Exception as e:
        logger.warning(f'  [{browser_type}] ⚠ Error in bot challenge bypass: {str(e)[:60]}')
        return True
