find_path(NEXUS_INCLUDE_DIR NAMES nexus/napi.h)
find_library(NEXUS_C_LIBRARIES NAMES NeXus)
find_library(NEXUS_CXX_LIBRARIES NAMES NeXusCPP)

set(NEXUS_LIBRARIES ${NEXUS_C_LIBRARIES} ${NEXUS_CXX_LIBRARIES})

include(FindPackageHandleStandardArgs)
find_package_handle_standard_args(NEXUS DEFAULT_MSG
	NEXUS_INCLUDE_DIR
	NEXUS_LIBRARIES
)
