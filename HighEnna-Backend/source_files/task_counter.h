#ifndef TASK_COUNTER_HEADER
#define TASK_COUNTER_HEADER

struct TaskCounter {
private:
    std::atomic<uint64_t> cur_count;
    std::atomic<uint64_t> ttl_count;
    uint64_t p_cur_count;
    uint64_t p_ttl_count;
public:
    TaskCounter() : cur_count(0), ttl_count(0) {}
    void add(uint64_t n) { cur_count+=n; ttl_count+=n; }
    void add() { ++cur_count; ++ttl_count; }
    void sub() { --cur_count; }
    void reset_total() { ttl_count = 0; }
    bool is_finished() const { return !cur_count; }
    
    int total() {
        uint64_t n_ttl_count = ttl_count.load(std::memory_order_relaxed);
        p_ttl_count = n_ttl_count == UINT64_MAX ? p_ttl_count : n_ttl_count;
        return p_ttl_count;
    }

    int current() {
        uint64_t n_ttl_count = ttl_count.load(std::memory_order_relaxed);
        if (n_ttl_count != UINT64_MAX)
            p_ttl_count =  n_ttl_count;
        uint64_t n_cur_count = cur_count.load(std::memory_order_relaxed);
        if (n_cur_count != UINT64_MAX)
            p_cur_count =  n_cur_count;
        return p_ttl_count - p_cur_count;
    }
};

#endif
