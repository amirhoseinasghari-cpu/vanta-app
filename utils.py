"""
Vanta - Utilities
Helper functions and decorators
"""
import functools
import time
from typing import Callable, Any


def retry(max_attempts: int = 3, delay: float = 1.0):
    """Decorator for retrying failed operations"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise e
                    time.sleep(delay)
            return None
        return wrapper
    return decorator


def log_execution(func: Callable) -> Callable:
    """Decorator to log function execution"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print(f"▶️  {func.__name__} started")
        start = time.time()
        try:
            result = func(*args, **kwargs)
            print(f"✅ {func.__name__} done ({time.time()-start:.2f}s)")
            return result
        except Exception as e:
            print(f"❌ {func.__name__} failed: {e}")
            raise
    return wrapper


class ErrorHandler:
    """Centralized error handling"""
    
    @staticmethod
    def show_error_popup(parent, message: str, title: str = "Error"):
        from kivy.uix.popup import Popup
        from kivy.uix.label import Label
        from kivy.uix.button import Button
        from kivy.uix.boxlayout import BoxLayout
        
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        layout.add_widget(Label(text=message, color=(1, 0.4, 0.4, 1)))
        
        btn = Button(
            text='OK',
            size_hint=(1, 0.3),
            background_color=(0.2, 0.2, 0.3, 1)
        )
        
        popup = Popup(
            title=title,
            content=layout,
            size_hint=(0.7, 0.4),
            auto_dismiss=False
        )
        
        btn.bind(on_press=popup.dismiss)
        layout.add_widget(btn)
        popup.open()
    
    @staticmethod
    def safe_execute(func: Callable, default_return: Any = None, 
                     error_msg: str = "Operation failed"):
        """Execute function safely with error handling"""
        try:
            return func()
        except Exception as e:
            print(f"⚠️  {error_msg}: {e}")
            return default_return


class Cache:
    """Simple in-memory cache"""
    _cache = {}
    
    @classmethod
    def get(cls, key: str, default=None):
        return cls._cache.get(key, default)
    
    @classmethod
    def set(cls, key: str, value: Any, ttl: int = 300):
        cls._cache[key] = {
            'value': value,
            'expires': time.time() + ttl
        }
    
    @classmethod
    def clear_expired(cls):
        now = time.time()
        expired = [k for k, v in cls._cache.items() if v['expires'] < now]
        for k in expired:
            del cls._cache[k]