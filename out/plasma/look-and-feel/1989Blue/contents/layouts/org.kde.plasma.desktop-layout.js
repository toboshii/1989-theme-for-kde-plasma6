// One layout for every 1989 variation.
// The top bar is the current panel. The bottom dock keeps Plasma's own launchers.

var trayItems = [
    "org.kde.kdeconnect",
    "org.kde.plasma.bluetooth",
    "org.kde.plasma.cameraindicator",
    "org.kde.plasma.clipboard",
    "org.kde.plasma.devicenotifier",
    "org.kde.plasma.manage-inputmethod",
    "org.kde.plasma.mediacontroller",
    "org.kde.plasma.notifications",
    "org.kde.plasma.keyboardindicator",
    "org.kde.plasma.weather",
    "org.kde.kscreen",
    "org.kde.plasma.battery",
    "org.kde.plasma.brightness",
    "org.kde.plasma.dwellclicker",
    "org.kde.plasma.keyboardlayout",
    "org.kde.plasma.networkmanagement",
    "org.kde.plasma.volume"
];

function addTopPanel(screen) {
    var panel = new Panel;
    panel.screen = screen;
    panel.location = "top";
    panel.height = 28;
    panel.hiding = "normal";
    panel.floating = false;
    panel.lengthMode = "fill";
    panel.alignment = "left";

    var kickoff = panel.addWidget("org.kde.plasma.kickoff");
    kickoff.currentConfigGroup = ["General"];
    kickoff.writeConfig("icon", "org.cachyos.hello");
    kickoff.writeConfig("favoritesPortedToKAstats", true);
    kickoff.writeConfig("systemFavorites", "suspend,hibernate,reboot,shutdown");

    panel.addWidget("org.kde.plasma.appmenu");
    panel.addWidget("org.kde.plasma.panelspacer");
    panel.addWidget("org.kde.plasma.panelspacer");

    var tray = panel.addWidget("org.kde.plasma.systemtray");
    tray.currentConfigGroup = ["General"];
    tray.writeConfig("extraItems", trayItems.join(","));
    tray.writeConfig("knownItems", trayItems.join(","));

    var clock = panel.addWidget("org.kde.plasma.digitalclock");
    clock.currentConfigGroup = ["Appearance"];
    clock.writeConfig("autoFontAndSize", false);
    clock.writeConfig("boldText", true);
    clock.writeConfig("customDateFormat", "ddd d MMM");
    clock.writeConfig("dateDisplayFormat", "BesideTime");
    clock.writeConfig("dateFormat", "custom");
    clock.writeConfig("fontFamily", "Hack");
    clock.writeConfig("fontStyleName", "bold");
    clock.writeConfig("fontWeight", "700");
    clock.writeConfig("use24hFormat", "2");
}

function addBottomPanel(screen) {
    var panel = new Panel;
    panel.screen = screen;
    panel.location = "bottom";
    panel.height = 51;
    panel.hiding = "dodgewindows";
    panel.floating = true;
    panel.lengthMode = "fit";
    panel.alignment = "center";
    panel.offset = 0;

    panel.addWidget("org.kde.plasma.marginsseparator");
    var tasks = panel.addWidget("org.kde.plasma.icontasks");
    tasks.currentConfigGroup = ["General"];
    tasks.writeConfig("iconSpacing", "0");
    tasks.writeConfig("indicateAudioStreams", false);
    tasks.writeConfig("maxStripes", "1");
    panel.addWidget("org.kde.plasma.marginsseparator");
}

function setWallpaper(desktop) {
    desktop.wallpaperPlugin = "org.kde.image";
    desktop.currentConfigGroup = ["Wallpaper", "org.kde.image", "General"];
    desktop.writeConfig("Image", "1989");
}

var desktops = desktopsForActivity(currentActivity());
var seen = {};
addTopPanel(0);
for (var i = 0; i < desktops.length; i++) {
    var desktop = desktops[i];
    setWallpaper(desktop);
    var screen = desktop.screen;
    if (seen[screen]) {
        continue;
    }
    seen[screen] = true;
    addBottomPanel(screen);
}
if (!seen[0]) {
    addBottomPanel(0);
}
