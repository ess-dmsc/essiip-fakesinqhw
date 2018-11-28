#pragma once

#include "H5Cpp.h"

namespace SINQAmorSim {

///  \author Michele Brambilla <mib.mic@gmail.com>
///  \date Wed Jun 08 16:49:17 2016
template <typename Instrument, typename Format> class NeXusSource {
public:
  using self_t = NeXusSource;
  using value_type = typename Format::value_type;
  using iterator = typename std::vector<value_type>::iterator;
  using const_iterator = typename std::vector<value_type>::const_iterator;

  iterator begin() { return data.begin(); }
  iterator end() { return data.end(); }
  const_iterator begin() const { return data.begin(); }
  const_iterator end() const { return data.end(); }

  NeXusSource(const std::string &filename, const int multiplier = 1) {
    try {
      H5::H5File file(filename, H5F_ACC_RDONLY);
      read(file);
    } catch (std::exception &e) {
      throw std::runtime_error(e.what());
    }

    if (multiplier > 1) {
      int nelem = data.size();
      for (int m = 1; m < multiplier; ++m)
        data.insert(data.end(), data.begin(), data.begin() + nelem);
    }
  }

  int count() const { return data.size(); }
  std::vector<value_type> get() { return data; }

private:
  Instrument instrum;
  std::vector<value_type> data;

  void read(H5::H5File &file) { instrum(file, data); }
};

///  \author Michele Brambilla <mib.mic@gmail.com>
///  \date Thu Jun 09 16:43:08 2016
class Rita2 {
public:
  Rita2() { path.emplace_back("/entry1/RITA-2/detector/counts"); }

  template <typename T>
  void operator()(const H5::H5File &file, std::vector<T> &stream) {

    {
      H5::DataSet dataset = file.openDataSet(path[0]);
      H5::DataSpace dataspace = dataset.getSpace();
      int rank = dataspace.getSimpleExtentNdims();
      dim.resize(rank);
      dataspace.getSimpleExtentDims(&dim[0], nullptr);
      H5::DataSpace memspace(rank, &dim[0]);
      data.resize(memspace.getSelectNpoints());
      dataset.read(&data[0], H5::PredType::NATIVE_INT, memspace, dataspace);
    }

    toEventFmt<T>(stream);
  }

  std::vector<std::string> path;

private:
  std::vector<int32_t> data;
  std::vector<hsize_t> dim;

  template <typename T> void toEventFmt(std::vector<T> &signal) {
    int offset, nCount;
    union {
      uint64_t value;
      struct LoHi {
        uint32_t low;
        uint32_t high;
      } part;
    } x;

    srand(time(nullptr));
    for (int i = 0; i < dim[0]; ++i) {
      for (int j = 0; j < dim[1]; ++j) {
        offset = dim[2] * (j + dim[1] * i);
        for (int k = 0; k < dim[2]; ++k) {
          nCount = data[offset + k];
          x.low = 1 << 31 | 1 << 30 | 1 << 29 | 1 << 28 | 2 << 24 | i << 12 | j;
          for (int l = 0; l < nCount; ++l) {
            x.part.high = rand();
            signal.push_back(x.value);
          }
        }
      }
    }
  }
};

///  \author Michele Brambilla <mib.mic@gmail.com>
///  \date Thu Jun 09 16:43:08 2016
struct Amor {
  static const int n_monitor = 2;
  std::vector<std::string>::iterator begin() { return path.begin(); }
  std::vector<std::string>::iterator end() { return path.end(); }
  std::vector<std::string>::const_iterator begin() const {
    return path.begin();
  }
  std::vector<std::string>::const_iterator end() const { return path.end(); }

  Amor() {
    path.emplace_back("/entry1/AMOR/area_detector/data");
    path.emplace_back("/entry1/AMOR/area_detector/time_binning");
  }

  template <typename T>
  void operator()(const H5::H5File &file, std::vector<T> &stream) {

    {
      H5::DataSet dataset = file.openDataSet(path[0]);
      H5::DataSpace dataspace = dataset.getSpace();
      int rank = dataspace.getSimpleExtentNdims();
      dim.resize(rank);
      dataspace.getSimpleExtentDims(&dim[0], nullptr);
      H5::DataSpace memspace(rank, &dim[0]);
      data.resize(memspace.getSelectNpoints());
      dataset.read(&data[0], H5::PredType::NATIVE_INT, memspace, dataspace);
    }
    {
      H5::DataSet dataset = file.openDataSet(path[1]);
      H5::DataSpace dataspace = dataset.getSpace();
      int rank = dataspace.getSimpleExtentNdims();
      hsize_t tof_dim{0};
      dataspace.getSimpleExtentDims(&tof_dim, nullptr);
      if (tof_dim != dim[2]) {
        throw std::runtime_error(
            "Time extent in histogram differs from ToF length");
      }
      dim.push_back(tof_dim);

      H5::DataSpace memspace(rank, &tof_dim);
      tof.resize(memspace.getSelectNpoints());
      dataset.read(&tof[0], H5::PredType::NATIVE_FLOAT, memspace, dataspace);
    }

    toEventFmt<T>(stream);
  }

  std::vector<std::string> path;

private:
  std::vector<int32_t> data;
  std::vector<float> tof;
  std::vector<hsize_t> dim;

