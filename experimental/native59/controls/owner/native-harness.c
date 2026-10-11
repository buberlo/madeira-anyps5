/* Root compiles this harness. It executes the exact production read helper,
 * injected bounded memory reads only; no Mach suspension/runtime claim. */
#include <stdio.h>
#include <stdlib.h>
#include "source/ios_critical_owner_sample.h"
#include "image-fixture.h"
#include "source/ios_critical_owner_mapping.h"
#define TEB UINT64_C(0x100000)
#define PEB UINT64_C(0x200000)
#define LDR UINT64_C(0x300000)
#define NODE UINT64_C(0x400000)
#define NAME UINT64_C(0x500000)
#define PE UINT64_C(0x600000)
#define POOL UINT64_C(0x1000000)
static struct ios_co_critical critical;
static unsigned read_calls, owner_reads, critical_reads, translate_calls, assertions;
static int change_owner, change_depth, change_critical, foreign_mapping, change_mapping,
           wrong_pe, loader_cycle, duplicate_module, missing_module, unreadable, bad_self;
static unsigned char dos[64], nt[88];
static uint64_t own_value; static uint32_t depth_value;
#define CHECK(x) do { ++assertions; if (!(x)) { fprintf(stderr,"failure:%d:%s\n",__LINE__,#x); exit(1); } } while (0)
static int give(void *out, size_t n, const void *value, size_t bytes)
{ if (n != bytes) return 0; memcpy(out, value, n); return 1; }
static int read_fake(uint64_t a, void *out, size_t n)
{
    uint64_t v; uint32_t w; uint16_t h; static const uint16_t name[12] = {'x','t','a','j','i','t','6','4','.','d','l','l'};
    ++read_calls; if (unreadable || read_calls > 1300) return 0;
    if (a == TEB+0x30) { v = bad_self ? TEB+0x1000 : TEB; return give(out,n,&v,8); }
    if (a == TEB+0x60) { v=PEB; return give(out,n,&v,8); }
    if (a == TEB+0x40) { v=0x24; return give(out,n,&v,8); }
    if (a == TEB+0x48) { v=0x28; return give(out,n,&v,8); }
    if (a == TEB+IOS_CO_CRITICAL_OFFSET) {
        struct ios_co_critical q=critical; if (change_critical && ++critical_reads == 2) ++q.depth;
        return give(out,n,&q,sizeof(q));
    }
    if (a == PEB+0x18) { v=LDR; return give(out,n,&v,8); }
    if (a == LDR+0x10) { v=NODE; return give(out,n,&v,8); }
    if (a == NODE) { v=loader_cycle ? NODE : (duplicate_module ? NODE+0x1000 : LDR+0x10); return give(out,n,&v,8); }
    if (a == NODE+0x1000) { v=LDR+0x10; return give(out,n,&v,8); }
    if (a == NODE+0x58 || a == NODE+0x1058) { h=(missing_module || loader_cycle) ? 22 : 24; return give(out,n,&h,2); }
    if (a == NODE+0x60 || a == NODE+0x1060) { v=NAME; return give(out,n,&v,8); }
    if (a == NODE+0x30 || a == NODE+0x1030) { v=PE; return give(out,n,&v,8); }
    if (a == NODE+0x40 || a == NODE+0x1040) { w=IOS_CO_IMAGE_BYTES; return give(out,n,&w,4); }
    if (a == NAME) return give(out,n,name,sizeof(name));
    if (a == PE) return give(out,n,dos,sizeof(dos));
    if (a == PE+120) return give(out,n,nt,sizeof(nt));
    if (a == POOL+IOS_CO_RPM_OWNER_RVA) { v=own_value; ++owner_reads; if (change_owner && owner_reads == 2) v^=0x1000; return give(out,n,&v,8); }
    if (a == POOL+IOS_CO_RPM_DEPTH_RVA) { w=depth_value; if (change_depth && owner_reads == 2) ++w; return give(out,n,&w,4); }
    return 0;
}
static void *translate_fake(void *a, void *peb)
{
    ++translate_calls; CHECK((uint64_t)(uintptr_t)peb == PEB);
    return (void *)(uintptr_t)((uint64_t)(uintptr_t)a - PE + POOL + (change_mapping && translate_calls >= 3 ? 0x1000 : 0));
}
static void *mapping_fake(const void *a, void **pe)
{
    (void)a; *pe=(void *)(uintptr_t)(wrong_pe ? PE+0x1000 : PE);
    return (void *)(uintptr_t)(foreign_mapping ? PEB+0x1000 : 0);
}
static const struct ios_co_ops ops={read_fake,translate_fake,mapping_fake};
static struct ios_co_sample capture(void) { struct ios_co_sample s; ios_co_capture(&ops,TEB,&s); return s; }
static void reset(void)
{
    critical=(struct ios_co_critical){123,TEB,2,0,0,0}; own_value=TEB|1; depth_value=2;
    read_calls=owner_reads=critical_reads=translate_calls=0;
    change_owner=change_depth=change_critical=foreign_mapping=change_mapping=wrong_pe=loader_cycle=duplicate_module=missing_module=unreadable=bad_self=0;
    memcpy(dos,fixture_dos,sizeof(dos)); memcpy(nt,fixture_nt,sizeof(nt));
}
static struct ios_co_mapping_row map_rows[2]; static unsigned map_reads; static int map_change;
static int map_read(void *opaque,unsigned i,struct ios_co_mapping_row *out)
{ (void)opaque; if(i>=2)return 0; *out=map_rows[i]; if(map_change && ++map_reads==2) ++out->pool; return 1; }
static uint64_t pick(int n,int reverse,uint64_t a,uint64_t *pe,uint64_t *own)
{ map_reads=0; return ios_co_mapping_pick(n,a,PEB,reverse,map_read,NULL,pe,own); }
static unsigned mapping_cases(void)
{
    uint64_t pe,own; unsigned n=0;
    map_rows[0]=(struct ios_co_mapping_row){PE,POOL,IOS_CO_IMAGE_BYTES,PEB,0}; map_rows[1]=map_rows[0];
    CHECK(pick(1,0,PE+IOS_CO_RPM_OWNER_RVA,NULL,NULL)==POOL+IOS_CO_RPM_OWNER_RVA); ++n;
    map_rows[0].owner=0; CHECK(pick(1,0,PE+8,NULL,NULL)==POOL+8); ++n;
    map_rows[0].owner=PEB+0x1000; CHECK(!pick(1,0,PE+8,NULL,NULL)); ++n;
    CHECK(pick(1,1,POOL+8,&pe,&own)==PE+8 && pe==PE && own==PEB+0x1000); ++n;
    map_rows[0]=map_rows[1]; CHECK(!pick(2,0,PE+8,NULL,NULL)); ++n;
    map_rows[0].owner=0; CHECK(pick(2,0,PE+8,NULL,NULL)==POOL+8); ++n;
    map_rows[1].owner=0; CHECK(!pick(2,0,PE+8,NULL,NULL)); ++n;
    CHECK(!pick(513,0,PE+8,NULL,NULL) && !map_reads); ++n;
    map_rows[0].pool=UINT64_MAX-8; CHECK(!pick(1,0,PE+8,NULL,NULL)); ++n;
    map_rows[0]=map_rows[1]; map_change=1; CHECK(!pick(1,0,PE+8,NULL,NULL)); map_change=0; ++n;
    return n;
}
int main(void)
{
    struct ios_co_sample s; unsigned cases=0;
    reset(); s=capture(); CHECK(s.reason==IOS_CO_OK && s.target_is_owner && s.rpm_equal && s.critical_shape); ++cases;
    reset(); own_value=TEB+0x1001; s=capture(); CHECK(s.rpm_equal && !s.target_is_owner && s.rpm_owner[0]==TEB+0x1001); ++cases;
    reset(); own_value=0; depth_value=0; s=capture(); CHECK(s.reason==IOS_CO_OK && !s.target_is_owner); ++cases;
    reset(); change_owner=1; s=capture(); CHECK(s.rpm_read && !s.rpm_equal && !s.target_is_owner); ++cases;
    reset(); change_depth=1; s=capture(); CHECK(!s.rpm_equal && s.rpm_depth[0]!=s.rpm_depth[1]); ++cases;
    reset(); critical=(struct ios_co_critical){0,TEB,2,1,0,0}; s=capture(); CHECK(s.critical_shape && !s.critical[0].token); ++cases;
    reset(); critical=(struct ios_co_critical){0}; s=capture(); CHECK(s.critical_shape); ++cases;
    reset(); change_critical=1; s=capture(); CHECK(s.critical_read && !s.critical_equal && !s.critical_shape); ++cases;
    reset(); critical.teb+=0x1000; s=capture(); CHECK(!s.critical_shape); ++cases;
    reset(); critical.flags=2; s=capture(); CHECK(!s.critical_shape); ++cases;
    reset(); foreign_mapping=1; s=capture(); CHECK(s.reason==IOS_CO_BAD_MAPPING && !s.rpm_read); ++cases;
    reset(); wrong_pe=1; s=capture(); CHECK(s.reason==IOS_CO_BAD_MAPPING && !s.rpm_read); ++cases;
    reset(); change_mapping=1; s=capture(); CHECK(s.reason==IOS_CO_MAPPING_CHANGED && !s.mapping_ok && !s.rpm_equal); ++cases;
    reset(); nt[8]^=1; s=capture(); CHECK(s.reason==IOS_CO_BAD_IMAGE && !s.rpm_read); ++cases;
    reset(); nt[80]^=1; s=capture(); CHECK(s.reason==IOS_CO_BAD_IMAGE); ++cases;
    reset(); dos[0]=0; s=capture(); CHECK(s.reason==IOS_CO_BAD_IMAGE); ++cases;
    reset(); duplicate_module=1; s=capture(); CHECK(s.reason==IOS_CO_BAD_LOADER && !s.rpm_read); ++cases;
    reset(); missing_module=1; s=capture(); CHECK(s.reason==IOS_CO_BAD_LOADER); ++cases;
    reset(); loader_cycle=1; s=capture(); CHECK(s.reason==IOS_CO_BAD_LOADER && s.loader_nodes==200 && read_calls<1300); ++cases;
    reset(); unreadable=1; s=capture(); CHECK(s.reason==IOS_CO_BAD_IDENTITY && !s.identity_ok); ++cases;
    reset(); bad_self=1; s=capture(); CHECK(s.reason==IOS_CO_BAD_IDENTITY); ++cases;
    reset(); ios_co_capture(&ops,0,&s); CHECK(s.reason==IOS_CO_NO_TEB && read_calls==0); ++cases;
    cases+=mapping_cases(); printf("OWNERSHIP_HELPER_CONTROLS cases=%u assertions=%u\n",cases,assertions); return 0;
}
