# ===========================================================
# Vanta NFT Art Platform - Optimized Version
# ===========================================================
from kivy.config import Config
Config.set('graphics', 'width', '1024')
Config.set('graphics', 'height', '768')
Config.set('graphics', 'window_state', 'maximized')

import os
os.environ['KIVY_NO_CONSOLELOG'] = '0'

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition, FadeTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Rectangle, Line, Color, RoundedRectangle
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.factory import Factory
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.core.clipboard import Clipboard
from kivy.properties import ListProperty, StringProperty, ObjectProperty

import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable

# App modules
from wallet_manager import wallet_manager, NETWORKS
from ipfs_manager import ipfs_manager
from nft_contract import get_contract_manager
from utils import ErrorHandler, log_execution

# Theme
Window.clearcolor = (0.02, 0.02, 0.05, 1)


# ===========================================================
# KV Styles
# ===========================================================
Builder.load_string('''
<NeonButton@Button>:
    background_color: 0, 0, 0, 0
    canvas.before:
        Color:
            rgba: 0, 1, 1, 0.3
        Line:
            width: 1.5
            rounded_rectangle: self.x, self.y, self.width, self.height, 12, 12, 12, 12
    color: 0, 1, 1, 1
    font_size: '16sp'
    bold: True
    
<NeonButtonPrimary@NeonButton>:
    canvas.before:
        Color:
            rgba: 0.8, 0, 1, 0.4
        Line:
            width: 2
            rounded_rectangle: self.x, self.y, self.width, self.height, 12, 12, 12, 12
    color: 1, 0.5, 1, 1

<CyberCard@ButtonBehavior+BoxLayout>:
    orientation: 'vertical'
    size_hint: None, None
    size: 160, 160
    canvas.before:
        Color:
            rgba: 0.05, 0.05, 0.1, 0.9
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [16, 16, 16, 16]
        Color:
            rgba: 1, 0, 1, 0.4
        Line:
            width: 1.5
            rounded_rectangle: self.x, self.y, self.width, self.height, 16, 16, 16, 16
    Label:
        id: icon_label
        font_size: '50sp'
        color: 1, 1, 1, 1
        size_hint_y: 0.6
    Label:
        id: text_label
        font_size: '16sp'
        color: 0.8, 0.9, 1, 1
        size_hint_y: 0.4
        bold: True

<BackBtn@Button>:
    text: '← Back'
    background_color: 0, 0, 0, 0
    canvas.before:
        Color:
            rgba: 1, 0.3, 0.3, 0.5
        Line:
            width: 1.5
            rounded_rectangle: self.x, self.y, self.width, self.height, 8, 8, 8, 8
    color: 1, 0.4, 0.4, 1
    size_hint: None, None
    size: 90, 40
    font_size: '14sp'

<GlassBar@BoxLayout>:
    canvas.before:
        Color:
            rgba: 0.08, 0.08, 0.12, 0.95
        Rectangle:
            pos: self.pos
            size: self.size

<CyberInput@TextInput>:
    background_color: 0.05, 0.05, 0.1, 1
    foreground_color: 0, 1, 1, 1
    cursor_color: 0, 1, 1, 1
    padding: [12, 10]
    font_size: '14sp'
    multiline: False
    background_normal: ''
    background_active: ''

<InfoCard@BoxLayout>:
    orientation: 'vertical'
    size_hint_y: None
    height: 80
    padding: 15
    canvas.before:
        Color:
            rgba: 0.06, 0.06, 0.1, 1
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [10, 10, 10, 10]
''')


