"""Top-level browse loop, setup and entry point (split from crawl.py)."""
import os
import time
import random
import logging
import threading
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException

from crawler import config
from crawler.config import browsers, HEALTH_CHECK_INTERVAL, PERSONA_MAX_AGE_DAYS
from crawler.sites import load_websites, get_domain, is_safe_url
from crawler.humanize import (
    SessionFatigueModel, get_time_of_day_multiplier, human_delay, realistic_delay,
    bezier_curve, human_mouse_movement, hover_before_click, fidget_mouse,
    smooth_scroll, reading_behavior, inject_realistic_errors,
    simulate_copy_paste, simulate_right_click,
)
from crawler.driver import create_driver, is_driver_alive
from crawler.interaction import (
    play_youtube_video, auto_accept_cookies, detect_and_click_ads,
    manage_tabs, handle_new_tab_from_ad, detect_and_bypass_bot_challenge,
)

logger = logging.getLogger('crawler.orchestrator')


BANNER = """
    ╔════════════════════════════════════════════════════════════╗
    ║   Browser Chaos Generator                                  ║
    ║   Automated browsing to generate web traffic               ║
    ╚════════════════════════════════════════════════════════════╝
    """


def _watchdog():
    """Backstop against any hang the command timeout doesn't catch.

    Runs in a daemon thread. If the browse loop makes no progress (the heartbeat
    file goes stale) for longer than WATCHDOG_TIMEOUT seconds, force-exit the
    process so Docker's restart policy brings up a fresh session. This is the
    last line of defence — the primary fix is the RemoteConnection command
    timeout, which turns a wedged call into a prompt exception.
    """
    timeout = int(os.getenv('WATCHDOG_TIMEOUT', '300'))
    hb_file = os.getenv('HEARTBEAT_FILE', '/tmp/crawler_heartbeat')
    while True:
        time.sleep(30)
        try:
            age = time.time() - os.path.getmtime(hb_file)
        except OSError:
            continue
        if age > timeout:
            logger.error('🐕 Watchdog: no progress for %ds (> %ds) — force-exiting for a clean restart',
                         int(age), timeout)
            os._exit(1)


def _write_heartbeat():
    """Touch the heartbeat file so the container healthcheck sees liveness.

    Called per-site, inside the per-site link traversal, and throughout the
    recovery paths, so that neither a deep slow site nor a multi-step session
    recovery is mistaken for a hang.
    """
    config.touch_heartbeat()


def _stats_summary():
    """Render the cumulative process metrics as one compact line."""
    s = config.STATS
    visited = s['sites_visited'] or 0
    reachable = visited - s['sites_unreachable'] - s['challenges_skipped']
    return (
        f"📊 stats: visited={visited} reachable={reachable} "
        f"unreachable={s['sites_unreachable']} challenges={s['challenges_skipped']} "
        f"ads_clicked={s['ads_clicked']} pages_with_ads={s['pages_with_ads']} "
        f"wd_errors={s['webdriver_errors']} recreated={s['sessions_recreated']} errors={s['errors']}"
    )


