/* Root-use native harness. It includes production helpers and exact extracted
 * thread.c functions/handler, using only thin object/request adapters below.
 * This file is source-only until root compiles/runs it. */
#define WINE_IOS 1
#include <assert.h>
#include <pthread.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <time.h>
#include "ios_fex_critical_native.h"
#include "ios_fex_critical_server.h"

#define STATUS_SUCCESS 0u
#define STATUS_PENDING 0x103u
#define STATUS_CANCELLED 0xc0000120u
#define STATUS_INVALID_PARAMETER 0xc000000du
#define STATUS_NOT_SUPPORTED 0xc00000bbu
#define IMAGE_FILE_MACHINE_AMD64 0x8664u
#define REQ_suspend_thread 11
#define REQ_suspend_process 12
#define RUNNING 0
struct sync { int signals; };
struct process { unsigned id, machine; int initialised, suspend; void *debug_obj, *debug_event; };
struct context {
    unsigned status;
    struct sync *sync;
    uint64_t ios_fex_generation;
    unsigned ios_fex_origin_process, ios_fex_origin_thread;
    int references;
};
struct thread {
    struct process *process;
    struct context *context, *ios_fex_pending_context;
    struct ios_fex_critical_scope ios_fex_scope;
    uint64_t teb, ios_fex_capture_generation, suspend_cookie;
    unsigned id, ios_ctx_seq, ios_fex_suspend_owner;
    int state, suspend, bypass_proc_suspend, ios_start_pending, ios_mach_suspended;
    int ios_fex_suspend_eligible;
    struct { struct { int req; } request_header; } req;
};
struct request { uint32_t magic, version, operation, reserved; uint64_t token, teb; };
struct reply { uint64_t token, teb; uint32_t depth; };
static struct thread *current;
static unsigned current_error, req_data_size;
static unsigned wake_calls, actual_due_results;
static int deadline_due, object_ready;
int ios_x64_signal_suspend_enabled = 1, ios_x64_signal_suspend_mode_ready = 1;
static int is_process_init_done(struct process *p) { return p->initialised; }
static void signal_sync(struct sync *s) { s->signals++; }
static void release_object(struct context *c) { assert(c->references > 0); c->references--; }
static unsigned get_req_data_size(void) { return req_data_size; }
static void set_error(unsigned s) { current_error = s; }
static int is_thread_wait_suspended(struct thread *thread);
static int wake_thread(struct thread *thread) {
    wake_calls++;
    if (!is_thread_wait_suspended(thread) && (deadline_due || object_ready)) {
        actual_due_results++;
        deadline_due = object_ready = 0;
        return 1;
    }
    return 0;
}
#define DECL_HANDLER(name) static void handle_##name(const struct request *req, struct reply *reply)
#include "production-server-bodies.inc"

static struct process process = {10, IMAGE_FILE_MACHINE_AMD64, 1, 0, 0, 0};
static struct thread target, requester;
static struct context context1, context2;
static struct sync sync1, sync2;
static unsigned checks;
#define CHECK(x) do { if (!(x)) { fprintf(stderr,"check failed at %d: %s\n",__LINE__,#x); return 1; } checks++; } while (0)

static void reset(void) {
    memset(&target,0,sizeof(target)); memset(&requester,0,sizeof(requester));
    memset(&context1,0,sizeof(context1)); memset(&context2,0,sizeof(context2));
    memset(&sync1,0,sizeof(sync1)); memset(&sync2,0,sizeof(sync2));
    process.initialised=1; process.suspend=0; process.debug_obj=process.debug_event=0;
    process.machine=IMAGE_FILE_MACHINE_AMD64;
    target.process=requester.process=&process;
    target.id=28; requester.id=24; target.teb=0x10000; requester.teb=0x20000;
    requester.req.request_header.req=REQ_suspend_thread;
    context1.status=context2.status=STATUS_PENDING;
    context1.sync=&sync1; context2.sync=&sync2;
    context1.references=context2.references=2; /* thread plus outstanding waiter handle */
    current=&target; current_error=req_data_size=0;
    wake_calls=actual_due_results=0; deadline_due=object_ready=0;
    ios_x64_signal_suspend_enabled=ios_x64_signal_suspend_mode_ready=1;
}