# ===========================================================
# Paint Widget
# ===========================================================
class PaintWidget(Widget):
    line_color = ListProperty([0.8, 0.0, 1.0, 1])
    line_width = 4
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self._update_bg, size=self._update_bg)
        self._update_bg()
    
    def _update_bg(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(0.03, 0.03, 0.05, 1)
            Rectangle(pos=self.pos, size=self.size)
    
    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return False
        
        with self.canvas:
            Color(*self.line_color)
            touch.ud['line'] = Line(
                points=[touch.x, touch.y],
                width=self.line_width,
                cap='round',
                joint='round'
            )
        return True
    
    def on_touch_move(self, touch):
        if 'line' in touch.ud:
            touch.ud['line'].points += [touch.x, touch.y]
    
    def clear_canvas(self):
        self.canvas.clear()
        self._update_bg()
    
    def export(self, filename: str) -> bool:
        """Export to PNG"""
        try:
            self.export_to_png(filename)
            return True
        except Exception as e:
            print(f"Export error: {e}")
            return False


# ===========================================================
# Base Screen
# ===========================================================
class BaseScreen(Screen):
    """Base screen with common functionality"""
    
    def show_loading(self, message: str = "Loading..."):
        self._popup = Popup(
            title='',
            content=Label(text=message, color=(0, 1, 1, 1)),
            size_hint=(0.4, 0.2),
            background_color=(0.05, 0.05, 0.1, 0.9),
            auto_dismiss=False
        )
        self._popup.open()
        return self._popup
    
    def hide_loading(self):
        if hasattr(self, '_popup') and self._popup:
            self._popup.dismiss()
    
    def show_error(self, message: str):
        ErrorHandler.show_error_popup(self, message)
    
    def animate_entry(self, widgets, delay=0.1):
        """Animate widgets on screen entry"""
        for i, widget in enumerate(widgets):
            widget.opacity = 0
            anim = Animation(opacity=1, duration=0.4, t='out_cubic')
            anim.start(widget)
            Clock.schedule_once(lambda dt, a=anim: a.start(widget), i * delay)


# ===========================================================
# Home Screen
# ===========================================================
class HomeScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'home'
        self._build_ui()
    
    def _build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=25, spacing=20)
        
        # Header
        header = Label(
            text='[b]VANTA[/b]\n[size=20]NFT ART STUDIO[/size]',
            font_size='48sp',
            color=(0, 1, 1, 1),
            markup=True,
            size_hint=(1, 0.25),
            halign='center'
        )
        
        # Grid
        grid = GridLayout(cols=2, spacing=20, size_hint=(1, 0.6), padding=20)
        
        cards = [
            ('🎨', 'Create', 'paint'),
            ('💎', 'Market', 'sell'),
            ('👛', 'Wallet', 'wallet'),
            ('⚙️', 'Settings', None),
        ]
        
        for icon, text, screen in cards:
            card = Factory.CyberCard()
            card.ids.icon_label.text = icon
            card.ids.text_label.text = text
            if screen:
                card.bind(on_press=lambda x, s=screen: self._navigate(s))
            grid.add_widget(card)
        
        # Footer
        footer = Label(
            text=f'Network: {wallet_manager.current_network.upper()}',
            color=(0.5, 0.5, 0.6, 1),
            font_size='12sp',
            size_hint=(1, 0.1)
        )
        
        layout.add_widget(header)
        layout.add_widget(grid)
        layout.add_widget(footer)
        self.add_widget(layout)
        self._grid_widgets = list(grid.children)
    
    def _navigate(self, screen_name: str):
        self.manager.transition = SlideTransition(direction='left')
        self.manager.current = screen_name
    
    def on_enter(self):
        Clock.schedule_once(lambda dt: self.animate_entry(self._grid_widgets), 0.1)


