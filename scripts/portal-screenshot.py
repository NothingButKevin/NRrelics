#!/usr/bin/env python3
"""Capture the visible SteamOS Gamescope frame through xdg-desktop-portal."""

from __future__ import annotations

import sys

import dbus
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib


def main() -> int:
    DBusGMainLoop(set_as_default=True)
    bus = dbus.SessionBus()
    portal = bus.get_object("org.freedesktop.portal.Desktop", "/org/freedesktop/portal/desktop")
    screenshot = dbus.Interface(portal, "org.freedesktop.portal.Screenshot")
    request = screenshot.Screenshot("", dbus.Dictionary({}, signature="sv"))
    result: dict[str, object] = {}
    loop = GLib.MainLoop()

    def response(code, values):
        result["code"] = int(code)
        result["uri"] = str(values.get("uri", ""))
        loop.quit()

    bus.add_signal_receiver(response, signal_name="Response", dbus_interface="org.freedesktop.portal.Request", path=request)
    GLib.timeout_add_seconds(10, loop.quit)
    loop.run()
    uri = result.get("uri", "")
    if result.get("code") != 0 or not uri.startswith("file://"):
        print("Portal screenshot failed or timed out", file=sys.stderr)
        return 1
    print(uri[7:])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
