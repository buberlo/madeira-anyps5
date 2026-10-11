/* The production native query body. No Darwin dynamic TLS or heap allocation. */
#ifndef IOS_FEX_CRITICAL_NATIVE_H
#define IOS_FEX_CRITICAL_NATIVE_H
#include <limits.h>
#include <signal.h>
#include "ios_fex_critical_abi.h"

#define IOS_CRITICAL_SUCCESS       0u
#define IOS_CRITICAL_UNSUCCESSFUL  0xc0000001u
#define IOS_CRITICAL_LENGTH        0xc0000004u
#define IOS_CRITICAL_PARAMETER     0xc000000du
#define IOS_CRITICAL_ACCESS        0xc0000022u
#define IOS_CRITICAL_OVERFLOW      0xc0000095u
#define IOS_CRITICAL_NOT_READY     0xc00000a3u
#define IOS_CRITICAL_STATE         0xc0000184u

/* Appended to native ntdll_thread_data in the already allocated, zeroed TEB.
 * A Mach-O _Thread_local first access can allocate and is unsuitable here. */
struct ios_fex_critical_native_state
{
    uint64_t token;
    uint64_t teb;
    uint32_t depth;
    uint32_t flags;
    uint32_t poisoned;
    uint32_t unregistered;
    sigset_t old_mask;
};

struct ios_fex_critical_native_ops
{
    int (*mask)(int, const sigset_t *, sigset_t *);
    uint32_t (*exchange)(uint32_t, uint64_t, uint64_t, uint64_t *, uint32_t *, uint64_t *);
};

static inline void ios_fex_critical_output(struct ios_fex_critical_request *out,
        uint32_t operation, const struct ios_fex_critical_native_state *state)
{
    out->magic = IOS_FEX_CRITICAL_MAGIC;
    out->version = IOS_FEX_CRITICAL_VERSION;
    out->operation = operation;
    out->depth = state->depth;
    out->token = state->token;
    out->teb = state->teb;
    out->flags = state->flags;
    out->reserved = 0;
}

/* mode: -1 genuinely uninitialised, 0 explicitly disabled, 1 enabled.
 * The caller obtains authoritative_teb from native NtCurrentTeb, never FEX.
 * The same body is used by the native harness with real pthread_sigmask. */
