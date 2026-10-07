import io
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest
from scripts.event_watch import html_to_text, watch_events
from scripts.local_paths import LOCAL_DATA, events_snapshot_root


class WatchTests(unittest.TestCase):
    def test_html(self):
        self.assertEqual(html_to_text('<p>A &amp;  B</p><script>bad</script><style>bad</style><noscript>bad</noscript><div>C<br>D</div>'), 'A & B\nC\nD\n')
        self.assertEqual(events_snapshot_root(), LOCAL_DATA / 'raw' / 'events')

    def test_snapshots(self):
        sources = [dict(id='a', url='https://example.com/a'), dict(id='b', url='https://example.com/b')]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            def run(day, fetcher, source=None):
                out = io.StringIO()
                status = watch_events(sources, root=root, fetcher=fetcher,
                                      now=datetime(2026, 10, day, tzinfo=timezone.utc), source=source, output=out)
                return status, out.getvalue()
            status, output = run(1, lambda url: '<p>First</p>')
            self.assertEqual(status, 0)
            self.assertIn('初回取得: a', output)
            self.assertIn('new: 2', output)
            self.assertEqual((root / '20261001T000000Z' / 'a.txt').read_text(), 'First\n')
            self.assertIn('unchanged: 2', run(2, lambda url: '<p>First</p>')[1])
            status, output = run(3, lambda url: '<p>Second</p>', 'a')
            self.assertIn('-First', output)
            self.assertIn('+Second', output)
            self.assertIn('changed: 1', output)
            def fail(url):
                if url.endswith('/a'):
                    raise OSError('offline')
                return '<p>First</p>'
            status, output = run(4, fail)
            self.assertEqual(status, 1)
            self.assertIn('ERROR: a: offline', output)
            self.assertIn('unchanged: 1', output)
            self.assertIn('failed: 1', output)
