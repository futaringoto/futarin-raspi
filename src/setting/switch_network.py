from subprocess import run

from enum import Enum


class Mode(Enum):
    AP = 1
    CLIENT = 2


def ap():
    run(["sudo", "systemctl", "stop", "systemd-networkd"])
    run(["sudo", "systemctl", "stop", "systemd-networkd.socket"])
    run(["sudo", "systemctl", "stop", "systemd-resolved"])

    run(["sudo", "ip", "addr", "add", "192.168.222.1", "dev", "wlan0"])
    run(
        [
            "sudo",
            "ip",
            "route",
            "add",
            "default",
            "via",
            "192.168.222.1",
            "dev",
            "wlan0",
        ]
    )

    run(["sudo", "systemctl", "start", "dnsmasq"])
    run(["sudo", "systemctl", "start", "hostapd"])


def client():
    run(["sudo", "systemctl", "stop", "hostapd"])
    run(["sudo", "systemctl", "stop", "dnsmasq"])

    run(["sudo", "ip", "addr", "flush", "dev", "wlan0"])

    run(["sudo", "systemctl", "start", "systemd-resolved"])
    run(["sudo", "systemctl", "start", "systemd-networkd"])