def browse():
    """Main browsing function - creates chaos by clicking through random links"""
    # Initialize global fatigue model for this session
    config.fatigue_model = SessionFatigueModel()

    # Bound persona growth once per session (drops old/overflowing personas).
    if config.persona_manager:
        try:
            config.persona_manager.clean_old_personas(
                max_age_days=PERSONA_MAX_AGE_DAYS,
                max_personas=int(os.getenv('PERSONA_MAX_PERSONAS', '1000'))
            )
        except Exception as e:
            logger.warning(f'⚠️  Persona cleanup failed: {str(e)[:60]}')

    browser_type = random.choice(browsers)
    logger.info(f'\n{"="*60}')
    logger.info(f'Starting {browser_type} browser')
    logger.info(f'{"="*60}')
    logger.info(f'⏰ Current time: {datetime.now().strftime("%H:%M")} (circadian factor: {get_time_of_day_multiplier()}x)')
    
    driver = create_driver(browser_type)
    
    # Store the current browsing tab (starts as main window)
    current_browsing_tab = driver.current_window_handle
    max_tabs = random.randint(5, 10)  # Random max tabs between 5-10
    
    # Keep track of websites visited in this session
    websites_visited = 0
    max_websites_per_session = random.randint(80, 120)  # 80-120 sites per session
    
    logger.info(f'[{browser_type}] 🎯 Session goal: Visit {max_websites_per_session} websites')
    logger.info(f'[{browser_type}] 📍 Initial tab: {current_browsing_tab[:8]}... (max {max_tabs} tabs)')
    
    while websites_visited < max_websites_per_session:
        try:
            # Heartbeat: signal liveness once per site for the healthcheck.
            _write_heartbeat()

            # Periodic health check + metrics summary every HEALTH_CHECK_INTERVAL websites
            if websites_visited > 0 and websites_visited % HEALTH_CHECK_INTERVAL == 0:
                logger.info(f'[{browser_type}] {_stats_summary()}')
                if not is_driver_alive(driver):
                    logger.warning(f'[{browser_type}] ⚠ Driver health check failed at website {websites_visited}')
                    raise WebDriverException("Driver health check failed")
            
            start_url = random.choice(config.sites)

            # Input safety: only navigate to http/https. Reject file://, data:,
            # chrome://, about:, javascript: and other schemes that could read local
            # files or reach privileged internal pages if the site list is poisoned.
            if not is_safe_url(start_url):
                logger.warning(f'[{browser_type}] 🚫 Skipping unsafe URL scheme: {start_url[:60]}')
                continue

            start_domain = get_domain(start_url)
            websites_visited += 1
            config.STATS['sites_visited'] += 1

            # Manage tabs before navigating
            current_browsing_tab, tab_switched = manage_tabs(driver, browser_type, current_browsing_tab, max_tabs)

            if tab_switched:
                # If we switched tabs, continue browsing the new tab
                logger.info(f'\n[{browser_type}] 🌐 Continuing on switched tab...')
                time.sleep(realistic_delay(2.0, variance=0.4))
            else:
                # Navigate to new URL
                logger.info(f'\n[{browser_type}] 🌐 Website {websites_visited}/{max_websites_per_session}: {start_url}')
                try:
                    driver.get(start_url)
                except WebDriverException as nav_err:
                    # Dead/unreachable domains (DNS failure, connection refused, TLS
                    # errors) are expected in a large crawl list — Firefox surfaces
                    # them as "Reached error page: about:neterror". Treat as a routine
                    # skip (concise WARNING, no traceback) instead of a hard error,
                    # unless the session itself actually died.
                    msg = str(nav_err).lower()
                    if any(s in msg for s in (
                        'neterror', 'dnsnotfound', 'dns_probe', 'connectionfailure',
                        'name_not_resolved', 'unreachable', 'connection refused',
                        'err_connection', 'err_name', 'err_address', 'err_cert',
                        'timed out', 'net::err',
                    )) and is_driver_alive(driver):
                        config.STATS['sites_unreachable'] += 1
                        logger.warning(f'[{browser_type}] 🔗 Unreachable site, skipping: '
                                       f'{start_domain} ({str(nav_err).splitlines()[0][:80]})')
                        continue
                    raise  # genuine WebDriver/session failure — handle below
            
            # Inject stealth script for Firefox
            if hasattr(driver, '_stealth_js'):
                try:
                    driver.execute_script(driver._stealth_js)
                except Exception:
                    pass
            
            # Detect and bypass bot challenges (Cloudflare, etc.)
            challenge_passed = detect_and_bypass_bot_challenge(driver, browser_type, max_attempts=3)
            _write_heartbeat()  # challenge handling can wait several seconds
            if not challenge_passed:
                config.STATS['challenges_skipped'] += 1
                logger.warning(f'  [{browser_type}] ⚠ Could not bypass bot challenge, skipping to next website')
                continue  # Skip to next website

            # Random human-like delay with fidgeting
            reading_behavior(driver, duration=random.uniform(2, 4))

            # Auto-accept cookies
            auto_accept_cookies(driver, browser_type)
            _write_heartbeat()

            # Inject realistic console errors (10% chance)
            inject_realistic_errors(driver)

            # Play YouTube videos if detected
            play_youtube_video(driver, browser_type)
            _write_heartbeat()

            # Simulate copy/paste behavior (5% chance)
            simulate_copy_paste(driver)

            # Simulate right-click behavior (5% chance)
            simulate_right_click(driver, browser_type)

            # Try to detect and click ads (60% chance)
            initial_tab_count = len(driver.window_handles)
            detect_and_click_ads(driver, browser_type, click_chance=0.6)
            _write_heartbeat()
            
            # Handle new tabs from ads (40% chance to switch to ad tab)
            if len(driver.window_handles) > initial_tab_count:
                current_browsing_tab, switched_to_ad = handle_new_tab_from_ad(driver, browser_type, current_browsing_tab)
                if switched_to_ad:
                    # We're now browsing the ad tab, inject stealth and continue
                    if hasattr(driver, '_stealth_js'):
                        try:
                            driver.execute_script(driver._stealth_js)
                        except Exception:
                            pass
                    
                    # Check for bot challenges on the new ad tab
                    challenge_passed = detect_and_bypass_bot_challenge(driver, browser_type, max_attempts=3)
                    if not challenge_passed:
                        logger.warning(f'  [{browser_type}] ⚠ Ad tab has bot challenge, closing it')
                        try:
                            driver.close()
                            # Switch back to original browsing tab
                            if current_browsing_tab in driver.window_handles:
                                driver.switch_to.window(current_browsing_tab)
                            elif driver.window_handles:
                                current_browsing_tab = driver.window_handles[0]
                                driver.switch_to.window(current_browsing_tab)
                        except Exception:
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
                    # Refresh liveness during long single-site traversals.
                    _write_heartbeat()

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
                        logger.info(f'  [{browser_type}] No links found at depth {current_depth}, moving to next website')
                        break
                    
                    # Get more links and filter less strictly
                    clickable = []
                    for link in links[:200]:  # Check more links
                        try:
                            if link.is_displayed() and link.is_enabled():
                                href = link.get_attribute('href')
                                if href and (href.startswith('http://') or href.startswith('https://')):
                                    clickable.append(link)
                        except Exception:
                            continue
                    
                    if not clickable:
                        logger.info(f'  [{browser_type}] No clickable links at depth {current_depth}, moving to next website')
                        break
                    
                    logger.info(f'  [{browser_type}] Found {len(clickable)} clickable links')
                    
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
                        except Exception:
                            continue
                    
                    logger.info(f'  [{browser_type}] Internal: {len(internal_links)}, External: {len(external_links)}')
                    
                    # Choose link strategy - prefer internal to stay on site longer
                    chosen_link = None
                    if internal_links and random.random() < 0.8:  # 80% prefer internal
                        chosen_link = random.choice(internal_links)
                        logger.info(f'  [{browser_type}] Depth {current_depth}: Choosing internal link')
                    elif external_links:
                        chosen_link = random.choice(external_links)
                        logger.info(f'  [{browser_type}] Depth {current_depth}: Choosing external link (will move to next website)')
                        # If we go external, break after this click to count as new website
                    elif internal_links:
                        chosen_link = random.choice(internal_links)
                    elif clickable:
                        chosen_link = random.choice(clickable)
                    
                    if chosen_link:
                        try:
                            href = chosen_link.get_attribute('href')
                            link_domain = get_domain(href)
                            logger.info(f'  [{browser_type}] Depth {current_depth}: {href[:80]}')
                            
                            # Try human-like hover and click (80% chance)
                            click_success = False

                            # Capture tab count BEFORE the click so we can detect new tabs
                            pre_click_tabs = len(driver.window_handles)

                            if random.random() < 0.8:
                                # Use hover_before_click for realistic behavior
                                try:
                                    click_success = hover_before_click(driver, chosen_link, hover_time=random.uniform(0.3, 0.9))
                                    if click_success:
                                        logger.info(f'  [{browser_type}] ✓ Used hover-and-click')
                                except Exception as e:
                                    logger.warning(f'  [{browser_type}] Hover-click failed: {str(e)[:40]}')
                            
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
                                        logger.info(f'  [{browser_type}] Click intercepted, trying alternative methods...')
                                        
                                        # Method 2: Scroll into view and click
                                        try:
                                            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", chosen_link)
                                            time.sleep(0.5)
                                            chosen_link.click()
                                            click_success = True
                                        except Exception:
                                            # Method 3: JavaScript click (most reliable)
                                            try:
                                                driver.execute_script("arguments[0].click();", chosen_link)
                                                click_success = True
                                                logger.info(f'  [{browser_type}] ✓ Used JavaScript click')
                                            except Exception as e2:
                                                logger.warning(f'  [{browser_type}] ✗ All click methods failed: {str(e2)[:40]}')
                                                # Method 4: Navigate directly
                                                try:
                                                    driver.get(href)
                                                    click_success = True
                                                    logger.info(f'  [{browser_type}] ✓ Navigated directly to URL')
                                                except Exception:
                                                    pass
                                    else:
                                        # Some other error, try JavaScript click
                                        try:
                                            driver.execute_script("arguments[0].click();", chosen_link)
                                            click_success = True
                                        except Exception:
                                            pass
                            
                            if not click_success:
                                logger.warning(f'  [{browser_type}] ⚠ Could not click link, skipping')
                                continue
                            
                            # Variable delay after click (humans don't click instantly, includes fatigue)
                            time.sleep(realistic_delay(3.5, variance=0.4))
                            
                            # Check if link opened new tabs
                            if len(driver.window_handles) > pre_click_tabs:
                                current_browsing_tab, switched_to_new = handle_new_tab_from_ad(driver, browser_type, current_browsing_tab)
                            
                            # Try to accept cookies on new page (but don't wait too long)
                            try:
                                auto_accept_cookies(driver, browser_type)
                            except Exception:
                                pass
                            
                            # Play YouTube videos if detected
                            try:
                                play_youtube_video(driver, browser_type)
                            except Exception:
                                pass
                            
                            # Occasionally try to click ads (60% chance)
                            if random.random() < 0.4:  # 40% of the time, try to click ads
                                try:
                                    initial_tabs = len(driver.window_handles)
                                    detect_and_click_ads(driver, browser_type, click_chance=0.6)
                                    
                                    # Handle new tabs from ads
                                    if len(driver.window_handles) > initial_tabs:
                                        current_browsing_tab, _ = handle_new_tab_from_ad(driver, browser_type, current_browsing_tab)
                                except Exception:
                                    pass
                            
                            current_depth += 1
                            
                            # If we went to external site, break to count as new website
                            if link_domain != start_domain:
                                logger.info(f'  [{browser_type}] 🔄 Moved to external site, counting as next website')
                                websites_visited += 1
                                start_domain = link_domain
                                break
                                
                        except Exception as click_error:
                            logger.warning(f'  [{browser_type}] Navigation failed: {str(click_error)[:50]}')
                            continue
                    else:
                        logger.info(f'  [{browser_type}] No suitable link found at depth {current_depth}')
                        break
                        
                except Exception as nav_error:
                    logger.info(f'  [{browser_type}] Navigation error: {str(nav_error)[:50]}')
                    break
            
            logger.info(f'[{browser_type}] ✓ Finished exploring website. Depth: {current_depth}/{max_depth}')
            time.sleep(realistic_delay(2.0, variance=0.4))
            
        except TimeoutException:
            logger.info(f'[{browser_type}] ⏱ Timeout, moving to next website')
            # Note: this site was already counted when it was chosen/navigated.

            # Check if driver is still alive after timeout
            if not is_driver_alive(driver):
                logger.warning(f'[{browser_type}] ⚠ Driver connection lost after timeout')
                # Fall through to WebDriverException handler below
                raise WebDriverException("Driver connection lost after timeout")
                
        except WebDriverException as e:
            error_msg = str(e)
            config.STATS['webdriver_errors'] += 1

            # Refresh liveness: recovery may make one or more bounded-but-slow
            # remote calls; without this a multi-step recovery could exceed the
            # healthcheck window and be killed mid-recovery.
            _write_heartbeat()

            # Check if driver connection is actually lost (comprehensive check)
            driver_is_dead = not is_driver_alive(driver)
            _write_heartbeat()

            # Only emit a full traceback when the session is actually dead (rare,
            # actionable). Transient element/timeout errors get one concise line so
            # they don't drown the logs.
            if driver_is_dead:
                logger.warning(f'[{browser_type}] WebDriver error (session lost): {error_msg.splitlines()[0][:120]}')
            else:
                logger.warning(f'[{browser_type}] WebDriver error (recoverable): {error_msg.splitlines()[0][:120]}')
                logger.debug('WebDriver error detail', exc_info=True)
            
            # Check if session is lost - needs recreation
            if driver_is_dead or any(phrase in error_msg.lower() for phrase in [
                'cannot find session',
                'invalid session id',
                'tried to run command without establishing',
                'unable to connect to renderer',
                'driver connection lost',
                'session deleted',
                'no such session'
            ]):
                config.STATS['sessions_recreated'] += 1
                logger.warning(f'[{browser_type}] 💀 Session is dead! Creating new session...')
                try:
                    # Close CDP WebSocket if it exists
                    if hasattr(driver, '_cdp_client') and driver._cdp_client:
                        try:
                            driver._cdp_client.close()
                        except Exception:
                            pass
                    try:
                        driver.quit()
                    except Exception:
                        pass
                except Exception:
                    pass
                
                # Create new driver and reset state
                try:
                    logger.info(f'[{browser_type}] 🔄 Creating fresh driver session...')
                    _write_heartbeat()
                    driver = create_driver(browser_type)
                    current_browsing_tab = driver.current_window_handle
                    max_tabs = random.randint(5, 10)
                    logger.info(f'[{browser_type}] ✅ New session created successfully')
                    logger.info(f'[{browser_type}] 📍 New tab: {current_browsing_tab[:8]}... (max {max_tabs} tabs)')
                    # Note: the failed site was already counted; don't double-count.
                except Exception as create_error:
                    logger.exception(f'[{browser_type}] Failed to create new session')
                    logger.warning(f'[{browser_type}] Exiting to restart container...')
                    break
            else:
                # Other WebDriver errors - try to continue
                logger.info(f'[{browser_type}] Trying to continue with same session...')
                # Note: this site was already counted when it was chosen/navigated.
                time.sleep(2)
        except Exception as e:
            config.STATS['errors'] += 1
            _write_heartbeat()
            logger.warning(f'[{browser_type}] Error during browse iteration: {str(e).splitlines()[0][:120]}')
            logger.debug('browse iteration error detail', exc_info=True)
            # A timed-out/wedged command surfaces here. If the session is no longer
            # responsive, end this session so the main loop starts a fresh driver
            # (rather than spinning on repeated timeouts).
            if not is_driver_alive(driver):
                config.STATS['sessions_recreated'] += 1
                logger.warning(f'[{browser_type}] Session unresponsive — ending it to restart with a fresh driver')
                break
            # Note: this site was already counted when it was chosen/navigated.

    # Session complete, close browser
    logger.info(f'\n[{browser_type}] ✅ Session complete! Visited {websites_visited} websites.')
    logger.info(f'[{browser_type}] {_stats_summary()}')
    logger.info(f'[{browser_type}] Closing browser and starting new session...')
    try:
        # Close CDP WebSocket if it exists
        if hasattr(driver, '_cdp_client') and driver._cdp_client:
            driver._cdp_client.close()
        driver.quit()
    except Exception:
        pass


