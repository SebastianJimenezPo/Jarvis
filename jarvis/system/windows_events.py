import ctypes
from ctypes import wintypes
from PySide6.QtCore import QAbstractNativeEventFilter
from PySide6.QtWidgets import QWidget
from pycaw.callbacks import MMNotificationClient
from pycaw.pycaw import AudioUtilities


class EndpointNotifications(MMNotificationClient):
    def __init__(self, callback, follow_default):
        super().__init__()
        self.callback, self.follow_default = callback, follow_default

    def on_default_device_changed(self, flow, flow_id, role, role_id, default_device_id):
        if self.follow_default and flow_id == 1 and role_id == 0:
            self.callback("devices_changed")

    def on_device_added(self, device_id):
        self.callback("devices_changed")

    def on_device_removed(self, device_id):
        self.callback("devices_changed")

    def on_device_state_changed(self, device_id, state, state_id):
        self.callback("devices_changed")


class WindowsEvents(QAbstractNativeEventFilter):
    def __init__(self, app, callback, follow_default):
        super().__init__()
        self.app, self.callback = app, callback
        # Hidden top-level HWND receives power broadcasts even without a main window.
        self.window = QWidget()
        self.window.winId()
        self.enumerator = AudioUtilities.GetDeviceEnumerator()
        self.notifications = EndpointNotifications(callback, follow_default)
        self.enumerator.RegisterEndpointNotificationCallback(self.notifications)
        app.installNativeEventFilter(self)

    def nativeEventFilter(self, event_type, message):
        msg = wintypes.MSG.from_address(int(message))
        if msg.message == 0x218:  # WM_POWERBROADCAST
            if msg.wParam == 4:
                self.callback("suspend")
            elif msg.wParam in (7, 18):
                self.callback("power_resume")
        if msg.message == 0x11:  # WM_QUERYENDSESSION: release resources before session end
            self.callback("stop")
        return False, 0

    def close(self):
        self.app.removeNativeEventFilter(self)
        self.enumerator.UnregisterEndpointNotificationCallback(self.notifications)
        self.window.close()
