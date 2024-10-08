#ifndef ENCODING_HEADER
#define ENCODING_HEADER

struct vector_hash {
    std::size_t operator()(const std::vector<uint8_t>& vec) const {
        size_t hash_val = vec.size();
        for (size_t i=0; i<vec.size(); ++i)
            hash_val ^= std::hash<size_t>{}(std::hash<uint8_t>{}(vec[i]) - std::hash<size_t>{}(i));
        return hash_val;
    }
};

void buffer_compress(const std::vector<uint8_t>& input, std::vector<uint16_t>& output) {
    std::unordered_map<std::vector<uint8_t>, uint16_t, vector_hash> dictionary;
    uint16_t dict_size = 256;
    for (uint16_t i = 0; i < 256; i++) {
        dictionary[{static_cast<uint8_t>(i)}] = i;
    }

    std::vector<uint8_t> w;

    for (uint8_t c : input) {
        std::vector<uint8_t> wc = w;
        wc.push_back(c);
        if (dictionary.count(wc)) {
            w = wc;
        } else {
            output.push_back(dictionary[w]);
            dictionary[wc] = dict_size++;
            w = {c};
        }
    }

    if (!w.empty()) {
        output.push_back(dictionary[w]);
    }
}

int buffer_decompress(const std::vector<uint16_t>& compressed, std::vector<uint8_t>& output) {
    try {
        std::unordered_map<uint16_t, std::vector<uint8_t>> dictionary;
        uint16_t dict_size = 256;
        for (uint16_t i = 0; i < 256; i++) {
            dictionary[i] = {static_cast<uint8_t>(i)};
        }

        std::vector<uint8_t> w = {static_cast<uint8_t>(compressed[0])};
        output = w;

        std::vector<uint8_t> entry;
        for (size_t i = 1; i < compressed.size(); i++) {
            uint16_t k = compressed[i];
            if (dictionary.count(k)) {
                entry = dictionary[k];
            } else if (k == dict_size) {
                entry = w;
                entry.push_back(w[0]);
            } else {
                return 1;
            }

            output.insert(output.end(), entry.begin(), entry.end());

            dictionary[dict_size++] = w;
            dictionary[dict_size - 1].push_back(entry[0]);

            w = entry;
        }
        return 0;
    } catch(const std::runtime_error& e){
        return 1;
    }
}

void buffer_encode(const std::vector<uint16_t>& input, std::vector<uint8_t>& output) {
    output.clear();
    output.reserve((16*input.size()+5)/6);

    uint32_t buffer = 0;
    uint8_t bits = 0;
    for (auto word : input){
        buffer |= static_cast<uint32_t>(word) << bits;
        bits += 16;
        while (bits>=6){
            output.push_back(48+(buffer&0x3F));
            buffer>>=6;
            bits-=6;
        }
    }
    if (bits)
        output.push_back(48+(buffer&0x3F));
}

int buffer_decode(const std::vector<uint8_t>& input, std::vector<uint16_t>& output) {
    try {
        output.clear();
        output.reserve(1 + 3 * input.size() / 8);

        uint32_t buffer = 0;
        uint8_t bits = 0;

        for (auto byte : input) {
            buffer |= (byte - 48) << bits;
            bits += 6;
            
            while (bits >= 16) {
                output.push_back(buffer & 0xFFFF);
                buffer >>= 16;
                bits -= 16;
            }
        }

        return 0;
    } catch(const std::runtime_error& e){
        return 1;
    }
}


#endif