# ===========================================================
# Paint Screen
# ===========================================================
class PaintScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'paint'
        self._build_ui()
    
    def _build_ui(self):
        layout = BoxLayout(orientation='vertical')
        
        # Toolbar
        toolbar = Factory.GlassBar(size_hint=(1, 0.08), padding=10, spacing=10)
        
        back_btn = Factory.BackBtn(on_press=lambda x: self._go_back())
        title = Label(text='Create Art', font_size='18sp', bold=True, color=(1,1,1,1))
        
        toolbar.add_widget(back_btn)
        toolbar.add_widget(title)
        
        # Paint area
        self.paint_area = PaintWidget(size_hint=(1, 0.75))
        
        # Color palette
        palette = BoxLayout(size_hint=(1, 0.05), spacing=3, padding=5)
        colors = [
            (1, 0, 0, 1), (0, 1, 0, 1), (0, 0, 1, 1),
            (1, 1, 0, 1), (1, 0, 1, 1), (0, 1, 1, 1),
            (1, 1, 1, 1), (0.8, 0, 1, 1), (0, 0, 0, 1)
        ]
        for color in colors:
            btn = Button(
                background_color=color,
                on_press=lambda x, c=color: setattr(self.paint_area, 'line_color', c)
            )
            palette.add_widget(btn)
        
        # Bottom controls
        controls = BoxLayout(size_hint=(1, 0.12), padding=10, spacing=10)
        
        clear_btn = Factory.NeonButton(text='Clear', on_press=lambda x: self.paint_area.clear_canvas())
        self.save_btn = Factory.NeonButtonPrimary(text='Save & Mint', on_press=self._save_and_mint)
        
        controls.add_widget(clear_btn)
        controls.add_widget(self.save_btn)
        
        layout.add_widget(toolbar)
        layout.add_widget(self.paint_area)
        layout.add_widget(palette)
        layout.add_widget(controls)
        self.add_widget(layout)
    
    def _go_back(self):
        self.manager.transition = SlideTransition(direction='right')
        self.manager.current = 'home'
    
    @log_execution
    def _save_and_mint(self, instance):
        """Handle save and mint flow"""
        if self.save_btn.text != "Save & Mint":
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"vanta_art_{timestamp}.png"
        
        self.save_btn.text = "Saving..."
        
        if not self.paint_area.export(filename):
            self.show_error("Failed to save image")
            self.save_btn.text = "Save & Mint"
            return
        
        self.save_btn.text = "Uploading..."
        
        def upload_step():
            image_uri = ipfs_manager.upload_image(filename)
            if not image_uri:
                Clock.schedule_once(lambda dt: self._on_error("IPFS upload failed"), 0)
                return
            
            metadata = ipfs_manager.create_metadata(
                name=f"Vanta Art #{timestamp}",
                description=f"Created on {timestamp}",
                image_uri=image_uri,
                attributes=[
                    {"trait_type": "Tool", "value": "Vanta Studio"},
                    {"trait_type": "Date", "value": timestamp}
                ]
            )
            
            metadata_uri = ipfs_manager.upload_metadata(metadata)
            if not metadata_uri:
                Clock.schedule_once(lambda dt: self._on_error("Metadata upload failed"), 0)
                return
            
            Clock.schedule_once(lambda dt: self._mint_nft(metadata_uri, filename, timestamp), 0)
        
        from threading import Thread
        Thread(target=upload_step, daemon=True).start()
    
    def _mint_nft(self, metadata_uri: str, filename: str, timestamp: str):
        """Mint NFT on blockchain"""
        self.save_btn.text = "Minting..."
        
        contract_mgr = get_contract_manager(wallet_manager)
        result = contract_mgr.mint_nft(metadata_uri)
        
        if not result:
            self._on_error("Minting failed")
            return
        
        self._save_nft_record(result, metadata_uri, filename, timestamp)
        
        self.save_btn.text = f"✓ Minted #{result['token_id'][:6]}"
        Clock.schedule_once(lambda dt: setattr(self.save_btn, 'text', 'Save & Mint'), 3)
    
    def _save_nft_record(self, result: dict, metadata_uri: str, filename: str, timestamp: str):
        """Save NFT to local database"""
        record = {
            'token_id': result['token_id'],
            'tx_hash': result['tx_hash'],
            'contract': result.get('contract', 'unknown'),
            'metadata_uri': metadata_uri,
            'image_file': filename,
            'created_at': timestamp,
            'network': wallet_manager.current_network
        }
        
        db_file = Path('my_nfts.json')
        try:
            nfts = json.loads(db_file.read_text()) if db_file.exists() else []
        except:
            nfts = []
        
        nfts.insert(0, record)
        db_file.write_text(json.dumps(nfts, indent=2))
    
    def _on_error(self, message: str):
        self.show_error(message)
        self.save_btn.text = "Save & Mint"


