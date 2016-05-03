#ifndef _LISTENERUTILS_H
#define _LISTENERUTILS_H
#include <iostream>
#include <type_traits>

#include "neventRequest.h"
/* #include "neventMonitor.h" */

using namespace std;
using namespace epics::pvData;
using namespace epics::pvAccess;


namespace utils {
  
  unsigned int getULong(std::string const& , PVStructure::shared_pointer const &,const std::string&);


  std::vector<uint64_t>& getArrayContent(std::string const &,
                                         PVStructure::shared_pointer const &,
                                         const std::string&,
                                         std::vector<uint64_t>&);



  template<class T>
    T& getContent(std::string const & channelName,
                  PVStructure::shared_pointer const & pv,
                  const std::string& field,
                  T& container) {
    
    PVField::shared_pointer v = pv->getSubField(field);
    if (v.get() == 0) {
      throw std::runtime_error("no " + field + " field");
    }
        
    Type valueType = v->getField()->getType();

    /* std::cout << field << " : " << std::is_fundamental<decltype(container)>::value */
    /*           << "(" << decltype(container) << ")" */
    /*           << "(" << typeid(container).name() << ")" */
    /*           << "\n"; */
    /* std::cout << field << " : " */
    /*           << std::rank<T>::value << "\t" */
    /*           << "is reference? " << std::is_reference<decltype(container)>::value << "\t" */
    /*           << "is reference? " << std::is_reference<std::remove_reference<decltype(container)> >::value */
    /*           << "\n"; */

    std::cout << field << " : is fundamental? "
              <<  std::is_fundamental<T>::value << "\t"
              << " "
              << "\n";
    
    if (std::is_fundamental<T>::value) {
      std::cout << "\tgetULong" << std::endl;
      /* container = pv->getSubField<PVULong>(field)->get(); */
      //      return container;
    }
    else {      
      std::cout << "\tgetScalarArray" << std::endl;
      PVScalarArray::shared_pointer a = pv->getSubField<PVScalarArray>(field);
      shared_vector<const uint64_t> cvalues;
      a->getAs(cvalues);
      
      if( container.size() != a->getLength() ) {
        container.resize(a->getLength());
      }
      
      std::copy(cvalues.begin(), cvalues.end(), container.begin());
      //      return container;
      
    }
    
    return container;
  }

/* std::vector<uint64_t>& getContent(std::string const & channelName, */
/*                                   PVStructure::shared_pointer const & pv, */
/*                                   const std::string& field, */
/*                                   std::vector<uint64_t>& container); */
/*  uint64_t& getContent(std::string const & channelName, */
/*                       PVStructure::shared_pointer const & pv, */
/*                       const std::string& field, */
/*                       uint64_t& container); */
  
  
  
  void do_something(Channel::shared_pointer const &,
                    shared_ptr<ChannelGetRequesterImpl> const&,
                    PVStructure::shared_pointer const&);
}
#endif //LISTENERUTILS_H
  
