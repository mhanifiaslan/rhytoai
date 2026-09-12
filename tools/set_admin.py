"""Firebase custom claim `{admin: true, role: owner|support}` basar/kaldirir
(W4 + AD1).

Admin paneli (/rytho-admin) yetkisi BU claim'den gelir; panelde ayri bir
kullanici listesi yoktur. Claim yalnizca buradan, yerel makinede servis
hesabi kimligiyle basilir — uygulama ici hicbir yol claim yazamaz.

Roller:
    owner   — her sey: sil, devre disi, surum esigi, ortak yazimlari,
              disa aktarim, yeniden hesapla, duyuru, elle toplama.
    support — okur + sinirli yazar (kredi, cihaz kilidi, auth linki,
              bildirim provasi / kendine test).
`role` tasimayan eski `admin:true` claim'i sunucuda owner sayilir (gecis);
yine de bir kez `--role owner` ile yeniden basmak temiz olur.

Kullanim (repo kokunden):
    backend/.venv/Scripts/python tools/set_admin.py --email aslan.mh@gmail.com
    backend/.venv/Scripts/python tools/set_admin.py --email ... --role support
    backend/.venv/Scripts/python tools/set_admin.py --uid <uid>
    backend/.venv/Scripts/python tools/set_admin.py --email ... --revoke

Kimlik: GOOGLE_APPLICATION_CREDENTIALS servis hesabi anahtari ya da
`gcloud auth application-default login` (proje: rhytoai).

NOT: Claim, kullanicinin MEVCUT oturumuna hemen yansimaz — ID token
yenilenince (<=1 saat) ya da cikis/giris yapinca gecerli olur.
"""
from __future__ import annotations

import argparse
import sys

import firebase_admin
from firebase_admin import auth

ROLLER = ("owner", "support")


def main() -> int:
    p = argparse.ArgumentParser(description="Rytho admin claim yonetimi")
    kimlik = p.add_mutually_exclusive_group(required=True)
    kimlik.add_argument("--email", help="Hedef kullanicinin e-postasi")
    kimlik.add_argument("--uid", help="Hedef kullanicinin uid'i")
    p.add_argument("--role", choices=ROLLER, default="owner",
                   help="Panel rolu (varsayilan: owner)")
    p.add_argument("--revoke", action="store_true",
                   help="admin + role claim'lerini kaldir (varsayilan: bas)")
    p.add_argument("--project", default="rhytoai")
    args = p.parse_args()

    firebase_admin.initialize_app(options={"projectId": args.project})

    kullanici = (auth.get_user_by_email(args.email) if args.email
                 else auth.get_user(args.uid))

    mevcut = dict(kullanici.custom_claims or {})
    print(f"Hedef : {kullanici.uid}")
    print(f"E-posta: {kullanici.email}")
    print(f"Mevcut claim'ler: {mevcut or '-'}")
    print(f"Islem : {'admin KALDIR' if args.revoke else f'admin BAS (role={args.role})'}")

    # Yanlis hesaba basilmasin: hedef ekrana yazildi, onay istenir.
    onay = input("Onayliyor musun? (evet/hayir): ").strip().lower()
    if onay != "evet":
        print("Vazgecildi.")
        return 1

    if args.revoke:
        mevcut.pop("admin", None)
        mevcut.pop("role", None)
    else:
        mevcut["admin"] = True
        mevcut["role"] = args.role
    auth.set_custom_user_claims(kullanici.uid, mevcut or None)

    print("Tamam. Claim, kullanicinin ID token'i yenilenince (<=1 saat) ya da"
          " cikis/giris sonrasi gecerli olur.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
