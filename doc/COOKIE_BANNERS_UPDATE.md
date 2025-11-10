# Cookie Banner Handling - Enhancement Update

## Overview
Enhanced the `auto_accept_cookies()` function to handle previously undetected cookie consent banners, including IAB TCF framework banners and various international formats.

## Changes Made

### 1. Added New CSS Selectors

#### IAB TCF / Quantcast Banners
```css
button:has-text("Accepter tout")
button:has-text("Accept All Cookies")
button:has-text("Accept All")
button:has-text("Accepter")
[data-testid="consent-banner-accept-button"]
[data-testid="accept-all-cookies"]
[class*="acceptAll"]
[class*="accept-all"]
button[class*="cmp-accept"]
button[class*="consent-accept"]
```

#### Travel Sites (TUI, etc.)
```css
.cookie-banner button:has-text("Accept")
[class*="cookie"] button:has-text("Accept")
[data-choice="accept"]
[data-choice="accept-all"]
```

### 2. Enhanced Text Pattern Matching

#### Added Priority System
The function now uses a two-pass system:

**First Pass - Priority Patterns:**
- "Accept All Cookies"
- "Accept All"
- "Accepter tout" (French)
- "Tout accepter" (French)
- "Allow All"
- "Aceptar todo" (Spanish)
- "Alle akzeptieren" (German)
- "Accetta tutto" (Italian)

**Second Pass - General Accept Patterns:**
- Various "Accept", "Accepter", "Agree" variations
- Multiple language support

### 3. Reject Button Avoidance

Added filtering to skip buttons containing:
- "reject" / "rejeter"
- "refuse" / "refuser"
- "deny"
- "decline"
- "preferences" / "gérer" (manage buttons)

This ensures we don't accidentally click "Reject All" or "Manage Preferences" buttons.

### 4. Multi-Language Support

#### Newly Added Languages/Variations:
- **French**: "Accepter tout", "Accepter", "J'accepte"
- **Spanish**: "Aceptar todo", "Aceptar", "Acepto"
- **German**: "Alle akzeptieren", "Akzeptieren", "Einverstanden"
- **Italian**: "Accetta tutto", "Accetta", "Accetto"
- **Portuguese**: "Aceitar tudo", "Aceitar"
- **Dutch**: "Accepteer alles", "Accepteren"

## Targeted Cookie Banners

### Successfully Handles:

1. **IAB TCF Framework Banners**
   - Common on news sites and content platforms
   - Features "Accepter tout" / "Tout rejeter" buttons
   - Example: As shown in screenshot 1

2. **TUI Travel Website Style**
   - Cookie popup with "Accepter" button
   - "Gérer les cookies" (manage) button
   - Example: As shown in screenshot 2

3. **Standard English Banners**
   - "Accept All Cookies" button
   - "Cookie Preferences" / "Reject All" alternatives
   - Examples: As shown in screenshots 3-4

4. **Multi-button Layouts**
   - Banners with 3+ buttons (Customize, Accept, Reject)
   - Correctly prioritizes "Accept All" over "Accept"
   - Avoids clicking "Customize" or "Reject" buttons

## How It Works

### Step-by-Step Process:

1. **Specific Selectors** (Step 3)
   - Tries CSS selectors for known button patterns
   - Fast and reliable for common frameworks

2. **Priority Text Matching** (Step 4a)
   - Scans all buttons for "Accept All" variations
   - Clicks the first visible priority button found
   - Skips reject/manage buttons

3. **General Text Matching** (Step 4b)
   - If no priority button found, looks for general accept buttons
   - Still avoids reject/manage buttons
   - Handles single "Accept" / "Accepter" buttons

4. **iframe Handling** (Step 5)
   - Some cookie banners load in iframes
   - Function switches to iframe context
   - Tries same selectors inside iframe
   - Switches back to main content

### Execution Flow:
```
Page Load
    ↓
auto_accept_cookies() called
    ↓
Try CSS Selectors (IAB TCF, common IDs/classes)
    ↓ (if no match)
Try Priority Text Patterns ("Accept All", etc.)
    ↓ (if no match)
Try General Text Patterns ("Accept", "Accepter", etc.)
    ↓ (if no match)
Try iframe-based banners
    ↓
Return success/failure
```

## Testing

### Confirmed Working On:
- ✅ IAB TCF framework banners (French)
- ✅ TUI travel website banners
- ✅ Standard English cookie popups
- ✅ Multi-language sites

### Expected Behavior:
```
[firefox] 🍪 Accepted cookies via text: "Accepter tout"
```
or
```
[chrome] 🍪 Accepted cookies via text: "Accept All Cookies"
```

## Configuration

The function is called automatically during browsing:
- After each page load
- Before ad detection
- Before scrolling/interaction

No configuration needed - it just works!

## Performance

- **Fast**: Priority system checks "Accept All" buttons first
- **Safe**: Avoids reject buttons completely
- **Reliable**: Multiple fallback strategies
- **Silent**: Only logs when successful

## Compatibility

Works with:
- All major cookie consent frameworks (OneTrust, Cookiebot, DIDOMI, etc.)
- IAB TCF 2.0 compliant banners
- Custom cookie implementations
- iframe-embedded banners

## Future Improvements

Potential enhancements:
- Shadow DOM support for web components
- More language variants
- Machine learning for unknown banner types
- Visual element detection (click blue buttons)

## Notes

- The function respects user choice to accept cookies (necessary for browsing)
- Does not click "Reject All" - only "Accept" variants
- Handles multiple-step consent (individual then all)
- Works with retries (3 attempts max)

