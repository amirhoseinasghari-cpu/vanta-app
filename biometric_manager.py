"""
Vanta - Biometric Authentication
Uses plyer for biometric verification with PIN fallback and skip option.
"""
from __future__ import annotations

from typing import Callable, Optional

try:
    from plyer import fingerprint
    PLYER_FINGERPRINT_AVAILABLE = hasattr(fingerprint, "authenticate")
except (ImportError, AttributeError):
    fingerprint = None
    PLYER_FINGERPRINT_AVAILABLE = False

# PIN for fallback (hashed in production; simulated for now)
FALLBACK_PIN = "1234"


class BiometricManager:
    """
    Handles biometric auth with graceful fallback.
    - Tries plyer fingerprint if available
    - Falls back to PIN input or Skip
    """

    def __init__(self) -> None:
        self._supported = PLYER_FINGERPRINT_AVAILABLE
        self._auth_popup = None

    @property
    def is_biometric_supported(self) -> bool:
        """Whether device supports biometric authentication."""
        return self._supported

    def request_auth(
        self,
        reason: str = "Authenticate to continue",
        on_success: Optional[Callable[[], None]] = None,
        on_fail: Optional[Callable[[str], None]] = None,
    ) -> None:
        """
        Request authentication. Calls on_success or on_fail.
        """
        from kivy.app import App
        app = App.get_running_app()
        if not app:
            if on_fail:
                on_fail("no_app")
            return

        def _on_success() -> None:
            if on_success:
                on_success()

        def _on_fail(msg: str = "failed") -> None:
            if on_fail:
                on_fail(msg)

        if self._supported and fingerprint:
            try:
                result = fingerprint.authenticate(title="Vanta", message=reason)
                if result:
                    _on_success()
                else:
                    _on_fail("biometric_failed")
            except Exception:
                self._show_pin_popup(reason, _on_success, _on_fail)
        else:
            self._show_pin_popup(reason, _on_success, _on_fail)

    def _show_pin_popup(
        self,
        reason: str,
        on_success: Callable[[], None],
        on_fail: Callable[[str], None],
    ) -> None:
        """Show PIN input popup with Skip option."""
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.button import Button
        from kivy.uix.label import Label
        from kivy.uix.popup import Popup
        from kivy.uix.textinput import TextInput

        content = BoxLayout(orientation="vertical", padding=20, spacing=15)
        content.add_widget(Label(text=reason, color=(1, 1, 1, 1)))
        pin_input = TextInput(
            multiline=False,
            password=True,
            hint_text="Enter PIN",
            size_hint_y=None,
            height=45,
            font_size=18,
        )
        content.add_widget(pin_input)
        btn_layout = BoxLayout(orientation="horizontal", size_hint_y=None, height=50, spacing=10)

        def _verify(_: object = None) -> None:
            if pin_input.text == FALLBACK_PIN:
                popup.dismiss()
                on_success()
            else:
                pin_input.text = ""
                pin_input.hint_text = "Wrong PIN, try again"

        def _skip(_: object = None) -> None:
            popup.dismiss()
            on_fail("skipped")

        btn_layout.add_widget(Button(text="Verify", background_color=(0.2, 0.2, 0.2, 1), on_release=_verify))
        btn_layout.add_widget(Button(text="Skip", background_color=(0.15, 0.15, 0.15, 1), on_release=_skip))
        content.add_widget(btn_layout)

        popup = Popup(
            title="Authentication",
            content=content,
            size_hint=(0.85, 0.4),
            separator_color=(0.2, 0.2, 0.2, 1),
        )
        popup.open()
        self._auth_popup = popup
