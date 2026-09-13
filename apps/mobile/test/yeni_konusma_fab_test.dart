// "Yeni konu" eyleminin YERİ — başparmak bölgesi bekçileri.
//
// Cihaz bulgusu (kullanıcı): "chat ekranına girildiğinde sağ üstte yer alan
// yeni bir konu başlatma düğmesini kullanmak için iki elle telefonu
// kullanmak gerekiyor." Eylem AppBar'ın sağ üst köşesindeydi; tek elle
// tutulan telefonda başparmak oraya varmıyor.
//
// Düzeltme alt-sağa genişletilmiş bir düğme koymak DEĞİL yalnızca: sağ
// üstteki ikonun KALKMASI da şart. Aynı eylem iki yerde dururken göz
// yine önce yukarıyı bulur ve şikâyet sürer. Bu dosya ikisini birden
// sabitler; ayrıca boş durumda TEK CTA kalmasını ve dar ekran + büyük
// yazı ölçeğinde taşma olmamasını.
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:rytho/core/conversations.dart';
import 'package:rytho/features/chat/chat_screen.dart';
import 'package:rytho/features/chat/conversation_list_screen.dart';
import 'package:rytho/l10n/app_localizations.dart';
import 'package:rytho/main.dart' show kMaxTextScale;
import 'package:rytho/theme/rytho_theme.dart';
import 'package:rytho/widgets/atlas_widgets.dart' show GoldButton;

// Ölçüt (320 dp × 1,3) tek yerde dursun diye harness PAYLAŞILIYOR.
import 'dar_ekran_test.dart' show darEkranda, tasmaYok;

/// İtilen rotaları toplar — ChatScreen'e gidildiğini rotadan doğrularız.
class _RotaGozcusu extends NavigatorObserver {
  final itilenler = <Route<dynamic>>[];

  @override
  void didPush(Route<dynamic> route, Route<dynamic>? previousRoute) {
    itilenler.add(route);
  }
}

Conversation _konu(String id) => Conversation(
      id: id,
      title: 'Konu $id',
      updatedAt: DateTime(2026, 9, 13, 10),
    );

Widget _ekran(List<Conversation> konular, {NavigatorObserver? gozcu}) =>
    ProviderScope(
      overrides: [
        // Firestore'a hiç gidilmez; liste testin verdiği kadardır.
        conversationsProvider.overrideWith((ref) => Stream.value(konular)),
      ],
      child: MaterialApp(
        locale: const Locale('tr'),
        localizationsDelegates: const [
          AppLocalizations.delegate,
          GlobalMaterialLocalizations.delegate,
          GlobalWidgetsLocalizations.delegate,
          GlobalCupertinoLocalizations.delegate,
        ],
        supportedLocales: AppLocalizations.supportedLocales,
        theme: buildRythoTheme(),
        navigatorObservers: gozcu != null ? [gozcu] : const [],
        // Yıldız alanı ve kademeli giriş SÜREKLİ animatör; açık kalırsa
        // `pumpAndSettle` hiç dönmez. Ölçülen şey yerleşim, hareket değil.
        builder: (context, child) => MediaQuery(
          data: MediaQuery.of(context).copyWith(disableAnimations: true),
          child: child!,
        ),
        home: const ConversationListScreen(),
      ),
    );

/// Akıştaki ilk değer bir mikro görevde gelir: tek kare yetmez.
Future<void> _bekle(WidgetTester tester) async {
  await tester.pump();
  await tester.pump(const Duration(milliseconds: 50));
}

