#pragma once

namespace SINQAmorSim {

enum class RunStatus { run, pause, stop, exit };
static std::string Status2Str(const int value) {
  switch (value) {
  case int(RunStatus::run):
    return "run";
  case int(RunStatus::pause):
    return "pause";
  case int(RunStatus::stop):
    return "stop";
  case int(RunStatus::exit):
    return "exit";
  default:
    return "unknown status";
  }
}

struct NoControl {
  NoControl() = default;
  NoControl(Configuration &){};

  NoControl(const NoControl &other) = default;

  NoControl &operator=(NoControl &other) = default;

  int update() { return -1; }

  int start(int) { return run(); }
  bool run() const { return true; }
  bool stop() const { return false; }
  bool pause() const { return false; }
  bool exit() const { return false; }
};

struct CommandlineControl {
  CommandlineControl(Configuration &configuration) : config{configuration} {
    status.store(int(RunStatus::stop));
  }
  CommandlineControl(const CommandlineControl &other) = default;

  CommandlineControl &operator=(CommandlineControl &other) {
    status.store(other.status);
    config.rate = other.config.rate;
    return *this;
  }

  int update() { return update_impl(); }

  int start(RunStatus value = RunStatus::run) {
    if (int(value) >= 0 && int(value) < 3) {
      status.store(int(value));
    }
    return run();
  }
  bool run() const { return status == int(RunStatus::run); }
  bool stop() const { return status == int(RunStatus::stop); }
  bool pause() const { return status == int(RunStatus::pause); }
  bool exit() const { return status == int(RunStatus::exit); }
  int rate() const { return config.rate; }

private:
  std::atomic<int> status;
  SINQAmorSim::Configuration &config;

  int update_impl() {
    std::cout << "status : " << Status2Str(status) << "\t"
              << "tr : " << std::to_string(config.rate) << "\n";
    std::string value;
    while (status != int(RunStatus::exit)) {
      std::cin >> value;
      if (std::string(value) == "run" || std::string(value) == "ru") {
        status.store(int(RunStatus::run));
      }
      if (std::string(value) == "pause" || std::string(value) == "pa") {
        status.store(int(RunStatus::pause));
      }
      if (std::string(value) == "stop" || std::string(value) == "st") {
        status.store(int(RunStatus::stop));
      }
      if (std::string(value) == "exit" || std::string(value) == "ex") {
        status.store(int(RunStatus::exit));
      }
      if (std::string(value) == "rate" || std::string(value) == "ra") {
        std::cout << "Insert the new transmission rate:" << std::endl;
        std::cin >> value;
        config.rate = std::stoi(value);
      }
      std::cout << "status : " << Status2Str(status) << "\t"
                << "tr : " << std::to_string(config.rate) << "\n";
    }
    return status.load();
  }
};

} // namespace SINQAmorSim
