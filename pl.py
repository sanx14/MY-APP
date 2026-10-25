import os
import sys
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.videoplayer import VideoPlayer
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.properties import StringProperty
from kivy.utils import platform

# --- 1. VIDEO LIST ITEM UI ---
class VideoRow(RecycleDataViewBehavior, BoxLayout):
    text = StringProperty('')
    path = StringProperty('')

    def __init__(self, **kwargs):
        super(VideoRow, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = 70
        self.padding = [8, 4]
        self.spacing = 2
        with self.canvas.before:
            from kivy.graphics import Color, Rectangle
            self._row_color = Color(0.12, 0.12, 0.16, 1)
            self._row_rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_rect, pos=self._update_rect)
        self.label = Label(
            text=self.text,
            size_hint_y=None,
            height=30,
            halign='left',
            valign='middle',
            font_size='14sp',
            color=(1, 1, 1, 1),
        )
        self.label.bind(size=self._set_label_text_size)
        self.add_widget(self.label)
        self.bind(text=self._on_text)

    def _update_rect(self, *args):
        self._row_rect.size = self.size
        self._row_rect.pos = self.pos

    def _set_label_text_size(self, instance, size):
        instance.text_size = (self.width - 16, None)

    def _on_text(self, instance, value):
        self.label.text = value

    def refresh_view_attrs(self, rv, index, data):
        self.text = data.get('text', '')
        self.path = data.get('path', '')
        return super(VideoRow, self).refresh_view_attrs(rv, index, data)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            app = App.get_running_app()
            app.play_video(self.path)
            return True
        return super(VideoRow, self).on_touch_down(touch)


