from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.properties import StringProperty

class StartScreen(Screen):
    def next_screen(self):
        km = self.ids.km_input.text.strip()
        if km:
            self.manager.get_screen("count").km = km
            self.manager.current = "count"

class CountScreen(Screen):
    km = StringProperty()
    per = StringProperty()

    def create_buttons(self):
        try:
            supports = int(self.ids.supports_input.text)
            spans = int(self.ids.spans_input.text)
        except ValueError:
            return

        photo_screen = self.manager.get_screen("photo")
        photo_screen.build_buttons(supports, spans)
        photo_screen.km = self.km
        photo_screen.per = self.per
        self.manager.current = "photo"

class PhotoScreen(Screen):
    km = StringProperty()
    per = StringProperty()

    def build_buttons(self, supports, spans):
        layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=10)
        layout.bind(minimum_height=layout.setter('height'))

        for i in range(1, supports + 1):
            layout.add_widget(Button(text=f"Опора №{i}", size_hint_y=None, height=60, on_release=self.take_photo))
        for i in range(1, spans + 1):
            layout.add_widget(Button(text=f"Пролёт №{i}", size_hint_y=None, height=60, on_release=self.take_photo))

        scroll = ScrollView(size_hint=(1, 1))
        scroll.add_widget(layout)
        self.ids.container.clear_widgets()
        self.ids.container.add_widget(scroll)

    def take_photo(self, btn): 
        print(f"Сделано фото: {btn.text}")

class BridgeApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(StartScreen(name="start"))
        sm.add_widget(CountScreen(name="count"))
        sm.add_widget(PhotoScreen(name="photo"))
        return sm

if __name__ == "__main__":
    BridgeApp().run()