# ===========================================================
# Sell/Market Screen
# ===========================================================
class SellScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'sell'
        self._build_ui()
    
    def _build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=15, spacing=10)
        
        toolbar = Factory.GlassBar(size_hint=(1, 0.08), padding=10)
        toolbar.add_widget(Factory.BackBtn(on_press=lambda x: self._go_back()))
        toolbar.add_widget(Label(text='Your Collection', font_size='18sp', bold=True, color=(1,1,1,1)))
        
        self.nft_container = BoxLayout(orientation='vertical', spacing=10, size_hint_y=None)
        self.nft_container.bind(minimum_height=self.nft_container.setter('height'))
        
        scroll = ScrollView(size_hint=(1, 0.82))
        scroll.add_widget(self.nft_container)
        
        controls = BoxLayout(size_hint=(1, 0.1), spacing=10)
        refresh_btn = Factory.NeonButton(text='↻ Refresh', on_press=lambda x: self._load_nfts())
        list_btn = Factory.NeonButtonPrimary(text='List New NFT', on_press=lambda x: None)
        
        controls.add_widget(refresh_btn)
        controls.add_widget(list_btn)
        
        layout.add_widget(toolbar)
        layout.add_widget(scroll)
        layout.add_widget(controls)
        self.add_widget(layout)
    
    def _go_back(self):
        self.manager.transition = SlideTransition(direction='right')
        self.manager.current = 'home'
    
    def on_enter(self):
        self._load_nfts()
    
    def _load_nfts(self):
        """Load and display NFTs"""
        self.nft_container.clear_widgets()
        
        try:
            db_file = Path('my_nfts.json')
            if not db_file.exists():
                self._show_empty()
                return
            
            nfts = json.loads(db_file.read_text())
            if not nfts:
                self._show_empty()
                return
            
            for nft in nfts:
                card = self._create_nft_card(nft)
                self.nft_container.add_widget(card)
                
        except Exception as e:
            print(f"Load NFTs error: {e}")
            self._show_empty()
    
    def _create_nft_card(self, nft: dict):
        """Create NFT card widget"""
        card = Factory.InfoCard()
        
        title_row = BoxLayout(size_hint_y=0.4)
        title_row.add_widget(Label(
            text=f"#{nft.get('token_id', '???')[:10]}...",
            color=(0, 1, 1, 1),
            font_size='16sp',
            bold=True,
            halign='left'
        ))
        title_row.add_widget(Label(
            text=nft.get('network', 'unknown').upper(),
            color=(0.5, 0.8, 1, 1),
            font_size='12sp',
            halign='right'
        ))
        
        details = Label(
            text=f"Tx: {nft.get('tx_hash', '???')[:16]}...\n{nft.get('created_at', 'Unknown date')}",
            color=(0.6, 0.6, 0.7, 1),
            font_size='11sp',
            halign='left',
            size_hint_y=0.6
        )
        
        card.add_widget(title_row)
        card.add_widget(details)
        return card
    
    def _show_empty(self):
        self.nft_container.add_widget(Label(
            text='No NFTs yet\nCreate your first artwork!',
            color=(0.5, 0.5, 0.6, 1),
            font_size='16sp',
            halign='center'
        ))


