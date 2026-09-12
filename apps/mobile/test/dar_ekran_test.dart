// Dar ekran + büyük yazı ölçeği taşma bekçileri (MU-turu).
//
// Cihaz bulgusu: dikey modda uzun başlık cümlesi ekrana sığmıyor, sağ taraf
// kırpılıyordu ("Bugün gökyüzünde senin için ✦ En yak…"). Kök neden
// `SectionHeader`'ın esnemeyen `Row` + `Spacer` yerleşimiydi.
//
// Bu dosya onu ve aynı sınıftaki komşularını sabitler: 320 dp genişlik
// (piyasadaki en dar Android telefon) × 1,3 yazı ölçeği (uygulamanın
// tavanı, bkz. `kMaxTextScale`) altında HİÇBİR widget taşmamalı.
// Flutter taşmayı hata olarak fırlatır; `tester.takeException()` yakalar.
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:rytho/l10n/app_localizations.dart';
import 'package:rytho/main.dart' show kMaxTextScale;
import 'package:rytho/theme/rytho_theme.dart';
import 'package:rytho/theme/rytho_tokens.dart';
import 'package:rytho/widgets/common.dart';

/// En dar hedef cihaz (Android 320 dp) — altına inen telefon yok.
const double kDarGenislik = 320;

/// Gerçek uzun metinler: l10n'daki en uzun Türkçe başlıklar.
const String kUzunBaslik = 'Bugün gökyüzünde senin için';
const String kUzunEk = '✦ En yakın kesinleşme: 18 Eylül';

/// [child]'ı dar ekranda ve verilen yazı ölçeğinde çizer.
Future<void> darEkranda(WidgetTester tester, Widget child,
    {double genislik = kDarGenislik, double olcek = kMaxTextScale}) async {
  tester.view.physicalSize = Size(genislik * 3, 1200);
  tester.view.devicePixelRatio = 3;
  addTearDown(tester.view.reset);
  await tester.pumpWidget(MaterialApp(
    locale: const Locale('tr'),
    localizationsDelegates: AppLocalizations.localizationsDelegates,
    supportedLocales: const [Locale('tr'), Locale('en')],
    theme: buildRythoTheme(),
    home: MediaQuery(
      data: MediaQueryData(
        size: Size(genislik, 1200),
        textScaler: TextScaler.linear(olcek),
        // Giriş animasyonları (flutter_animate) testte zamanlayıcı bırakır;
        // ölçülen şey YERLEŞİM, hareket değil.
        disableAnimations: true,
      ),
      child: Scaffold(
        backgroundColor: RythoColors.ink,
        body: SingleChildScrollView(child: child),
      ),
    ),
  ));
}

/// Taşma yok mu? Flutter taşmayı çizim anında fırlatır.
void tasmaYok(WidgetTester tester, {String? neden}) {
  expect(tester.takeException(), isNull, reason: neden);
}

void main() {
  group('SectionHeader — cihazda kırpılan başlık', () {
    testWidgets('uzun başlık + uzun ek bilgi 320 dp × 1,3 ölçekte taşmaz',
        (tester) async {
      await darEkranda(
          tester,
          SectionHeader(kUzunBaslik,
              trailing: Text(kUzunEk, style: RythoType.dataSmall)));
      tasmaYok(tester, neden: 'başlık satırı ekran dışına çıkıyor');
      // İkisi de EKRANDA: ek bilgi alt satıra iner, kısaltılmaz.
      expect(find.text(kUzunBaslik), findsOneWidget);
      expect(find.text(kUzunEk), findsOneWidget);
    });

    testWidgets('sığan başlık tek satırda: ek bilgi SAĞDA kalır',
        (tester) async {
      // ⚠️ Test yazı tipi her harfi punto kadar geniş kare çizer (Ahem);
      // gerçek cihazdan ~2 kat geniş. Bu yüzden "sığıyor" hâli KISA
      // metinlerle kurulur — asıl iddia yerleşim davranışı: tek satıra
      // sığan çift, eski `Row` + `Spacer` görünümünü korur.
      await darEkranda(
          tester,
          const SectionHeader('Şu an',
              trailing: Text('13 Eyl', style: TextStyle(fontSize: 11))),
          genislik: 390,
          olcek: 1.0);
      tasmaYok(tester);
      final baslik = tester.getRect(find.text('Şu an'));
      final ek = tester.getRect(find.text('13 Eyl'));
      expect(ek.left, greaterThan(baslik.right),
          reason: 'sığdığında eski görünüm korunur');
      expect(ek.right, closeTo(390 - RythoSpace.xl, 1),
          reason: 'ek bilgi sağ kenara yaslanır');
      expect((ek.center.dy - baslik.center.dy).abs(), lessThan(10),
          reason: 'aynı satırda');
    });

    testWidgets('ek bilgi yokken başlık solda kalır (tek çocuk)',
        (tester) async {
      await darEkranda(tester, const SectionHeader(kUzunBaslik));
      tasmaYok(tester);
      expect(tester.getRect(find.text(kUzunBaslik)).left,
          closeTo(RythoSpace.xl, 0.5));
    });

    testWidgets('çok uzun tek kelime bile taşmaz', (tester) async {
      await darEkranda(
          tester, const SectionHeader('Gökyüzündekikesinleşmelerinözeti'));
      tasmaYok(tester);
    });
  });

  group('Ortak satır bileşenleri', () {
    testWidgets('SettingsRow uzun başlık + uzun alt yazıda taşmaz',
        (tester) async {
      await darEkranda(
          tester,
          SettingsRow(
            icon: Icons.face_retouching_natural_outlined,
            title: 'Biyometrik işleme rızası ve yüz okuma ayarları',
            subtitle: 'Fotoğrafın sunucuya gönderilmez; ölçüm cihazda yapılır '
                've sonuç saklanmaz.',
            onTap: () {},
          ));
      tasmaYok(tester);
    });

    testWidgets('LabelValueRow uzun etiket + uzun değerde taşmaz',
        (tester) async {
      await darEkranda(
          tester,
          const LabelValueRow(
            label: 'Doğum saati bilinmiyor beyanı',
            value: 'Yükselen ve ev hesapları yapılmadı',
          ));
      tasmaYok(tester);
    });

    testWidgets('ErrorCard uzun hata metninde taşmaz', (tester) async {
      await darEkranda(
          tester,
          ErrorCard(
            message: 'Bağlantı kurulamadı. İnternetini kontrol edip tekrar '
                'dene; sorun sürerse birkaç dakika sonra yeniden açmayı dene.',
            onRetry: () {},
          ));
      tasmaYok(tester);
    });

    testWidgets('EmptyState uzun metinde taşmaz', (tester) async {
      await darEkranda(
          tester,
          const EmptyState(
            emoji: '💬',
            title: 'Henüz hiç konuşma başlatmadın',
            description:
                'Rytho\'ya bugünün gökyüzünü, ilişkilerini ya da aklına '
                'takılan herhangi bir şeyi sorabilirsin.',
          ));
      tasmaYok(tester);
    });
  });
}
