from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.lang import Builder
from kivy.properties import StringProperty, NumericProperty


class StartScreen(Screen):
    def next(self):
        name = self.ids.structure_name.text.strip()
        if name:
            self.manager.structure_name = name
            self.manager.current = "count"


class CountScreen(Screen):
    def next(self):
        try:
            self.manager.path_count = int(self.ids.path_count.text)
            self.manager.support_count = int(self.ids.support_count.text)
            self.manager.span_count = int(self.ids.span_count.text)
            self.manager.current = "navigation"
        except ValueError:
            pass


class NavigationScreen(Screen):
    title = StringProperty("")  # ← Добавили свойство для безопасного отображения названия

    def on_pre_enter(self):
        # Обновляем заголовок, когда экран активируется
        self.title = f"Структура сооружения: {self.manager.structure_name}"

        layout = self.ids.sections
        layout.clear_widgets()

        from kivy.uix.button import Button
        from kivy.uix.label import Label
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.scrollview import ScrollView

        sections = [
            ("Мостовое полотно", self.manager.path_count),
            ("Опоры", self.manager.support_count),
            ("Пролётные строения", self.manager.span_count)
        ]

        for section_name, count in sections:
            layout.add_widget(Label(text=section_name, font_size=20, size_hint_y=None, height=40))

            scroll = ScrollView(size_hint=(1, None), height=150)
            box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=5)
            box.bind(minimum_height=box.setter('height'))

            for i in range(1, count + 1):
                btn = Button(
                    text=f"{section_name} {i}",
                    size_hint_y=None,
                    height=50,
                    background_normal='',
                    background_color=(0.2, 0.6, 0.9, 1),
                )
                box.add_widget(btn)
            scroll.add_widget(box)
            layout.add_widget(scroll)


class BridgeManager(ScreenManager):
    structure_name = StringProperty("")
    path_count = NumericProperty(0)
    support_count = NumericProperty(0)
    span_count = NumericProperty(0)


class BridgeApp(App):
    def build(self):
        Builder.load_file("bridge.kv")
        return BridgeManager()


if __name__ == "__main__":
    BridgeApp().run()
