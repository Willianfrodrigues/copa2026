import json
from http.server import BaseHTTPRequestHandler
from _helpers import verify_user, create_token, init_db, get_db, json_response, error_response, cors_headers

def init_log_table():
    conn = get_db()
    cur  = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS login_log (
            id         SERIAL PRIMARY KEY,
            username   TEXT NOT NULL,
            ip         TEXT,
            user_agent TEXT,
            success    BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """)
    conn.commit()
    cur.close(); conn.close()

def log_access(username, ip, user_agent, success=True):
    try:
        init_log_table()
        conn = get_db()
        cur  = conn.cursor()
        cur.execute(
            "INSERT INTO login_log (username, ip, user_agent, success) VALUES (%s, %s, %s, %s)",
            (username, ip, user_agent, success)
        )
        conn.commit()
        cur.close(); conn.close()
    except Exception:
        pass  # nunca quebra o login por causa do log

class handler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self.send_response(200)
        for k, v in cors_headers().items():
            self.send_header(k, v)
        self.end_headers()

    def do_POST(self):
        try:
            init_db()
            length = int(self.headers.get("Content-Length", 0))
            body   = json.loads(self.rfile.read(length))

            username = body.get("username", "")
            ip       = self.headers.get("X-Forwarded-For", self.headers.get("X-Real-IP", "—")).split(",")[0].strip()
            ua       = self.headers.get("User-Agent", "—")[:200]

            user = verify_user(username, body.get("password", ""))
            if not user:
                log_access(username, ip, ua, success=False)
                resp = error_response("Usuário ou senha incorretos.", 401)
            else:
                log_access(user["username"], ip, ua, success=True)
                token = create_token(user)
                resp  = json_response({
                    "token":     token,
                    "username":  user["username"],
                    "role":      user["role"],
                    "client":    user["client"],
                    "campaigns": user["campaigns"]
                })

            self.send_response(resp["statusCode"])
            for k, v in resp["headers"].items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(resp["body"].encode())

        except Exception as e:
            resp = error_response(str(e), 500)
            self.send_response(500)
            for k, v in resp["headers"].items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(resp["body"].encode())
