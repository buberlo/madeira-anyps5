/* Diagnostic-only, allocation-free reads of exact Native58 FEX globals and
 * native TEB state. A matching signed-package contract is required by the
 * collector; header identity is not a replacement for that byte proof. */
#ifndef IOS_CRITICAL_OWNER_SAMPLE_H
#define IOS_CRITICAL_OWNER_SAMPLE_H
#include <stdint.h>
#include <stddef.h>
#include <string.h>

#define IOS_CO_MAX_LDR 200u
#define IOS_CO_MAX_ROWS 256u
#define IOS_CO_RPM_OWNER_RVA UINT64_C(0x421500)
#define IOS_CO_RPM_DEPTH_RVA UINT64_C(0x4214d0)
#define IOS_CO_IMAGE_BYTES UINT64_C(0x46a000)
#define IOS_CO_CRITICAL_OFFSET UINT64_C(0x3d8)

struct ios_co_critical {
    uint64_t token, teb;
    uint32_t depth, flags, poisoned, unregistered;
};
struct ios_co_sample {
    uint64_t target_teb, self, peb, process_id, thread_id;
    uint64_t pe_base, live_owner, live_depth, mapping_owner;
    uint64_t rpm_owner[2];
    uint32_t rpm_depth[2];
    struct ios_co_critical critical[2];
    unsigned identity_ok, critical_read, critical_equal, critical_shape;
    unsigned image_ok, mapping_ok, rpm_read, rpm_equal, target_is_owner;
    unsigned reason, loader_nodes;
};
struct ios_co_ops {
    int (*read)(uint64_t, void *, size_t);
    void *(*translate)(void *, void *);
    void *(*pool_owner)(const void *, void **);
};
enum { IOS_CO_OK, IOS_CO_NO_TEB, IOS_CO_BAD_IDENTITY, IOS_CO_BAD_LOADER,
       IOS_CO_BAD_IMAGE, IOS_CO_BAD_MAPPING, IOS_CO_READ_FAILED,
       IOS_CO_MAPPING_CHANGED };

static int ios_co_ptr(uint64_t p) { return p > 0x10000 && !(p & 7) && p < UINT64_MAX - 0x500000; }
static int ios_co_image(const struct ios_co_ops *ops, uint64_t base)
{
    unsigned char dos[64], nt[88]; uint32_t off, timestamp, image_bytes;
    static const unsigned char expected_dos[64] = {
        0x4d,0x5a,0x78,0x00,0x01,0x00,0x00,0x00,0x04,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
        0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x40,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
        0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
        0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x78,0x00,0x00,0x00 };
    if (!ios_co_ptr(base) || !ops->read(base, dos, sizeof(dos)) || memcmp(dos, expected_dos, sizeof(dos))) return 0;
    memcpy(&off, dos + 60, 4);
    if (off != 120 || !ops->read(base + off, nt, sizeof(nt))) return 0;
    memcpy(&timestamp, nt + 8, 4); memcpy(&image_bytes, nt + 24 + 56, 4);
    return !memcmp(nt, "PE\0\0", 4) && nt[4] == 0x64 && nt[5] == 0x86 && nt[6] == 15 && !nt[7] &&
           timestamp == UINT32_C(1791660933) && nt[20] == 240 && !nt[21] && nt[24] == 0x0b && nt[25] == 2 &&
           image_bytes == IOS_CO_IMAGE_BYTES;
}

/* Only the sampled thread's bounded loader list is read. No name truncation,
 * nearest-image search, process-global module lookup or arbitrary heap scan. */
static int ios_co_find_fex(const struct ios_co_ops *ops, uint64_t peb, struct ios_co_sample *out)
{
    uint64_t ldr, head, cur, next, base, buf; uint32_t bytes; uint16_t len, name[12];
    static const uint16_t exact_name[12] = {'x','t','a','j','i','t','6','4','.','d','l','l'};
    unsigned hits = 0;
    if (!ios_co_ptr(peb) || !ops->read(peb + 0x18, &ldr, 8) || !ios_co_ptr(ldr)) return 0;
    head = ldr + 0x10;
    if (!ops->read(head, &cur, 8)) return 0;
    for (out->loader_nodes = 0; cur != head && out->loader_nodes < IOS_CO_MAX_LDR; ++out->loader_nodes) {
        if (!ios_co_ptr(cur) || !ops->read(cur, &next, 8) || !ops->read(cur + 0x58, &len, 2)) return 0;
        if (len == sizeof(exact_name)) {
            if (!ops->read(cur + 0x60, &buf, 8) || !ios_co_ptr(buf) || !ops->read(buf, name, sizeof(name))) return 0;
            if (!memcmp(name, exact_name, sizeof(name))) {
                if (++hits != 1 || !ops->read(cur + 0x30, &base, 8) || !ios_co_ptr(base) ||
                    !ops->read(cur + 0x40, &bytes, 4) || bytes != IOS_CO_IMAGE_BYTES) return 0;
                out->pe_base = base;
            }
        }
        cur = next;
    }
    return cur == head && hits == 1;
}

