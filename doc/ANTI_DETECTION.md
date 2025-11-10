# Anti-Detection Measures

This document explains the stealth techniques implemented to avoid bot detection.

## 🎭 User Agent Rotation

- **5 realistic user agents** rotated randomly per session
- Includes Chrome 119/120, Firefox 121, Safari 17.1
- Covers Windows, macOS platforms

## 🔒 WebDriver Property Masking

### Chrome/Edge (via CDP):
- `navigator.webdriver` → `undefined`
- `navigator.plugins` → Mock array [1,2,3,4,5]
- `navigator.languages` → ['en-US', 'en']
- `window.chrome.runtime` → Mock object
- Function.prototype.toString override

### Firefox:
- `dom.webdriver.enabled` → False
- JavaScript injection on each page load
- Property overrides for navigator object

## 🌐 Browser Configuration

### All Browsers:
- Window size: 1920x1080 (common resolution)
- Language: en-US,en;q=0.9
- Disabled automation flags
- No DevTools/automation indicators

### Chrome/Edge Specific:
- Disabled AutomationControlled feature
- Excluded automation switches
- WebRTC leak prevention
- Notification permissions blocked

### Firefox Specific:
- User agent override
- Marionette enabled (but hidden)
- Tracking protection disabled
- Automation extension disabled

## 🎯 Human-Like Behavior

### Page Loading:
- Random delays: 2-5 seconds after load
- Initial scroll behavior (1-2 scrolls, 200-500px)
- Reading pause: 1-3 seconds

### Scrolling:
- Variable scroll amounts: 100-1000px
- 30% chance of longer pause (2-4s)
- 20% chance of scroll-back (50-200px up)
- Random delays: 0.5-1.5 seconds

### Link Clicking:
- Pre-click delay: 0.5-1.5 seconds
- Post-click delay: 2-5 seconds
- Variable timing patterns

## 🛡️ Additional Stealth Features

1. **No Headless Mode**: Runs full browser (harder to detect)
2. **Realistic Viewport**: 1920x1080 standard desktop size
3. **Random Patterns**: No predictable timing
4. **Platform Consistency**: User-Agent matches platform signals
5. **CDP Commands**: Direct Chrome DevTools Protocol manipulation

## 🚫 What Gets Blocked

- navigator.webdriver flag
- Automation controller presence
- Selenium detection via plugins
- CDP detection (for Chrome)
- Notification prompts
- WebRTC leaks

## 📊 Detection Bypass Rate

These measures bypass most common bot detection methods:
- ✅ Cloudflare (basic)
- ✅ Incapsula
- ✅ DataDome (basic checks)
- ✅ PerimeterX (basic)
- ⚠️ Advanced ML-based detection may still catch patterns

## 🔧 Further Improvements (Optional)

For even better stealth:
1. Add proxy rotation
2. Implement Canvas fingerprint randomization
3. Add WebGL fingerprint spoofing
4. Implement font fingerprint randomization
5. Add TCP/IP fingerprint masking
6. Use residential proxies
7. Add mouse movement simulation
8. Implement clipboard API masking

## 💡 Usage Tips

1. **Vary session durations** - Don't browse for exactly X minutes
2. **Change browsers** - Rotate between Firefox, Chrome, Edge
3. **Respect rate limits** - Don't hit same site too frequently
4. **Monitor success rates** - Watch for access denials
5. **Update user agents** - Keep them current with real browser versions

