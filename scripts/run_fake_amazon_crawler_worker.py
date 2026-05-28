import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer


FAKE_PRODUCT_PAYLOAD = {
    "product_title": "Fake Worker Silicone Can Strainer",
    "price": "$9.99",
    "rating": "4.7",
    "review_count": "321",
    "category_hint": "Kitchen > Tools",
    "bullet_points": [
        "Compact silicone strainer clips onto cans.",
        "Designed for draining beans, tuna, and vegetables.",
    ],
    "review_items": [
        {
            "title": "Saves time",
            "text": "This saves time when draining cans and keeps beans from falling into the sink.",
        },
        {
            "title": "Easy to store",
            "text": "Small enough to store in a drawer and easy to clean after dinner.",
        },
        {
            "text": "I like that it fits different cans and does not take counter space.",
        },
    ],
}


class FakeAmazonCrawlerHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/amazon":
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", "0") or "0")
        raw_body = self.rfile.read(length).decode("utf-8") if length else "{}"

        try:
            body = json.loads(raw_body or "{}")
        except json.JSONDecodeError:
            body = {}

        payload = dict(FAKE_PRODUCT_PAYLOAD)
        payload["input_url"] = body.get("url", "")
        payload["final_url"] = body.get("url", "")

        encoded = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, format, *args):
        return


def main() -> None:
    port = int(os.getenv("FAKE_AMAZON_CRAWLER_PORT", "8765"))
    server = HTTPServer(("127.0.0.1", port), FakeAmazonCrawlerHandler)
    print(f"fake_amazon_crawler_worker: http://127.0.0.1:{port}/amazon")
    server.serve_forever()


if __name__ == "__main__":
    main()
