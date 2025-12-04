from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.lang import Builder
from kivy.properties import StringProperty, NumericProperty, DictProperty
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.utils import platform

from datetime import datetime
import os
import zipfile

try:
    # Пытаемся импортировать камеру plyer; на десктопе может отсутствовать
    from plyer import camera
except Exception:  # pragma: no cover - на некоторых платформах plyer может быть недоступен
    camera = None

if platform == "android":
    try:
        from android.storage import primary_external_storage_path
    except Exception:  # pragma: no cover
        primary_external_storage_path = None
else:
    primary_external_storage_path = None


class StartScreen(Screen):
    def next(self):
        name = self.ids.structure_name.text.strip()
        if name:
            self.manager.structure_name = name
            self.manager.transition.direction = "left"
            self.manager.current = "count"


class CountScreen(Screen):
    def next(self):
        try:
            self.manager.path_count = int(self.ids.path_count.text)
            self.manager.support_count = int(self.ids.support_count.text)
            self.manager.span_count = int(self.ids.span_count.text)
            self.manager.transition.direction = "left"
            self.manager.current = "navigation"
        except ValueError:
            pass

    def back(self):
        self.manager.transition.direction = "right"
        self.manager.current = "start"


class NavigationScreen(Screen):
    title = StringProperty("")
    status_message = StringProperty("")

    def on_pre_enter(self):
        self.title = f"Структура сооружения: {self.manager.structure_name}"
        layout = self.ids.sections
        layout.clear_widgets()

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
                element_name = f"{section_name} {i}"
                btn = Button(
                    text=element_name,
                    size_hint_y=None,
                    height=50,
                    background_normal='',
                    background_color=(0.2, 0.6, 0.9, 1),
                    on_press=lambda inst, name=element_name, sec=section_name: self.open_element(
                        name=name, section=sec
                    ),
                )
                box.add_widget(btn)
            scroll.add_widget(box)
            layout.add_widget(scroll)

    def open_element(self, name, section):
        # Инициализируем данные элемента в менеджере, если ещё не было
        if name not in self.manager.elements_data:
            self.manager.elements_data[name] = {
                "photos": [],
                "section": section,
            }
        else:
            # Обновляем информацию о разделе, если она пустая
            if not self.manager.elements_data[name].get("section"):
                self.manager.elements_data[name]["section"] = section
        # Проверяем, есть ли уже экран для этого элемента
        if not self.manager.has_screen(name):
            screen = ElementScreen(name=name)
            self.manager.add_widget(screen)
        self.manager.transition.direction = "left"
        self.manager.current = name

    def back(self):
        self.manager.transition.direction = "right"
        self.manager.current = "count"


class ElementScreen(Screen):
    """Экран конкретного элемента сооружения"""
    def on_pre_enter(self):
        self.ids.title_label.text = self.name
        self.update_photo_counter()

    def update_photo_counter(self):
        """Обновить счётчик фотографий на экране элемента."""
        data = self.manager.elements_data.get(self.name, {})
        photos = data.get("photos", [])
        if "photo_counter" in self.ids:
            self.ids.photo_counter.text = f"Фотографий: {len(photos)}"

    def _build_photo_path(self) -> str:
        """Сформировать путь для сохранения новой фотографии элемента."""
        app = App.get_running_app()
        base_dir = app.user_data_dir

        structure_name = self.manager.structure_name or "Сооружение"
        element_data = self.manager.elements_data.get(self.name, {})
        section = element_data.get("section") or "Прочее"

        target_dir = os.path.join(base_dir, structure_name, section, self.name)
        os.makedirs(target_dir, exist_ok=True)

        filename = datetime.now().strftime("photo_%Y%m%d_%H%M%S.jpg")
        return os.path.join(target_dir, filename)

    def add_photo(self):
        """Вызов системной камеры и сохранение фото для текущего элемента."""
        if camera is None:
            # На платформе без камеры просто игнорируем (для разработки на ПК)
            if "photo_counter" in self.ids:
                self.ids.photo_counter.text = "Камера недоступна на этой платформе"
            return

        file_path = self._build_photo_path()

        def _on_complete(path):
            # Обработчик завершения съёмки
            if path and os.path.exists(path):
                element = self.manager.elements_data.setdefault(self.name, {"photos": [], "section": ""})
                element.setdefault("photos", []).append(path)
                self.update_photo_counter()

        camera.take_picture(filename=file_path, on_complete=_on_complete)

    def back(self):
        self.manager.transition.direction = "right"
        self.manager.current = "navigation"


class BridgeManager(ScreenManager):
    structure_name = StringProperty("")
    path_count = NumericProperty(0)
    support_count = NumericProperty(0)
    span_count = NumericProperty(0)
    # Данные по элементам сооружения:
    # { "Мостовое полотно 1": {"photos": [<пути к файлам>], "section": "Мостовое полотно"}, ... }
    elements_data = DictProperty({})


class BridgeApp(App):
    def build(self):
        Builder.load_file("bridge.kv")
        return BridgeManager(transition=SlideTransition())

    def _get_downloads_dir(self) -> str:
        """Определить путь к папке Загрузки в зависимости от платформы."""
        # Android: основное внешнее хранилище + Download
        if platform == "android" and primary_external_storage_path:
            base = primary_external_storage_path()
            downloads_dir = os.path.join(base, "Download")
            os.makedirs(downloads_dir, exist_ok=True)
            return downloads_dir

        # Десктоп: папка Загрузки в домашнем каталоге или текущая директория
        home = os.path.expanduser("~")
        downloads_dir = os.path.join(home, "Downloads")
        if not os.path.isdir(downloads_dir):
            downloads_dir = os.getcwd()
        return downloads_dir

    def export_zip(self) -> str:
        """Сформировать ZIP с фотографиями и сохранить его в папку Загрузки.

        Возвращает человекочитаемое сообщение о результате операции (на русском).
        """
        manager = self.root
        structure_name = manager.structure_name or "Сооружение"

        if not manager.elements_data:
            return "Нет данных по элементам для экспорта."

        downloads_dir = self._get_downloads_dir()

        # Имя файла без недопустимых символов
        safe_name = "".join(ch for ch in structure_name if ch not in '\\/:*?"<>|')
        zip_filename = f"RZD_{safe_name}.zip"
        zip_path = os.path.join(downloads_dir, zip_filename)

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for element_name, data in manager.elements_data.items():
                photos = data.get("photos") or []
                if not photos:
                    continue

                section = data.get("section") or "Прочее"
                for photo_path in photos:
                    if not os.path.exists(photo_path):
                        continue
                    arcname = os.path.join(
                        safe_name,
                        section,
                        element_name,
                        os.path.basename(photo_path),
                    )
                    zipf.write(photo_path, arcname=arcname)

        return f"ZIP-файл сформирован и сохранён: {zip_path}"


if __name__ == "__main__":
    BridgeApp().run()
