# Contributing to NEXUS WiFi Radar

Thank you for considering contributing to NEXUS! This document provides guidelines and instructions for contributing.

## 🎯 Ways to Contribute

- 🐛 **Bug Reports** — Report issues you encounter
- ✨ **Feature Requests** — Suggest new functionality
- 📝 **Documentation** — Improve README, docstrings, examples
- 🔧 **Code** — Submit bug fixes or new features
- 🌐 **OUI Database** — Add missing vendor MAC prefixes
- 🎨 **Themes** — Create new visual skins
- 🔒 **Security Rules** — Add threat detection patterns

## 🐛 Reporting Bugs

Before submitting a bug report:
1. Check existing [issues](https://github.com/your-repo/nexus-wifi-radar/issues)
2. Try the latest version
3. Verify it's not a configuration issue

**Good bug report includes:**
- OS version (Windows 10/11, Ubuntu 22.04, etc.)
- Python version (`python --version`)
- NEXUS version
- Steps to reproduce
- Expected vs actual behavior
- Error messages/logs (if any)

**Example:**
```
**Environment:**
- OS: Windows 11 23H2
- Python: 3.11.9
- NEXUS: v2.0.0

**Steps to reproduce:**
1. Launch: `python -m nexus gui`
2. Click "Start Scan"
3. App freezes after 5 seconds

**Expected:** Scan completes, networks displayed
**Actual:** App freezes, no error message

**Logs:**
[Paste relevant logs here]
```

## ✨ Feature Requests

We welcome feature suggestions! Before submitting:
1. Check if it already exists in issues
2. Consider if it fits NEXUS's scope (WiFi intelligence)
3. Think about backward compatibility

**Good feature request includes:**
- Clear description of the feature
- Use case / problem it solves
- Example of how it would work
- (Optional) Implementation ideas

## 🔧 Development Setup

### 1. Fork and Clone

```bash
git clone https://github.com/YOUR-USERNAME/nexus-wifi-radar.git
cd nexus-wifi-radar
```

### 2. Create Virtual Environment

**Windows:**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Development Dependencies

```bash
pip install -e ".[dev]"
```

This installs:
- `pytest` — Testing framework
- `pytest-cov` — Coverage reporting
- `black` — Code formatter
- `ruff` — Fast linter

### 4. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
```

## 📝 Code Guidelines

### Style

- **PEP 8** compliance
- **Type hints** for all public APIs
- **Docstrings** for modules, classes, and public functions
- **Black** formatting (line length: 100)

**Example:**
```python
def estimate_distance(rssi_dbm: int, frequency_mhz: int, environment: str = "indoor") -> float:
    """
    Estimate distance from RSSI using log-distance path loss model.
    
    Args:
        rssi_dbm: Received signal strength in dBm (-30 to -100)
        frequency_mhz: WiFi frequency in MHz (2412-5825)
        environment: "indoor", "outdoor", or "open_space"
    
    Returns:
        Estimated distance in meters
    
    Example:
        >>> estimate_distance(-65, 2437, "indoor")
        12.5
    """
    # Implementation...
```

### Architecture

- **Core modules** (`core/`) — No UI dependencies, reusable
- **Platform modules** (`platform/`) — OS-specific, inherit from base `Scanner`
- **UI modules** (`ui/`) — Can depend on core, not platform
- **Immutable dataclasses** — Use `@dataclass(frozen=True)` when possible

### Commits

- Use conventional commit format: `type(scope): message`
- Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`
- Keep commits atomic (one logical change per commit)

**Examples:**
```bash
feat(vendor): add 50 new OUI entries for IoT devices
fix(windows): handle netsh output with non-ASCII characters
docs(readme): update installation instructions for Ubuntu 24.04
refactor(radar): extract blip rendering to separate method
test(scanner): add tests for edge cases in MAC parsing
```

## 🧪 Testing

### Run Tests

```bash
# All tests
pytest -v

# Specific file
pytest tests/test_vendor.py -v

# With coverage
pytest --cov=nexus --cov-report=html
```

### Writing Tests

Place tests in `tests/` directory. Name test files `test_*.py`.

**Example:**
```python
# tests/test_distance.py
from nexus.core.distance import estimate_distance

def test_distance_estimation_indoor():
    """Test indoor distance calculation at 2.4GHz."""
    distance = estimate_distance(-65, 2437, "indoor")
    assert 10 < distance < 15  # Should be ~12.5m

def test_distance_estimation_outdoor():
    """Test outdoor distance calculation."""
    distance = estimate_distance(-65, 2437, "outdoor")
    assert distance > 15  # Should be further than indoor
```

### Test Coverage

Aim for:
- **Core modules**: 80%+ coverage
- **Platform modules**: 60%+ coverage (harder to test hardware)
- **UI modules**: Not required (but welcome)

## 🌐 Adding OUI Entries

To add missing MAC vendor prefixes:

### 1. Find OUI

Look up MAC address on [IEEE OUI Database](https://standards-oui.ieee.org/) or [MAC Vendors](https://macvendors.com/)

### 2. Add to `nexus/core/vendor.py`

Find the appropriate section (e.g., `# Smart Home Devices`) and add:

```python
"A1B2C3": "Device Manufacturer",
```

**Rules:**
- OUI must be uppercase, no colons
- Group related vendors together
- Add comment for first entry in new category
- Sort alphabetically within sections

### 3. Test

```python
from nexus.core.vendor import lookup_vendor

vendor = lookup_vendor("A1:B2:C3:11:22:33")
assert vendor == "Device Manufacturer"
```

## 🎨 Creating Themes

To add a new visual theme:

### 1. Create Skin File

Create `nexus/ui/skins/your_theme.py`:

```python
"""Your Theme Name — Brief description."""

class YourThemeSkin:
    """Your cyberpunk theme."""
    
    name = "Your Theme"
    description = "Description of the theme"
    
    colors = {
        "bg_main": "#1a1a2e",
        "bg_panel": "#16213e",
        "text_primary": "#eaeaea",
        "text_secondary": "#9fa2b4",
        "text_accent": "#e94560",
        "radar_bg": "#0f0f0f",
        "radar_grid": "#2a2a3e",
        "radar_blip": "#00ff00",
        "threat": "#ff0000",
        "anomaly": "#ffff00",
        "insight": "#00ffff",
    }
    
    fonts = {
        "main": ("Consolas", 10),
        "header": ("Consolas", 14, "bold"),
        "small": ("Consolas", 8),
    }
```

### 2. Register Skin

Add to `nexus/ui/skins/__init__.py`:

```python
from nexus.ui.skins.your_theme import YourThemeSkin

AVAILABLE_SKINS = {
    # ... existing skins ...
    "your_theme": YourThemeSkin,
}
```

### 3. Test

Launch NEXUS and select your theme from the theme selector.

## 🔒 Adding Detection Rules

To add custom threat detection:

### 1. Create Rule Class

In `nexus/security/rules.py`:

```python
class YourCustomRule:
    """Detect suspicious pattern X."""
    
    name = "your_rule_name"
    description = "Detects networks with [pattern]"
    severity = ThreatSeverity.MEDIUM
    
    def evaluate(self, network: Network, all_networks: List[Network]) -> Optional[Threat]:
        """Evaluate network against this rule."""
        if self._is_suspicious(network):
            return Threat(
                category=ThreatCategory.SUSPICIOUS_BEHAVIOR,
                severity=self.severity,
                network=network,
                description=f"Detected: {network.ssid}"
            )
        return None
    
    def _is_suspicious(self, network: Network) -> bool:
        # Your detection logic
        return False
```

### 2. Register Rule

Add to `BUILTIN_RULES` in same file:

```python
BUILTIN_RULES = [
    # ... existing rules ...
    YourCustomRule(),
]
```

## 📤 Submitting Changes

### 1. Run Tests

```bash
pytest -v
```

### 2. Format Code

```bash
black nexus/
```

### 3. Check Linting

```bash
ruff check nexus/
```

### 4. Commit and Push

```bash
git add .
git commit -m "feat(component): add your feature"
git push origin feature/your-feature-name
```

### 5. Create Pull Request

1. Go to original repository on GitHub
2. Click "New Pull Request"
3. Select your fork and branch
4. Fill in PR template:
   - What does this change?
   - Why is it needed?
   - How was it tested?
   - Screenshots (if UI change)

### 6. Code Review

Maintainers will review your PR. Be prepared to:
- Answer questions
- Make requested changes
- Squash commits if needed

## 🏅 Recognition

Contributors are acknowledged in:
- Project README
- Release notes
- Git commit history

## 📜 License

By contributing, you agree that your contributions will be licensed under the MIT License.

## ❓ Questions

- **General questions**: Open a [Discussion](https://github.com/your-repo/nexus-wifi-radar/discussions)
- **Bug reports**: Open an [Issue](https://github.com/your-repo/nexus-wifi-radar/issues)
- **Security issues**: Email maintainers directly (not public issues)

---

Thank you for contributing to NEXUS! 🎯
