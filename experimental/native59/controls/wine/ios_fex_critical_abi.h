/* Isolated source proposal. Private native Wine/FEX ABI, never a guest context. */
#ifndef IOS_FEX_CRITICAL_ABI_H
#define IOS_FEX_CRITICAL_ABI_H
#include <stdint.h>

#define IOS_FEX_CRITICAL_QUERY_CLASS 0x7fff4152u
#define IOS_FEX_CRITICAL_MAGIC 0x41504353u
#define IOS_FEX_CRITICAL_VERSION 1u
#define IOS_FEX_CRITICAL_ENTER 1u
#define IOS_FEX_CRITICAL_LEAVE 2u
#define IOS_FEX_CRITICAL_INACTIVE 1u

struct ios_fex_critical_request
{
    uint32_t magic;
    uint32_t version;
    uint32_t operation;
    uint32_t depth;
    uint64_t token;
    uint64_t teb;
    uint32_t flags;
    uint32_t reserved;
};

/* ENTER: depth/token/teb/flags/reserved all zero. LEAVE: exact last ENTER
 * tuple, changing only operation. Nested results retain the outer token.
 * Successful outer LEAVE returns depth=0/token=0 and retains teb/flags.
 * ReturnLength is exactly 40 on success; refused LEAVE changes no state.
 * The native implementation owns the complete prior signal mask. */
#if defined(__cplusplus)
static_assert(sizeof(struct ios_fex_critical_request) == 40);
#elif defined(__STDC_VERSION__) && __STDC_VERSION__ >= 201112L
_Static_assert(sizeof(struct ios_fex_critical_request) == 40, "private ABI40");
#endif
#endif
