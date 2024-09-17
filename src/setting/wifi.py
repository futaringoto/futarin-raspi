FILE_PATH = "./linux/netplan-config.yaml"


def save(ssid, password):
    print("WIFI called")
    yaml = "\n".join(
        [
            "network:",
            "  version: 2",
            "  wifis:",
            "    wlan0:",
            "      dhcp4: true",
            "      access-points:",
            f"        {ssid}:",
            f"          password: {password}",
            "",
        ]
    )

    with open(FILE_PATH, "w") as f:
        f.write(yaml)
