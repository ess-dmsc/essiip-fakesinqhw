find_path(HDF5_INCLUDE_DIR NAMES hdf5.h H5Cpp.h HINTS ${HDF5_ROOT}/include)

find_library(HDF5_C_LIBRARIES NAMES hdf5-shared hdf5  HINTS ${HDF5_ROOT}/lib)
find_library(HDF5_CXX_LIBRARIES NAMES hdf5_cpp-shared hdf5_cpp HINTS ${HDF5_ROOT}/lib)
set(HDF5_LIBRARIES ${HDF5_C_LIBRARIES} ${HDF5_CXX_LIBRARIES})

find_package_handle_standard_args(HDF5 DEFAULT_MSG
  HDF5_INCLUDE_DIR HDF5_LIBRARIES
  )
