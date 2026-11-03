import importlib.util
import unittest
import tempfile
import hashlib
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("download_raw", "scripts/download_raw.py")
raw = importlib.util.module_from_spec(spec)
spec.loader.exec_module(raw)


class RawRecoveryTests(unittest.TestCase):
    def test_aliases_keep_queries_and_strip_wayback_wrapper(self):
        self.assertEqual(raw.key("http://www.theroadislife.com:80/a.htm?x=1#comments"),
                         "https://theroadislife.com/a.htm?x=1")
        self.assertEqual(raw.key("https://web.archive.org/web/20100406044023id_/http://www.theroadislife.com/"),
                         "https://theroadislife.com/")

    def test_index_resume_key(self):
        rows, resume = raw.parse_index('[["timestamp","original"],["20100101","http://example.com/"]]\n\nNEXT')
        self.assertEqual(rows[0]["timestamp"], "20100101")
        self.assertEqual(resume, "NEXT")

    def test_scope_excludes_cgi_and_unrelated_material(self):
        self.assertTrue(raw.scope("http://www.theroadislife.com/archives/2007/06/full_circle.htm"))
        for path in ["poland/index.htm", "usa/", "pre-trip/site_design/index.htm",
                     "help.gif", "images/theroadiscrap3-thumb.jpg"]:
            self.assertTrue(raw.scope("https://theroadislife.com/archives/" + path))
        for url in ["https://example.com/", "http://theroadislife.com/cgi-bin/mt/mt-search.cgi",
                    "http://theroadislife.com/thesmokestacks/index.html",
                    "http://theroadislife.com/archives/2005/10/spam.examplecom",
                    "http://theroadislife.com/archives/2005/10/post.htm?spam=1"]:
            self.assertFalse(raw.scope(url))

    def test_reject_errors_and_corrupt_images(self):
        meta = dict(curl_exit=0, http_status=200)
        self.assertFalse(raw.acceptable(b"<title>Wayback Machine</title>", meta, "blog"))
        self.assertFalse(raw.acceptable(b"not an image", meta, "image"))
        self.assertFalse(raw.acceptable(b"truncated", dict(curl_exit=28, http_status=200), "blog"))
        self.assertTrue(raw.acceptable(b"<h1>A historical post</h1>", meta, "blog"))

    def test_download_preserves_bytes_and_provenance(self):
        body = b'<html><title>Blog</title><p>caf\xc3\xa9</p></html>'
        meta = dict(curl_exit=0, http_status=200, content_type="text/html",
                    final_url="https://web.archive.org/web/20090601000000id_/http://theroadislife.com/a.htm",
                    requested_url="request", headers="HTTP/2 200", retrieved_at="now")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with patch.object(raw, "ROOT", root), patch.object(raw, "RAW", root / "raw"), \
                    patch.object(raw, "request", return_value=(body, meta)):
                _, result = raw.download(("url", dict(original_url="http://theroadislife.com/a.htm",
                                                     kind="blog", captures=[])))
                self.assertEqual(result["status"], "downloaded")
                self.assertEqual(result["response"]["capture_timestamp"], "20090601000000")
                self.assertEqual((root / result["response"]["path"]).read_bytes(), body)

    def test_corrupt_object_is_repaired_on_download(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with patch.object(raw, "ROOT", root), patch.object(raw, "RAW", root / "raw"):
                meta = raw.store_response(b"original", dict(final_url="https://example.com/"))
                path = root / meta["path"]
                path.write_bytes(b"broken")
                raw.store_response(b"original", dict(final_url="https://example.com/"))
                self.assertEqual(path.read_bytes(), b"original")

    def test_discovery_only_queues_relevant_sources(self):
        body = b'''<a href="/archives/2007/06/post.htm#comments">post</a>
        <img src="http://farm2.static.flickr.com/123/photo.jpg">
        <a href="http://spam.example/">comment link</a>
        <a href="/cgi-bin/mt/mt-search.cgi">search</a>'''
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "source").write_bytes(body)
            with patch.object(raw, "ROOT", root):
                queue = {}
                raw.discover(queue, dict(original_url="http://www.theroadislife.com/",
                                        response=dict(path="source", content_type="text/html")))
                self.assertEqual(len(queue), 2)
                self.assertEqual({e["kind"] for e in queue.values()}, {"blog", "image"})
                self.assertEqual((root / "source").read_bytes(), body)

    def test_resume_does_not_redownload_valid_objects(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "object").write_bytes(b"saved")
            queue = {"https://theroadislife.com/a.htm": dict(
                kind="blog", original_url="https://theroadislife.com/a.htm", status="downloaded",
                response=dict(path="object", sha256=hashlib.sha256(b"saved").hexdigest()))}
            with patch.object(raw, "ROOT", root), patch.object(raw, "RAW", root / "raw"), \
                    patch.object(raw, "seed"), patch.object(raw, "load_queue", return_value=queue), \
                    patch.object(raw, "discover"), patch.object(raw, "report"), \
                    patch.object(raw, "download") as download, \
                    patch("sys.argv", ["download_raw.py", "download"]):
                raw.main()
                download.assert_not_called()

    def test_history_preserves_distinct_aggregate_digests(self):
        url = "https://theroadislife.com/"
        queue = {url: dict(kind="blog", original_url=url, captures=[
            dict(timestamp="20050101000000", original=url, digest="A"),
            dict(timestamp="20050201000000", original=url, digest="A"),
            dict(timestamp="20060101000000", original=url, digest="B"),
            dict(timestamp="20040101000000", original=url, digest="C"),
        ])}
        raw.seed_history(queue)
        self.assertEqual(sum(e["kind"] == "blog-history" for e in queue.values()), 2)


if __name__ == "__main__":
    unittest.main()