# --- 2. LIBRARY SCREEN (Video Scanner, Sort & Filter) ---
class LibraryScreen(Screen):
    def __init__(self, **kwargs):
        super(LibraryScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Title
        layout.add_widget(Label(text='SANX Player - Video Library', font_size='20sp', bold=True, size_hint_y=None, height=40))

        # Filter & Sort Control Bar
        filter_layout = BoxLayout(size_hint_y=None, height=40, spacing=10)
        
        btn_sort_date = Button(text='Sort: Newest', background_color=(0.1, 0.5, 0.9, 1))
        btn_sort_date.bind(on_press=self.sort_by_date)
        
        btn_sort_name = Button(text='Sort: Name', background_color=(0.2, 0.6, 0.8, 1))
        btn_sort_name.bind(on_press=self.sort_by_name)

        filter_layout.add_widget(btn_sort_date)
        filter_layout.add_widget(btn_sort_name)
        layout.add_widget(filter_layout)

        # RecycleView for Video List
        self.rv = RecycleView()
        self.rv.viewclass = 'VideoRow'
        self.rv.layout_manager = RecycleBoxLayout(orientation='vertical', default_size=(None, 65), default_size_hint=(1, None), size_hint_y=None)
        self.rv.add_widget(self.rv.layout_manager)
        self.rv.layout_manager.bind(minimum_height=self.rv.layout_manager.setter('height'))
        
        layout.add_widget(self.rv)
        self.add_widget(layout)

        self.video_data = []
        self.request_android_permissions()
        self.scan_device_videos()

    def request_android_permissions(self):
        # Runtime storage permission for Android (works on low & high API)
        if platform == 'android':
            try:
                from android.permissions import request_permissions, Permission
                request_permissions([
                    Permission.READ_EXTERNAL_STORAGE,
                    Permission.WRITE_EXTERNAL_STORAGE,
                ])
            except Exception:
                # Permission module not available; continue, paths will be checked at runtime
                pass

    def _android_storage_paths(self):
        """Return storage paths safe across low & high API Android devices."""
        paths = []
        if platform == 'android':
            try:
                from android.storage import primary_external_storage_path
                ext = primary_external_storage_path()
                if ext and os.path.exists(ext):
                    paths.append(ext)
            except Exception:
                pass
            # Legacy mount points (work on older/low API devices)
            for p in ['/sdcard', '/storage/emulated/0', '/mnt/sdcard']:
                if p not in paths and os.path.exists(p):
                    paths.append(p)
        # Common folders (only added if they exist)
        for folder in ['Download', 'Movies', 'DCIM', 'Videos']:
            for base in list(paths):
                cand = os.path.join(base, folder)
                if cand not in paths and os.path.exists(cand):
                    paths.append(cand)
        # App working directory (always available)
        cwd = os.getcwd()
        if cwd not in paths:
            paths.append(cwd)
        return paths

    def scan_device_videos(self):
        videos = []
        if platform == 'android':
            search_paths = self._android_storage_paths()
        else:
            search_paths = [
                '/sdcard/Download',
                '/sdcard/Movies',
                '/sdcard/DCIM',
                os.getcwd()
            ]

        video_extensions = ('.mp4', '.mkv', '.avi', '.mov', '.3gp', '.webm')

        for path in search_paths:
            if os.path.exists(path):
                for root, dirs, files in os.walk(path):
                    # Skip hidden/system dirs to keep scan fast on mobile
                    dirs[:] = [d for d in dirs if not d.startswith('.')]
                    for file in files:
                        if file.lower().endswith(video_extensions):
                            full_path = os.path.join(root, file)
                            try:
                                mtime = os.path.getmtime(full_path)
                            except Exception:
                                mtime = 0
                            videos.append({'path': full_path, 'name': file, 'mtime': mtime})

        # Default Sort: Newest / Last modified first
        videos.sort(key=lambda x: x['mtime'], reverse=True)
        self.video_data = videos
        self.update_rv_list()

    def update_rv_list(self):
        self.rv.data = [{'text': f"{v['name']}\n{v['path']}", 'path': v['path']} for v in self.video_data]

    def sort_by_date(self, instance):
        self.video_data.sort(key=lambda x: x['mtime'], reverse=True)
        self.update_rv_list()

    def sort_by_name(self, instance):
        self.video_data.sort(key=lambda x: x['name'].lower())
        self.update_rv_list()


# --- 3. VIDEO PLAYER SCREEN ---
class PlayerScreen(Screen):
    def __init__(self, **kwargs):
        super(PlayerScreen, self).__init__(**kwargs)
        self.player_layout = FloatLayout()
        self.add_widget(self.player_layout)
        self.player = None
        self.current_video_path = ''
        self.audio_track_index = 0  # Multi-audio track switcher index
        self.update_clock = None

    def load_video(self, video_path):
        self.current_video_path = video_path
        self.player_layout.clear_widgets()

        # Platform-safe video options.
        # mediacodec / framedrop / ast are ffpyplayer-specific and only apply on desktop.
        # On Android, keep options minimal so VideoPlayer works with the native provider
        # on both low-API and high-API devices (video will actually display).
        if platform == 'android':
            video_options = {
                'allow_stretch': True,
                'eos': 'loop',
            }
        else:
            # High-res & Heavy file rendering optimization (Hardware Acceleration via mediacodec & framedrop)
            video_options = {
                'allow_stretch': True,
                'eos': 'loop',
                'mediacodec': 1,
                'framedrop': True,
                'ast': str(self.audio_track_index),  # Multi-audio stream support (desktop)
            }

        self.player = VideoPlayer(
            source=video_path,
            state='play',
            options=video_options
        )
        self.player.size_hint = (1, 1)
        self.player_layout.add_widget(self.player)

        # --- CONTROLS OVERLAY LAYOUT ---
        self.controls = BoxLayout(
            orientation='vertical',
            size_hint=(0.95, 0.22),
            pos_hint={'center_x': 0.5, 'y': 0.03},
            spacing=8,
            padding=5
        )

        # 1. Timeline / Progress Bar (Interactive Seeking: Touch anywhere to jump time)
        self.progress_bar = Slider(
            min=0, max=100, value=0,
            size_hint_y=None, height=30
        )
        self.progress_bar.bind(on_touch_up=self.on_seek_slider)
        self.controls.add_widget(self.progress_bar)

        # 2. Buttons Layout (Back, << 14s, Play/Pause, 14s >>, Audio Track Switcher)
        btn_layout = BoxLayout(orientation='horizontal', spacing=8, size_hint_y=None, height=45)

        btn_back = Button(text='📁 List', background_color=(0.8, 0.2, 0.2, 0.85), font_size='14sp')
        btn_back.bind(on_press=lambda x: App.get_running_app().go_to_library())

        btn_rewind = Button(text='<< 14s', background_color=(0.1, 0.5, 0.9, 0.85), font_size='14sp')
        btn_rewind.bind(on_press=self.rewind_14s)

        self.btn_play = Button(text='Pause', background_color=(0.2, 0.8, 0.2, 0.85), font_size='14sp')
        self.btn_play.bind(on_press=self.toggle_play)

        btn_forward = Button(text='14s >>', background_color=(0.1, 0.5, 0.9, 0.85), font_size='14sp')
        btn_forward.bind(on_press=self.forward_14s)

        # Multi Audio Track Toggle Button
        self.btn_audio = Button(text=f'Audio: {self.audio_track_index + 1}', background_color=(0.6, 0.2, 0.8, 0.85), font_size='14sp')
        self.btn_audio.bind(on_press=self.toggle_audio_track)

        btn_layout.add_widget(btn_back)
        btn_layout.add_widget(btn_rewind)
        btn_layout.add_widget(self.btn_play)
        btn_layout.add_widget(btn_forward)
        btn_layout.add_widget(self.btn_audio)

        self.controls.add_widget(btn_layout)
        self.player_layout.add_widget(self.controls)

        # Auto-hide timer settings (3 seconds)
        self.controls_visible = True
        self.hide_event = None
        self.reset_hide_timer()

        # Timeline progress sync clock
        if self.update_clock:
            Clock.unschedule(self.update_clock)
        self.update_clock = Clock.schedule_interval(self.update_progress, 0.5)

    def update_progress(self, dt):
        if self.player and self.player.duration > 0 and self.player.state == 'play':
            self.progress_bar.max = self.player.duration
            if not self.progress_bar.touch_control:
                self.progress_bar.value = self.player.position

    def on_seek_slider(self, instance, touch):
        if instance.collide_point(*touch.pos):
            if self.player and self.player.duration > 0:
                # User touch pannura edathukku video timeline seek/jump aagum
                self.player.position = self.progress_bar.value
            return True
        return False

    def on_touch_down(self, touch):
        # Screen la touch panna controls show aagum & timer reset aagum
        if self.collide_point(*touch.pos):
            self.show_controls()
            self.reset_hide_timer()
        return super(PlayerScreen, self).on_touch_down(touch)

    def reset_hide_timer(self):
        if self.hide_event:
            Clock.unschedule(self.hide_event)
        # 3 seconds ku apram controls hide aagum
        self.hide_event = Clock.schedule_once(self.hide_controls, 3.0)

    def hide_controls(self, dt=None):
        if self.controls_visible:
            anim = Animation(opacity=0, duration=0.4)
            anim.start(self.controls)
            self.controls_visible = False

    def show_controls(self):
        if not self.controls_visible:
            anim = Animation(opacity=1, duration=0.3)
            anim.start(self.controls)
            self.controls_visible = True

    def rewind_14s(self, instance):
        if self.player and self.player.duration > 0:
            self.player.position = max(0.0, self.player.position - 14.0)

    def forward_14s(self, instance):
        if self.player and self.player.duration > 0:
            self.player.position = min(self.player.duration, self.player.position + 14.0)

    def toggle_play(self, instance):
        if self.player:
            if self.player.state == 'play':
                self.player.state = 'pause'
                self.btn_play.text = 'Play'
            else:
                self.player.state = 'play'
                self.btn_play.text = 'Pause'

    def toggle_audio_track(self, instance):
        # Switch audio stream index (0 -> 1 -> 0)
        self.audio_track_index = 1 if self.audio_track_index == 0 else 0
        self.btn_audio.text = f'Audio: {self.audio_track_index + 1}'
        current_pos = self.player.position if self.player else 0
        self.load_video(self.current_video_path)
        if self.player:
            self.player.position = current_pos


# --- 4. MAIN APP CONTROLLER ---
class SANXPlayerApp(App):
    def build(self):
        self.title = 'SANX Player'
        self.sm = ScreenManager()
        
        self.library_screen = LibraryScreen(name='library')
        self.player_screen = PlayerScreen(name='player')
        
        self.sm.add_widget(self.library_screen)
        self.sm.add_widget(self.player_screen)

        # File Manager external open intent check
        if len(sys.argv) > 1:
            file_path = sys.argv[1]
            if os.path.exists(file_path):
                Clock.schedule_once(lambda dt: self.play_video(file_path), 0.5)

        return self.sm

    def play_video(self, path):
        self.player_screen.load_video(path)
        self.sm.current = 'player'

    def go_to_library(self):
        if self.player_screen.player:
            self.player_screen.player.state = 'stop'
        self.sm.current = 'library'


if __name__ == '__main__':
    SANXPlayerApp().run()