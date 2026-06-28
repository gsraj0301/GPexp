import 'package:path_provider/path_provider.dart' as path_provider;
import 'package:sqflite/sqflite.dart';
import 'package:share_plus/share_plus.dart';
import 'package:workmanager/workmanager.dart';

const String dailyTaskName = "dailyWhatsAppSummary";

@pragma('vm:entry-point')
void callbackDispatcher() {
  Workmanager().executeTask((taskName, inputData) async {
    if (taskName == dailyTaskName) {
      try {
        await _sendDailySummary();
      } catch (e) {
        print("WhatsApp summary error: $e");
      }
    }
    return Future.value(true);
  });
}

Future<void> _sendDailySummary() async {
  final dir = await path_provider.getApplicationDocumentsDirectory();
  final dbPath = '${dir.path}/expenses.db';

  final db = await openDatabase(dbPath);

  try {
    final enabledResult = await db.rawQuery(
      "SELECT value FROM settings WHERE key = 'whatsapp_enabled'",
    );
    if (enabledResult.isEmpty || enabledResult.first['value'] != 'true') {
      return;
    }

    final today = _todayStr();
    final sentResult = await db.rawQuery(
      "SELECT value FROM settings WHERE key = 'whatsapp_last_sent'",
    );
    if (sentResult.isNotEmpty && sentResult.first['value'] == today) {
      return;
    }

    final now = DateTime.now();
    final yesterday = now.subtract(const Duration(days: 1));
    final yesterdayStr = _formatDate(yesterday);

    final monthResult = await db.rawQuery(
      "SELECT id FROM expense_months WHERE is_closed = 0 LIMIT 1",
    );
    if (monthResult.isEmpty) return;
    final monthId = monthResult.first['id'] as int;

    final expenses = await db.rawQuery(
      "SELECT category, amount FROM expenses WHERE month_id = ? AND date = ? ORDER BY id",
      [monthId, yesterdayStr],
    );

    if (expenses.isEmpty) {
      await db.rawInsert(
        "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
        ['whatsapp_last_sent', today],
      );
      return;
    }

    final monthNames = [
      "", "January", "February", "March", "April", "May", "June",
      "July", "August", "September", "October", "November", "December",
    ];
    final buf = StringBuffer();
    buf.writeln(
        "📅 Yesterday's Expenses (${monthNames[yesterday.month]} ${yesterday.day}, ${yesterday.year})");
    buf.writeln("");

    double total = 0;
    String? lastCategory;
    for (final exp in expenses) {
      final cat = exp['category'] as String;
      final amt = exp['amount'] as num;

      if (cat != lastCategory) {
        if (lastCategory != null) buf.writeln("");
        buf.writeln(cat);
        lastCategory = cat;
      }
      buf.writeln("  • ₹${amt.toStringAsFixed(2)}");
      total += amt.toDouble();
    }

    buf.writeln("");
    buf.writeln("─────────────");
    buf.writeln("Total: ₹${total.toStringAsFixed(2)}");

    await Share.share(buf.toString(), subject: "Daily Expenses");

    await db.rawInsert(
      "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
      ['whatsapp_last_sent', today],
    );
  } finally {
    await db.close();
  }
}

String _todayStr() {
  final now = DateTime.now();
  return '${now.year}-${_pad(now.month)}-${_pad(now.day)}';
}

String _formatDate(DateTime d) {
  return '${d.year}-${_pad(d.month)}-${_pad(d.day)}';
}

String _pad(int n) => n.toString().padLeft(2, '0');
