/* Diagnostic-only bounded mapping selection. No allocation, lock, callback
 * into Wine/FEX, logging or permissive foreign-owner fallback. The registry
 * is not a transactional snapshot: stability checks are observational only. */
#ifndef IOS_CRITICAL_OWNER_MAPPING_H
#define IOS_CRITICAL_OWNER_MAPPING_H
#include <stdint.h>
#define IOS_CO_MAX_MAPPINGS 512u
struct ios_co_mapping_row { uint64_t pe, pool, bytes, owner; unsigned unmapped; };
typedef int (*ios_co_mapping_read)(void *, unsigned, struct ios_co_mapping_row *);
static int ios_co_row_equal(const struct ios_co_mapping_row *a, const struct ios_co_mapping_row *b)
{ return a->pe==b->pe && a->pool==b->pool && a->bytes==b->bytes && a->owner==b->owner && a->unmapped==b->unmapped; }
static int ios_co_row_valid(const struct ios_co_mapping_row *r)
{ return r->pe>0x10000 && r->pool>0x10000 && r->pe!=r->pool && r->bytes && !r->unmapped &&
         r->bytes<=UINT64_MAX-r->pe && r->bytes<=UINT64_MAX-r->pool; }
/* reverse=0: exact owner wins, otherwise one explicit NULL-parent mapping.
 * reverse=1: require one pool mapping and return its actual owner/base.
 * Never return an original PE address or a foreign fallback. */
static uint64_t ios_co_mapping_pick(int count, uint64_t address, uint64_t owner, int reverse,
                                  ios_co_mapping_read read_row, void *opaque,
                                  uint64_t *pe_out, uint64_t *owner_out)
{
    unsigned i, hits[2]={0,0}, index[2]={0,0}; struct ios_co_mapping_row chosen[2]={{0},{0}}, a,b;
    int rank; uint64_t base;
    if (pe_out) *pe_out=0;
    if (owner_out) *owner_out=0;
    if (count<0 || (unsigned)count>IOS_CO_MAX_MAPPINGS || !address || (!reverse && !owner)) return 0;
    for (i=0;i<(unsigned)count;++i) {
        if (!read_row(opaque,i,&a) || !read_row(opaque,i,&b) || !ios_co_row_equal(&a,&b)) return 0;
        if (!ios_co_row_valid(&a)) continue;
        base=reverse ? a.pool : a.pe;
        if (address<base || address-base>=a.bytes) continue;
        rank=reverse ? 0 : (a.owner==owner ? 0 : (!a.owner ? 1 : -1));
        if (rank<0) continue;
        ++hits[rank]; chosen[rank]=a; index[rank]=i;
    }
    rank=hits[0] ? 0 : 1;
    if (hits[rank]!=1 || !read_row(opaque,index[rank],&b) || !ios_co_row_equal(&chosen[rank],&b)) return 0;
    if (pe_out) *pe_out=b.pe;
    if (owner_out) *owner_out=b.owner;
    return reverse ? b.pe+(address-b.pool) : b.pool+(address-b.pe);
}
#endif
