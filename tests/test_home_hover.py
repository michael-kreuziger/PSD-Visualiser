"""Exercise Home module links with real mouse and keyboard events."""

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QFont
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from psd_visualiser.app import MODULES, MainWindow


class HomeModuleInteractionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.app.setStyle("Fusion")
        cls.app.setFont(QFont("DejaVu Sans", 10))

    def setUp(self):
        self.window = MainWindow()
        self.window.show()
        self.app.processEvents()
        self.home = self.window.pages["home"]

    def tearDown(self):
        self.window.close()
        self.window.deleteLater()
        self.app.processEvents()

    def test_module_links_stay_text_sized_and_use_normal_cursor(self):
        for width in (1024, 1280):
            self.window.resize(width, 720)
            self.app.processEvents()
            for button in self.home.module_buttons:
                with self.subTest(width=width, module=button.text()):
                    self.assertTrue(button.font().underline())
                    self.assertLess(button.width(), self.home.viewport().width() / 2)
                    self.assertLessEqual(button.width(), button.sizeHint().width() + 2)
                    QTest.mouseMove(button, button.rect().center())
                    self.app.processEvents()
                    hovered = QApplication.widgetAt(button.mapToGlobal(button.rect().center()))
                    self.assertIs(hovered, button)
                    self.assertEqual(hovered.cursor().shape(), Qt.CursorShape.ArrowCursor)

    def test_hover_shades_only_the_text_sized_button(self):
        button = self.home.module_buttons[0]
        empty = QPoint(self.home.viewport().width() - 20,
                       self.home.viewport().height() - 20)
        QTest.mouseMove(self.home.viewport(), empty)
        self.app.processEvents()
        before = button.grab().toImage()
        # This point lies inside the top padding, away from text and focus borders.
        sample = QPoint(before.width() // 2, round(2 * before.devicePixelRatio()))
        self.assertEqual(before.pixelColor(sample).name(), "#ffffff")
        QTest.mouseMove(button, button.rect().center())
        self.app.processEvents()
        after = button.grab().toImage()
        self.assertEqual(after.pixelColor(sample).name(), "#eeeeee")

        content = self.home.widget()
        beside = button.mapTo(content, QPoint(button.width() + 20, button.height() // 2))
        image = content.grab().toImage()
        beside *= image.devicePixelRatio()
        self.assertEqual(image.pixelColor(beside).name(), "#ffffff")

    def test_mouse_click_and_focused_enter_open_each_module(self):
        for button, module in zip(self.home.module_buttons, MODULES):
            with self.subTest(module=module.key, activation="mouse"):
                QTest.mouseClick(button, Qt.MouseButton.LeftButton)
                self.app.processEvents()
                self.assertEqual(self.window.current_key, module.key)
                self.window.show_page("home")
                self.app.processEvents()
            with self.subTest(module=module.key, activation="enter"):
                button.setFocus(Qt.FocusReason.TabFocusReason)
                self.app.processEvents()
                self.assertTrue(button.hasFocus())
                QTest.keyClick(button, Qt.Key.Key_Return)
                self.app.processEvents()
                self.assertEqual(self.window.current_key, module.key)
                self.window.show_page("home")
                self.app.processEvents()


if __name__ == "__main__":
    unittest.main()
