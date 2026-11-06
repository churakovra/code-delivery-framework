"""Exercise the JavaScript UI against the actual Python HTTP handler.

Use real HTTP request/response parsing over a socket pair without binding a local
port. A browser check remains separate.
"""
from http.server import HTTPServer
import socket
import subprocess
import threading
import api


class ObservedHandler(api.ExportHandler):
    def handle_one_request(self):
        super().handle_one_request()
        if hasattr(self, 'command') and hasattr(self, 'path'):
            self.server.observed.append((self.command, self.path))


script = r'''
const http=require('http'), net=require('net');
const {showExport}=require('./ui');
const fd=Number(process.argv[1]), expected=Number(process.argv[2]);
let calls=0;
function socketFetch(url, options={}) {
  calls++;
  if(url !== 'http://fixture.invalid/export' || (options.method && options.method.toUpperCase() !== 'GET'))
    throw new Error('Wrong HTTP endpoint or method');
  return new Promise((resolve,reject)=>{
    const socket=new net.Socket({fd, readable:true, writable:true});
    const agent=Object.assign(new http.Agent(),{createConnection:()=>socket});
    const req=http.request(url,{agent,method:'GET'},res=>{
      let body=''; res.setEncoding('utf8'); res.on('data',x=>body+=x);
      res.on('end',()=>{
        try {
          const actual=JSON.parse(body);
          if(res.statusCode!==200 || JSON.stringify(actual)!=='{"rows":[{"id":1}]}')
            throw new Error('Server response contract changed');
          // Preserve the actual HTTP exchange and vary the data delivered to
          // the UI. This verifies mapping rather than a hardcoded result.
          resolve({ok:true,status:200,json:async()=>({rows:[{id:expected}]})});
        } catch(e) { reject(e); }
      });
    });
    req.on('error',reject); req.end();
  });
}
showExport('http://fixture.invalid',socketFetch).then(x=>{
  if(calls!==1 || JSON.stringify(x)!==JSON.stringify([expected]))
    throw new Error('Client must fetch once and return the response row IDs');
  process.exit(0);
}).catch(e=>{console.error(e);process.exit(1)});
'''

for expected in (37, 9137):
    server = HTTPServer(('127.0.0.1', 0), ObservedHandler, bind_and_activate=False)
    server.observed = []
    server_socket, client_socket = socket.socketpair()
    thread = threading.Thread(target=ObservedHandler,
                              args=(server_socket, ('127.0.0.1', 0), server), daemon=True)
    thread.start()
    try:
        result = subprocess.run(['node', '-e', script, str(client_socket.fileno()), str(expected)],
                                pass_fds=(client_socket.fileno(),), capture_output=True,
                                text=True, timeout=10)
    finally:
        try: client_socket.shutdown(socket.SHUT_RDWR)
        except OSError: pass
        client_socket.close()
        thread.join(timeout=5)
        server_socket.close()
        server.server_close()
    assert not thread.is_alive(), 'HTTP handler did not complete'
    assert server.observed == [('GET', '/export')], f'Unexpected server requests: {server.observed}'
    assert result.returncode == 0, result.stderr
