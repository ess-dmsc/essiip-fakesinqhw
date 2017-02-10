import threading
import time
import socket
import logging
import Queue
import sys
import signal
import re

class ConnectionClosedException(Exception):
    pass

class StoppableThread(threading.Thread):
    def __init__(self, object_to_run, name, logger, sleeptime=1):
        super(StoppableThread, self).__init__()
        self._stop = threading.Event()
        self.logger = logger
        self.name = name
        self.object = object_to_run
        self.sleeptime = sleeptime
        self.started = False
        
        if not isinstance(object_to_run, AbstractRunnable):
            raise ValueError("need a AbstractRunnable to run...")
 
    def run(self):
        self.logger.info("Starting thread %s", self.name)        
        
        self.object.set_thread(self)
        self.started = True
        
        while not self.stopped():
            self.object.run()
            time.sleep(self.sleeptime)

        self.object.shutdown() 

    def stop(self):
        if self.started is True:
            self.logger.info("Stopping thread %s", self.name)

        self._stop.set() 

    def stopped(self):
        return self._stop.isSet() 

class AbstractRunnable(object):
    def __init__(self, logger):
        self.thread = None
        self.logger = logger
    
    def set_thread(self, thread):
        self.thread = thread
    
    def run(self):
        pass
    
    def shutdown(self):
        pass
    