# ===========================================================
# Wallet Screen
# ===========================================================
class WalletScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'wallet'
        self._build_ui()
        wallet_manager.add_listener(self._on_wallet_update)
    
    def _build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        toolbar = Factory.GlassBar(size_hint=(1, 0.08), padding=10)
        toolbar.add_widget(Factory.BackBtn(on_press=lambda x: self._go_back()))
        toolbar.add_widget(Label(text='Wallet', font_size='18sp', bold=True, color=(1,1,1,1)))
        
        card = BoxLayout(orientation='vertical', size_hint=(1, 0.5), spacing=15, padding=20)
        with card.canvas.before:
            Color(0.05, 0.05, 0.08, 1)
            self.card_rect = RoundedRectangle(pos=card.pos, size=card.size, radius=[20, 20, 20, 20])
            Color(1, 0.4, 0.8, 0.3)
            Line(rounded_rectangle=(card.x, card.y, card.width, card.height, 20, 20, 20, 20), width=2)
        card.bind(pos=self._update_card, size=self._update_card)
        
        self.balance_label = Label(
            text='0.0000 ETH',
            font_size='42sp',
            bold=True,
            color=(1, 0.4, 0.8, 1)
        )
        
        # ⬇️ اصلاح شده - بدون font_name
        self.addr_label = Label(
            text='No wallet',
            font_size='13sp',
            color=(0.6, 0.7, 0.8, 1)
        )
        
        actions = BoxLayout(spacing=10, size_hint_y=0.4)
        
        copy_btn = Factory.NeonButton(text='Copy', on_press=self._copy_address)
        import_btn = Factory.NeonButton(text='Import', on_press=self._show_import)
        refresh_btn = Factory.NeonButton(text='↻', on_press=lambda x: self._refresh(), size_hint=(0.3, 1))
        
        actions.add_widget(copy_btn)
        actions.add_widget(import_btn)
        actions.add_widget(refresh_btn)
        
        self.net_btn = Factory.NeonButton(
            text=f"⛓ {wallet_manager.current_network.upper()}",
            on_press=self._switch_network
        )
        
        card.add_widget(Label(text='BALANCE', color=(0.5, 0.5, 0.6, 1), font_size='12sp', size_hint_y=0.15))
        card.add_widget(self.balance_label)
        card.add_widget(self.addr_label)
        card.add_widget(actions)
        card.add_widget(self.net_btn)
        
        history = BoxLayout(orientation='vertical', size_hint=(1, 0.4))
        history.add_widget(Label(text='Recent Activity', color=(0, 1, 1, 1), font_size='16sp', bold=True))
        history.add_widget(Label(text='No transactions', color=(0.5, 0.5, 0.6, 1)))
        
        layout.add_widget(toolbar)
        layout.add_widget(card)
        layout.add_widget(history)
        self.add_widget(layout)
    
    def _update_card(self, instance, value):
        self.card_rect.pos = instance.pos
        self.card_rect.size = instance.size
    
    def _go_back(self):
        self.manager.transition = SlideTransition(direction='right')
        self.manager.current = 'home'
    
    def on_enter(self):
        self._refresh()
    
    def _refresh(self):
        addr = wallet_manager.address
        self.addr_label.text = wallet_manager.get_short_address(8) if addr else "No wallet"
        
        balance = wallet_manager.get_balance()
        symbol = wallet_manager.get_network_config().symbol
        self.balance_label.text = f"{balance:.4f} {symbol}"
    
    def _on_wallet_update(self):
        Clock.schedule_once(lambda dt: self._refresh(), 0)
    
    def _copy_address(self, instance):
        if wallet_manager.address:
            Clipboard.copy(wallet_manager.address)
            instance.text = "✓"
            Clock.schedule_once(lambda dt: setattr(instance, 'text', 'Copy'), 1.5)
    
    def _switch_network(self, instance):
        current = wallet_manager.current_network
        networks = list(NETWORKS.keys())
        idx = networks.index(current)
        next_net = networks[(idx + 1) % len(networks)]
        
        if wallet_manager.set_network(next_net):
            self.net_btn.text = f"⛓ {next_net.upper()}"
            self._refresh()
    
    def _show_import(self, instance):
        content = BoxLayout(orientation='vertical', spacing=10, padding=15)
        
        content.add_widget(Label(text='Enter Private Key:', color=(1,1,1,1), halign='left'))
        
        key_input = Factory.CyberInput(password=True)
        content.add_widget(key_input)
        
        warning = Label(
            text='⚠️ Never share your private key with anyone!',
            color=(1, 0.4, 0.4, 1),
            font_size='11sp'
        )
        content.add_widget(warning)
        
        btn_box = BoxLayout(spacing=10, size_hint_y=0.4)
        
        popup = Popup(
            title='Import Wallet',
            content=content,
            size_hint=(0.85, 0.45),
            background_color=(0.05, 0.05, 0.1, 0.95)
        )
        
        def do_import(btn):
            pk = key_input.text.strip()
            if pk.startswith('0x'):
                pk = pk[2:]
            
            try:
                from eth_account import Account
                account = Account.from_key(pk)
                
                data = {"private_key": account.key.hex(), "address": account.address}
                Path('vanta_wallet.json').write_text(json.dumps(data))
                
                global wallet_manager
                wallet_manager = WalletManager()
                wallet_manager.add_listener(self._on_wallet_update)
                
                popup.dismiss()
                self._refresh()
                
            except Exception as e:
                ErrorHandler.show_error_popup(self, f"Invalid key: {e}")
        
        btn_box.add_widget(Factory.NeonButton(text='Cancel', on_press=popup.dismiss))
        btn_box.add_widget(Factory.NeonButtonPrimary(text='Import', on_press=do_import))
        
        content.add_widget(btn_box)
        popup.open()


# ===========================================================
# App
# ===========================================================
class VantaApp(App):
    def build(self):
        sm = ScreenManager(transition=FadeTransition(duration=0.2))
        sm.add_widget(HomeScreen())
        sm.add_widget(PaintScreen())
        sm.add_widget(SellScreen())
        sm.add_widget(WalletScreen())
        return sm


if __name__ == '__main__':
    VantaApp().run()