static unsigned registration(unsigned op, uint64_t token, uint64_t teb, struct reply *out) {
    struct request req={IOS_FEX_CRITICAL_MAGIC,IOS_FEX_CRITICAL_VERSION,op,0,token,teb};
    current_error=0; current=&target;
    handle_ios_fex_critical_scope(&req,out);
    return current_error;
}
static void publish(struct context *ctx, int old_count) {
    current=&requester; target.context=ctx; target.ios_ctx_seq=0x41505335u;
    ios_fex_publish_pending(&target,ctx);
    target.suspend=old_count+1; ios_fex_record_suspend(&target,old_count);
    current=&target;
}

static int server_cases(void) {
    struct reply reply;
    uint64_t token, generation;
    reset();
    CHECK(!registration(1,0,target.teb,&reply)); token=reply.token;
    CHECK(token && reply.depth==1 && !target.ios_fex_scope.pending_context);
    publish(&context1,0); generation=context1.ios_fex_generation;
    CHECK(target.suspend==1 && target.ios_fex_suspend_eligible);
    CHECK(target.ios_fex_scope.pending_context==&context1 && target.ios_fex_scope.capture_generation==generation);
    CHECK(is_thread_suspended(&target) && !is_thread_wait_suspended(&target));
    CHECK(context1.status==STATUS_PENDING && sync1.signals==0);
    deadline_due=1; CHECK(wake_thread(&target)==1 && actual_due_results==1);
    CHECK(target.suspend==1 && context1.status==STATUS_PENDING); /* real wait, never fake ACK */
    target.process->suspend=1; CHECK(is_thread_wait_suspended(&target)); target.process->suspend=0;
    target.process->debug_obj=&process; CHECK(is_thread_wait_suspended(&target)); target.process->debug_obj=0;
    target.process->debug_event=&process; CHECK(is_thread_wait_suspended(&target)); target.process->debug_event=0;
    target.ios_mach_suspended=1; CHECK(is_thread_wait_suspended(&target)); target.ios_mach_suspended=0;
    target.ios_fex_scope.capture_generation++; CHECK(is_thread_wait_suspended(&target)); target.ios_fex_scope.capture_generation=generation;
    target.ios_fex_scope.pending_context=&context2; CHECK(is_thread_wait_suspended(&target)); target.ios_fex_scope.pending_context=&context1;
    context1.ios_fex_origin_process++; CHECK(is_thread_wait_suspended(&target)); context1.ios_fex_origin_process--;
    context1.ios_fex_origin_thread++; CHECK(is_thread_wait_suspended(&target)); context1.ios_fex_origin_thread--;
    current=&requester; requester.req.request_header.req=REQ_suspend_process;
    ios_fex_record_suspend(&target,1); target.suspend=2;
    CHECK(!target.ios_fex_suspend_eligible && is_thread_wait_suspended(&target));
    requester.req.request_header.req=REQ_suspend_thread;
    ios_fex_record_suspend(&target,2); CHECK(!target.ios_fex_suspend_eligible); /* taint stays */
    target.suspend=1; target.ios_fex_suspend_eligible=1;
    ios_fex_ack_context(&target,&context1,99);
    CHECK(context1.status==STATUS_SUCCESS && sync1.signals==1 && target.suspend_cookie==99);
    CHECK(!target.ios_fex_scope.pending_context && is_thread_wait_suspended(&target));
    ios_fex_cancel_pending(&target); CHECK(target.context==&context1 && context1.references==2); /* ACK preserved */
    CHECK(!registration(2,token,target.teb,&reply));
    CHECK(!reply.token && !reply.depth && reply.teb==target.teb);

    reset(); publish(&context1,0);
    deadline_due=1; CHECK(is_thread_wait_suspended(&target));
    CHECK(!registration(1,0,target.teb,&reply)); token=reply.token;
    CHECK(actual_due_results==1 && !is_thread_wait_suspended(&target)); /* enter after PENDING wakes due wait */
    target.suspend=0; ios_fex_cancel_pending(&target);
    CHECK(!target.context && !target.ios_fex_scope.pending_context && !target.ios_ctx_seq);
    CHECK(context1.status==STATUS_CANCELLED && sync1.signals==1 && context1.references==1);
    /* Old handle owns canceled object. A delayed handler creates a different ordinary
     * context; it cannot revive/ACK the canceled generation or scope binding. */
    target.context=&context2; CHECK(!ios_fex_exact_private_pending(&target));
    CHECK(context1.status==STATUS_CANCELLED && sync1.signals==1);
    target.context=0; publish(&context2,0);
    CHECK(context2.ios_fex_generation>context1.ios_fex_generation && !is_thread_wait_suspended(&target));
    CHECK(!registration(2,token,target.teb,&reply)); CHECK(is_thread_wait_suspended(&target));

    reset(); process.initialised=0; target.ios_start_pending=1; target.suspend=1;
    CHECK(!registration(1,0,target.teb,&reply)); token=reply.token;
    CHECK(is_thread_wait_suspended(&target)); /* startup count is NEVER bypassed */
    process.initialised=1; CHECK(is_thread_wait_suspended(&target));
    CHECK(!registration(2,token,target.teb,&reply));
    reset(); target.ios_start_pending=1; target.suspend=1; /* secondary thread, process already initialised */
    CHECK(!registration(1,0,target.teb,&reply)); token=reply.token;
    CHECK(is_thread_wait_suspended(&target));
    CHECK(!registration(2,token,target.teb,&reply));
    reset(); process.initialised=0; target.suspend=1;
    CHECK(registration(1,0,target.teb,&reply));
    target.ios_start_pending=1; target.context=&context1;
    CHECK(registration(1,0,target.teb,&reply));
    reset(); CHECK(registration(1,0,target.teb+8,&reply)); CHECK(!target.ios_fex_scope.token);
    reset(); ios_x64_signal_suspend_mode_ready=0; CHECK(registration(1,0,target.teb,&reply));
    reset(); CHECK(!registration(1,0,target.teb,&reply)); token=reply.token;
    CHECK(registration(2,token+1,target.teb,&reply)); CHECK(target.ios_fex_scope.token==token);
    target.process->suspend=1; target.ios_mach_suspended=1;
    CHECK(!registration(2,token,target.teb,&reply)); /* leave balanced despite later hard hold */
    return 0;
}

