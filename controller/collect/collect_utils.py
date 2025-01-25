from pynput import mouse, keyboard


class MouseKeyboardListener:
    """
    监听鼠标键盘事件，
    应用类可继承并重写 `on_mouse_move`, `on_mouse_click`, `on_mouse_scroll` 方法以实现自定义监听。"""
    def __init__(self, hotkey="Q", verbose=False):
        self.hotkey = hotkey
        self.verbose = verbose
        self.stop_listening = False
        self.mouse_listener = None
        self.keyboard_listener = None

    def on_mouse_move(self, x, y):
        if self.verbose:
            print(f'Mouse moved to ({x}, {y})')

    def on_mouse_click(self, x, y, button, pressed):
        if self.verbose:
            if pressed:
                print(f'Mouse clicked at ({x}, {y}) with {button}')
            else:
                print(f'Mouse released at ({x}, {y}) with {button}')

    def on_mouse_scroll(self, x, y, dx, dy):
        if self.verbose:
            print(f'Mouse scrolled at ({x}, {y})({dx}, {dy})')

    def _on_move(self, x, y):
        if not self.stop_listening:
            self.on_mouse_move(x, y)

    def _on_click(self, x, y, button, pressed):
        if not self.stop_listening:
            self.on_mouse_click(x, y, button, pressed)

    def _on_scroll(self, x, y, dx, dy):
        if not self.stop_listening:
            self.on_mouse_scroll(x, y, dx, dy)

    def on_keyboard_press(self, key):
        print("Keyboard Press", key)
        try:
            if hasattr(key, "char") and key.char == self.hotkey:
                print(f"{key.char=} {self.hotkey=}")
                self.stop_listening = True
                print("Exiting program...")
                return False  # 返回 False 停止监听
        except AttributeError:
            import traceback
            traceback.print_exc()
            print("break", key)
            self.stop_listening = True
            return False

            if all(getattr(keyboard.Key, mod) == key for mod in self.hotkey):
                self.stop_listening = True
                print("Exiting program...")
                return False  # 返回 False 停止监听

    def on_keyboard_release(self, key):
        pass

    def start_listening(self):
        self.logger.info("MouseKeyboardListener Starting listening")
        self.mouse_listener = mouse.Listener(
            on_move=self._on_move,
            on_click=self._on_click,
            on_scroll=self._on_scroll)
        self.keyboard_listener = keyboard.Listener(
            on_press=self.on_keyboard_press,
            on_release=self.on_keyboard_release)

        self.mouse_listener.start()
        self.keyboard_listener.start()

        # 主循环，检查停止标志
        while not self.stop_listening:
            pass

        # 停止监听器
        self.mouse_listener.stop()
        self.keyboard_listener.stop()

# 使用示例
if __name__ == "__main__":
    listener = MouseKeyboardListener(hotkey="q")
    listener.start_listening()