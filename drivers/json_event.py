################################################################################
# Resonance Project                                                            #
# Resonance implemented with Pyretic platform                                  #
# author: Hyojoon Kim (joonk@gatech.edu)                                       #
# author: Nick Feamster (feamster@cc.gatech.edu)                               #
# author: Muhammad Shahbaz (muhammad.shahbaz@gatech.edu)                       #
################################################################################

from threading import Thread
import socket
import SocketServer
import json

from pyretic.lib.corelib import *
from pyretic.pyresonance.fsm_policy import Event

class JSONEvent():

    port = 50001
    
    def __init__(self, addr='127.0.0.1'):
        self.handler = None
        self.addr = addr
        self.port = JSONEvent.port
        JSONEvent.port += 1
        p1 = Thread(target=self.event_listener)
        p1.daemon = True
        p1.start()
        
    def register_callback(self,handler):
        self.handler = handler

    def event_listener(self):

        def parse_json(data):
            return json.loads(data)

        def unicode_dict_to_ascii(d):
            new_d = dict()
            for k,v in d.items():
                if isinstance(v,str):
                    new_d[k.encode('ascii','ignore')] = v.encode('ascii','ignore')
                elif isinstance(v,unicode):
                    new_d[k.encode('ascii','ignore')] = v.encode('ascii','ignore')
                elif isinstance(v,dict):   
                    new_d[k.encode('ascii','ignore')] = unicode_dict_to_ascii(v)
                else:
                    new_d[k.encode('ascii','ignore')] = v           
                    
            return new_d


        message = ''
    
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((self.addr, self.port))
        s.listen(1)
        
        while 1:
            message = ''
            
            conn, addr = s.accept()
            print 'Received connection from', addr
            
            while 1:
                data = conn.recv(1024)
                
                if not data: 
                    conn.close()
                    break
                
                message = message + data
                unicode_dict = parse_json(message)
                ascii_dict = unicode_dict_to_ascii(unicode_dict)

                def convert(field,value):
                    if field == 'srcip' or field == 'dstip':
                        return IPAddr(value)
                    elif field == 'srcmac' or field == 'dstmac':
                        return EthAddr(value)
                    else:
                        return int(value)

                name = ascii_dict['name']
                value = ascii_dict['value']
                if not 'flow' in ascii_dict:
                    flow = None
                else:
                    flow = frozendict(
                        { k : convert(k,v) for 
                          k,v in ascii_dict['flow'].items() 
                          if v } )
            
                if self.handler:
                    self.handler(Event(name,value,flow))
                return_value = 'ok'
                conn.sendall(return_value)