static volatile sig_atomic_t delivered;
static unsigned exchanges;
static int refuse_enter, refuse_leave, wrong_reply_teb, fail_restore;
static struct ios_fex_critical_native_state native_state;
static void signal_handler(int sig) { if (sig==SIGUSR1) delivered++; }
static int real_mask(int how,const sigset_t *set,sigset_t *old) {
    if (how==SIG_SETMASK && fail_restore) return 1;
    return pthread_sigmask(how,set,old);
}
static uint32_t exchange(unsigned op,uint64_t teb,uint64_t token,uint64_t *out,unsigned *depth,uint64_t *out_teb) {
    struct reply reply;
    exchanges++;
    if ((op==1 && refuse_enter) || (op==2 && refuse_leave)) return IOS_CRITICAL_ACCESS;
    unsigned status=registration(op,token,teb,&reply);
    if (!status) { *out=reply.token; *depth=reply.depth; *out_teb=wrong_reply_teb ? teb+8 : reply.teb; }
    return status;
}
static const struct ios_fex_critical_native_ops ops={real_mask,exchange};
static struct ios_fex_critical_request enter_request(void) {
    struct ios_fex_critical_request req={IOS_FEX_CRITICAL_MAGIC,IOS_FEX_CRITICAL_VERSION,1,0,0,0,0,0};
    return req;
}
static unsigned query(struct ios_fex_critical_request *req,int mode,int self,unsigned *length) {
    return ios_fex_critical_native_query(&native_state,&ops,target.teb,mode,self,req,sizeof(*req),length);
}
static int native_cases(void) {
    sigset_t initial, mask, pending;
    struct sigaction action={0};
    struct ios_fex_critical_request outer,inner,leave,bad;
    unsigned len;
    reset(); memset(&native_state,0,sizeof(native_state)); delivered=exchanges=0;
    refuse_enter=refuse_leave=wrong_reply_teb=fail_restore=0;
    CHECK(!pthread_sigmask(SIG_SETMASK,0,&initial));
    mask=initial; sigdelset(&mask,SIGUSR1); sigaddset(&mask,SIGUSR2);
    CHECK(!pthread_sigmask(SIG_SETMASK,&mask,0));
    action.sa_handler=signal_handler; sigemptyset(&action.sa_mask);
    CHECK(!sigaction(SIGUSR1,&action,0));
    outer=enter_request(); CHECK(!query(&outer,1,1,&len) && len==40 && outer.depth==1);
    CHECK(exchanges==1 && native_state.depth==1 && target.ios_fex_scope.token==outer.token);
    CHECK(!pthread_sigmask(SIG_SETMASK,0,&pending) && sigismember(&pending,SIGUSR1) && sigismember(&pending,SIGUSR2));
    CHECK(!pthread_kill(pthread_self(),SIGUSR1)); CHECK(!sigpending(&pending) && sigismember(&pending,SIGUSR1) && !delivered);
    inner=enter_request(); CHECK(!query(&inner,1,1,&len) && inner.depth==2 && inner.token==outer.token && exchanges==1);
    bad=outer; bad.operation=2; CHECK(query(&bad,1,1,&len) && native_state.depth==2 && !delivered);
    leave=inner; leave.operation=2; CHECK(!query(&leave,1,1,&len) && leave.depth==1 && exchanges==1 && !delivered);
    refuse_leave=1; leave=outer; leave.operation=2;
    CHECK(query(&leave,1,1,&len)==IOS_CRITICAL_ACCESS && native_state.depth==1 && target.ios_fex_scope.token==outer.token);
    CHECK(!delivered && !pthread_sigmask(SIG_SETMASK,0,&pending) && sigismember(&pending,SIGUSR1));
    bad=leave; CHECK(query(&bad,1,0,&len)==IOS_CRITICAL_ACCESS && native_state.depth==1); /* failed handle leave */
    refuse_leave=0; CHECK(!query(&leave,1,1,&len) && !leave.depth && !leave.token && leave.teb==outer.teb && !native_state.depth);
    CHECK(delivered==1); CHECK(!pthread_sigmask(SIG_SETMASK,0,&pending) && !sigismember(&pending,SIGUSR1) && sigismember(&pending,SIGUSR2));
    reset(); memset(&native_state,0,sizeof(native_state)); refuse_enter=1;
    outer=enter_request(); CHECK(query(&outer,1,1,&len)==IOS_CRITICAL_ACCESS && !native_state.depth && !target.ios_fex_scope.token);
    CHECK(!pthread_sigmask(SIG_SETMASK,0,&pending) && !sigismember(&pending,SIGUSR1) && sigismember(&pending,SIGUSR2));
    refuse_enter=0; outer=enter_request(); CHECK(query(&outer,-1,1,&len)==IOS_CRITICAL_NOT_READY && !native_state.depth);
    outer=enter_request(); CHECK(!query(&outer,0,1,&len) && outer.flags==1 && !outer.token);
    inner=enter_request(); CHECK(query(&inner,1,1,&len)==IOS_CRITICAL_STATE && native_state.depth==1);
    inner=enter_request(); CHECK(!query(&inner,0,1,&len) && inner.depth==2);
    inner.operation=2; CHECK(!query(&inner,0,1,&len)); outer.operation=2; CHECK(!query(&outer,0,1,&len));
    outer=enter_request(); CHECK(!query(&outer,1,1,&len));
    inner=enter_request(); CHECK(!query(&inner,0,1,&len) && !inner.flags && inner.token==outer.token); /* active cannot become modeoff */
    inner.operation=2; CHECK(!query(&inner,0,1,&len)); outer.operation=2; CHECK(!query(&outer,0,1,&len));
    reset(); memset(&native_state,0,sizeof(native_state)); process.initialised=0; target.suspend=1; target.ios_start_pending=1;
    outer=enter_request(); CHECK(!query(&outer,1,1,&len)); process.initialised=1;
    inner=enter_request(); CHECK(!query(&inner,1,1,&len) && inner.token==outer.token);
    inner.operation=2; CHECK(!query(&inner,1,1,&len)); outer.operation=2; CHECK(!query(&outer,1,1,&len));
    reset(); memset(&native_state,0,sizeof(native_state)); target.suspend=1; target.ios_start_pending=1;
    outer=enter_request(); CHECK(!query(&outer,1,1,&len));
    inner=enter_request(); CHECK(!query(&inner,1,1,&len) && inner.token==outer.token);
    inner.operation=2; CHECK(!query(&inner,1,1,&len)); outer.operation=2; CHECK(!query(&outer,1,1,&len));
    reset(); memset(&native_state,0,sizeof(native_state)); outer=enter_request(); CHECK(!query(&outer,1,1,&len));
    outer.operation=2; fail_restore=1; CHECK(query(&outer,1,1,&len)==IOS_CRITICAL_UNSUCCESSFUL && native_state.poisoned && native_state.unregistered);
    CHECK(!target.ios_fex_scope.token); CHECK(!pthread_sigmask(SIG_SETMASK,0,&pending) && sigismember(&pending,SIGUSR1));
    fail_restore=0; CHECK(!pthread_sigmask(SIG_SETMASK,&mask,0)); ios_fex_critical_native_discard(&native_state);
    reset(); wrong_reply_teb=1; outer=enter_request(); CHECK(query(&outer,1,1,&len)==IOS_CRITICAL_STATE && native_state.poisoned);
    CHECK(target.ios_fex_scope.token && !pthread_sigmask(SIG_SETMASK,0,&pending) && sigismember(&pending,SIGUSR1));
    wrong_reply_teb=0; CHECK(!pthread_sigmask(SIG_SETMASK,&initial,0));
    return 0;
}