void main() {
  testWidgets('sağ üstteki "yeni konu" ikonu KALKTI', (tester) async {
    await tester.pumpWidget(_ekran([_konu('a'), _konu('b')]));
    await _bekle(tester);

    expect(find.byIcon(Icons.add_comment_outlined), findsNothing,
        reason: 'eylem sağ üstte kalırsa tek elle erişim sorunu sürer');
    expect(
        find.descendant(
            of: find.byType(AppBar), matching: find.byType(IconButton)),
        findsNothing,
        reason: 'AppBar artık eylem taşımıyor');
  });

  testWidgets('dolu listede FAB var ve dokunuş ChatScreen rotasını iter',
      (tester) async {
    final gozcu = _RotaGozcusu();
    await tester.pumpWidget(_ekran([_konu('a'), _konu('b')], gozcu: gozcu));
    await _bekle(tester);

    final fab = find.byType(YeniKonuFab);
    expect(fab, findsOneWidget);
    // Ekran okuyucu tek düğme duyar, etiketi uygulamanın dilinde.
    expect(find.bySemanticsLabel('Yeni konu'), findsOneWidget);
    // Dokunma hedefi: 48 dp tabanının altına inilmez.
    expect(tester.getSize(fab).height,
        greaterThanOrEqualTo(kMinInteractiveDimension));
    // Başparmak bölgesi: düğme ekranın ALT YARISINDA ve SAĞ yarısında.
    final ekran = tester.getSize(find.byType(ConversationListScreen));
    final kutu = tester.getRect(fab);
    expect(kutu.center.dy, greaterThan(ekran.height / 2));
    expect(kutu.center.dx, greaterThan(ekran.width / 2));

    await tester.tap(fab);
    // ChatScreen ÇİZDİRİLMEZ (Firebase ister); rotanın kimliği yeter.
    expect(gozcu.itilenler.length, 2, reason: 'ana rota + itilen rota');
    final rota = gozcu.itilenler.last;
    expect(rota, isA<MaterialPageRoute<dynamic>>());
    expect(
        (rota as MaterialPageRoute<dynamic>)
            .builder(tester.element(find.byType(ConversationListScreen))),
        isA<ChatScreen>());
    // Geçiş animasyonu başlamadan ağacı söküyoruz.
    await tester.pumpWidget(const SizedBox.shrink());
  });

  testWidgets('boş durumda FAB YOK, tek CTA GoldButton', (tester) async {
    await tester.pumpWidget(_ekran(const []));
    await _bekle(tester);

    expect(find.byType(GoldButton), findsOneWidget);
    expect(find.byType(YeniKonuFab), findsNothing,
        reason: 'boş ekranda iki birincil CTA hiyerarşiyi siler');
  });

  testWidgets('son satır düğmenin altında kalmaz', (tester) async {
    // Alt boşluk düğmenin kapladığı alanı hesaba katmazsa son konuya
    // dokunulamaz — kullanıcı onu hiç açamaz.
    final konular = [for (var i = 0; i < 12; i++) _konu('$i')];
    await tester.pumpWidget(_ekran(konular));
    await _bekle(tester);

    final liste = find.byType(Scrollable).first;
    await tester.drag(liste, const Offset(0, -2000));
    await _bekle(tester);

    // Metin değil KARTIN kendisi ölçülür: kartın alt kenarı düğmenin
    // altına kayarsa satır dokunulamaz hâle gelir.
    final sonKart = find.ancestor(
        of: find.text('Konu 11'), matching: find.byType(Dismissible));
    expect(sonKart, findsOneWidget);
    expect(tester.getRect(sonKart).bottom,
        lessThan(tester.getRect(find.byType(YeniKonuFab)).top),
        reason: 'sona kadar kaydırıldığında son satır düğmenin ÜSTÜNDE');
  });

  testWidgets('320 dp × 1,3 yazı ölçeğinde taşma yok', (tester) async {
    // Tam ekran widget'ı paylaşılan dar-ekran harness'ına giriyor; yükseklik
    // `SingleChildScrollView` içinde sınırsız kalmasın diye kelepçelendi.
    await darEkranda(
      tester,
      SizedBox(
        height: 640,
        child: ProviderScope(
          overrides: [
            conversationsProvider.overrideWith(
                (ref) => Stream.value([_konu('a'), _konu('b')])),
          ],
          child: const ConversationListScreen(),
        ),
      ),
      olcek: kMaxTextScale,
    );
    await _bekle(tester);

    tasmaYok(tester, neden: 'yeni konu düğmesi dar ekranda taşıyor');
    expect(find.byType(YeniKonuFab), findsOneWidget);
  });
}
