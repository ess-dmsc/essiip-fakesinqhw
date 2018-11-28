#ifndef _FILE_WRITER_H
#define _FILE_WRITER_H

#include <fstream>
#include <string>

///  \author Michele Brambilla <mib.mic@gmail.com>
///  \date Fri Jun 17 12:21:46 2016
struct FileWriterGen {

  FileWriterGen() {
    of.open("output.bin", std::ofstream::binary);
    if (!of.good()) {
      throw std::runtime_error("Error opening file");
    }
  }

  ~FileWriterGen() { of.close(); }

  template <typename T>
  void send(const T *data, const int size, const int flag = 0) {
    std::cout << "current position: " << of.tellp() << std::endl;
    of.seekp(0);
    std::cout << "intial position: " << of.tellp() << std::endl;
    if (!of.good()) {
      throw std::runtime_error("Error writing output");
    }
    std::cout << "data size is" << size << std::endl;
    of.write(reinterpret_cast<const char *>(data), size);
    if (of.rdstate() != std::ifstream::goodbit) {
      std::cout << "eof" << (of.rdstate() != std::ofstream::eofbit) << "fail"
                << (of.rdstate() != std::ofstream::failbit) << "bad"
                << (of.rdstate() != std::ofstream::badbit) << std::endl;
      throw std::runtime_error("Error writing output");
    }
    std::cout << "final position: " << of.tellp() << std::endl;
    of.flush();
  }

private:
  std::ofstream of;
};

#endif // FILE_WRITER_H
