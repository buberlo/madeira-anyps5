#include "ShaderDiskCache.hpp"
#include "ShaderCacheVersion.hpp"
#include <windows.h>
#include <cstdio>
#include <cstring>
extern "C" int CandidateFixtureMain(int,char**);
int main(int argc,char** argv){
 char path[32768]{};const HMODULE driver=GetModuleHandleW(L"libSceAgcDriver.prx");
 const auto n=driver?GetModuleFileNameA(driver,path,sizeof(path)):0;
 if(argc!=2||!n||n>=sizeof(path)||std::strcmp(path,argv[1])){
  std::fprintf(stderr,"ACTUAL_DRIVER_IDENTITY_REJECTED\n");return 2;
 }
 const auto sourceVersion=ShaderRecompiler::ShaderDiskCache::SourceVersion();
 if(ShaderRecompiler::ShaderDiskCache::FormatVersion!=28u || sourceVersion!=ShaderRecompiler::ShaderDiskCache::Generated::SourceVersion){
  std::fprintf(stderr,"ACTUAL_DRIVER_CACHE_IDENTITY_REJECTED\n");return 2;
 }
 std::printf("ACTUAL_DRIVER_CACHE_SOURCE_VERSION %016llx\n",static_cast<unsigned long long>(sourceVersion));
 std::printf("ACTUAL_DRIVER_CACHE_FORMAT %u\n",ShaderRecompiler::ShaderDiskCache::FormatVersion);
 std::printf("ACTUAL_DRIVER_PATH %s\n",path);std::fflush(stdout);
 return CandidateFixtureMain(argc-1,argv+1);
}
