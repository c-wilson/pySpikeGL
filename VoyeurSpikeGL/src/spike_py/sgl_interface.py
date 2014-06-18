'''
Created on Jun 13, 2014

@author: Chris Wilson
'''
import socket
import time
import numpy as np
from array import array

import matplotlib.pyplot as plt


class SGLInterface(object):
    '''
    classdocs
    '''
    last_sample_read = 0
    acquiring = False


    def __init__(self):
        '''
        Constructor
        '''
        self.net_client = NetClient()
        self.query_acquire()
        return
    
    def close_connect(self):
        self.net_client.close()
        return
    
    def get_ver(self):
        #returns version number.
        self.net_client.send_string('GETVERSION')
        self.version = self.net_client.recieve_ok()
        self.net_client.close()
        print self.version
        return
    
    def get_params(self):
        #returns a string of parameters from net_client.
        self.net_client.send_string('GETPARAMS')
        param_string = self.net_client.recieve_ok()
        param_list = param_string.splitlines()
        self.params = dict()
        for param in param_list:
            param_split = param.split(' = ') #split the keys and the values
            try: # convert string into numeric when possible.
                param_split[1] = int(param_split[1])     
            except:
                try:
                    param_split[1] = float(param_split[1])
                except:
                    pass
            self.params[param_split[0]] = param_split[1]
        return self.params
    
    def set_params(self,params):
        if self.query_acquire():
            print 'Cannot set params during acquisition.'
            return False
        self.net_client.send_string('SETPARAMS')
        rcd = self.net_client.recieve_string()
        if rcd.find('READY') == -1:
            print 'SPIKEGL did not return READY for params.'
            return False
        for key, val in params.iteritems():
            line = str(key) + ' = ' + str(val)
            self.net_client.send_string(line)
        self.net_client.send_string('') #send blank line at the end as per protocol...
        self.net_client.recieve_ok()
        return True
    
    def set_save_file(self, filename): # FILENAME should be in 'C:/folder/whatever.bin' format.
        if type(filename) is not str:
            print 'SPIKEGL FILENAME MUST BE A VALID STRING.'
        sendstring = 'SETSAVEFILE ' + filename
        self.net_client.send_string(sendstring)
        self.net_client.recieve_ok()
        return
    
    def query_acquire(self):
        self.net_client.send_string('ISACQ')
        re = self.net_client.recieve_ok()
        if int(re) == 1:
            self.acquiring = True
        elif int(re) == 0:
            self.acquiring = False
        return self.acquiring
    
    def start_acquire(self, params = None):
        if not params:
            params = self.get_params()
        if type(params) != dict:
            print 'PARAMETERS MUST BE IN FORM OF DICTIONARY'
            return False
        if self.query_acquire():
            return True
        self.set_params(params)
        self.net_client.send_string('STARTACQ')
        done = self.net_client.recieve_ok()
        if done:
            self.acquiring = True
        return done
    
    def stop_acquire(self):
        self.net_client.send_string('STOPACQ')
        done = self.net_client.recieve_ok()
        if done:
            self.saving = False
            self.acquiring = False
        return done
    
    def query_save(self):
        self.net_client.send_string('ISSAVING')
        re = self.net_client.recieve_ok()
        if int(re) == 1:
            self.saving = True
        elif int(re) == 0:
            self.saving = False
        return self.saving
    
    def stop_save(self, filename = None):
        if self.query_save():
            return True
        if not self.query_acquire():
            return False
        if filename:
            self.set_save_file(filename)
        self.net_client.send_string('SETSAVING 1')
        done = self.net_client.recieve_ok()
        if done:
            self.saving = True
        return done
        
    def save_stop(self):
        self.net_client.send_string('SETSAVING 0')
        done = self.net_client.recieve_ok()
        if done:
            self.saving = False
        return done
          
    def hide_console(self):
        self.net_client.send_string('CONSOLEHIDE')
        self.net_client.recieve_ok()
        return 
    
    def unhide_console(self):
        self.net_client.send_string('CONSOLEUNHIDE')
        self.net_client.recieve_ok()
        return 
    
    def get_time(self):
        self.net_client.send_string('GETTIME')
        time = self.net_client.recieve_ok()
        return float(time)
    
    def get_scancount(self, close = True):
        if not self.acquiring and not self.query_acquire():
            return False
        self.net_client.send_string('GETSCANCOUNT')
        return int(self.net_client.recieve_ok(close=close))
    
    def query_channels(self):
        self.net_client.send_string('GETCHANNELSUBSET')
        self.channels = self.net_client.recieve_ok()
        return self.channels
    
    
    def get_daq_data(self, end_sample, num_samples, channels, close = True, ):
        # returns a m by n matrix of m samples from n channels.
        if not self.acquiring and not self.query_acquire():
            return False
        start_sample = end_sample - num_samples
        if channels.__class__ is int: #make iterable.
            channels = [channels]
        chan_str = ''
        for ch in channels:
            chan_str = chan_str + str(ch) + '#'
        line = 'GETDAQDATA '+ str(start_sample) + ' ' + str(num_samples) + ' ' + chan_str + ' 1'
        print line
        self.net_client.send_string(line)
        bufstr = self.net_client.recieve_ok(20971520, close, 20, True)
        print 'length buffer' +str(len(bufstr))
        handshake,_,buf = bufstr.partition('\n')
        dims = handshake.split(' ')
        if len(buf)< int(dims[2])*int(dims[3]) + 2:
            buf = buf + self.net_client.recieve_ok(20971520, close, 20)
            print 'short'
        try:
            arr = np.array(array('h',buf[:-3]))
        except:
            print bufstr
