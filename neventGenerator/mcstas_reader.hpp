#pragma once

/*! creates an event stream from a mcstas simulation output
 *
 *  \author Michele Brambilla <mib.mic@gmail.com>
 *  \date Fri Jun 10 12:16:01 2016
 */
namespace mcstas {

template <typename Instrument> struct McStasSource {
  using self_t = McStasSource;
  using value_type = uint64_t;

  std::vector<value_type>::iterator begin() { return data.begin(); }
  std::vector<value_type>::iterator end() { return data.end(); }
  std::vector<value_type>::const_iterator begin() const { return data.begin(); }
  std::vector<value_type>::const_iterator end() const { return data.end(); }

  McStasSource(std::map<std::string, std::string> p) : instrum(p) {
    instrum.fill(data);
  }

  int count() const { return data.size(); }

private:
  Instrument instrum;
  std::vector<value_type> data;
};

struct D1 {
  using value_type = int;

  std::vector<value_type>::iterator begin() { return v.begin(); }
  std::vector<value_type>::iterator end() { return v.end(); }
  std::vector<value_type>::const_iterator begin() const { return v.begin(); }
  std::vector<value_type>::const_iterator end() const { return v.end(); }

  D1(std::string &s, std::vector<int> &dest) : in(s), v(dest), n_col(0) {}

  void operator()( // const int t,
      const int n) {
    extract_values( // t,
        n);
  }

private:
  std::ifstream in;
  std::vector<int> &v;
  int n_col;

  void extract_values( // const int t,
      const int n) {
    std::string value;
    while (in.good()) {
      std::getline(in, value);
      if (value[0] == '#')
        continue;
      n_col++;
      int counter = 0;
      char *token = std::strtok(&value[0], " ");
      while (token) {
        if (counter == n) {
          v.push_back(atoi(token));
        }
        ++counter;
        token = std::strtok(nullptr, " ");
      }
    }
  }
};

struct D2 {
  using value_type = int;

  std::vector<value_type>::iterator begin() { return v.begin(); }
  std::vector<value_type>::iterator end() { return v.end(); }
  std::vector<value_type>::const_iterator begin() const { return v.begin(); }
  std::vector<value_type>::const_iterator end() const { return v.end(); }

  D2(std::string &s, std::vector<int> &dest) : in(s), v(dest) {}

  void operator()(const int n) { extract_values(n); }

  int n_row, n_col;

private:
  std::ifstream in;
  std::vector<int> &v;

  void extract_values(const int n) {
    std::string value;
    bool is_value = false;
    int block = -1;

    while (in.good()) {
      std::getline(in, value);
      if (value[0] == '#') {
        is_value = false;
        continue;
      }
      if (is_value == false) {
        ++block;
        is_value = true;
      }
      if (block != n)
        continue;
      n_row++;
      char *token = std::strtok(&value[0], " ");
      while (token) {
        v.push_back(atoi(token));
        //          std::cout << atof(token) << "\t";
        token = std::strtok(nullptr, " ");
        n_col++;
      }
    }
  }
};

struct Rita2 {

  Rita2(std::map<std::string, std::string> &p)
      : tof(p["1D"], t), area(p["2D"], pos) {}

  template <class T> void fill(std::vector<T> &data) {
    load();
    toEventFmt(data);
  }

  std::vector<int> t, pos;

private:
  D1 tof;
  D2 area;
  int sum_tof, sum_area;

  void load() {
    //      tof(3);
    area(2);
    sum_tof = std::accumulate(tof.begin(), tof.end(), 0);
    sum_area = std::accumulate(area.begin(), area.end(), 0);
  }

  template <typename T> void toEventFmt(std::vector<T> &signal) {
    int pos = 0;

    union {
      uint64_t value;
      struct LoHi {
        uint32_t low;
        uint32_t high;
      } parts;
    } x;

    for (auto it = area.begin(); it != area.end(); ++it, ++pos) {
      for (int count = 0; count < (*it); ++count) {
        x.parts.high = rand();
        x.parts.low = (1 << 31 | 1 << 30 | 1 << 29 | 1 << 28 | 2 << 24 |
                       pos / area.n_col << 12 | pos % area.n_col);
        signal.push_back(x.value);
      }
    }
  }
};

} // namespace