class Server(AbstractRunnable):    
    def __init__(self, name, address, port, con_factory, thread_overwatch, logger):
        super(Server, self).__init__(logger)
        self.port = port
        self.address = address
        self.con_factory = con_factory
        self.runningthreads = thread_overwatch
        self.name = name
        self.state = Session(logger)

    def setup(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
        self.socket.settimeout(0.5)
         
        if self.address is None:
            self.address = self.socket.gethostname()

        server_address = (self.address, self.port)
        self.logger.info('Starting server on %s port %s', server_address[0], server_address[1])
 
        self.socket.bind(server_address)
        self.socket.listen(1)
        self.logger.info('Started server listening for new connections') 

    def shutdown(self):
        self.socket.close()

    def run(self):
        con = Connection(self.socket, self.state, self.logger)
        
        if not con.accept():
            return 

        self.logger.info('Connected to client %s', con.get_client_address())
        
        thread = self.con_factory.thread(con)
        thread.start()
        
        self.runningthreads.add(thread)
        
    def get_state(self):
        return self.state
        
        
class Session(object):
    def __init__(self, logger):
        self.logger = logger
        self.array = {}
        
    def set(self, key, parameter):
        self.logger.info("Setting session parameter: %s = %s", key, parameter)
        self.array.update({key:parameter})
    
    def exists(self, key):
        return key in self.array
    
    def get(self, key):
        if self.exists(key):
            return self.array[key]
        else:
            return None
        
    def unset(self, key):
        del self.array[key]
        
class Connection(object):
    def __init__(self, socket, server_state, logger):
        self.socket = socket
        self.connection = None
        self.client_address = '0.0.0.0'
        self.logger = logger
        self.error = None
        # Note: the nonblocking message queue contains only messages which should be executed imediately
        # e.g. StopMessage, StatusMessage.
        # The blocking message queue must be blocking, since: while sputtering there should no other action be done!
        self.msg_queue = Queue.Queue()
        self.msg_nonblocking_queue = Queue.Queue()
        self.buffer = ""
        self.session_obj = Session(logger)
        self.server_session = server_state
 
    def session(self):
        return self.session_obj
    
    def server_session(self):
        return self.server_session

    def accept(self):
        if self.socket is None:
            return False
        try:
            self.connection, self.client_address = self.socket.accept()
            return True
        except socket.timeout:
            return False
 
    def get_message_queue(self):
        return self.msg_queue
   
    def get_nonblocking_message_queue(self):
        return self.msg_nonblocking_queue
           
    def read(self):
        if self.connection is None:
            return None
        
        buffer = []
        new_buffer = ""
 
        while True:           
            data = self.connection.recv(4096)
            self.logger.debug("Received data from %s: %s", self.client_address, repr(data))
            
            # okay, we received a terminating sequence
            if "\n" in data:
                if "\r\n" in data:
                    search = "\r\n"
                else:
                    search = "\n"
                    
                position = data.find(search)
                
                if position == -1:
                    self.logger.error("Could not find the terminating sequence in message. Should never happen")
                    raise ValueError()
                
                new_buffer = data[position+len(search):]
                data = data[:position]
                buffer.append(data)
                break
                
            # if we receive an empty string, then the connection was closed by the other side
            if len(data) == 0:
                if len(buffer) > 0:
                    # thats okay, since we already received some date..
                    break
                else:
                    # hm, so nothing received at all.
                    raise ConnectionClosedException()

            buffer.append(data)
            
            # well that should be enough data...
            if len(buffer) > 10:
                # deprecated
                self.logger.warning("Received more than 40960 bytes of data. Skipping the rest...")
                raise ValueError()
              
        message = self.buffer + ''.join(buffer)
        self.buffer = new_buffer
        
        self.logger.info('Read message: %s', repr(message))
        return message
       
    def set_error(self, error_message):
        self.error = str(error_message)
   
    def get_error(self):
        return self.error
       
    def has_error(self):
        return not self.error is None
 
    def send(self, message):
        if self.connection is None:
            return False
        try:
            self.logger.info('Sending data: %s', repr(message))
            suc = (self.connection.sendall(message))
            return True
 
        except:
            return False
        
    def send_response(self, response):
        if not isinstance(response, Response):
            self.logger.error("Tried to send a response, which was not an instance of Response: %s", str(response))

        try:
            response_string = response.get_response() + "\r\n"

        except:
            self.logger.error("Could get response: " + str(response))
            return False

        if self.send(response_string) is False:
            self.logger.error("Could not send response: %s", response_string)
            return False

        return True

    def shutdown(self, mode):
        if self.connection is None:
            return True

        try:
            self.connection.shutdown(mode)
            return True

        except:
            return False

    def close(self):
        if self.connection is None:
            return True

        try:
            self.shutdown(socket.SHUT_RDWR)
            self.connection.close()
            self.connection = None

        except:
            self.connection = None

    def is_open(self):
        return not self.connection is None

    def get_client_address(self):
        return self.client_address

class ConnectionHandler(AbstractRunnable):
    def __init__(self, connection, message_dispatcher, logger):
        super(ConnectionHandler, self).__init__(logger)
        self.connection = connection
        self.msg_dispatcher = message_dispatcher

    def shutdown(self):
        self.connection.close()

    def run(self):
        try:
            while self.connection.is_open():
                try:   
                    message = self.connection.read()
                except ConnectionClosedException:
                    # now we can stop our thread, since the conenction was closed 
                    self.logger.warning("Connection %s closed by peer", self.connection.get_client_address())
                    self.thread.stop()
                    return 
                except ValueError as  e:
                    # TODO. in case of an error?
                    self.connection.close()
                    self.thread.stop()
                    self.connection.set_error(e)
                    message = ""
                    
                self.msg_dispatcher.dispatch(message, self.connection)
 
        except Queue.Empty:
            return

class MessageDispatcher(object):
    def __init__(self, logger, parser):
        self.logger = logger
        self.handlers = []
        self.parser = parser

    def add(self, message):
        if not isinstance(message, AbstractMessageHandler):
            raise ValueError("message is not an instance of AbstractMessageHandler")

        self.handlers.append(message)

    def dispatch(self, raw_message, connection):
        
        message = self.parser.parse(raw_message)
        
        for handle in self.handlers:
            if handle.can_handle(message, connection):
                
                self.logger.info("Found message handler %s for message %s", handle.__class__.__name__, repr(message))
                
                try:
                    response = handle.handle(message, connection)
                except:
                    self.logger.error("Could not handle message '%s'", message)
                    connection.set_error("Could not handle last message")
                    response = NackResponse()
                
                if connection.send_response(response) is False:
                    self.logger.error("Could not send response <" + repr(response) + "> for message <" + repr(message)+ " >")
                    connection.set_error("Could not send response")

                return

class AbstractMessage(object):
    def __init__(self, raw):
        self.raw = raw
    
    def get_raw(self):
        return self.raw
    
    def __str__(self):
        return "<" + self.__class__.__name__ + ">(" + repr(self.raw) + ")"
    
    def __repr__(self):
        return self.__str__()
    
class UnknownMessage(AbstractMessage):
    pass

class GetterMessage(AbstractMessage):
    def __init__(self, raw, key):
        super(GetterMessage, self).__init__(raw)
        self.key = key
    
    def get_key(self):
        return self.key
        
class SetterMessage(AbstractMessage):
    def __init__(self, raw, key, value):
        super(SetterMessage, self).__init__(raw)
        self.key = key
        self.value = value
        
    def get_key(self):
        return self.key
    
    def get_value(self):
        return self.value
    
class AbstractMessageParser(object):
    def __init__(self, logger):
        self.logger = logger
        
    def parse(self, message):
        raise NotImplementedError()
    
class MessageParser(AbstractMessageParser):
    def __init__(self, logger):
        super(MessageParser, self).__init__(logger)
        self.parsers = []
        
    def add_parser(self, parser):
        if not isinstance(parser, AbstractMessageParser):
            raise ValueError("parser not instance of AbstractMessageParser")
            
        self.parsers.append(parser)
        
    def parse(self, raw_message):
        try:
            for parser in self.parsers:
                message = parser.parse(raw_message)
                if not message is None:
                    self.logger.debug("Message %s parsed by %s", repr(raw_message), parser.__class__.__name__)
                    return message
                
            self.logger.debug("No parser found for message %s", repr(raw_message))
                        
            return UnknownMessage(raw_message)
        except:
            #TODO:
            self.logger.error("Exception while parsing message %s", repr(raw_message))
            return UnknownMessage(raw_message)
        
class GetterMessageParser(AbstractMessageParser):
    def parse(self, message):
        m = re.search("^([a-z]{3,})=\?$", message, re.IGNORECASE)
        if m is None:
            return None
        
        return GetterMessage(message, m.group(1))
    
class SetterMessageParser(AbstractMessageParser):
    def parse(self, message):
        m = re.search("^([a-z]{3,})=([a-z0-9]*)$", message, re.IGNORECASE) 
        if m is None:
            return None
        
        return SetterMessage(message, m.group(1), m.group(2))
            
class AbstractMessageHandler(object):
    def __init__(self, logger):
        self.logger = logger

    def can_handle(self, message, connection):
        if connection.has_error():
            return False

        return self._can_handle(message, connection)

    def _can_handle(self, message, connection):
        raise NotImplementedError()       

    def handle(self, message, connection):
        raise NotImplementedError()

class FallbackMessageHandler(AbstractMessageHandler):
    def can_handle(self, message, connection):
        return True

    def handle(self, message, connection):
        return NackResponse()

class SetterMessageHandler(AbstractMessageHandler):
    def can_handle(self, message, connection):
        return isinstance(message, SetterMessage)
    
    def handle(self, message, connection):
        if not self.can_handle(message, connection):
            self.logger.error("Called handle, even though it said it cannot handle the message...")
            return NackResponse()
        
        key = message.get_key()
        value = message.get_value()
        
        if len(value) == 0:
            connection.session().unset(key)    
        else:
            connection.session().set(key, value)
        return AckResponse()
    
class GetterMessageHandler(AbstractMessageHandler):
    def can_handle(self, message, connection):
        return isinstance(message, GetterMessage)

    def handle(self, message, connection):
        if not self.can_handle(message, connection):
            self.logger.error("Called handle, even though it said it cannot handle the message...")
            return NackResponse()
        
        key = message.get_key()
       
        if not connection.session().exists(key):
            self.logger.warning("Could not find session parameter '%s'", key)
            return NackResponse()
        else:
            return ParameterResponse(key, connection.session().get(key))
        
class Response(object):
    def __init__(self):
        pass

    def __str__(self):
        try:
            return self.get_response()
        except:
            return "<Error: Could not get response in class " + self.__class__.__name__ + ">"

    def __repr__(self):
        return self.__str__()

    def get_response(self):
        return ""

class AckResponse(Response):
    def get_response(self):
        return "ACK"

class NackResponse(Response):
    def get_response(self):
        return "NACK"
    
class ParameterResponse(Response):
    def __init__(self, key, value):
        self.key = key
        self.value = value

    def get_response(self):
        return self.key + "=" + self.value
    
class ConnectionThreadFactory(object):
    def __init__(self, dispatcher, logger):
        self.logger = logger
        self.message_dispatcher = dispatcher
        self.i = -1
    
    def thread(self, connection):
        self.i = self.i + 1
        to_run = ConnectionHandler(connection, self.message_dispatcher, self.logger)
        thread = StoppableThread(to_run, "ConnectionThread-" + str(self.i), self.logger)
        thread.daemon = True
        return thread
 
class ThreadOverwatch(object):
    def __init__(self):
        self.threads = []

    def add(self, thread):
        if not isinstance(thread, StoppableThread):
            raise ValueError("given thread is not an instance of StoppableThread")
            
        self.threads.append(thread)
        self._removeunused()
    
    def _removeunused(self):
        threads_updated = []
        
        for thread in self.threads:
            if not thread.stopped():
                threads_updated.append(thread)
        
        self.threads = threads_updated
    
    def stop(self):
        for thread in self.threads:
            thread.stop()
    
def main():
    serverthread = None
    connectionthread = None

    thread_overwatch = ThreadOverwatch()
    
    def signal_handler(signal, frame):
        logger.info("Stopping all threads ...")
        thread_overwatch.stop()
        sys.exit(0)


    #### CONFIG ####
    logger = logging.getLogger("BeamlineLogger")
    formatter = logging.Formatter('[*] %(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(formatter)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(ch)

    port = 1992
    ip = "127.0.0.1"
    #### CONFIG END ###
    msg_parser = MessageParser(logger)
    msg_parser.add_parser(GetterMessageParser(logger))
    msg_parser.add_parser(SetterMessageParser(logger))

    # TODO:
    msg_dispatcher = MessageDispatcher(logger, msg_parser)
    msg_dispatcher.add(GetterMessageHandler(logger))
    msg_dispatcher.add(SetterMessageHandler(logger))
    msg_dispatcher.add(FallbackMessageHandler(logger))
    
    con_factory = ConnectionThreadFactory(msg_dispatcher, logger)
    
    server = Server("Beamline", ip, port, con_factory, thread_overwatch, logger)
    server.setup()
    serverthread = StoppableThread(server, "Server", logger)
    serverthread.deamon = True 

    signal.signal(signal.SIGINT, signal_handler)
    
    # Add threads to the watchdog...
    thread_overwatch.add(serverthread)

    serverthread.start()

    while True:
        time.sleep(1) 

main()
