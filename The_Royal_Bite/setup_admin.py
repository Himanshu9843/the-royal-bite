"""Run on the server to set/change the admin password. No plaintext password saved."""
import getpass, json, secrets, os
from pathlib import Path
from server import DATA,password_hash
p=getpass.getpass('Choose admin password (at least 12 characters): ')
if len(p)<12 or len(p)>256: raise SystemExit('Use 12–256 characters.')
if p!=getpass.getpass('Confirm password: '): raise SystemExit('Passwords did not match.')
salt=secrets.token_hex(16); target=DATA/'admin.json'
target.write_text(json.dumps({'salt':salt,'hash':password_hash(p,salt)})); os.chmod(target,0o600)
print('Admin password configured. Restart the server to invalidate old sessions.')