def configure_logging():
    """Configure stdlib logging from the environment.

    Level comes from LOG_LEVEL (default INFO). Format is an ISO-8601 timestamp
    followed by the level and message.
    """
    level_name = os.getenv('LOG_LEVEL', 'INFO').upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(
        level=level,
        format='%(asctime)s %(levelname)s %(message)s',
        datefmt='%Y-%m-%dT%H:%M:%S',
    )


def setup():
    """Initialize runtime globals that touch disk/external state.

    Kept out of import time so that importing this module (or the future split
    modules) has no side effects: no persona storage is opened and websites.txt
    is not read until the process actually starts crawling.
    """
    if config.PERSONA_MANAGER_AVAILABLE and config.persona_manager is None:
        config.persona_manager = config.PersonaManager()
    if not config.sites:
        config.sites = load_websites()


def main():
    """Entry point: configure logging, initialize state, then loop forever."""
    configure_logging()
    setup()

    # Start the liveness watchdog (daemon) before crawling begins.
    threading.Thread(target=_watchdog, name='watchdog', daemon=True).start()

    # Keep the ASCII banner as a plain print so it renders without log framing.
    print(BANNER)

    logger.info("Available browsers: %s", ', '.join(browsers))
    logger.info("Starting in 5 seconds...")
    time.sleep(5)

    consecutive_failures = 0
    while True:
        try:
            browse()
            # Clean session completion — reset the failure backoff.
            consecutive_failures = 0
        except Exception:
            consecutive_failures += 1
            backoff = min(300, 5 * (2 ** consecutive_failures))
            logger.exception('Fatal error in browse loop')
            logger.warning('Restarting in %ss (consecutive failures: %s)...',
                           backoff, consecutive_failures)
            time.sleep(backoff)


if __name__ == '__main__':
    main()