#             print 'length buff: '+ str(len(buf))
#             print 'handshake: ' + handshake + _ + buf
            return None
        arr.shape = (int(dims[3]),int(dims[2]))
        return arr
    
    def get_next_data(self, channels, max_read = 5000):
        if self.acquiring or self.query_acquire():
            self.acquiring = True
        else:
            return False
        current_sample = self.get_scancount(close = False)
        num_samples = current_sample - self.last_sample_read  #gives the number of samples since the last acquistion.
        if num_samples > max_read:
            num_samples = max_read
        if num_samples == 0:
            return None
        samples = self.get_daq_data(current_sample, num_samples, channels, False)
        self.last_sample_read = current_sample
        return num_samples, samples
    
    
class NetClient(object):
    
    '''
    classdocs
    '''    
    stream_matrix = []
    
    def __init__(self,hostname = 'localhost', port = 4142):
        self.HOSTNAME = hostname
        self.PORT = port
        try:
            self.connect()
            self.close()
        except socket.error as msg:
            self.close()   
        return
    
    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # IPv4, TCP (UDP is socket.SOCK_DGRAM)
        self.sock.connect((self.HOSTNAME,self.PORT))
        self.sock.settimeout(0.5)#wait only 0.5 second before timing out.
        return
    
    def close(self):
        if self.sock:
            self.sock.close()
        self.sock = None
        return
    
    def _reconnect(self):
        if self.sock:
            self.close()
        self.connect()
        return
    
    def send_string(self, send_string, line_end = '\n'):
        if type(send_string) is not str:
            print 'The input to this function must be a string.'
            return None
        send_string = send_string + line_end # add line ending to the string.
        if not self.sock:
            self.connect() 
            time.sleep(0.001)           
        try:
            self.sock.sendall(send_string)
        except socket.error as msg:
            print "reconnecting"
            self._reconnect()
            self.send_string(send_string, line_end)
        return
    
    def recieve_string(self, buffer_size = 4096):
        recieved = ''
        try:
            recieved = self.sock.recv(buffer_size)
        except socket.error as msg:
            self._reconnect()
        return recieved
    
    def recieve_ok(self, buffer_size = 2048, close = True, iterations = 10, return_all = False):
        recieved = self.recieve_string(buffer_size)
        tries = 0
        while recieved.find('OK\n') == -1 and recieved.find('ERROR') == -1 and tries < iterations:
            if recieved is None:
                recieved = ''
            recieved = recieved + self.recieve_string(buffer_size)
            tries += 1
            time.sleep(0.01)
        if recieved.find('ERROR') != -1:
            print 'ERROR IN RECIEVING VALUE from recieve_ok method!'
            print recieved
            return None
        if tries >= iterations:
            print 'Conducted ' +str(iterations) +' without recieving OK'
        if close:
            self.close() #close socket...
        if return_all is True:
            ret = recieved
        else:
            ret = recieved[:recieved.find('\nOK')]
        
        if ret == '':
            return True
        else:
            return ret 
    
if __name__ == '__main__':
    test = SGLInterface()
    a=test.get_next_data([1],10000)
    a = a[1]
    time.sleep(0.1)
    for i in range (400):
        u = test.get_next_data([1],10000)
        if u:
            a = np.append(a, u[1], 0)
        time.sleep(0.1)
        print str(i)
    plt.plot(a)
    plt.show()
        
    pass
        
        