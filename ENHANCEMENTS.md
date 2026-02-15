# Vanta - Advanced Features Integration

This document describes the three advanced features added to Vanta and how they integrate with the main application.

---

## 1. Biometric Authentication

**File:** `biometric_manager.py`

**Behavior:**
- Uses `plyer` for biometric verification when available (Fingerprint/FaceID on supported devices)
- Falls back to PIN input (default: `1234`) when biometrics are not supported or fail
- Offers a "Skip" option for development or when the user prefers not to authenticate

**Integration Points:**
- **WalletScreen:** Biometric auth is required when entering the screen. On success or skip, wallet data is displayed. On cancel, navigates back to Home.
- **SellScreen:** Biometric auth is required when "List for Sale" is pressed. On success or skip, the transaction proceeds.

**Adding to main.py:**
```python
from biometric_manager import BiometricManager

# In VantaApp.__init__:
self._biometric_manager = BiometricManager()

# In build():
self.biometric_manager = self._biometric_manager
```

**Usage:**
```python
app.biometric_manager.request_auth(
    reason=app.translations.get("authenticate"),
    on_success=lambda: do_sensitive_action(),
    on_fail=lambda reason: handle_failure(reason),  # reason can be "skipped"
)
```

**PIN Fallback:** Change `FALLBACK_PIN` in `biometric_manager.py` (default: `"1234"`). In production, hash and verify securely.

---

## 2. Multi-Chain Support (Ethereum + Polygon)

**File:** `wallet_manager.py`

**New Methods:**
- `set_network(network: str)` – Switch between `"ethereum"` and `"polygon"`
- `get_rpc_url()` – Returns RPC URL for current network
- `get_chain_id()` – Returns chain ID (1 for ETH, 137 for Polygon)
- `get_symbol()` – Returns `"ETH"` or `"MATIC"`
- `get_web3()` – Returns Web3 instance for current network

**Integration:**
- **WalletScreen:** Network switcher buttons (Ethereum / Polygon). Balance and RPC update when switching.
- **App._load_balance():** Uses `wallet_manager.get_web3()` and `wallet_manager.get_symbol()` for dynamic RPC and display.

**Adding the network switcher to KV:**
```kv
BoxLayout:
    VantaButton:
        text: app.translations.get('ethereum')
        on_release: root.switch_network('ethereum')
    VantaButton:
        text: app.translations.get('polygon')
        on_release: root.switch_network('polygon')
```

**RPC URLs (configurable in `wallet_manager.py`):**
- Ethereum: `https://eth.llamarpc.com`
- Polygon: `https://polygon-rpc.com`

---

## 3. Analytics Dashboard

**File:** `main.py` (AnalyticsScreen, PriceChartBars)

**Behavior:**
- New **AnalyticsScreen** with mock data: Total Views (1,247), Sales Volume (0.42 ETH), Likes (89)
- **Price History** shown as colored bars (no external chart library)
- Uses the Vantablack theme

**Structure:**
- `AnalyticsScreen` – Screen with `views_count`, `sales_volume`, `likes_count` StringProperties
- `PriceChartBars` – Horizontal bar chart from `_BarWidget` instances
- `_BarWidget` – Single bar drawn with Kivy `Canvas`

**Adding to ScreenManager (kv_style.kv):**
```kv
<ScreenManager>:
    AnalyticsScreen:
        name: 'analytics'
```

**Adding tile on HomeScreen:**
```kv
VantaIconTile:
    id: analytics_tile
    text: app.translations.get('analytics')
    on_release: app.root.current = 'analytics'
```

**Translations:** Add keys `analytics`, `total_views`, `total_sales`, `likes`, `price_history` to `en.json` and `fa.json`.

---

## Dependencies

Add to `requirements.txt`:
```
plyer>=2.1.0
```

Install:
```bash
pip install plyer
```

---

## Testing

1. **Biometric:** On desktop, the PIN popup appears (plyer fingerprint is not available). Use PIN `1234` or Skip.
2. **Multi-Chain:** Switch networks in WalletScreen; balance and symbol should update.
3. **Analytics:** Open Analytics from Home; verify mock data and price bars.
