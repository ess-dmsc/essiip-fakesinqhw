#pragma once

#include <ctime>
#include <future>
#include <random>

#include "Configuration.hpp"
#include "Stats.hpp"

#if HAVE_ZMQ
#include "zmq_generator.hpp"
#endif

#include "file_writer.hpp"
#include "kafka_generator.hpp"

#include "control.hpp"
#include "timestamp_generator.hpp"

using milliseconds = std::chrono::milliseconds;
using nanoseconds = std::chrono::nanoseconds;

/*! \class Generator
 *  \author Michele Brambilla <mib.mic@gmail.com>
 *  \date Wed Jun 08 15:19:52 2016 */
template <typename Streamer, typename Control, typename Serialiser>
class Generator {
  using self_t = Generator<Streamer, Control, Serialiser>;

public:
  Generator(SINQAmorSim::Configuration &configuration)
      : Streaming{new Control(configuration)}, Config{configuration} {

    SINQAmorSim::KafkaOptions Options;
    for (int tid = 0; tid < Config.num_threads; ++tid) {
      Stream.emplace_back(
          new Streamer(Config.producer.broker,
                       Config.producer.topic + "-" + std::to_string(tid),
                       Config.source_name, Config.options));
      if (!Stream[tid]) {
        throw std::runtime_error("Error creating the stream instance");
        return;
      }
    }
    if (!Streaming) {
      throw std::runtime_error("Error creating the control instance");
      return;
    }
    Statistics.setNumThreads(Config.num_threads);
    Statistics.setControl(Streaming);
  }

  template <class T> void run(std::vector<T> &EventsData) {
    std::vector<std::future<void>> Handle;

    for (int tid = 0; tid < Config.num_threads; ++tid) {
      Handle.push_back(std::async(std::launch::async, &self_t::runImpl<T>, this,
                                  std::ref(EventsData), tid));
    }
    auto Report =
        std::async(std::launch::async, [&]() { Statistics.report(); });
    Streaming->update();
    try {
      for (auto &h : Handle) {
        h.get();
      }
      Report.get();
    } catch (std::exception e) {
      std::cout << e.what() << "\n";
      return;
    }
  }

  template <class T> void listen(std::vector<T> &EventsData) {
    std::future<void> Handle;
    Handle = std::async(std::launch::async, &self_t::listenImpl<T>, this,
                        std::ref(EventsData));
    try {
      Handle.get();
    } catch (std::exception e) {
      std::cout << e.what() << "\n";
      return;
    }
  }

private:
  std::vector<std::unique_ptr<Streamer>> Stream;
  std::shared_ptr<Control> Streaming{nullptr};
  SINQAmorSim::Configuration Config;
  Stats<Control> Statistics;

  template <class T> void runImpl(std::vector<T> &Events, int tid) {
    using namespace std::chrono;
    uint64_t PulseID = 0;

    using system_clock = std::chrono::system_clock;
    auto StartTime = system_clock::now();
    std::time_t to_time = system_clock::to_time_t(StartTime);
    auto Timeout = std::localtime(&to_time);

    while (!Streaming->exit()) {
      if (Streaming->stop()) {
        std::this_thread::sleep_for(milliseconds(100));
        continue;
      }

      nanoseconds PulseTime =
          duration_cast<nanoseconds>(system_clock::now().time_since_epoch());
      try {
        if (Streaming->run()) {

          Stream[tid]->send(PulseID, PulseTime, Events, Events.size());
        } else {
          Stream[tid]->send(PulseID, PulseTime, Events, 0);
        }
      } catch (std::exception &e) {
        std::cout << e.what() << "\n";
        break;
      }
      // Make sure that messages have been sent to prevent queue full
      if (PulseID % 1000 == 1) {
        while (Stream[tid]->outqLen()) {
          Stream[tid]->poll();
        }
      }
      ++PulseID;
      if (PulseID % Streaming->rate() == 0) {
        ++Timeout->tm_sec;
        std::this_thread::sleep_until(
            system_clock::from_time_t(mktime(Timeout)));
        Stream[tid]->poll(0);
      }

      auto ElapsedTime = system_clock::now() - StartTime;
      if (std::chrono::duration_cast<std::chrono::seconds>(ElapsedTime)
              .count() > Config.report_time) {
        // Make sure that messages have been sent before collecting stats and
        // recompute (real) time
        while (Stream[tid]->outqLen()) {
          Stream[tid]->poll(-1);
        }
        // update stats
        Statistics.add(Stream[tid]->getNumMessages(), Stream[tid]->getMbytes(),
                       tid);
        Stream[tid]->getNumMessages() = 0;
        Stream[tid]->getMbytes() = 0;
        StartTime = system_clock::now();
      }
    }
  }

  template <class T> void listenImpl(std::vector<T> &Events) {

    int PulseID = -1, MessagesLost = -1;
    uint64_t PacketID;
    uint64_t ReceivedBytes = 0;
    int MessagesReceived = 0;

    using system_clock = std::chrono::system_clock;
    auto StartTime = system_clock::now();

    while (true) {

      auto Message = Stream[0]->recv(Events);
      PacketID = Message.first;
      if (PacketID - PulseID != 0) {
        PulseID = PacketID;
        ++MessagesLost;
      } else {
        ++MessagesReceived;
        ReceivedBytes += Message.second;
      }
      if (std::chrono::duration_cast<std::chrono::seconds>(system_clock::now() -
                                                           StartTime)
              .count() > Config.report_time) {
        std::cout << "Missed " << MessagesLost << " packets" << std::endl;
        std::cout << "Received " << MessagesReceived << "packets"
                  << " @ " << ReceivedBytes * 1e-1 * 1e-6 << "MB/s"
                  << std::endl;
        MessagesReceived = 0;
        MessagesLost = 0;
        ReceivedBytes = 0;
        StartTime = system_clock::now();
      }
      PulseID++;
    }
  }
};
