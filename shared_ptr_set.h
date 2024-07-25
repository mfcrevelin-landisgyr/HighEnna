#ifndef SHARED_POINTER_SET_H
#define SHARED_POINTER_SET_H

namespace std {
    template <typename T, typename Hash = std::hash<T>, typename KeyEqual = std::equal_to<T>>
    struct shared_ptr_set {
        std::unordered_set<std::shared_ptr<T>, Hash, KeyEqual> set;

        struct PtrHash {
            size_t operator()(const std::shared_ptr<T>& ptr) const {
                return Hash{}(*ptr);
            }
        };

        struct PtrEqual {
            bool operator()(const std::shared_ptr<T>& lhs, const std::shared_ptr<T>& rhs) const {
                return KeyEqual{}(*lhs, *rhs);
            }
        };

        bool insert(const T& value) {
            auto it = std::find_if(set.begin(), set.end(), [&value](const std::shared_ptr<T>& ptr) {
                return *ptr == value;
            });
            if (it == set.end()) {
                set.insert(std::make_shared<T>(value));
                return true;
            }
            return false;
        }

        bool contains(const T& value) const {
            return std::any_of(set.begin(), set.end(), [&value](const std::shared_ptr<T>& ptr) {
                return *ptr == value;
            });
        }

        bool erase(const T& value) {
            auto it = std::find_if(set.begin(), set.end(), [&value](const std::shared_ptr<T>& ptr) {
                return *ptr == value;
            });
            if (it != set.end()) {
                set.erase(it);
                return true;
            }
            return false;
        }

        void clear() {
            set.clear();
        }

        bool empty() const {
            return set.empty();
        }

        size_t size() const {
            return set.size();
        }

        std::shared_ptr<T> get(const T& value) const {
            auto it = std::find_if(set.begin(), set.end(), [&value](const std::shared_ptr<T>& ptr) {
                return *ptr == value;
            });
            if (it != set.end()) {
                return it;
            }
            return nullptr;
        }

        // Iterator types
        using iterator = typename std::unordered_set<std::shared_ptr<T>, PtrHash, PtrEqual>::iterator;
        using const_iterator = typename std::unordered_set<std::shared_ptr<T>, PtrHash, PtrEqual>::const_iterator;

        iterator begin() { return set.begin(); }
        const_iterator begin() const { return set.begin(); }
        iterator end() { return set.end(); }
        const_iterator end() const { return set.end(); }
    };
}

#endif