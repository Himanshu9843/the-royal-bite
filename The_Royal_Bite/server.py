"""The Royal Bite: persistent photo galleries and server-side admin authentication."""
import os, json, sqlite3, secrets, hashlib, hmac, time, base64, io, re, threading, warnings
from pathlib import Path
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from http.cookies import SimpleCookie
from urllib.parse import urlsplit
from PIL import Image, ImageOps, UnidentifiedImageError
ROOT=Path(__file__).resolve().parent
DATA=Path(os.environ.get('DATA_DIR',ROOT/'data')); DATA.mkdir(parents=True,exist_ok=True)
UPLOADS=DATA/'uploads'; UPLOADS.mkdir(exist_ok=True)
CREDENTIALS=DATA/'admin.json'
PORT=int(os.environ.get('PORT','8000'))
ORIGIN=os.environ.get('PUBLIC_ORIGIN',f'http://localhost:{PORT}').rstrip('/')
SECURE=ORIGIN.startswith('https://')
SESSIONS={}; FAILURES={}; LOCK=threading.Lock()
CATEGORIES={'kitty-party','birthday-party','celebrations'}
ASSET_NAMES={'brand.webp', 'coffee.webp', 'table.webp', 'pizza.webp', 'vegetables.webp', 'paneer.webp', 'mocktail.webp', 'breads.webp', 'chinese.webp', 'tandoori.webp', 'rajasthani.webp', 'soups.webp', 'chef.webp', 'sandwich.webp', 'dessert.webp'}
Image.MAX_IMAGE_PIXELS=24_000_000

def db():
    c=sqlite3.connect(DATA/'gallery.sqlite3'); c.row_factory=sqlite3.Row; return c
with db() as c:
    c.execute('CREATE TABLE IF NOT EXISTS photos(id TEXT PRIMARY KEY, title TEXT, category TEXT, date TEXT, created REAL)')

def password_hash(p,salt):
    return hashlib.scrypt(p.encode(),salt=bytes.fromhex(salt),n=16384,r=8,p=1).hex()

