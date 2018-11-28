#pragma once

#include <atomic>
#include <chrono>
#include <condition_variable>
#include <iostream>
#include <mutex>
#include <numeric>
#include <string>
#include <thread>
#include <vector>

#include <nlohmann/json.hpp>

template <typename Control> class Stats {

  using system_clock = std::chrono::system_clock;

public:
  void setNumThreads(const int NumThreads) {
    NumMessages.resize(NumThreads);
    MBytes.resize(NumThreads);
  }

  void add(const int Messages, const int MB, const int ThreadId) {
    NumMessages[ThreadId] += Messages;
    MBytes[ThreadId] += MB;
    ThreadCount++;
    if (ThreadCount == NumMessages.size()) {
      WaitUntilReady.notify_all();
      ThreadCount = 0;
    }
  }

  void report() {
    while (Ctrl->stop()) {
      std::this_thread::sleep_for(std::chrono::milliseconds(100));
    }

    while (Ctrl->run() || Ctrl->pause()) {
      if (Ctrl->pause()) {
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
        continue;
      }
      std::chrono::time_point<std::chrono::system_clock> StartTime =
          system_clock::now();
      std::unique_lock<std::mutex> Lock(CountGuard);
      WaitUntilReady.wait(Lock);
      std::chrono::time_point<std::chrono::system_clock> Now =
          system_clock::now();

      int Messages = std::accumulate(NumMessages.begin(), NumMessages.end(), 0);
      int MB = std::accumulate(MBytes.begin(), MBytes.end(), 0);

      std::fill(NumMessages.begin(), NumMessages.end(), 0);
      std::fill(MBytes.begin(), MBytes.end(), 0);

      nlohmann::json Message;
      Message["packets"] = Messages;
      Message["MB"] = MB;
      Message["MB/s"] =
          1e3 * MB /
          std::chrono::duration_cast<std::chrono::milliseconds>(Now - StartTime)
              .count();
      Message["timestamp"] = getCurrentTimestamp();
      Message["num_threads"] = MBytes.size();
      std::cout << Message.dump(4) << "\n";
      StartTime = Now;
    }
  }

  void setControl(std::shared_ptr<Control> &Control_) { Ctrl = Control_; }

private:
  std::shared_ptr<Control> Ctrl;

  uint64_t getCurrentTimestamp() {
    return std::chrono::duration_cast<std::chrono::nanoseconds>(
               std::chrono::system_clock::now().time_since_epoch())
        .count();
  }

  std::vector<int> NumMessages;
  std::vector<int> MBytes;
  std::mutex CountGuard;
  std::condition_variable WaitUntilReady;
  std::atomic<size_t> ThreadCount{0};
};