static int ios_co_mapping(const struct ios_co_ops *ops, struct ios_co_sample *out, int repeat)
{
    void *pe1 = NULL, *pe2 = NULL; uint64_t owner, depth, identity1, identity2;
    owner = (uint64_t)(uintptr_t)ops->translate((void *)(uintptr_t)(out->pe_base + IOS_CO_RPM_OWNER_RVA), (void *)(uintptr_t)out->peb);
    depth = (uint64_t)(uintptr_t)ops->translate((void *)(uintptr_t)(out->pe_base + IOS_CO_RPM_DEPTH_RVA), (void *)(uintptr_t)out->peb);
    if (!ios_co_ptr(owner) || !ios_co_ptr(depth) || owner == out->pe_base + IOS_CO_RPM_OWNER_RVA ||
        owner - depth != IOS_CO_RPM_OWNER_RVA - IOS_CO_RPM_DEPTH_RVA) return 0;
    identity1 = (uint64_t)(uintptr_t)ops->pool_owner((void *)(uintptr_t)owner, &pe1);
    identity2 = (uint64_t)(uintptr_t)ops->pool_owner((void *)(uintptr_t)depth, &pe2);
    /* FEX may have the explicit shared-parent copy (owner NULL). Never admit
     * any permissive foreign-process fallback; translation is silent and exact. */
    if ((uint64_t)(uintptr_t)pe1 != out->pe_base || pe1 != pe2 || identity1 != identity2 ||
        (identity1 && identity1 != out->peb)) return 0;
    if (repeat) return owner == out->live_owner && depth == out->live_depth && identity1 == out->mapping_owner;
    out->live_owner = owner; out->live_depth = depth; out->mapping_owner = identity1;
    return 1;
}

/* Caller must own a successful Mach thread_suspend while this body runs and
 * resume before logging. Other threads remain live: equal double reads are
 * observational consistency, not an atomic multi-thread snapshot or unwind. */
static void ios_co_capture(const struct ios_co_ops *ops, uint64_t teb, struct ios_co_sample *out)
{
    const struct ios_co_sample zero = {0}; struct ios_co_sample final_image = {0}; uint64_t self2, peb2;
    *out = zero; out->target_teb = teb; out->reason = IOS_CO_NO_TEB;
    if (!ios_co_ptr(teb) || (teb & 0xfff)) return;
    out->reason = IOS_CO_BAD_IDENTITY;
    if (!ops->read(teb + 0x30, &out->self, 8) || out->self != teb ||
        !ops->read(teb + 0x60, &out->peb, 8) || !ios_co_ptr(out->peb) ||
        !ops->read(teb + 0x40, &out->process_id, 8) || !out->process_id ||
        !ops->read(teb + 0x48, &out->thread_id, 8) || !out->thread_id) return;
    out->identity_ok = 1;
    out->critical_read = ops->read(teb + IOS_CO_CRITICAL_OFFSET, &out->critical[0], sizeof(out->critical[0])) &&
                         ops->read(teb + IOS_CO_CRITICAL_OFFSET, &out->critical[1], sizeof(out->critical[1]));
    out->critical_equal = out->critical_read && !memcmp(&out->critical[0], &out->critical[1], sizeof(out->critical[0]));
    out->critical_shape = out->critical_equal && out->critical[0].flags <= 1 && out->critical[0].poisoned <= 1 &&
        out->critical[0].unregistered <= 1 && ((!out->critical[0].depth && !out->critical[0].token && !out->critical[0].teb) ||
        (out->critical[0].depth && out->critical[0].teb == teb &&
         ((out->critical[0].flags == 1 && !out->critical[0].token) || (!out->critical[0].flags && out->critical[0].token))));
    out->reason = IOS_CO_BAD_LOADER;
    if (!ios_co_find_fex(ops, out->peb, out)) return;
    out->reason = IOS_CO_BAD_IMAGE;
    if (!(out->image_ok = ios_co_image(ops, out->pe_base))) return;
    out->reason = IOS_CO_BAD_MAPPING;
    if (!(out->mapping_ok = ios_co_mapping(ops, out, 0))) return;
    out->reason = IOS_CO_READ_FAILED;
    if (!ops->read(out->live_owner, &out->rpm_owner[0], 8) || !ops->read(out->live_depth, &out->rpm_depth[0], 4) ||
        !ops->read(out->live_owner, &out->rpm_owner[1], 8) || !ops->read(out->live_depth, &out->rpm_depth[1], 4)) return;
    out->rpm_read = 1; out->reason = IOS_CO_MAPPING_CHANGED;
    if (!ios_co_mapping(ops, out, 1) || !ops->read(teb + 0x30, &self2, 8) || self2 != out->self ||
        !ops->read(teb + 0x60, &peb2, 8) || peb2 != out->peb ||
        !ios_co_find_fex(ops, out->peb, &final_image) || final_image.pe_base != out->pe_base ||
        !ios_co_image(ops, out->pe_base)) { out->mapping_ok = 0; return; }
    out->rpm_equal = out->rpm_owner[0] == out->rpm_owner[1] && out->rpm_depth[0] == out->rpm_depth[1];
    out->target_is_owner = out->rpm_equal && out->rpm_owner[0] == (teb | 1);
    out->reason = IOS_CO_OK;
}
#endif
