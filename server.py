"""Loopback-only local demo server. Python standard library, zero install step."""
import argparse
import json
import mimetypes
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from agent.agent import run_agent,configured
from core.data import STORE

WEB=Path(__file__).resolve().parent/'web'

class Handler(BaseHTTPRequestHandler):
    server_version='PaymentClarity/1.0'
    def log_message(self,format,*args):pass
    def send(self,status,body,kind='application/json'):
        if kind=='application/json':body=json.dumps(body,ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header('Content-Type',kind+'; charset=utf-8')
        self.send_header('Content-Length',str(len(body)))
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Referrer-Policy','no-referrer')
        self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
        self.end_headers()
        try:self.wfile.write(body)
        except (BrokenPipeError,ConnectionResetError):pass
    def allowed_host(self):
        return self.headers.get('Host') in {f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}'}
    def do_GET(self):
        if not self.allowed_host():return self.send(403,{'error':'Local access only'})
        path=urlparse(self.path).path
        if path=='/api/health':return self.send(200,{'status':'ok','version':STORE.version,'live_ai_configured':configured(),'payments':len(STORE.payments),'clients':len(STORE.clients)})
        if path=='/api/payments':return self.send(200,{'payments':list(STORE.payments.values()),'version':STORE.version})
        allowed={'/':'index.html','/app.js':'app.js','/styles.css':'styles.css','/favicon.svg':'favicon.svg'}
        if path not in allowed:return self.send(404,{'error':'Not found'})
        file=WEB/allowed[path]
        return self.send(200,file.read_bytes(),mimetypes.guess_type(file.name)[0] or 'text/plain')
    def do_POST(self):
        if not self.allowed_host():return self.send(403,{'error':'Local access only'})
        origin=self.headers.get('Origin')
        if origin and origin not in {f'http://127.0.0.1:{self.server.server_port}',f'http://localhost:{self.server.server_port}'}:return self.send(403,{'error':'Cross-origin request denied'})
        if self.headers.get('Sec-Fetch-Site')=='cross-site':return self.send(403,{'error':'Cross-site request denied'})
        if urlparse(self.path).path!='/api/investigate':return self.send(404,{'error':'Not found'})
        if self.headers.get('Content-Type','').split(';')[0]!='application/json':return self.send(415,{'error':'JSON required'})
        try:
            length=int(self.headers.get('Content-Length','0'))
            if not 0<length<=8192:return self.send(413,{'error':'Request must be under 8 KB'})
            body=json.loads(self.rfile.read(length))
            if not isinstance(body,dict):raise ValueError()
            payment_id=body.get('payment_id');question=body.get('question','What review is required and what is the next action?')
            if not isinstance(payment_id,str) or len(payment_id)>50 or not isinstance(question,str) or not 1<=len(question.strip())<=2000:raise ValueError()
        except (ValueError,TypeError,UnicodeError):return self.send(400,{'error':'Supply a payment ID and a question of 1–2000 characters.'})
        try:return self.send(200,run_agent(question=question,payment_id=payment_id))
        except KeyError:return self.send(404,{'error':'Payment not found'})
        except Exception:return self.send(500,{'error':'The investigation could not be completed. Check the source data and try again.'})

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8780);args=parser.parse_args()
    with ThreadingHTTPServer(('127.0.0.1',args.port),Handler) as server:
        print(f'Payment Clarity is running at http://127.0.0.1:{args.port}',flush=True)
        print('Local synthetic-data demo. Press Ctrl+C to stop.',flush=True)
        try:server.serve_forever()
        except KeyboardInterrupt:pass

if __name__=='__main__':main()
