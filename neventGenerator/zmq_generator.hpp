#pragma once

#include <assert.h>
#include <exception>
#include <sstream>
#include <string>

#include <zmq.h>

#include "header.hpp"
#include "serialiser.hpp"

namespace generator {

/*! \struct ZmqGen
 *  Uses 0MQ as data the streamer.
 *
 *  \author Michele Brambilla <mib.mic@gmail.com>
 *  \date Wed Jun 08 15:19:27 2016
 * @tparam mode_selector transmitter = 0, receiver = 1
 */
template <int mode_selector> struct ZmqGen {
  static const int max_header_size = 10000;
  static const int max_recv_size = 100000000;

  ZmqGen(const std::string &SocketAddress) {
    context = zmq_ctx_new();
    int rc;
    if (!mode_selector) {
      socket = zmq_socket(context, ZMQ_PUSH);
      std::cout << "tcp://" << SocketAddress << "\n";
      rc = zmq_bind(socket, ("tcp://" + SocketAddress).c_str());
      //    socket.setsockopt(zmq::SNDHWM, 100);
    } else {
      socket = zmq_socket(context, ZMQ_PULL);
      std::cout << "tcp://" << SocketAddress << "\n";
      rc = zmq_connect(socket, ("tcp://" + SocketAddress).c_str());
    }
    assert(rc == 0);
  }

  /// \brief
  template <typename T> void send(const T *data, int size, const int flag = 0) {
    /*! @tparam T data type
     *  @param data data to be sent
     *  @param size number of elements
     *  @param flag optional flag (default = 0) */
    // std::cout << "->" << data
    //           << "," << size
    //           << std::endl;
    zmq_send(socket, data, size, flag);
    // std::cout << std::endl;
  }

  template <typename T>
  void send(std::string h, T *data, int nev, SINQAmorSim::NoSerialiser<T>) {
    /*! @tparam T data type
     *  @param h data header
     *  @param data pointer to data array to be sent
     *  @param nev number of elements in data array */
    /*! Sends two different messages for header and data. If there are no
        events, data is not sent */

    if (nev > 0) {
      zmq_send(socket, &h[0], h.size(), ZMQ_SNDMORE);
      zmq_send(socket, data, nev * sizeof(T), 0);
    } else {
      zmq_send(socket, &h[0], h.size(), 0);
    }
    // std::cout << "->" << h
    //           << "," << h.size()
    //           << "," << nev
    //           << std::endl;
  }

  template <typename T>
  void send(std::string h, T *data, int nev,
            SINQAmorSim::FlatBufSerialiser<T>) {
    // /*! @tparam T data type
    //  *  @param h data header
    //  *  @param data pointer to data array to be sent
    //  *  @param nev number of elements in data array */
    // /*! Serialises the message using FlatBuffers and sends it */
    // SINQAmorSim::FlatBufSerialiser<T> s;
    // s(h.c_str(),data,nev);
    // zmq_send(socket,(char*)s(),s.size(),0);
    // // std::cout << "->" << h
    // //           << "," << h.size()
    // //           << "," << nev
    // //           << std::endl;

    // // std::ofstream of("first.out",std::ofstream::binary);
    // // of.write((char*)s(h.c_str(),data,nev),s.size());
    // // of.close();
  }

  template <typename T>
  int recv(std::string &h, std::vector<T> &data, SINQAmorSim::NoSerialiser<T>) {
    /*! @tparam T data type
     *  @param h string containing received data header
     *  @param data vector containing received event data
     *  @result pid packet ID */
    /*! Receives the message split into header and events. Parse header to
        determine the expected number of events. If equal 0 does not wait for
        events. If greater than 0 and ZMQ_RCVMORE == true receives event
        data. Otherwise throws an error.
    */
    int rcvmore;
    int s = zmq_recv(socket, &h[0], max_header_size, 0);
    zmq_getsockopt(socket, ZMQ_RCVMORE, &rcvmore, &optlen);

    auto info = parse_header(h);
    std::cout << " pid =  " << info.first << std::endl;
    std::cout << " nev =  " << info.second << std::endl;

    uint64_t *x;
    if (rcvmore && (info.second > 0)) {
      if (info.second > data.size()) {
        data.resize(info.second);
      }
      int s = zmq_recv(socket, &data[0], info.second, 0);
    } else if (rcvmore != info.second)
      std::cout << "Error receiving data: "
                << "recvmore = " << rcvmore << "info.second = " << info.second
                << std::endl;
    return info.first;
  }

  template <typename T>
  int recv(std::string &h, std::vector<T> &data,
           SINQAmorSim::FlatBufSerialiser<T>) {
    /*! @tparam T data type
     *  @param h string containing received data header
     *  @param data vector containing received event data
     *  @result pid packet ID */
    /*! Receives the serialised message and unserialise it. */

    // zmq_msg_t msg;
    // SINQAmorSim::FlatBufSerialiser<T> s;

    // int rc = zmq_msg_init (&msg);
    // assert (rc == 0);
    // zmq_msg_recv (&msg,socket,0);

    // std::cout << "\tzmq_recv size: " << zmq_msg_size(&msg) << std::endl;

    // s.extract(reinterpret_cast<char*>(zmq_msg_data(&msg)),h,data);
    // zmq_msg_close (&msg);
    // auto info = parse_header(h);
    // std::cout << " pid =  " << info.first << std::endl;
    // std::cout << "n events = " << info.second << std::endl;

    // return info.first;
  }

private:
  void *context; /// pointer to 0MQ context
  void *socket;  /// pointer to 0MQ socket
  char *d = NULL;
  int max_event_size = 0;
  size_t optlen = sizeof(int);
};

} // namespace generator
