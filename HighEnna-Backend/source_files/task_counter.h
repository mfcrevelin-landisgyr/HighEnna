#ifndef TASK_COUNTER_HEADER
#define TASK_COUNTER_HEADER

struct TaskCounter {
private:
    std::atomic<uint64_t> cur_count;
    std::atomic<uint64_t> ttl_count;
public:
    TaskCounter() : cur_count(0), ttl_count(0) {}
    void add(uint64_t n) { cur_count+=n; ttl_count+=n; }
    void add() { ++cur_count; ++ttl_count; }
    void sub() { --cur_count; }
    void reset_total() { ttl_count = 0; }
    int total() const { return ttl_count; }
    int current() const { return ttl_count-cur_count; }
    bool is_finished() const { return !cur_count; }
};

#endif
