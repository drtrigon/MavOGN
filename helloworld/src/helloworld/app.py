"""
My first application
"""

import toga
from toga.style.pack import COLUMN, ROW

import helloworld.mavlink_adsb_emulator_ogn_udp_injection as external
import threading
import traceback
import time

HINT = \
"""Energy Saving: Muss AUSgeschaltet werden damit diese App funktioniert!

Notification/Popup: "SpeedyBee eFLY-WIFI hat kein internetzugriff"
          Ja -> WIFI wird Internet Gateway -> kein Internet mehr
        Nein -> WIFI Verbindung wird beendet
  Ignorieren -> WIFI & Mobile bleibt bestehen, Gateway bleibt Mobile
                MAVLink down (Telemetrie) OK, up (Params, Missions) NOT OK
"""


class HelloWorld(toga.App):
    def startup(self):
        """Construct and show the Toga application.

        Usually, you would add your application to a main content box.
        We then create a main window (with a name matching the app), and
        show the main window.
        """
        main_box = toga.Box(direction=COLUMN)

        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = main_box
        self.main_window.show()

        button = toga.Button(
            "start",
            on_press=self.say_hello,
            margin=10,
        )
        button2 = toga.Button(
            "stopp",
            on_press=self.bye,
            margin=10,
        )

        main_box.add(button)
        main_box.add(button2)

        self.label = toga.Label("ready", margin=10)
        main_box.add(self.label)

        self.multiline = toga.MultilineTextInput(value=HINT, readonly=True)#, style=toga.style.Pack(height=200))
        main_box.add(self.multiline)

        self.t = threading.Thread()

    def say_hello(self, widget):
        #print(f"Hello, {self.name_input.value}")
        if self.t.is_alive():
            return
        external.__exception = None
        self.t = threading.Thread(target=external.main)
        self.t.start()
        self.label.text = "running"
#        self.update()
        self.timer = threading.Timer(1., self.update)  # WORK-A-ROUND: ANDROID (instead of call_later)
        self.timer.start()

    def bye(self, widget):
        external.__kill = True
        self.t.join()
        del external.__kill

    def update(self):
        if external.__exception:
            self.label.text = f"{time.asctime()} : {traceback.format_exception(external.__exception)[-1].strip()}"
            external.__exception = None
        if self.t.is_alive():
#            self.loop.call_later(1., self.update)  # DOES NOT WORK ON ANDROID
            self.timer.run()
        else:
            self.label.text = "ready"

def main():
    return HelloWorld()
