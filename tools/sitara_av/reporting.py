"""Conceptual "who reports to whom" diagram for a Sitara install: Galaxy and Pub/Sub in the cloud, StarWatch clients on the site LAN.

    from sitara_av import reporting
    reporting.diagram(sheet, site="SITE LAN (back AV closet)", render_title="APPLICATION NODE",
                      hardware=("AV hardware", "D8, SX40, servers,", "switches (drivers TBC)"))

Roles, not cables. The cloud holds Galaxy (Cloud Run) and Google Pub/Sub (status, logs, analytics up; commands down). The application node
runs a StarWatch client that launches and watches the application and talks to it over Photon (telemetry out) and Electron (control in).
The surveyor node is always a Protectli V1210 running a StarWatch client in survey mode plus MeshCentral: it surveys and controls the
hardware and gives out-of-band management of the application node. StarWatch only connects out; Photon and Electron stay on the application node.
Fills one A3 sheet below the title line (y 32 to 252 mm) with the notes at the bottom left.
"""
from .sheet import T

UP, DOWN, INK, WHITE = "88 62 210", "176 84 0", "30 30 30", "255 255 255"


def diagram(s, site="SITE LAN", render_title="APPLICATION NODE", hardware=("AV hardware", "devices polled and", "controlled (drivers TBC)"),
            surveyor=True, uplink="internet / site uplink (TBC)", notes=True):
    def box(x0, y0, x1, y1, lines, fill=WHITE, title_bold=True):
        s.rect(x0, y0, x1, y1, INK, fill, width=0.25)
        for i, ln in enumerate(lines):
            s.text(ln, x0 + 2.0, y0 + 5.5 + i * 5.0, T, bold=(i == 0 and title_bold))

    # zones
    s.rect(20.0, 32.0, 400.0, 118.0, "88 62 210", "239 236 255", width=0.3)
    s.text("CLOUD  (Google Cloud Platform)", 23.0, 38.5, T, True)
    s.rect(20.0, 128.0, 400.0, 250.0, INK, "230 240 255", width=0.3, stroke_type="dash")
    s.text(site, 150.0, 134.5, T, True)
    s.line([(20.0, 123.0), (400.0, 123.0)], "120 120 120", width=0.2, stroke_type="dot")
    s.text(uplink, 335.0, 121.0, T)

    # cloud
    box(25.0, 66.0, 62.0, 110.0, ["GitHub", "releases", "(app", "builds)"])
    s.rect(70.0, 44.0, 300.0, 112.0, INK, WHITE, width=0.25)
    s.text("Google Pub/Sub", 73.0, 50.0, T, True)
    cells = [("STATUS", ["heartbeat,", "app state"], "up"), ("LOGS", ["batched", "app logs"], "up"),
             ("ANALYTICS", ["usage", "events"], "up"), ("COMMANDS", ["restart,", "update, reboot"], "down")]
    for i, (name, det, d) in enumerate(cells):
        cx = 73.0 + i * 56.5
        s.rect(cx, 56.0, cx + 54.0, 109.0, UP if d == "up" else DOWN, "250 250 255", width=0.2)
        s.text(name, cx + 2.0, 62.0, T, True)
        for j, ln in enumerate(det):
            s.text(ln, cx + 2.0, 69.0 + j * 5.0, T)
        s.text("reported up" if d == "up" else "sent down", cx + 2.0, 100.0, T)
    box(320.0, 62.0, 395.0, 114.0, ["Galaxy CMS", "Django on Cloud Run", "Cloud SQL + Storage", "dashboards,", "System Control"])
    box(320.0, 38.0, 395.0, 52.0, ["Operators (browser)"], title_bold=False)
    s.arrow([(357.0, 52.0), (357.0, 62.0)], UP)
    s.text("HTTPS", 360.0, 58.5, T)
    s.arrow([(300.0, 74.0), (320.0, 74.0)], UP)
    s.text("webhook", 301.0, 72.0, 1.8)
    s.arrow([(320.0, 98.0), (300.0, 98.0)], DOWN)
    s.text("publish", 301.0, 96.0, 1.8)

    # render node
    s.rect(25.0, 138.0, 197.0, 246.0, INK, WHITE, width=0.25)
    s.text(render_title, 28.0, 144.0, T, True)
    box(30.0, 150.0, 100.0, 232.0, ["StarWatch client", "launches + restarts", "the application", "process monitoring,", "crash recovery", "logs, node health,", "application state", "app updates", "from GitHub"], fill="239 236 255")
    box(137.0, 150.0, 192.0, 232.0, ["Application", "(Unreal /", "SitaraCore)", "renders the", "show"], fill="239 236 255")
    s.arrow([(137.0, 180.0), (100.0, 180.0)], UP)
    s.text("Photon: telemetry out", 102.0, 177.5, 1.8)
    s.arrow([(100.0, 205.0), (137.0, 205.0)], DOWN)
    s.text("Electron: control in", 102.0, 202.5, 1.8)

    # site <-> cloud (StarWatch only connects out)
    s.arrow([(45.0, 110.0), (45.0, 150.0)], DOWN)
    s.text("app builds", 47.0, 128.0, T)
    s.arrow([(78.0, 150.0), (78.0, 112.0)], UP)
    s.arrow([(92.0, 112.0), (92.0, 150.0)], DOWN)
    s.text("up: status, logs, analytics", 96.0, 135.0, T)
    s.text("down: commands", 96.0, 141.0, T)

    if surveyor:
        s.rect(203.0, 138.0, 395.0, 246.0, INK, WHITE, width=0.25)
        s.text("SURVEYOR NODE (Protectli V1210)", 206.0, 144.0, T, True)
        box(208.0, 150.0, 285.0, 232.0, ["StarWatch client", "(survey mode)", "surveys hardware,", "control interface", "for hardware,", "OOB management", "of the application node"], fill="239 236 255")
        box(306.0, 150.0, 390.0, 184.0, ["MeshCentral", "OOB: power, console"])
        box(318.0, 192.0, 390.0, 228.0, list(hardware))
        s.arrow([(285.0, 166.0), (306.0, 166.0)], DOWN)
        s.text("local", 288.0, 164.0, 1.8)
        s.arrow([(285.0, 212.0), (318.0, 212.0)], DOWN)
        s.text("poll", 290.0, 208.0, 1.8)
        s.text("control", 288.0, 217.0, 1.8)
        s.arrow([(312.0, 184.0), (312.0, 238.0), (197.0, 238.0)], DOWN)
        s.text("OOB management (power cycle, recovery)", 210.0, 236.0, T)
        s.arrow([(262.0, 150.0), (262.0, 112.0)], UP)
        s.arrow([(277.0, 112.0), (277.0, 150.0)], DOWN)
        s.text("up: status, logs", 281.0, 135.0, T)
        s.text("down: commands", 281.0, 141.0, T)

    if notes:
        s.notes(["Read it as roles: the cloud holds Galaxy and Pub/Sub; the site holds the StarWatch clients and the hardware. Violet arrows are data reported up, orange arrows are control or commands sent down.",
                 "StarWatch only connects out to Pub/Sub; the site accepts no inbound connection from the cloud. Photon and Electron stay on the application node (local to the app). The surveyor's MeshCentral stays on the LAN.",
                 "Why two clients: the application-node client keeps the show running and reports on it; the surveyor client watches the hardware around it and can recover the application node when its own client cannot."],
                20.0, 253.0, 270.0, T)
