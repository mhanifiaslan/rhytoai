"""Hesap silme akisinin l10n anahtarlarini ekler (tek seferlik).

Calistirma:  python tool/add_account_keys.py
"""
from __future__ import annotations

import collections
import io
import json
import pathlib
import sys

L10N = pathlib.Path("lib/l10n")

TR = collections.OrderedDict([
    ("deleteAccount", "Hesabı sil"),
    ("deleteAccountTitle", "Hesabını silmek üzeresin"),
    ("deleteAccountBody",
     "Bu işlem geri alınamaz. Silinecekler: doğum kaydın, sohbetten "
     "biriktirdiğimiz notlar, arkadaşlıkların, kullanıcı adın ve sana özel "
     "üretilmiş tüm okumalar."),
    ("deleteAccountKeeps",
     "Gönderdiğin şikayet kayıtları saklanır; başkalarının güvenliğiyle "
     "ilgili oldukları için silinmez."),
    ("deleteAccountSubscription",
     "Aboneliğin varsa uygulama mağazandan ayrıca iptal etmelisin; "
     "hesabı silmek aboneliği durdurmaz."),
    ("deleteAccountConfirmHint", "Onaylamak için SİL yaz"),
    ("deleteAccountConfirmWord", "SİL"),
    ("deleteAccountAction", "Hesabımı kalıcı olarak sil"),
    ("deleteAccountFailed", "Hesap silinemedi. Lütfen tekrar dene."),
    ("deleteAccountReauth",
     "Güvenlik için tekrar giriş yapman gerekiyor. Çıkış yapıp yeniden giriş "
     "yaptıktan sonra bu işlemi tekrarla."),
    ("cancel", "Vazgeç"),
])

EN = collections.OrderedDict([
    ("deleteAccount", "Delete account"),
    ("deleteAccountTitle", "You're about to delete your account"),
    ("deleteAccountBody",
     "This cannot be undone. We will delete your birth record, the notes we "
     "built up from your conversations, your friendships, your username and "
     "every reading generated for you."),
    ("deleteAccountKeeps",
     "Reports you filed are kept — they concern other people's safety, so we "
     "do not remove them."),
    ("deleteAccountSubscription",
     "If you have a subscription you must also cancel it in your app store; "
     "deleting the account does not stop the billing."),
    ("deleteAccountConfirmHint", "Type DELETE to confirm"),
    ("deleteAccountConfirmWord", "DELETE"),
    ("deleteAccountAction", "Permanently delete my account"),
    ("deleteAccountFailed", "The account could not be deleted. Please retry."),
    ("deleteAccountReauth",
     "For security you need to sign in again. Sign out, sign back in, and "
     "repeat this step."),
    ("cancel", "Cancel"),
])


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

        with io.open(yol, "w", encoding="utf-8", newline="\n") as dosya:
            json.dump(veri, dosya, ensure_ascii=False, indent=2)
            dosya.write("\n")
        print(f"{ad}: {eklenen} anahtar eklendi")

    return 0


if __name__ == "__main__":
    sys.exit(main())
