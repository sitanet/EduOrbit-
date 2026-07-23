import 'package:flutter_test/flutter_test.dart';
import 'package:eduorbit_core/storage/hive_cache.dart';
import 'package:eduorbit_core/sync/sync_queue.dart';
import 'package:eduorbit_core/feature_flags/feature_flag_service.dart';

void main() {
  group('SyncQueue', () {
    late SyncQueue queue;

    setUp(() {
      queue = SyncQueue();
    });

    test('should enqueue and dequeue mutations in FIFO order', () {
      queue.enqueue({'type': 'attendance.mark', 'data': {'student': '001', 'status': 'present'}});
      queue.enqueue({'type': 'grade.entry', 'data': {'student': '002', 'score': 85}});

      expect(queue.size, 2);

      final first = queue.dequeue();
      expect(first?['type'], 'attendance.mark');

      final second = queue.dequeue();
      expect(second?['type'], 'grade.entry');

      expect(queue.size, 0);
    });

    test('should peek without removing', () {
      queue.enqueue({'type': 'finance.payment', 'amount': 5000});

      final peeked = queue.peek();
      expect(peeked?['type'], 'finance.payment');
      expect(queue.size, 1);
    });

    test('should handle empty queue gracefully', () {
      expect(queue.dequeue(), isNull);
      expect(queue.peek(), isNull);
      expect(queue.size, 0);
    });

    test('should clear all queued mutations', () {
      queue.enqueue({'type': 'test.1'});
      queue.enqueue({'type': 'test.2'});
      queue.enqueue({'type': 'test.3'});

      queue.clear();
      expect(queue.size, 0);
    });
  });

  group('HiveCache', () {
    test('should store and retrieve values', () {
      final cache = HiveCache();
      cache.put('school_name', 'EduOrbit Academy');

      final result = cache.get<String>('school_name');
      expect(result, 'EduOrbit Academy');
    });

    test('should return null for missing keys', () {
      final cache = HiveCache();
      final result = cache.get<String>('nonexistent');
      expect(result, isNull);
    });

    test('should invalidate specific keys', () {
      final cache = HiveCache();
      cache.put('temp_data', 'will_be_removed');
      cache.invalidate('temp_data');

      final result = cache.get<String>('temp_data');
      expect(result, isNull);
    });
  });
}
