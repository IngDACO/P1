"""Sirve el PDF de prueba con CORS abierto, para que el navegador lo baje ÍNTEGRO.

⚠️ Pasar 3.5 KB de base64 por el puente de JS ya corrompió el fichero una vez (`atob`
falló). Por HTTP la integridad la garantiza el transporte y se comprueba con el tamaño.
Es local y efímero: se apaga al terminar la prueba.
"""
import http.server, socketserver

class CORS(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()
    def log_message(self, *a):
        pass

with socketserver.TCPServer(("127.0.0.1", 8777), CORS) as s:
    s.serve_forever()