/* A second real pthread uses its own native state and signal mask. The exchange
 * uses the SAME production registration helper under a test serialization lock;
 * it does not model masks or replace pthread_sigmask. No protected-lock/context
 * cycle is claimed solved by this harness. */
static pthread_mutex_t two_lock=PTHREAD_MUTEX_INITIALIZER;
static struct ios_fex_critical_scope two_scope[2];
static uint64_t two_next;
static uint32_t two_exchange(unsigned op,uint64_t teb,uint64_t token,uint64_t *out,unsigned *depth,uint64_t *out_teb) {
    struct ios_fex_critical_facts facts={.running=1,.amd64=1,.mode_enabled=1,.initialised=1};
    pthread_mutex_lock(&two_lock);
    struct ios_fex_critical_scope *scope = &two_scope[teb == 0x30000 ? 0 : 1];
    unsigned status=ios_fex_critical_register(scope,&facts,teb,teb,op,token,&two_next,out,depth);
    *out_teb=teb;
    pthread_mutex_unlock(&two_lock);
    return status;
}
static void *second_thread(void *unused) {
    struct ios_fex_critical_native_state state={0};
    const struct ios_fex_critical_native_ops second_ops={pthread_sigmask,two_exchange};
    struct ios_fex_critical_request req=enter_request();
    sigset_t before,during,after;
    unsigned len;
    (void)unused;
    if (pthread_sigmask(SIG_SETMASK,0,&before)) return (void *)1;
    sigdelset(&before,SIGUSR1);
    if (pthread_sigmask(SIG_SETMASK,&before,0) || ios_fex_critical_native_query(&state,&second_ops,0x30000,1,1,&req,40,&len)) return (void *)1;
    if (pthread_sigmask(SIG_SETMASK,0,&during) || !sigismember(&during,SIGUSR1)) return (void *)2;
    req.operation=2;
    if (ios_fex_critical_native_query(&state,&second_ops,0x30000,1,1,&req,40,&len) || pthread_sigmask(SIG_SETMASK,0,&after)) return (void *)3;
    for (int s=1;s<NSIG;s++) if (sigismember(&before,s)!=sigismember(&after,s)) return (void *)4;
    return 0;
}

int main(void) {
    pthread_t second;
    void *result;
    sigset_t before,after;
    struct ios_fex_critical_native_state own_state={0};
    const struct ios_fex_critical_native_ops own_ops={pthread_sigmask,two_exchange};
    struct ios_fex_critical_request own=enter_request();
    unsigned len;
    if (server_cases() || native_cases()) return 1;
    CHECK(!pthread_sigmask(SIG_SETMASK,0,&before));
    CHECK(!ios_fex_critical_native_query(&own_state,&own_ops,0x40000,1,1,&own,40,&len));
    CHECK(!pthread_create(&second,0,second_thread,0)); CHECK(!pthread_join(second,&result) && !result);
    CHECK(own_state.depth==1 && two_scope[1].token==own.token && !two_scope[0].token);
    own.operation=2;
    CHECK(!ios_fex_critical_native_query(&own_state,&own_ops,0x40000,1,1,&own,40,&len));
    CHECK(!pthread_sigmask(SIG_SETMASK,0,&after));
    for (int s=1;s<NSIG;s++) CHECK(sigismember(&before,s)==sigismember(&after,s));
    printf("NATIVE_CRITICAL_HELPER_CHECKS %u\n",checks);
    return 0;
}
