'''
Created on Jun 13, 2014

@author: Chris Wilson
'''
import socket
import time
import numpy as np
from array import array
from PyQt4 import QtCore
from math import pow


class TestInterface(object):
    fs = 20833
    def get_next_data(self, channels, max_read = 50000):
        return 0.01* np.random.randn(len(channels),self.fs *2 )
    
    

class SGLInterface(QtCore.QObject):
    '''
    classdocs
    '''
    last_sample_read = 0
    acquiring = False
    acquisition_complete = QtCore.pyqtSignal()
    params = None
    adc_scale = None


    def __init__(self,**kwargs):
        '''
        Constructor
        '''
        super(SGLInterface,self).__init__()
        self.net_client = NetClient()
        self.query_acquire()
        self.fs = 20833
        return
        
    
    def close_connect(self):
        self.net_client.close()
        return
    
    def set_adc_scale(self):
        if not self.params:
            self.get_params()
        
        Vdd = self.params['aoRangeMax']
        Vss = self.params['aoRangeMin']
        ADC_bits = 16
        gain = self.params['auxGain']
#         
#         Vdd = 2
#         Vss = -2
#         ADC_bits = 16.
#         gain = 200.
        scale = ((Vdd-Vss)/(pow(2.,16.)))/gain
        self.adc_scale = np.float64(scale)
    
    
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
            if val:
                line = str(key) + ' = ' + str(val)
                self.net_client.send_string(line)
        self.net_client.send_string('') #send blank line at the end as per protocol...
        ok = self.net_client.recieve_ok()
        if ok:
            self.params = params
        return True
    
    def set_save_file(self, filename): # FILENAME should be in 'C:/folder/whatever.bin' format.
        if type(filename) is not str:
            print type(filename)
            print filename
            print 'SPIKEGL FILENAME MUST BE A VALID STRING.'
        sendstring = 'SETSAVEFILE ' + filename
        self.net_client.send_string(sendstring)
        ok = self.net_client.recieve_ok()
        if ok == 'OK':
            print 'SpikeGL save filename set.'
            return True
        else:
            print 'SpikeGL save filename NOT SET'
            return False
    
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
        done =self.set_params(params)
        if not done:
            return False
        self.net_client.send_string('STARTACQ\n')
        time.sleep(.1)
        done = self.net_client.recieve_ok()
        if done == 'OK':
            self.acquiring = True
            print 'SpikeGL acquisition started.'
            return True
        else:
            return False
    
    def stop_acquire(self):
        self.net_client.send_string('STOPACQ\n')
        done = self.net_client.recieve_ok()
        if done == 'OK':
            self.saving = False
            self.acquiring = False
            return True
        else:
            return False
    
    def query_save(self):
        self.net_client.send_string('ISSAVING')
        re = self.net_client.recieve_ok()
        if int(re) == 1:
            self.saving = True
        elif int(re) == 0:
            self.saving = False
        return self.saving
    
    def start_save(self, filename = None):
        if self.query_save():
            return True
        if not self.query_acquire():
            return False
        if filename:
            name_set = self.set_save_file(filename)
        if not name_set:
            return False
        self.net_client.send_string('SETSAVING 1')
        done = self.net_client.recieve_ok()
        if done == 'OK':
            self.saving = True
            print 'SpikeGL save started.'
            return True
        else:
            print 'ERROR: SpikeGL'
            return False
        
    def stop_save(self):
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
        # returns a m by n matrix of m channels with n samples.
        if not self.adc_scale:
            self.set_adc_scale()
        
        if not self.acquiring and not self.query_acquire():
            return False
        start_sample = end_sample - num_samples
        if channels.__class__ is int: #make iterable.
            channels = [channels]
        chan_str = ''
        for ch in channels:
            chan_str = chan_str + str(ch) + '#'
        line = 'GETDAQDATA '+ str(start_sample) + ' ' + str(num_samples) + ' ' + chan_str + ' 1'
#         print line
        self.net_client.send_string(line)
        self.bufstr = self.net_client.recieve_ok(1048576, close, 1000, True)
#         print 'length buffer' +str(len(self.bufstr))
        handshake,_,self.buf = self.bufstr.partition('\n')
        dims = handshake.split(' ')
#         print dims
        if len(self.buf)< int(dims[2])*int(dims[3]) + 2:
            self.buf = self.buf + self.net_client.recieve_ok(20971520, close, 20)
            print 'short'
        try:
            self.data = np.fromstring(self.buf, dtype=np.int16, count = int(dims[3]) * int(dims[2]))
            self.data = self.data.astype(np.float64,copy = False)
        except:
#             print bufstr
            print 'length buff: '+ str(len(self.buf))
            print 'handshake: ' + handshake 
            return None
        
        self.data.shape = (int(dims[3]),int(dims[2]))
#         arr.shape = (int(dims[3]),int(dims[2])) THIS WOULD RESHAPE TO BE FORTRANIC.
        self.data = self.data.T * self.adc_scale
        return
    
    @QtCore.pyqtSlot(list, int) 
    def get_next_data(self, channels, max_read = 5000):
#         times = time.time()
        if self.acquiring or self.query_acquire():
            self.acquiring = True
        else:
            return False
        current_sample = self.get_scancount(close = False)
        
        num_samples = current_sample - self.last_sample_read  #gives the number of samples since the last acquistion.

        if num_samples > max_read:
            num_samples = max_read
            print 'reducing'
        if num_samples == 0:
            self.data = np.array([],dtype = np.float64)
            print 'no data'
            return None
        self.last_sample_read = current_sample
        self.get_daq_data(current_sample, num_samples, channels, False)
#         print time.time()-times
        self.acquisition_complete.emit()
        return
    
    
class NetClient(object):
    
    '''
    classdocs
    '''    
    stream_matrix = []
    recv_str = ''
    
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
        self.sock.settimeout(1)#wait only 0.2 second before timing out.
        self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
#         print 'connect'
        return
    
    def close(self):
        if self.sock:
            self.sock.shutdown(socket.SHUT_RDWR)
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
        except (socket.error, AttributeError) as msg:
            self._reconnect()
        return recieved
    
    def recieve_ok(self, buffer_size = 2048, close = True, iterations = 10, return_all = False):
        self.recv_buffer=[]
        recieved = ''
        tries = 0
        while recieved.find('OK\n') == -1 and recieved.find('ERROR') == -1 and tries < iterations:
            recieved = self.recieve_string(buffer_size)            
            if recieved:
                self.recv_buffer.append(recieved)
            tries += 1
        
#         print tries
        if recieved.find('ERROR') != -1:
            print 'ERROR IN RECIEVING VALUE from recieve_ok method!'
            print recieved
            return None
        elif tries >= iterations:
            print 'Conducted ' +str(iterations) +' without recieving OK'
        else:
            self.recv_str = ''.join(self.recv_buffer)
#             print 'joining'
        if close:
            self.close() #close socket...
        
        
        if return_all is False:
            self.recv_str = self.recv_str[:self.recv_str.find('\nOK')]
        
        if self.recv_str == '':
            return True
        else:
            return self.recv_str 
    
if __name__ == '__main__':
    test = SGLInterface()
    time.sleep(1)
    params = test.get_params()
    time.sleep(1)
    print 'starting acq'
    test.start_acquire(params)
    test.start_save('D:\\test.bin')
    time.sleep(3)    
    
    
    print 'stopping acq'
    test.stop_acquire()
    
    test.close_connect()
    
    pass
        
        