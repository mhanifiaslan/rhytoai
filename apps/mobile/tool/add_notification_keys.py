"""Bildirim tercih ekranının l10n anahtarlarini ekler (tek seferlik).

ARB dosyalarina dogrudan yazmak yerine betik kullaniliyor: her iki dile ayni
anahtar kumesinin girdigi garanti olsun ve Turkce karakterler kabuk uzerinden
gecerken bozulmasin.

Calistirma:  python tool/add_notification_keys.py
"""
from __future__ import annotations

import collections
import io
import json
import pathlib
import sys

L10N = pathlib.Path("lib/l10n")

TR = collections.OrderedDict([
    ("notifications", "Bildirimler"),
    ("notifyDaily", "Günlük okuma"),
    ("notifyDailyBody", "Sabahları bugünün gökyüzü hazır olduğunda haber ver."),
    ("notifyStreak", "Seri hatırlatması"),
    ("notifyStreakBody", "Akşam, serin kırılmadan önce kısa bir hatırlatma."),
    ("notifyFriends", "Arkadaş tepkileri"),
    ("notifyFriendsBody", "Bir arkadaşın sana tepki gönderdiğinde haber ver."),
    ("quietHours", "Sessiz saatler"),
    ("quietHoursBody", "Bu aralıkta bildirim gönderilmez."),
    ("quietHoursRange", "{from}:00 – {to}:00"),
    ("quietHoursOff", "Kapalı"),
    ("notificationsDisabledHint",
     "Bildirimler cihaz ayarlarından kapalı. Açmak için sistem ayarlarına git."),
    ("enableNotifications", "Bildirimleri aç"),
])

EN = collections.OrderedDict([
    ("notifications", "Notifications"),
    ("notifyDaily", "Daily reading"),
    ("notifyDailyBody", "Let me know each morning when today's sky is ready."),
    ("notifyStreak", "Streak reminder"),
    ("notifyStreakBody", "A short evening nudge before your streak breaks."),
    ("notifyFriends", "Friend reactions"),
    ("notifyFriendsBody", "Let me know when a friend sends you a reaction."),
    ("quietHours", "Quiet hours"),
    ("quietHoursBody", "No notifications are sent during this window."),
    ("quietHoursRange", "{from} – {to}"),
    ("quietHoursOff", "Off"),
    ("notificationsDisabledHint",
     "Notifications are off in your device settings. Turn them on there to "
     "receive them."),
    ("enableNotifications", "Turn on notifications"),
])

PLACEHOLDERS = {
    "quietHoursRange": {"from": {"type": "Object"}, "to": {"type": "Object"}},
}


def main() -> int:
    if not L10N.is_dir():
        print("lib/l10n bulunamadi — betigi apps/mobile icinden calistirin.")
        return 2

    for ad, tablo in (("app_tr.arb", TR), ("app_en.arb", EN)):
        yol = L10N / ad
        with io.open(yol, encoding="utf-8") as dosya:
            veri = json.load(dosya, object_pairs_hook=collections.OrderedDict)

        eklenen = 0
        for anahtar, deger in tablo.items():
            if anahtar in veri:
                print(f"  zaten var, atlandi: {ad} -> {anahtar}")
                continue
            veri[anahtar] = deger
            eklenen += 1
            if anahtar in PLACEHOLDERS:
                veri["@" + anahtar] = {"placeholders": PLACEHOLDERS[anahtar]}

        with io.open(yol, "w", encoding="utf-8", newline="\n") as dosya:
            json.dump(veri, dosya, ensure_ascii=False, indent=2)
            dosya.write("\n")
        print(f"{ad}: {eklenen} anahtar eklendi")

    return 0


if __name__ == "__main__":
    sys.exit(main())