class Handler(BaseHTTPRequestHandler):
    server_version='RoyalBite'
    def log_message(self,fmt,*args):
        # Never log request bodies, credentials, or session tokens.
        pass
    def send(self,status,body,ctype='application/json',cookie=None):
        if isinstance(body,(dict,list)): body=json.dumps(body).encode()
        elif isinstance(body,str): body=body.encode()
        self.send_response(status); self.send_header('Content-Type',ctype)
        self.send_header('Content-Length',str(len(body))); self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Referrer-Policy','same-origin'); self.send_header('X-Frame-Options','SAMEORIGIN')
        self.send_header('Cache-Control','no-store' if self.path.startswith('/api/') else 'no-cache')
        self.send_header('Content-Security-Policy',"default-src 'self'; img-src 'self' data:; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'self'")
        if cookie: self.send_header('Set-Cookie',cookie)
        self.end_headers(); self.wfile.write(body)
    def session(self):
        try:
            cookies=SimpleCookie(self.headers.get('Cookie','')); token=cookies['rb_session'].value
            with LOCK:
                s=SESSIONS.get(token)
                if s and s['expires']>time.time(): return token,s
                SESSIONS.pop(token,None)
        except (KeyError,ValueError): pass
        return None,None
    def cookie(self,token,age=28800):
        return f'rb_session={token}; Path=/; HttpOnly; SameSite=Strict; Max-Age={age}'+('; Secure' if SECURE else '')
    def auth(self):
        token,s=self.session()
        if not s: self.send(401,{'error':'Please sign in again.'}); return None
        if not hmac.compare_digest(self.headers.get('X-CSRF-Token',''),s['csrf']):
            self.send(403,{'error':'Invalid security token. Reload and sign in again.'}); return None
        return token
    def body(self):
        if self.headers.get('Content-Type','').split(';')[0]!='application/json': raise ValueError('JSON request required.')
        length=int(self.headers.get('Content-Length','0'))
        if not 0<length<=14_100_000: raise ValueError('Request too large or empty.')
        result=json.loads(self.rfile.read(length))
        if not isinstance(result,dict): raise ValueError('Invalid request.')
        return result
    def do_GET(self):
        path=urlsplit(self.path).path
        if path=='/menu.pdf':
            return self.send(200,(ROOT/'site/menu.pdf').read_bytes(),'application/pdf')
        if path.startswith('/assets/') and path.split('/')[-1] in ASSET_NAMES:
            return self.send(200,(ROOT/'site/assets'/path.split('/')[-1]).read_bytes(),'image/webp')
        if path=='/api/photos':
            with db() as c: rows=[dict(r) for r in c.execute('SELECT id,title,category,date FROM photos ORDER BY created DESC')]
            for r in rows: r['url']='/uploads/'+r['id']+'.webp'
            return self.send(200,rows)
        if path=='/api/session':
            _,s=self.session(); return self.send(200,{'authenticated':bool(s),'csrf':s['csrf'] if s else ''})
        if re.fullmatch(r'/uploads/[a-f0-9]{32}\.webp',path):
            p=UPLOADS/Path(path).name
            if p.exists(): return self.send(200,p.read_bytes(),'image/webp')
            return self.send(404,{'error':'Photo not found.'})
        if path in {'/','/menu','/chef-special','/kitty-party','/birthday-party','/celebrations','/gallery','/visit','/admin'}:
            return self.send(200,(ROOT/'site/index.html').read_bytes(),'text/html; charset=utf-8')
        return self.send(404,{'error':'Not found.'})
    def do_POST(self): self.mutate()
    def do_DELETE(self): self.mutate()
    def mutate(self):
        if self.headers.get('Origin')!=ORIGIN:
            return self.send(403,{'error':'Untrusted origin. Check PUBLIC_ORIGIN on the server.'})
        path=urlsplit(self.path).path
        try:
            if path=='/api/login' and self.command=='POST':
                data=self.body(); ip=self.client_address[0]; now=time.time()
                with LOCK:
                    FAILURES[ip]=[t for t in FAILURES.get(ip,[]) if now-t<900]
                    if len(FAILURES[ip])>=5: return self.send(429,{'error':'Too many attempts. Please wait 15 minutes.'})
                if not CREDENTIALS.exists(): return self.send(503,{'error':'Admin access has not been configured by the host.'})
                conf=json.loads(CREDENTIALS.read_text()); password=data.get('password','')
                if not isinstance(password,str) or len(password)>256: raise ValueError('Invalid password.')
                if not hmac.compare_digest(password_hash(password,conf['salt']),conf['hash']):
                    with LOCK: FAILURES[ip].append(now)
                    return self.send(401,{'error':'Incorrect password.'})
                token=secrets.token_hex(32); csrf=secrets.token_hex(32)
                with LOCK:
                    FAILURES.pop(ip,None)
                    for k,v in list(SESSIONS.items()):
                        if v['expires']<=now: SESSIONS.pop(k,None)
                    if len(SESSIONS)>100: SESSIONS.clear()
                    SESSIONS[token]={'csrf':csrf,'expires':now+28800}
                return self.send(200,{'csrf':csrf},cookie=self.cookie(token))
            token=self.auth()
            if not token: return
            if path=='/api/logout' and self.command=='POST':
                with LOCK: SESSIONS.pop(token,None)
                return self.send(200,{'ok':True},cookie=self.cookie('',0))
            if path=='/api/photos' and self.command=='POST':
                d=self.body(); title=d.get('title',''); category=d.get('category'); date=d.get('date','')
                if not isinstance(title,str) or not 1<=len(title.strip())<=120: raise ValueError('A caption of 1–120 characters is required.')
                if category not in CATEGORIES or d.get('consent') is not True: raise ValueError('Choose a page and confirm publishing permission.')
                if not isinstance(date,str) or (date and not re.fullmatch(r'\d{4}-\d{2}-\d{2}',date)): raise ValueError('Invalid date.')
                if date:
                    from datetime import date as Date
                    Date.fromisoformat(date)
                raw=base64.b64decode(d.get('image',''),validate=True)
                if len(raw)>10*1024*1024: raise ValueError('Photos must be smaller than 10 MB.')
                with warnings.catch_warnings():
                    warnings.simplefilter('error',Image.DecompressionBombWarning)
                    im=Image.open(io.BytesIO(raw))
                    if im.format not in {'JPEG','PNG','WEBP'}: raise ValueError('Use a JPG, PNG or WebP photograph.')
                    im=ImageOps.exif_transpose(im); im.thumbnail((2400,2400)); im=im.convert('RGB')
                photo_id=secrets.token_hex(16); output=UPLOADS/(photo_id+'.webp')
                im.save(output,'WEBP',quality=88) # Re-encode pixels; no original filename or EXIF metadata is published.
                try:
                    with db() as c: c.execute('INSERT INTO photos VALUES(?,?,?,?,?)',(photo_id,title.strip(),category,date,time.time()))
                except Exception:
                    output.unlink(missing_ok=True); raise
                return self.send(201,{'ok':True,'id':photo_id})
            if self.command=='DELETE' and re.fullmatch(r'/api/photos/[a-f0-9]{32}',path):
                photo_id=path.rsplit('/',1)[1]
                with db() as c: c.execute('DELETE FROM photos WHERE id=?',(photo_id,))
                (UPLOADS/(photo_id+'.webp')).unlink(missing_ok=True)
                return self.send(200,{'ok':True})
            return self.send(404,{'error':'Not found.'})
        except (ValueError,TypeError,KeyError,UnidentifiedImageError,Image.DecompressionBombError,Image.DecompressionBombWarning, OSError):
            return self.send(400,{'error':'Invalid upload or request. Use a valid JPG, PNG or WebP under 10 MB and complete all fields.'})
        except Exception:
            return self.send(500,{'error':'Unable to save changes. Please try again or contact your host.'})

if __name__=='__main__':
    print(f'The Royal Bite: {ORIGIN} (bind: {os.environ.get("HOST","127.0.0.1")}:{PORT})',flush=True)
    print('Configure HTTPS before public deployment. Keep data on persistent storage.',flush=True)
    ThreadingHTTPServer((os.environ.get('HOST','127.0.0.1'),PORT),Handler).serve_forever()
