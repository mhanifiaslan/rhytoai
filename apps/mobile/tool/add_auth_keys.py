"""Giris ekraninin yeni l10n anahtarlarini ekler (tek seferlik).

Calistirma:  python tool/add_auth_keys.py
"""
from __future__ import annotations

import collections
import io
import json
import pathlib
import sys

L10N = pathlib.Path("lib/l10n")

TR = collections.OrderedDict([
    ("signInWithApple", "Apple ile giriş"),
    # Hukuki onay: kullanici kabul ettigini OKUYABILMELI.
    ("consentPrefix", "Devam ederek "),
    ("consentAnd", " ve "),
    ("consentSuffix", " metinlerini kabul etmiş olursun."),
    ("insightNote",
     "Yorumlar içgörü amaçlıdır; tıbbi, hukuki veya finansal tavsiye değildir."),
    # Yas beyani
    ("ageConfirm", "13 yaşından büyüğüm"),
    ("ageRequired", "Devam etmek için yaş beyanını onaylaman gerekiyor."),
    # Sifre kurali
    ("passwordRuleHint", "En az 8 karakter, harf ve rakam içermeli."),
    ("passwordTooShort", "Şifre en az 8 karakter olmalı."),
    ("passwordTooSimple", "Şifre harf ve rakam (veya sembol) içermeli."),
    # E-posta dogrulama
    ("verificationSent",
     "Doğrulama bağlantısı {email} adresine gönderildi. Gelen kutunu kontrol et."),
    # Sifre sifirlama — sonuc ne olursa olsun ayni notr mesaj
    ("resetLinkSentNeutral",
     "Bu adres kayıtlıysa şifre sıfırlama bağlantısı gönderildi."),
    # Saglayici cakismasi
    ("useGoogleInstead",
     "Bu e-posta Google hesabıyla açılmış. Yukarıdaki Google düğmesiyle giriş yap."),
])

EN = collections.OrderedDict([
    ("signInWithApple", "Sign in with Apple"),
    ("consentPrefix", "By continuing you accept the "),
    ("consentAnd", " and the "),
    ("consentSuffix", "."),
    ("insightNote",
     "Readings are for insight; they are not medical, legal or financial advice."),
    ("ageConfirm", "I am over 13 years old"),
    ("ageRequired", "Please confirm your age to continue."),
    ("passwordRuleHint", "At least 8 characters, with letters and numbers."),
    ("passwordTooShort", "Password must be at least 8 characters."),
    ("passwordTooSimple", "Password must mix letters with numbers or symbols."),
    ("verificationSent",
     "A verification link was sent to {email}. Please check your inbox."),
    ("resetLinkSentNeutral",
     "If this address is registered, a reset link has been sent."),
    ("useGoogleInstead",
     "This email was registered with Google. Use the Google button above."),
])

PLACEHOLDERS = {
    "verificationSent": {"email": {"type": "Object"}},
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