  template <typename T> void toEventFmt(std::vector<T> &signal) {
    throw std::runtime_error("Error, stream format unknown");
  }
};

template <>
void Amor::toEventFmt<PSIformat::value_type>(
    std::vector<PSIformat::value_type> &signal) {
  // unsigned long nEvents = std::accumulate(data.begin(), data.end(), 0);
  int offset, nCount;
  int detID = 0;

  union {
    uint64_t value;
    struct LoHi {
      uint32_t low;
      uint32_t high;
    } part;
  } x;

  for (hsize_t i = 0; i < dim[0]; ++i) {
    for (hsize_t j = 0; j < dim[1]; ++j) {
      detID++;
      offset = dim[2] * (j + dim[1] * i);
      for (hsize_t k = 0; k < dim[2]; ++k) {
        nCount = data[offset + k];
        x.part.high = std::round(tof[k] / 10.);
        x.part.low = 1 << 31 | 1 << 30 | 1 << 29 | 1 << 28 | 2 << 24 | detID;
        for (int l = 0; l < nCount; ++l) {
          signal.push_back(x.value);
        }
      }
    }
  }
}

template <>
void Amor::toEventFmt<ESSformat::value_type>(
    std::vector<ESSformat::value_type> &signal) {
  unsigned long nEvents = std::accumulate(data.begin(), data.end(), 0);
  uint32_t detID = 0;
  int offset, nCount;
  int counter = 0;

  std::cout << "ESSformat : " << nEvents << " events\n";

  signal.resize(2 * nEvents);
  for (hsize_t i = 0; i < dim[0]; ++i) {
    for (hsize_t j = 0; j < dim[1]; ++j) {
      offset = dim[2] * (j + dim[1] * i);
      for (hsize_t k = 0; k < dim[2]; ++k) {
        nCount = data[offset + k];
        for (int l = 0; l < nCount; ++l) {
          signal[counter] = std::round(tof[k] / 10.);
          signal[counter + nEvents] = detID;
          counter++;
        }
      }
    }
    detID++;
  }
}


///  \author Mark Koennecke, mark.koennecke@psi.ch
///  \date November 2018
struct Focus {
  static const int n_monitor = 2;
  std::vector<std::string>::iterator begin() { return path.begin(); }
  std::vector<std::string>::iterator end() { return path.end(); }
  std::vector<std::string>::const_iterator begin() const {
    return path.begin();
  }
  std::vector<std::string>::const_iterator end() const { return path.end(); }

  Focus() {
    path.emplace_back("/entry1/FOCUS/merged/counts");
    path.emplace_back("/entry1/FOCUS/merged/time_binning");
  }

  template <typename T>
  void operator()(const H5::H5File &file, std::vector<T> &stream) {

    {
      H5::DataSet dataset = file.openDataSet(path[0]);
      H5::DataSpace dataspace = dataset.getSpace();
      int rank = dataspace.getSimpleExtentNdims();
      dim.resize(rank);
      dataspace.getSimpleExtentDims(&dim[0], nullptr);
      H5::DataSpace memspace(rank, &dim[0]);
      data.resize(memspace.getSelectNpoints());
      dataset.read(&data[0], H5::PredType::NATIVE_INT, memspace, dataspace);
    }
    {
      H5::DataSet dataset = file.openDataSet(path[1]);
      H5::DataSpace dataspace = dataset.getSpace();
      int rank = dataspace.getSimpleExtentNdims();
      hsize_t tof_dim{0};
      dataspace.getSimpleExtentDims(&tof_dim, nullptr);
      if (tof_dim != dim[1]) {
        throw std::runtime_error(
            "Time extent in histogram differs from ToF length");
      }
      dim.push_back(tof_dim);

      H5::DataSpace memspace(rank, &tof_dim);
      tof.resize(memspace.getSelectNpoints());
      dataset.read(&tof[0], H5::PredType::NATIVE_FLOAT, memspace, dataspace);
    }

    toEventFmt<T>(stream);
  }

  std::vector<std::string> path;

private:
  std::vector<int32_t> data;
  std::vector<float> tof;
  std::vector<hsize_t> dim;

  template <typename T> void toEventFmt(std::vector<T> &signal) {
    throw std::runtime_error("Error, stream format unknown");
  }
};

  template <>
  void Focus::toEventFmt<PSIformat::value_type>(
						std::vector<PSIformat::value_type> &signal) {
  int offset, nCount;
  int detID = 0;

    union {
      uint64_t value;
      struct LoHi {
	uint32_t low;
	uint32_t high;
      } part;
    } x;

    for (hsize_t i = 0; i < dim[0]; ++i) {
      detID++;
      offset = i*dim[1];
      for (hsize_t k = 0; k < dim[1]; ++k) {
        nCount = data[offset + k];
        x.part.high = std::round(tof[k] / 10.);
        x.part.low =  detID;
        for (int l = 0; l < nCount; ++l) {
          signal.push_back(x.value);
        }
      }
    }
  }


template <>
void Focus::toEventFmt<ESSformat::value_type>(
    std::vector<ESSformat::value_type> &signal) {
  unsigned long nEvents = std::accumulate(data.begin(), data.end(), 0);
  uint32_t detID = 0;
  int offset, nCount;
  int counter = 0;

  std::cout << "ESSformat : " << nEvents << " events\n";

  signal.resize(2 * nEvents);
  for (hsize_t i = 0; i < dim[0]; ++i) {
      offset = i*dim[1];
      for (hsize_t k = 0; k < dim[1]; ++k) {
        nCount = data[offset + k];
        for (int l = 0; l < nCount; ++l) {
          signal[counter] = std::round(tof[k] / 10.);
          signal[counter + nEvents] = detID;
          counter++;
        }
      }
      detID++;
    }
}


} // namespace SINQAmorSim
