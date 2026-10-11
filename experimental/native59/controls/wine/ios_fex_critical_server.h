/* Shared production registration/predicate code, directly includable by native tests. */
#ifndef IOS_FEX_CRITICAL_SERVER_H
#define IOS_FEX_CRITICAL_SERVER_H
#include <stdint.h>
#include "ios_fex_critical_abi.h"

struct ios_fex_critical_scope
{
    uint64_t token;
    uint64_t teb;
    const void *pending_context;
    uint64_t capture_generation;
};

struct ios_fex_critical_facts
{
    int running;
    int amd64;
    int mode_enabled;
    int initialised;
    int start_pending;
    int logical_suspend;
    int process_suspend;
    int debug_hold;
    int mach_hold;
    int context_present;
    int exact_private_pending;
    int scope_matches_pending;
    int eligible_suspend_origin;
};

/* The server constructs every fact under its existing serial request dispatch. */
static inline int ios_fex_critical_registration_allowed(const struct ios_fex_critical_facts *f)
{
    if (!f->running || !f->amd64 || !f->mode_enabled || f->process_suspend ||
        f->debug_hold || f->mach_hold) return 0;
    /* A secondary thread can still be starting in an already initialised process. */
    if (f->start_pending && f->logical_suspend == 1 && !f->context_present) return 1;
    if (!f->initialised)
        return !f->context_present && !f->logical_suspend;
    if (!f->logical_suspend) return !f->context_present || f->exact_private_pending;
    return f->exact_private_pending && f->eligible_suspend_origin;
}

/* This does not alter the logical count or manufacture a context ACK. */
static inline int ios_fex_critical_wait_deferred(const struct ios_fex_critical_scope *scope,
                                               uint64_t actual_teb,
                                               const struct ios_fex_critical_facts *f)
{
    return scope->token && scope->teb == actual_teb && f->running && f->amd64 &&
           f->mode_enabled && f->initialised && !f->start_pending && f->logical_suspend > 0 &&
           !f->process_suspend && !f->debug_hold && !f->mach_hold &&
           f->exact_private_pending && f->scope_matches_pending && f->eligible_suspend_origin;
}

/* Only the serialized publisher/ENTER handler calls this with its actual context
 * object and fresh nonzero generation, never a client-provided context pointer. */
static inline void ios_fex_critical_bind_pending(struct ios_fex_critical_scope *scope,
                                               const void *context, uint64_t generation)
{
    scope->pending_context = scope->token && generation ? context : 0;
    scope->capture_generation = scope->pending_context ? generation : 0;
}

static inline uint32_t ios_fex_critical_register(struct ios_fex_critical_scope *scope,
        const struct ios_fex_critical_facts *f, uint64_t actual_teb, uint64_t supplied_teb,
        uint32_t operation, uint64_t supplied_token, uint64_t *next_token,
        uint64_t *result_token, uint32_t *result_depth)
{
    if (!actual_teb || supplied_teb != actual_teb) return 0xc0000022u;
    if (operation == IOS_FEX_CRITICAL_ENTER)
    {
        if (supplied_token || scope->token || !ios_fex_critical_registration_allowed(f))
            return 0xc0000184u;
        if (*next_token == UINT64_MAX) return 0xc0000095u;
        scope->token = ++*next_token;
        scope->teb = actual_teb;
        ios_fex_critical_bind_pending(scope, 0, 0);
        *result_token = scope->token;
        *result_depth = 1;
    }
    else if (operation == IOS_FEX_CRITICAL_LEAVE)
    {
        /* A later hard/process/debug hold must not prevent a balanced unlock+leave. */
        if (!scope->token || supplied_token != scope->token || scope->teb != actual_teb)
            return 0xc0000184u;
        scope->token = 0;
        scope->teb = 0;
        ios_fex_critical_bind_pending(scope, 0, 0);
        *result_token = 0;
        *result_depth = 0;
    }
    else return 0xc000000du;
    return 0;
}
#endif
