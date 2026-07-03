"""WebDriver creation and stealth injection (split from crawl.py)."""
import os
import time
import random
import logging
from selenium import webdriver
from selenium.webdriver.remote.remote_connection import RemoteConnection

from crawler import config
from crawler.config import PERSONA_ROTATION_STRATEGY
from crawler.fingerprint import (
    generate_random_user_agent, generate_random_language, generate_random_screen,
    generate_random_gpu, generate_random_hardware, generate_random_connection,
    get_timezone_for_language, generate_random_battery, generate_random_media_devices,
    generate_random_fonts, generate_random_plugins, generate_random_webrtc,
    derive_platform_from_ua,
)

logger = logging.getLogger('crawler.driver')


def create_driver(browser_type, max_retries=3):
    """Create a Selenium WebDriver for automated browsing with anti-detection
    
    Args:
        browser_type: The browser to create (chrome, firefox, etc.)
        max_retries: Maximum number of retry attempts for session creation
        
    Returns:
        WebDriver instance
        
    Raises:
        Exception: If unable to create driver after max_retries attempts
    """
    
    # ============================================
    # PERSONA ROTATION
    # ============================================
    # When a persona manager is available and rotation is enabled, try to reuse a
    # previously-stored fingerprint so we look like a returning visitor across
    # sessions instead of a brand-new device every time. Fall back to a fresh
    # fingerprint whenever no suitable persona exists.
    _REQUIRED_FP_KEYS = ('user_agent', 'accept_language', 'screen', 'gpu', 'hardware',
                         'connection', 'timezone_offset', 'battery', 'media_devices',
                         'fonts', 'webrtc', 'plugins')

    def _persona_family_matches(persona_bt):
        # Chrome and Chromium share the same engine/UA family; treat as compatible.
        chromium = {'chrome', 'chromium'}
        if persona_bt in chromium and browser_type in chromium:
            return True
        return persona_bt == browser_type

    reused_persona = None
    if config.persona_manager and PERSONA_ROTATION_STRATEGY != 'new':
        try:
            candidate = config.persona_manager.get_persona_for_rotation(PERSONA_ROTATION_STRATEGY)
            if candidate and isinstance(candidate.get('fingerprint'), dict):
                fp = candidate['fingerprint']
                if (all(k in fp for k in _REQUIRED_FP_KEYS)
                        and _persona_family_matches(fp.get('browser_type'))):
                    reused_persona = candidate
        except Exception as e:
            logger.warning(f'[{browser_type}] ⚠️  Persona rotation lookup failed: {str(e)[:60]}')

    if reused_persona:
        fp = reused_persona['fingerprint']
        user_agent = fp['user_agent']
        accept_language = fp['accept_language']
        screen = fp['screen']
        gpu = fp['gpu']
        hardware = fp['hardware']
        connection = fp['connection']
        timezone_offset = fp['timezone_offset']
        battery = fp['battery']
        media_devices = fp['media_devices']
        fonts = fp['fonts']
        webrtc = fp['webrtc']
        plugins_js = fp['plugins']
        try:
            config.persona_manager.update_persona_usage(reused_persona['id'])
            logger.info(f'[{browser_type}] ♻️  Reusing persona {reused_persona["id"]} '
                  f'(strategy: {PERSONA_ROTATION_STRATEGY})')
        except Exception as e:
            logger.warning(f'[{browser_type}] ⚠️  Failed to update persona usage: {str(e)[:60]}')
    else:
        # Generate a fresh fingerprint (UA coherent with the real browser family).
        user_agent = generate_random_user_agent(browser_type)
        accept_language = generate_random_language()
        screen = generate_random_screen()
        gpu = generate_random_gpu()
        hardware = generate_random_hardware()
        connection = generate_random_connection()
        timezone_offset = get_timezone_for_language(accept_language)
        battery = generate_random_battery()
        media_devices = generate_random_media_devices()
        fonts = generate_random_fonts()
        plugins_js = generate_random_plugins(browser_type)
        webrtc = generate_random_webrtc()

        # Save the fresh persona to disk for rotation across future sessions.
        if config.persona_manager:
            try:
                fingerprint_data = config.fingerprint_to_dict(
                    browser_type, user_agent, accept_language, screen, gpu, hardware,
                    connection, timezone_offset, battery, media_devices, fonts, webrtc, plugins_js
                )
                persona_id = config.persona_manager.create_persona(fingerprint_data)
                logger.info(f'[{browser_type}] 💾 Saved persona: {persona_id}')
            except Exception as e:
                logger.warning(f'[{browser_type}] ⚠️  Failed to save persona: {str(e)[:50]}')

    logger.info(f'[{browser_type}] Generated UA: {user_agent[:80]}...')
    logger.info(f'[{browser_type}] Language: {accept_language.split(",")[0]}')
    logger.info(f'[{browser_type}] Screen: {screen["width"]}x{screen["height"]} @ {screen["devicePixelRatio"]}x DPR')
    logger.info(f'[{browser_type}] GPU: {gpu["vendor"]} / {gpu["renderer"][:50]}{"... [Multi-GPU]" if gpu["isMultiGPU"] else ""}')
    logger.info(f'[{browser_type}] Hardware: {hardware["hardwareConcurrency"]} cores, {hardware["deviceMemory"]}GB RAM, {hardware["maxTouchPoints"]} touch')
    logger.info(f'[{browser_type}] Connection: {connection["effectiveType"]}, {connection["rtt"]}ms RTT, {connection["downlink"]}Mbps')
    logger.info(f'[{browser_type}] Timezone: UTC{timezone_offset/60:+.0f}')
    logger.info(f'[{browser_type}] Battery: {"Charging" if battery["charging"] else "Discharging"} at {int(battery["level"]*100)}%')
    logger.info(f'[{browser_type}] WebRTC: {len(webrtc["localIPs"])} local IPs')
    logger.info(f'[{browser_type}] Media: {len(media_devices)} devices, Fonts: {len(fonts)} installed, Plugins: randomized')

    # navigator.platform coherent with the chosen UA (used by CDP override below).
    cdp_platform = derive_platform_from_ua(user_agent)

    # ============================================
    # SHARED STEALTH JAVASCRIPT (all browsers)
    # ============================================
    # Single reusable stealth body built from the generated fingerprint values.
    # It is injected PRE-DOCUMENT via CDP for Chromium/Edge (runs before any page
    # script and persists across navigations) and post-load via execute_script for
    # Firefox (which cannot use CDP). One source of truth guarantees Chromium/Edge
    # get the same GPU/screen/hardware/canvas/audio/WebRTC/timezone spoofing that
    # previously only Firefox received.
    stealth_js = f'''
            // ============================================
            // ADVANCED WEBDRIVER ARTIFACT REMOVAL
            // ============================================

            // Remove all Gecko/Firefox driver artifacts (harmless no-ops on Chromium)
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

            // ============================================
            // CANVAS FINGERPRINTING PROTECTION
            // ============================================
            // Deterministic per-session noise applied WITHOUT writing back to the
            // live canvas (writing back corrupts legitimate canvas/WebGL rendering).
            // toDataURL/toBlob render into a throwaway copy canvas that we noise;
            // getImageData returns a noised copy of the pixels. We always call the
            // ORIGINAL getImageData internally so noise is never applied twice.
            const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
            const originalToBlob = HTMLCanvasElement.prototype.toBlob;
            const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;

            // Consistent per-session seed so the fingerprint is stable within a session
            const noiseSeed = {random.random()};

            function simpleHash(str) {{
                let hash = 0;
                for (let i = 0; i < str.length; i++) {{
                    hash = ((hash << 5) - hash) + str.charCodeAt(i);
                    hash = hash & hash;
                }}
                return Math.abs(hash);
            }}

            // Apply tiny deterministic noise in place on an ImageData (a copy).
            function applyCanvasNoise(imageData) {{
                const data = imageData.data;
                for (let i = 0; i < data.length; i += 4) {{
                    const noise = (simpleHash(i.toString() + noiseSeed) % 3) - 1;
                    data[i]   = Math.min(255, Math.max(0, data[i]   + noise));
                    data[i+1] = Math.min(255, Math.max(0, data[i+1] + noise));
                    data[i+2] = Math.min(255, Math.max(0, data[i+2] + noise));
                }}
                return imageData;
            }}

            // Render into an offscreen copy, noise the copy, read the copy back.
            function noisedCopyContext(sourceCanvas) {{
                const copy = document.createElement('canvas');
                copy.width = sourceCanvas.width;
                copy.height = sourceCanvas.height;
                const ctx = copy.getContext('2d');
                ctx.drawImage(sourceCanvas, 0, 0);
                const imageData = originalGetImageData.call(ctx, 0, 0, copy.width, copy.height);
                applyCanvasNoise(imageData);
                ctx.putImageData(imageData, 0, 0);
                return copy;
            }}

            HTMLCanvasElement.prototype.toDataURL = function(...args) {{
                try {{
                    return originalToDataURL.apply(noisedCopyContext(this), args);
                }} catch (e) {{
                    return originalToDataURL.apply(this, args);
                }}
            }};

            if (originalToBlob) {{
                HTMLCanvasElement.prototype.toBlob = function(callback, ...rest) {{
                    try {{
                        return originalToBlob.call(noisedCopyContext(this), callback, ...rest);
                    }} catch (e) {{
                        return originalToBlob.call(this, callback, ...rest);
                    }}
                }};
            }}

            // getImageData returns a noised COPY; the source canvas is never mutated.
            CanvasRenderingContext2D.prototype.getImageData = function(...args) {{
                const imageData = originalGetImageData.apply(this, args);
                return applyCanvasNoise(imageData);
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

            // Font fingerprinting - tiny noise on text metrics. Keep 'width' WRITABLE
            // and configurable so legitimate code that reassigns it does not throw.
            const availableFonts = {str(fonts)};
            const originalMeasureText = CanvasRenderingContext2D.prototype.measureText;
            CanvasRenderingContext2D.prototype.measureText = function(text) {{
                const metrics = originalMeasureText.call(this, text);
                const noise = (Math.random() - 0.5) * 0.0002;
                try {{
                    Object.defineProperty(metrics, 'width', {{
                        value: metrics.width + noise,
                        writable: true,
                        configurable: true
                    }});
                }} catch (e) {{}}
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
            const randomLocalIPs = {str(webrtc["localIPs"])};
            const OriginalRTCPeerConnection = window.RTCPeerConnection || window.webkitRTCPeerConnection || window.mozRTCPeerConnection;
            if (OriginalRTCPeerConnection) {{
                const PatchedRTCPeerConnection = function(...args) {{
                    const pc = new OriginalRTCPeerConnection(...args);
                    const originalCreateOffer = pc.createOffer;
                    const originalCreateAnswer = pc.createAnswer;

                    // Inject random IPs into SDP
                    const injectRandomIPs = (sdp) => {{
                        if (sdp && sdp.sdp && randomLocalIPs.length > 0) {{
                            const randomIP = randomLocalIPs[Math.floor(Math.random() * randomLocalIPs.length)];
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
                PatchedRTCPeerConnection.prototype = OriginalRTCPeerConnection.prototype;
                window.RTCPeerConnection = PatchedRTCPeerConnection;
                if (window.webkitRTCPeerConnection) {{
                    window.webkitRTCPeerConnection = PatchedRTCPeerConnection;
                }}
                if (window.mozRTCPeerConnection) {{
                    window.mozRTCPeerConnection = PatchedRTCPeerConnection;
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

    if browser_type == 'chrome' or browser_type == 'chromium':
        options = webdriver.ChromeOptions()
        
        # Set browser name for Selenium Grid to pick the right nodes
        # Selenium Grid uses 'chrome' for both chrome and chromium
        options.set_capability('browserName', 'chrome')
        
        # Enable remote debugging so we can connect to CDP from outside the container
        options.add_argument('--remote-debugging-port=9222')
        options.add_argument('--remote-debugging-address=0.0.0.0')
        
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
        
        # Enable remote debugging so we can connect to CDP from outside the container
        options.add_argument('--remote-debugging-port=9222')
        options.add_argument('--remote-debugging-address=0.0.0.0')
        
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
    
    # ============================================
    # RETRY LOGIC FOR SESSION CREATION
    # ============================================
    logger.info(f'[{browser_type}] Creating browser session with stealth mode...')
    
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            # Keep the heartbeat fresh during session creation so a slow/retrying
            # connect isn't seen as a hang by the healthcheck.
            config.touch_heartbeat()
            if attempt > 1:
                logger.info(f'[{browser_type}] 🔄 Retry attempt {attempt}/{max_retries}...')
                time.sleep(5 * attempt)  # Exponential backoff
            
            # Bound EVERY remote command so a wedged node/session/page can never
            # hang the browse loop forever. In selenium 4.15 this is a CLASS-level
            # urllib3 timeout fed to the connection PoolManager, so it must be set
            # BEFORE the connection is built (i.e. before webdriver.Remote). The
            # default is socket._GLOBAL_DEFAULT_TIMEOUT -> get_timeout() None ->
            # PoolManager(timeout=None) -> infinite wait: the root cause of the
            # permanent chrome/edge hangs. 120s is well above page-load (30s).
            _cmd_timeout = int(os.getenv('WEBDRIVER_COMMAND_TIMEOUT', '90'))
            try:
                RemoteConnection.set_timeout(_cmd_timeout)  # selenium 4.15 API
            except Exception:
                # Newer selenium deprecates the classmethod; set the class attr the
                # PoolManager reads directly as a fallback. The in-process watchdog
                # remains the backstop if neither applies.
                try:
                    RemoteConnection._timeout = _cmd_timeout
                except Exception:
                    pass

            driver = webdriver.Remote(
                command_executor=f"http://{os.getenv('SELENIUM_HUB', 'selenium-hub:4444')}/wd/hub",
                options=options
            )

            # If successful, break out of retry loop
            logger.info(f'[{browser_type}] ✅ Session created successfully')
            break
            
        except Exception as e:
            last_error = e
            error_msg = str(e)
            logger.exception(f'[{browser_type}] Session creation attempt {attempt}/{max_retries} failed')
            
            if attempt < max_retries:
                if 'timeout' in error_msg.lower() or 'timed out' in error_msg.lower():
                    logger.info(f'[{browser_type}] 💤 Selenium Grid is overloaded, waiting before retry...')
                elif 'unable to connect to renderer' in error_msg.lower():
                    logger.warning(f'[{browser_type}] 💥 Renderer crash, waiting before retry...')
            else:
                # Final attempt failed
                logger.warning(f'[{browser_type}] ❌ Failed to create session after {max_retries} attempts')
                raise Exception(f"Could not create {browser_type} session after {max_retries} attempts: {error_msg}")
    
    # ============================================
    # CDP SETUP - Selenium Grid 4 Native Support
    # ============================================
    # Selenium Grid 4 has built-in CDP support via WebSocket tunneling
    # driver.execute_cdp_cmd() works directly with RemoteWebDriver
    
    if browser_type in ['chrome', 'chromium', 'edge']:
        logger.info(f'[{browser_type}] 🔧 Initializing CDP (Chrome DevTools Protocol)...')
        
        try:
            # Test basic CDP connection
            version = driver.execute_cdp_cmd('Browser.getVersion', {})
            browser_version = version.get('product', 'Unknown')
            protocol_version = version.get('protocolVersion', 'Unknown')
            logger.info(f'[{browser_type}] ✓ CDP connected: {browser_version}')
            logger.info(f'[{browser_type}]   Protocol version: {protocol_version}')
            
            # Enable CDP domains for page-level commands
            try:
                logger.info(f'[{browser_type}] 🔌 Enabling CDP domains...')
                driver.execute_cdp_cmd('Network.enable', {})
                logger.info(f'[{browser_type}]   ✓ Network domain enabled')
                
                driver.execute_cdp_cmd('Page.enable', {})
                logger.info(f'[{browser_type}]   ✓ Page domain enabled')
                
                # Apply CDP-based stealth
                logger.info(f'[{browser_type}] 🎭 Applying CDP stealth overrides...')
                
                # Override user agent via CDP (more reliable than --user-agent flag).
                # 'platform' is derived from the chosen UA so navigator.platform,
                # navigator.userAgent and the OS token all agree (no Win32-on-Linux tell).
                driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                    "userAgent": user_agent,
                    "platform": cdp_platform,
                    "acceptLanguage": accept_language
                })
                logger.info(f'[{browser_type}]   ✓ User agent overridden via CDP (platform: {cdp_platform})')
                logger.info(f'[{browser_type}]   UA: {user_agent[:60]}...')
                
                # Set extra HTTP headers for authenticity
                driver.execute_cdp_cmd('Network.setExtraHTTPHeaders', {
                    'headers': {
                        'Accept-Language': accept_language,
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                        'DNT': '1',
                        'Upgrade-Insecure-Requests': '1'
                    }
                })
                logger.info(f'[{browser_type}]   ✓ Extra HTTP headers configured')
                
                # Disable cache for realistic behavior
                driver.execute_cdp_cmd('Network.setCacheDisabled', {'cacheDisabled': True})
                logger.info(f'[{browser_type}]   ✓ Network cache disabled')
                
                # Set download behavior (prevent downloads from blocking)
                driver.execute_cdp_cmd('Page.setDownloadBehavior', {
                    'behavior': 'deny'
                })
                logger.info(f'[{browser_type}]   ✓ Downloads blocked')

                # Inject the comprehensive stealth JS PRE-DOCUMENT so the GPU/screen/
                # hardware/canvas/audio/WebRTC/timezone spoofing runs before any page
                # script and persists across navigations. This finally gives
                # Chromium/Edge the same coverage Firefox already had.
                try:
                    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                        'source': stealth_js
                    })
                    logger.info(f'[{browser_type}]   ✓ Comprehensive stealth JS injected pre-document (persists across navigations)')
                except Exception as inject_err:
                    logger.warning(f'[{browser_type}]   ⚠ Pre-document stealth injection failed: {str(inject_err)[:80]}')
                    logger.info(f'[{browser_type}]   ℹ Falling back to post-load JS stealth injection')
                    driver._stealth_js = stealth_js

                logger.info(f'[{browser_type}] ✅ Full CDP stealth active!')

            except Exception as e:
                logger.warning(f'[{browser_type}] ⚠ Page-level CDP commands failed: {str(e)[:80]}')
                logger.info(f'[{browser_type}] ℹ Falling back to JavaScript-based stealth')
                # Ensure stealth still applies post-load when CDP page commands fail.
                driver._stealth_js = stealth_js
                
        except (AttributeError, Exception) as e:
            logger.warning(f'[{browser_type}] ⚠ Native CDP unavailable: {str(e)[:80]}')
            logger.info(f'[{browser_type}] ℹ Using JavaScript stealth only')
            # No CDP at all — fall back to post-load JS injection so Chromium/Edge
            # still receive the full stealth body via execute_script in browse().
            driver._stealth_js = stealth_js
    
    elif browser_type == 'firefox':
        # Firefox cannot use CDP, so store the shared stealth body for post-load
        # injection via execute_script in browse() (same body Chromium/Edge get).
        driver._stealth_js = stealth_js
        logger.info(f'[{browser_type}] ✓ Prepared comprehensive stealth script (will inject on page load)')
    
    try:
        driver.set_page_load_timeout(30)
        driver.set_script_timeout(30)
        driver.set_window_size(screen["width"], screen["height"])
    except Exception:
        # If we can't finish configuring the session, don't leave a zombie
        # session hanging around on the hub — quit it before re-raising.
        try:
            driver.quit()
        except Exception:
            pass
        raise

    logger.info(f'[{browser_type}] ✓ Browser ready with advanced stealth mode')
    
    return driver


def is_driver_alive(driver):
    """
    Check if the WebDriver connection is still alive
    Returns True if connection is good, False if connection is lost
    """
    try:
        # The probe is bounded by the global RemoteConnection timeout set in
        # create_driver, so a hung hub connection cannot block forever here.
        _ = driver.current_url
        return True
    except Exception as e:
        error_msg = str(e).lower()
        # Only treat the session as alive for errors that clearly indicate a
        # live session (e.g. a transient page/navigation issue). For anything
        # else (timeouts, connection loss, unknown errors) assume the driver is
        # dead so that recovery/session recreation actually triggers.
        if any(phrase in error_msg for phrase in [
            'unexpected alert',
            'javascript error',
            'stale element'
        ]):
            return True
        # Default: assume dead so recovery kicks in.
        return False
