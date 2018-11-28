#pragma once

#include <cctype>
#include <chrono>
#include <sstream>
#include <string>
#include <utility>

#include <librdkafka/rdkafkacpp.h>

#include "header.hpp"
#include "serialiser.hpp"
#include "utils.hpp"

namespace SINQAmorSim {

uint64_t getCurrentTimestamp() {
  return std::chrono::duration_cast<std::chrono::nanoseconds>(
             std::chrono::system_clock::now().time_since_epoch())
      .count();
}

struct KafkaGeneratorInfo {
  double Mbytes{0};
  double NumMessages{0};
};

class DeliveryReport : public RdKafka::DeliveryReportCb {
public:
  void dr_cb(RdKafka::Message &Message) override {
    if (Message.errstr() == "Success") {
      Info.NumMessages++;
      Info.Mbytes += Message.len() * 1e-6;
    } else {
      std::cout << Message.errstr() << std::endl;
    }
  }

  double &getNumMessages() { return Info.NumMessages; }
  double &getMbytes() { return Info.Mbytes; }

private:
  KafkaGeneratorInfo Info;
};

////////////////
// Producer

template <class Serialiser> class KafkaTransmitter {

public:
  KafkaTransmitter(const std::string &Brokers, const std::string &TopicName,
                   const std::string &SourceName,
                   const KafkaOptions &Options = {})
      : Topic{TopicName}, Source{SourceName} {
    if (Brokers.empty() || Topic.empty()) {
      throw std::runtime_error("Broker and/or topic not set");
    }

    std::unique_ptr<RdKafka::Conf> Configuration{
        RdKafka::Conf::create(RdKafka::Conf::CONF_GLOBAL)};
    if (!Configuration) {
      throw std::runtime_error("Unable to create RdKafka::Conf");
    }

    std::string Error;
    Configuration->set("metadata.broker.list", Brokers, Error);
    if (!Error.empty()) {
      std::cerr << Error << std::endl;
    }
    if (!Error.empty()) {
      std::cerr << Error << std::endl;
    }
    Configuration->set("api.version.request", "true", Error);
    if (!Error.empty()) {
      std::cerr << Error << std::endl;
    }
    Configuration->set("dr_cb", &DeliveryCallback, Error);
    if (!Error.empty()) {
      std::cerr << Error << std::endl;
    }
    for (auto &Option : Options) {
      Configuration->set(Option.first, Option.second, Error);
      if (!Error.empty()) {
        std::cerr << Error << std::endl;
      }
    }

    Producer.reset(RdKafka::Producer::create(Configuration.get(), Error));
    if (!Producer) {
      throw std::runtime_error("Failed to create producer: " + Error);
    }

    RdKafka::Metadata *md;
    auto Err = Producer->metadata(true, nullptr, &md, 1000);
    if (Err == RdKafka::ERR__TIMED_OUT) {
      throw std::runtime_error("Failed to retrieve Metadata: " + Error);
    }
    Metadata.reset(md);

    SerialiserWorker.reset(new Serialiser{Source});
  }

  template <typename T> size_t send(std::vector<T> &Data, const int nev = -1) {
    RdKafka::ErrorCode resp = Producer->produce(
        Topic, RdKafka::Topic::PARTITION_UA, RdKafka::Producer::RK_MSG_COPY,
        &Data[0], Data.size() * sizeof(T), nullptr, 0, getCurrentTimestamp(),
        nullptr);
    if (resp != RdKafka::ERR_NO_ERROR) {
      throw std::runtime_error(RdKafka::err2str(resp) + " : " + Topic);
    }
    return int(Producer->poll(10));
  }

  template <typename T>
  size_t send(const uint64_t &, const std::chrono::nanoseconds &,
              std::vector<T> &, const int = 1) {
    return 0;
  }

  int poll(const int &Seconds = -1) { return Producer->poll(Seconds); }
  int outqLen() { return Producer->outq_len(); }

  double &getNumMessages() { return DeliveryCallback.getNumMessages(); }
  double &getMbytes() { return DeliveryCallback.getMbytes(); }

private:
  std::unique_ptr<RdKafka::Metadata> Metadata{nullptr};
  std::unique_ptr<RdKafka::Producer> Producer{nullptr};
  std::string Topic;
  std::string Source;

  DeliveryReport DeliveryCallback;
  std::unique_ptr<Serialiser> SerialiserWorker{nullptr};
};

template <>
template <typename T>
size_t KafkaTransmitter<FlatBufferSerialiser>::send(
    const uint64_t &PacketID, const std::chrono::nanoseconds &PulseTime,
    std::vector<T> &Events, const int NumEvents) {
  size_t BufferSize{0};
  if (NumEvents) {
    SerialiserWorker->serialise(PacketID, PulseTime, Events);
    BufferSize = SerialiserWorker->size();
    RdKafka::ErrorCode resp = Producer->produce(
        Topic, RdKafka::Topic::PARTITION_UA, RdKafka::Producer::RK_MSG_COPY,
        reinterpret_cast<void *>(SerialiserWorker->get()),
        SerialiserWorker->size(), nullptr, 0, // timestamp_now()
        PulseTime.count(), nullptr);
    if (resp != RdKafka::ERR_NO_ERROR) {
      throw std::runtime_error(RdKafka::err2str(resp) + " : " + Topic);
    }
  }
  return BufferSize;
}

////////////////
// Consumer

template <class Serialiser> struct KafkaListener {

  KafkaListener(const std::string &Brokers, const std::string &TopicName,
                const std::string &SourceName, const KafkaOptions &Options)
      : Source{SourceName} {
    std::unique_ptr<RdKafka::Conf> Configuration{
        RdKafka::Conf::create(RdKafka::Conf::CONF_GLOBAL)};
    std::unique_ptr<RdKafka::Conf> TopicConfiguration{
        RdKafka::Conf::create(RdKafka::Conf::CONF_TOPIC)};

    std::string Error;
    Configuration->set("metadata.broker.list", Brokers, Error);
    if (!Error.empty()) {
      std::cerr << Error << std::endl;
    }
    for (auto &Option : Options) {
      Configuration->set(Option.first, Option.second, Error);
      if (!Error.empty()) {
        std::cerr << Error << std::endl;
      }
    }

    if (TopicName.empty()) {
      std::cerr << "Topic required." << std::endl;
      exit(1);
    }
    Consumer.reset(RdKafka::Consumer::create(Configuration.get(), Error));
    if (!Consumer) {
      std::cerr << "Failed to create consumer: " << Error << std::endl;
      exit(1);
    }
    Topic.reset(RdKafka::Topic::create(Consumer.get(), TopicName,
                                       TopicConfiguration.get(), Error));
    if (!Topic) {
      std::cerr << "Failed to create topic: " << Error << std::endl;
      exit(1);
    }

    RdKafka::ErrorCode ErrorCode =
        Consumer->start(Topic.get(), Partition, StartOffset);
    if (ErrorCode != RdKafka::ERR_NO_ERROR) {
      std::cerr << "Failed to start consumer: " << RdKafka::err2str(ErrorCode)
                << std::endl;
      exit(1);
    }
  }

  template <typename T>
  std::pair<uint64_t, uint64_t> recv(std::vector<T> &data) {
    return std::pair<uint64_t, uint64_t>{0, 0};
  }

private:
  int32_t Partition = 0;
  int64_t StartOffset = RdKafka::Topic::OFFSET_END;
  std::string Source;

  std::unique_ptr<RdKafka::Consumer> Consumer{nullptr};
  std::unique_ptr<RdKafka::Topic> Topic{nullptr};
};

template <>
template <typename T>
std::pair<uint64_t, uint64_t>
KafkaListener<FlatBufferSerialiser>::recv(std::vector<T> &Events) {

  std::unique_ptr<RdKafka::Message> Message{nullptr};
  FlatBufferSerialiser SerialiserWorker;

  do {
    Message.reset(Consumer->consume(Topic.get(), Partition, 1000));
    if ((Message->err() != RdKafka::ERR_NO_ERROR) &&
        (Message->err() != RdKafka::ERR__TIMED_OUT) &&
        (Message->err() != RdKafka::ERR__PARTITION_EOF)) {
      std::cerr << "message error: " << RdKafka::err2str(Message->err())
                << std::endl;
    }
  } while (Message->err() != RdKafka::ERR_NO_ERROR);

  uint64_t MessageID = -1;
  std::chrono::nanoseconds PulseTime{0};
  std::string MessageSource;
  SerialiserWorker.extract(reinterpret_cast<const char *>(Message->payload()),
                           Events, MessageID, PulseTime, MessageSource);
  if (!Source.empty()) {
    if (Source != MessageSource) {
      return std::pair<uint64_t, uint64_t>{0, 0};
    }
  }
  return std::pair<uint64_t, uint64_t>{MessageID, Message->len()};
}

} // namespace SINQAmorSim
