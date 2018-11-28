#pragma once

#include "schemas/ev42_events_generated.h"

// WARNING:
// the schema has to match to the serialise template type
// this must change

namespace SINQAmorSim {

///  \author Michele Brambilla <mib.mic@gmail.com>
///  \date Thu Jul 28 14:32:29 2016
class FlatBufferSerialiser {
public:
  FlatBufferSerialiser(const std::string &source_name = "AMOR.event.stream")
      : source{source_name} {}
  FlatBufferSerialiser(const FlatBufferSerialiser &other) = default;
  FlatBufferSerialiser(FlatBufferSerialiser &&other) = default;
  ~FlatBufferSerialiser() = default;

  // WARNING: template parameter has to match schema data type
  template <class T>
  std::vector<char> &serialise(const int &message_id,
                               const std::chrono::nanoseconds &pulse_time,
                               const std::vector<T> &message = {}) {
    auto nev = message.size() / 2;
    flatbuffers::FlatBufferBuilder builder;
    auto source_name = builder.CreateString(source);
    auto time_of_flight = builder.CreateVector(&message[0], nev);
    auto detector_id = builder.CreateVector(&message[nev], nev);
    auto event =
        CreateEventMessage(builder, source_name, message_id, pulse_time.count(),
                           time_of_flight, detector_id);
    FinishEventMessageBuffer(builder, event);
    buffer_.resize(builder.GetSize());
    buffer_.assign(builder.GetBufferPointer(),
                   builder.GetBufferPointer() + builder.GetSize());
    return buffer_;
  }

  template <class T>
  void extract(const std::vector<char> &message, std::vector<T> &data,
               uint64_t &pid, std::chrono::nanoseconds &pulse_time,
               std::string &source_name) {
    extract_impl<T>(static_cast<const void *>(&message[0]), data, pid,
                    pulse_time, source_name);
  }

  template <class T>
  void extract(const char *msg, std::vector<T> &data, uint64_t &pid,
               std::chrono::nanoseconds &pulse_time, std::string &source_name) {
    extract_impl<T>(static_cast<const void *>(msg), data, pid, pulse_time,
                    source_name);
  }

  char *get() { return &buffer_[0]; }
  size_t size() { return buffer_.size(); }

  const std::vector<char> &buffer() { return buffer_; }

  bool verify() {
    auto p = const_cast<const char *>(&buffer_[0]);
    flatbuffers::Verifier verifier(reinterpret_cast<const unsigned char *>(p),
                                   buffer_.size());
    return VerifyEventMessageBuffer(verifier);
  }
  bool verify(const std::vector<char> &other) {
    auto p = const_cast<const char *>(&other[0]);
    flatbuffers::Verifier verifier(reinterpret_cast<const unsigned char *>(p),
                                   buffer_.size());
    return VerifyEventMessageBuffer(verifier);
  }

private:
  template <class T>
  void extract_impl(const void *msg, std::vector<T> &data, uint64_t &pid,
                    std::chrono::nanoseconds &pulse_time,
                    std::string &source_name) {
    auto event = GetEventMessage(msg);
    data.resize(2 * event->time_of_flight()->size());
    std::copy(event->time_of_flight()->begin(), event->time_of_flight()->end(),
              data.begin());
    std::copy(event->detector_id()->begin(), event->detector_id()->end(),
              data.begin() + event->time_of_flight()->size());
    pid = event->message_id();
    size_t timestamp = event->pulse_time();
    pulse_time = std::chrono::nanoseconds(timestamp);
    source_name = std::string{event->source_name()->c_str()};
  }

  std::vector<char> buffer_;
  std::string source;
};

///  \author Michele Brambilla <mib.mic@gmail.com>
///  \date Fri Jun 17 12:22:01 2016
class NoSerialiser {
public:
  NoSerialiser(const std::string & = "") {}
  NoSerialiser(const NoSerialiser &other) = default;
  NoSerialiser(NoSerialiser &&other) = default;
  ~NoSerialiser() = default;

  NoSerialiser() = default;
  char *get() { return nullptr; }

  const int size() { return 0; }
};

} // serialiser
