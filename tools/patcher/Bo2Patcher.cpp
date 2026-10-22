// Bo2Patcher: applies patch/bo2pl.patch (see tools/build_patch.py) to the user's own game files.
//
//   Bo2Patcher check   <game dir> [bo2pl.patch]
//   Bo2Patcher patch   <game dir> [bo2pl.patch] [--force]
//   Bo2Patcher restore <game dir> [bo2pl.patch]
//
// The manifest lists, per file, the size and CRC-32 of the supported original and a set of byte
// ranges (offset, length, CRC-32 of the original bytes, new bytes). A file is "original" when every
// range still has its original CRC and the whole file matches, and "patched" when every range holds
// the new bytes. Before the first change a full copy "<file>.plbackup" is written next to the file;
// `restore` puts it back.
//
// Exit codes (the installer turns them into messages): 0 ok, 1 usage, 2 error, 3 unsupported game
// build, 4 game is running, 5 not enough disk space, 6 file changed by something else / backup
// missing, 7 no write access.
#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

#ifdef _WIN32
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <tlhelp32.h>
#endif

namespace fs = std::filesystem;

namespace {

constexpr int kOk = 0, kUsage = 1, kError = 2, kBuild = 3, kRunning = 4, kSpace = 5, kChanged = 6, kWrite = 7;

struct Range {
    uint64_t offset = 0;
    uint32_t oldCrc = 0;
    std::vector<uint8_t> bytes;  // new bytes; the length is the range length
    uint32_t newCrc = 0;
};

struct Entry {
    std::string rel;
    uint64_t size = 0;
    uint32_t crc = 0;
    std::vector<Range> ranges;
};

enum class State { Original, Patched, Unsupported, Changed };

uint32_t Crc32(const uint8_t* p, size_t n, uint32_t crc = 0) {
    static uint32_t table[256];
    static bool init = false;
    if (!init) {
        for (uint32_t i = 0; i < 256; ++i) {
            uint32_t c = i;
            for (int k = 0; k < 8; ++k) c = (c & 1) ? 0xEDB88320u ^ (c >> 1) : c >> 1;
            table[i] = c;
        }
        init = true;
    }
    crc = ~crc;
    for (size_t i = 0; i < n; ++i) crc = table[(crc ^ p[i]) & 0xFF] ^ (crc >> 8);
    return ~crc;
}

std::vector<uint8_t> HexToBytes(const std::string& hex) {
    std::vector<uint8_t> out;
    out.reserve(hex.size() / 2);
    for (size_t i = 0; i + 1 < hex.size(); i += 2) out.push_back(uint8_t(std::stoul(hex.substr(i, 2), nullptr, 16)));
    return out;
}

bool ReadFile(const fs::path& p, std::vector<uint8_t>& out) {
    std::ifstream f(p, std::ios::binary);
    if (!f) return false;
    f.seekg(0, std::ios::end);
    auto n = f.tellg();
    f.seekg(0);
    out.resize(size_t(n));
    if (n > 0) f.read(reinterpret_cast<char*>(out.data()), n);
    return bool(f);
}

bool ParseManifest(const fs::path& path, std::vector<Entry>& entries, std::string& err) {
    std::ifstream f(path);
    if (!f) { err = "cannot open the patch file " + path.string(); return false; }
    std::string line;
    if (!std::getline(f, line) || line.rfind("BO2PL-PATCH 1", 0) != 0) { err = "not a BO2PL-PATCH 1 file"; return false; }
    while (std::getline(f, line)) {
        while (!line.empty() && (line.back() == '\r' || line.back() == ' ')) line.pop_back();
        if (line.empty() || line[0] == '#') continue;
        std::istringstream in(line);
        std::string kind;
        in >> kind;
        if (kind == "file") {
            Entry e;
            std::string w1, w2, crc;
            in >> e.rel >> w1 >> e.size >> w2 >> crc;
            e.crc = uint32_t(std::stoul(crc, nullptr, 16));
            entries.push_back(e);
        } else if (kind == "range" && !entries.empty()) {
            Range r;
            std::string off, crc, hex;
            uint64_t len = 0;
            in >> off >> len >> crc >> hex;
            r.offset = std::stoull(off, nullptr, 16);
            r.oldCrc = uint32_t(std::stoul(crc, nullptr, 16));
            r.bytes = HexToBytes(hex);
            if (r.bytes.size() != len) { err = "bad range length in the patch file"; return false; }
            r.newCrc = Crc32(r.bytes.data(), r.bytes.size());
            entries.back().ranges.push_back(std::move(r));
        } else {
            err = "unknown line in the patch file: " + line;
            return false;
        }
    }
    if (entries.empty()) { err = "the patch file lists no files"; return false; }
    return true;
}

// Case-insensitive path lookup relative to the game dir (the shipped files are mixed case).
fs::path Resolve(const fs::path& base, const std::string& rel) {
    fs::path cur = base;
    std::stringstream parts(rel);
    std::string part;
    while (std::getline(parts, part, '/')) {
        fs::path found;
        std::error_code ec;
        for (auto& e : fs::directory_iterator(cur, ec)) {
            std::string a = e.path().filename().string(), b = part;
            std::transform(a.begin(), a.end(), a.begin(), ::tolower);
            std::transform(b.begin(), b.end(), b.begin(), ::tolower);
            if (a == b) { found = e.path(); break; }
        }
        cur = found.empty() ? cur / part : found;
    }
    return cur;
}

State Classify(const Entry& e, const std::vector<uint8_t>& data) {
    if (data.size() != e.size) return State::Unsupported;
    size_t orig = 0, patched = 0;
    for (auto& r : e.ranges) {
        if (r.offset + r.bytes.size() > data.size()) return State::Unsupported;
        uint32_t c = Crc32(data.data() + r.offset, r.bytes.size());
        if (c == r.oldCrc) ++orig;
        else if (c == r.newCrc) ++patched;
    }
    if (!e.ranges.empty() && patched == e.ranges.size()) return State::Patched;
    if (orig == e.ranges.size()) return Crc32(data.data(), data.size()) == e.crc ? State::Original : State::Unsupported;
    return State::Changed;
}

const char* Name(State s) {
    switch (s) {
        case State::Original: return "original";
        case State::Patched: return "patched";
        case State::Unsupported: return "unsupported build";
        default: return "changed by something else";
    }
}

bool GameRunning() {
#ifdef _WIN32
    HANDLE snap = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    if (snap == INVALID_HANDLE_VALUE) return false;
    PROCESSENTRY32 pe{};
    pe.dwSize = sizeof(pe);
    bool found = false;
    for (BOOL ok = Process32First(snap, &pe); ok && !found; ok = Process32Next(snap, &pe))
        found = _stricmp(pe.szExeFile, "bo2.exe") == 0;
    CloseHandle(snap);
    return found;
#else
    // Wine/Proton: the process is called bo2.exe (comm) and/or its argv[0] ends in bo2.exe.
    auto lower = [](std::string s) { std::transform(s.begin(), s.end(), s.begin(), ::tolower); return s; };
    std::error_code ec;
    for (auto& e : fs::directory_iterator("/proc", ec)) {
        std::string pid = e.path().filename().string();
        if (pid.empty() || !std::all_of(pid.begin(), pid.end(), ::isdigit)) continue;
        std::string comm;
        std::ifstream(e.path() / "comm") >> comm;
        if (lower(comm) == "bo2.exe") return true;
        std::ifstream f(e.path() / "cmdline", std::ios::binary);
        std::string argv0;
        std::getline(f, argv0, '\0');
        size_t cut = argv0.find_last_of("/\\");
        if (lower(cut == std::string::npos ? argv0 : argv0.substr(cut + 1)) == "bo2.exe") return true;
    }
    return false;
#endif
}

bool Writable(const fs::path& p) {
    FILE* f = std::fopen(p.string().c_str(), "r+b");
    if (!f) return false;
    std::fclose(f);
    return true;
}

bool WriteRanges(const fs::path& p, const Entry& e) {
    FILE* f = std::fopen(p.string().c_str(), "r+b");
    if (!f) return false;
    bool ok = true;
    for (auto& r : e.ranges) {
        if (std::fseek(f, long(r.offset), SEEK_SET) != 0 || std::fwrite(r.bytes.data(), 1, r.bytes.size(), f) != r.bytes.size()) { ok = false; break; }
    }
    ok = (std::fflush(f) == 0) && ok;
    std::fclose(f);
    return ok;
}

fs::path BackupPath(const fs::path& p) { return fs::path(p.string() + ".plbackup"); }

struct Target {
    const Entry* entry;
    fs::path path;
    std::vector<uint8_t> data;
    State state;
};

int Load(const fs::path& game, const std::vector<Entry>& entries, std::vector<Target>& out, bool force) {
    for (auto& e : entries) {
        Target t{&e, Resolve(game, e.rel), {}, State::Unsupported};
        if (!ReadFile(t.path, t.data)) { std::cerr << "cannot read " << t.path << "\n"; return kBuild; }
        t.state = Classify(e, t.data);
        std::cout << e.rel << ": " << Name(t.state) << "\n";
        if (t.state == State::Unsupported && !force) return kBuild;
        out.push_back(std::move(t));
    }
    return kOk;
}

int Check(const fs::path& game, const std::vector<Entry>& entries) {
    std::vector<Target> targets;
    if (int rc = Load(game, entries, targets, false)) return rc;
    for (auto& t : targets)
        if (t.state == State::Changed) return kChanged;
    if (GameRunning()) { std::cerr << "the game is running\n"; return kRunning; }
    for (auto& t : targets)
        if (!Writable(t.path)) { std::cerr << "no write access to " << t.path << "\n"; return kWrite; }
    return kOk;
}

int Patch(const fs::path& game, const std::vector<Entry>& entries, bool force) {
    std::vector<Target> targets;
    if (int rc = Load(game, entries, targets, force)) return rc;
    for (auto& t : targets)
        if (t.state == State::Changed && !force) { std::cerr << t.entry->rel << " was changed by something else; verify the game files (or use --force)\n"; return kChanged; }
    if (GameRunning()) { std::cerr << "the game is running\n"; return kRunning; }

    uint64_t need = 16ull << 20;
    for (auto& t : targets)
        if (t.state == State::Original) need += t.data.size();
    std::error_code ec;
    auto space = fs::space(game, ec);
    if (!ec && space.available < need) { std::cerr << "not enough disk space\n"; return kSpace; }
    for (auto& t : targets)
        if (!Writable(t.path)) { std::cerr << "no write access to " << t.path << "\n"; return kWrite; }

    std::vector<size_t> done;
    for (size_t i = 0; i < targets.size(); ++i) {
        auto& t = targets[i];
        if (t.state == State::Patched) { std::cout << t.entry->rel << ": already patched\n"; continue; }
        // The file is verified original (or forced): keep a full copy before the first write.
        fs::copy_file(t.path, BackupPath(t.path), fs::copy_options::overwrite_existing, ec);
        if (ec) { std::cerr << "cannot write the backup of " << t.path << ": " << ec.message() << "\n"; return kWrite; }
        if (!WriteRanges(t.path, *t.entry)) {
            std::cerr << "writing " << t.path << " failed\n";
            for (size_t j : done) fs::copy_file(BackupPath(targets[j].path), targets[j].path, fs::copy_options::overwrite_existing, ec);
            fs::copy_file(BackupPath(t.path), t.path, fs::copy_options::overwrite_existing, ec);
            return kWrite;
        }
        done.push_back(i);
        std::vector<uint8_t> check;
        if (!ReadFile(t.path, check) || Classify(*t.entry, check) != State::Patched) {
            std::cerr << "verification of " << t.path << " failed\n";
            for (size_t j : done) fs::copy_file(BackupPath(targets[j].path), targets[j].path, fs::copy_options::overwrite_existing, ec);
            return kError;
        }
        std::cout << t.entry->rel << ": patched (" << t.entry->ranges.size() << " ranges), backup " << BackupPath(t.path).filename() << "\n";
    }
    return kOk;
}

int Restore(const fs::path& game, const std::vector<Entry>& entries) {
    if (GameRunning()) { std::cerr << "the game is running\n"; return kRunning; }
    int rc = kOk;
    for (auto& e : entries) {
        fs::path path = Resolve(game, e.rel), backup = BackupPath(path);
        std::vector<uint8_t> cur, bak;
        if (!ReadFile(path, cur)) { std::cout << e.rel << ": file is missing, nothing to restore\n"; continue; }
        State s = Classify(e, cur);
        if (s == State::Original) {
            std::cout << e.rel << ": already original\n";
            std::error_code ec;
            fs::remove(backup, ec);
            continue;
        }
        if (!ReadFile(backup, bak) || Classify(e, bak) != State::Original) {
            std::cerr << e.rel << ": no valid backup; verify the game files in your Steam or GOG client\n";
            rc = kChanged;
            continue;
        }
        std::error_code ec;
        fs::copy_file(backup, path, fs::copy_options::overwrite_existing, ec);
        std::vector<uint8_t> after;
        if (ec || !ReadFile(path, after) || Classify(e, after) != State::Original) { std::cerr << e.rel << ": restore failed\n"; return kWrite; }
        fs::remove(backup, ec);
        std::cout << e.rel << ": restored\n";
    }
    return rc;
}

}  // namespace

int main(int argc, char** argv) {
    std::vector<std::string> args(argv + 1, argv + argc);
    bool force = false;
    args.erase(std::remove_if(args.begin(), args.end(), [&](const std::string& a) { if (a == "--force") { force = true; return true; } return false; }), args.end());
    if (args.size() < 2 || args.size() > 3) {
        std::cerr << "usage: Bo2Patcher check|patch|restore <game dir> [bo2pl.patch] [--force]\n";
        return kUsage;
    }
    const std::string& cmd = args[0];
    fs::path game = args[1];
    fs::path manifestPath = args.size() == 3 ? fs::path(args[2]) : fs::path(argv[0]).parent_path() / "bo2pl.patch";
    if (cmd != "check" && cmd != "patch" && cmd != "restore") { std::cerr << "unknown command " << cmd << "\n"; return kUsage; }
    std::vector<Entry> entries;
    std::string err;
    if (!ParseManifest(manifestPath, entries, err)) { std::cerr << err << "\n"; return kError; }
    try {
        if (cmd == "check") return Check(game, entries);
        if (cmd == "patch") return Patch(game, entries, force);
        return Restore(game, entries);
    } catch (const std::exception& ex) {
        std::cerr << "error: " << ex.what() << "\n";
        return kError;
    }
}