static inline uint32_t ios_fex_critical_native_query(
        struct ios_fex_critical_native_state *state,
        const struct ios_fex_critical_native_ops *ops, uint64_t authoritative_teb,
        int mode, int self_handle, struct ios_fex_critical_request *data,
        unsigned int length, unsigned int *return_length)
{
    struct ios_fex_critical_request input, output;
    struct ios_fex_critical_native_state saved;
    uint32_t status, server_depth;
    uint64_t server_token, server_teb;
    sigset_t blocked, original_mask;

    if (return_length) *return_length = 0;
    if (!self_handle) return IOS_CRITICAL_ACCESS;
    if (length != sizeof(input)) return IOS_CRITICAL_LENGTH;
    if (!data || !authoritative_teb) return IOS_CRITICAL_PARAMETER;
    input = *data;
    if (input.magic != IOS_FEX_CRITICAL_MAGIC || input.version != IOS_FEX_CRITICAL_VERSION ||
        input.reserved || (input.operation != IOS_FEX_CRITICAL_ENTER &&
                           input.operation != IOS_FEX_CRITICAL_LEAVE)) return IOS_CRITICAL_PARAMETER;
    if (state->poisoned) return IOS_CRITICAL_STATE;

    if (input.operation == IOS_FEX_CRITICAL_ENTER)
    {
        if (input.depth || input.token || input.teb || input.flags) return IOS_CRITICAL_PARAMETER;
        if (mode < 0) return IOS_CRITICAL_NOT_READY;
        if (state->depth)
        {
            if (state->teb != authoritative_teb || state->unregistered) return IOS_CRITICAL_STATE;
            /* An early mode-off scope must not absorb a later enabled scope. */
            if ((state->flags & IOS_FEX_CRITICAL_INACTIVE) && mode) return IOS_CRITICAL_STATE;
            if (state->depth == UINT_MAX) return IOS_CRITICAL_OVERFLOW;
            state->depth++;
        }
        else if (!mode)
        {
            state->teb = authoritative_teb;
            state->flags = IOS_FEX_CRITICAL_INACTIVE;
            state->token = 0;
            state->depth = 1;
        }
        else
        {
            sigemptyset(&blocked);
            sigaddset(&blocked, SIGUSR1);
            if (ops->mask(SIG_BLOCK, &blocked, &original_mask)) return IOS_CRITICAL_UNSUCCESSFUL;
            status = ops->exchange(IOS_FEX_CRITICAL_ENTER, authoritative_teb, 0,
                                   &server_token, &server_depth, &server_teb);
            if (status)
            {
                /* A server refusal has not registered a scope. Restore ALL prior bits. */
                if (ops->mask(SIG_SETMASK, &original_mask, NULL))
                {
                    state->old_mask = original_mask;
                    state->poisoned = 1;
                    return IOS_CRITICAL_UNSUCCESSFUL;
                }
                return status;
            }
            if (!server_token || server_depth != 1 || server_teb != authoritative_teb)
            {
                /* A malformed success may have registered: keep SIGUSR1 blocked. */
                state->old_mask = original_mask;
                state->poisoned = 1;
                return IOS_CRITICAL_STATE;
            }
            state->teb = authoritative_teb;
            state->flags = 0;
            state->token = server_token;
            state->depth = 1;
            state->unregistered = 0;
            state->old_mask = original_mask;
        }
        ios_fex_critical_output(&output, input.operation, state);
    }
    else
    {
        if (!state->depth || state->teb != authoritative_teb || input.depth != state->depth ||
            input.token != state->token || input.teb != state->teb || input.flags != state->flags)
            return IOS_CRITICAL_STATE;
        if (state->depth > 1)
        {
            state->depth--;
            ios_fex_critical_output(&output, input.operation, state);
        }
        else
        {
            saved = *state;
            if (!(state->flags & IOS_FEX_CRITICAL_INACTIVE))
            {
                status = ops->exchange(IOS_FEX_CRITICAL_LEAVE, authoritative_teb, state->token,
                                       &server_token, &server_depth, &server_teb);
                if (status) return status; /* Refusal preserves mask, tuple and registration. */
                if (server_token || server_depth || server_teb != authoritative_teb)
                {
                    state->poisoned = 1;
                    return IOS_CRITICAL_STATE;
                }
            }
            /* The locks are released and the server scope is inactive. Clear TLS BEFORE
             * unmasking: an immediately delivered handler may enter a fresh, real scope. */
            state->depth = 0;
            state->token = 0;
            state->teb = 0;
            state->flags = 0;
            state->unregistered = 0;
            if (!(saved.flags & IOS_FEX_CRITICAL_INACTIVE) &&
                ops->mask(SIG_SETMASK, &saved.old_mask, NULL))
            {
                *state = saved;
                state->unregistered = 1;
                state->poisoned = 1; /* Do not submit a second unregister or acquire locks. */
                return IOS_CRITICAL_UNSUCCESSFUL;
            }
            saved.depth = 0;
            saved.token = 0;
            ios_fex_critical_output(&output, input.operation, &saved);
        }
    }
    *data = output;
    if (return_length) *return_length = sizeof(output);
    return IOS_CRITICAL_SUCCESS;
}

/* Only the exiting native thread calls this after its existing FEX hold teardown.
 * pthread termination discards its mask; never unmask/LEAVE somebody else's scope. */
static inline void ios_fex_critical_native_discard(struct ios_fex_critical_native_state *state)
{
    const struct ios_fex_critical_native_state empty = {0};
    *state = empty;
}
#endif
