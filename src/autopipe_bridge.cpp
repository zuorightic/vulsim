#include "autopipe_bridge.hpp"

#include <llvm/Support/JSON.h>
#include <llvm/Support/FormatVariadic.h>
#include <cerrno>
#include <filesystem>
#include <fstream>
#include <sstream>
#include <set>
#include <cctype>
#ifndef _WIN32
#include <fcntl.h>
#include <sys/wait.h>
#include <unistd.h>
#endif

namespace {
std::string contents(const std::filesystem::path &path) {
    std::ifstream stream(path);
    if (!stream) throw VulException("Cannot read auto-pipeline artifact: " + path.string());
    return {std::istreambuf_iterator<char>(stream), {}};
}

std::filesystem::path resourceRoot(const std::string &lib) {
    // Prefer the current checkout when a binary was copied or a checkout moved.
    for (const auto &path : {std::filesystem::absolute(lib).parent_path(),
                             std::filesystem::path(VUL_AUTOPIPE_SOURCE_DIR)}) {
        if (std::filesystem::is_regular_file(path / "tools/autopipe/vul_entry.py") &&
            std::filesystem::is_regular_file(path / "vullib/models/autopipe/manifest.json"))
            return path;
    }
    throw VulException("Auto-pipeline resources not found; use -l /path/to/checkout/vullib");
}

std::vector<int> widthList(const std::string &text, const llvm::json::Array &defaults, int maximum) {
    std::vector<int> values;
    if (text.empty()) {
        for (const auto &value : defaults) {
            auto n = value.getAsInteger();
            if (!n) throw VulException("Invalid candidate profile width");
            values.push_back(static_cast<int>(*n));
        }
    } else {
        std::size_t start = 0;
        for (;;) {
            const auto end = text.find(',', start);
            const auto item = text.substr(start, end == std::string::npos ? end : end - start);
            std::size_t used = 0;
            long long number;
            try { number = std::stoll(item, &used); }
            catch (const std::exception &) { throw VulException("Candidate widths require comma-separated integers"); }
            while (used < item.size() && std::isspace(static_cast<unsigned char>(item[used]))) ++used;
            if (used != item.size() || number < 0 || number > maximum)
                throw VulException("Candidate width outside 0.." + std::to_string(maximum));
            values.push_back(static_cast<int>(number));
            if (end == std::string::npos) break;
            start = end + 1;
        }
    }
    std::set<int> unique(values.begin(), values.end());
    if (values.empty() || values.size() != unique.size()) throw VulException("Candidate widths must be nonempty and distinct");
    for (int n : values) if (n < 0 || n > maximum) throw VulException("Invalid candidate profile width");
    return values;
}
}

void validateAutoPipelineSearchOptions(const rtlgen::AutoPipelineOptions &options, const std::string &lib_include_dir) {
    const auto root = resourceRoot(lib_include_dir);
    auto policy = llvm::json::parse(contents(root / "tools/autopipe/candidate_profiles.json"));
    auto catalog = llvm::json::parse(contents(root / "vullib/models/autopipe/workloads.json"));
    if (!policy || !catalog || !policy->getAsObject() || !catalog->getAsObject())
        throw VulException("Invalid candidate profile catalog");
    auto &p = *policy->getAsObject();
    auto defaults = p.getObject("generic");
    const llvm::json::Array *mul = defaults ? defaults->getArray("mul_block_widths") : nullptr;
    const llvm::json::Array *add = defaults ? defaults->getArray("add_limb_widths") : nullptr;
    if (!options.candidate_profile.empty() && options.candidate_profile != "generic") {
        auto cases = catalog->getAsObject()->getArray("cases");
        mul = add = nullptr;
        if (cases) for (const auto &entry : *cases) {
            auto row = entry.getAsObject();
            if (!row) continue;
            auto id = row->getString("id");
            if (!id || *id != options.candidate_profile) continue;
            auto search = row->getObject("structural_search");
            if (search) { mul = search->getArray("mul_block_widths"); add = search->getArray("add_sub_limb_widths"); }
            break;
        }
    }
    auto max_mul = p.getInteger("max_mul_block_width"), max_add = p.getInteger("max_add_limb_width"), max_structures = p.getInteger("max_structures");
    if (!mul || !add || !max_mul || !max_add || !max_structures)
        throw VulException("Unknown or invalid --candidate-profile: " + options.candidate_profile);
    const auto m = widthList(options.mul_block_widths, *mul, *max_mul);
    const auto a = widthList(options.add_limb_widths, *add, *max_add);
    if (m.size() * a.size() > static_cast<std::size_t>(*max_structures))
        throw VulException("Candidate profile permits at most " + std::to_string(*max_structures) + " structural combinations");
}

RTLzzLogicRTLResult generateAutoPipeline(
    const rtlgen::PipelineRTLUnit &unit, const std::string &source_file,
    const std::string &lib_include_dir,
    const std::map<std::string, std::vector<std::uint64_t>> &input_reset_values,
    const rtlgen::AutoPipelineOptions &options,
    bool release
) {
    RTLzzLogicRTLResult result;
#ifdef _WIN32
    result.error = "Model-guided auto-pipeline currently requires Linux/POSIX";
#else
    try {
        namespace fs = std::filesystem;
        const auto root = resourceRoot(lib_include_dir);
        const auto output = fs::absolute(source_file + ".autopipe");
        fs::create_directories(output);
        llvm::json::Object reset, bindings;
        for (const auto &[name, words] : input_reset_values) {
            llvm::json::Array values;
            for (auto word : words) { std::ostringstream s; s << std::hex << word; values.push_back(s.str()); }
            reset[name] = std::move(values);
        }
        for (const auto &[port, signal] : unit.bindings) bindings[port] = signal;
        llvm::json::Object request{
            {"schema", "vul-autopipe-request-v1"}, {"source_file", fs::absolute(source_file).string()},
            {"top", unit.top_function}, {"iv", unit.input_valid_name}, {"ov", unit.output_valid_name},
            {"reset", std::move(reset)}, {"bindings", std::move(bindings)}, {"L", unit.latency},
            {"platform", options.target_backend}, {"period_ps", options.target_period_ps},
            {"timeout_s", options.timeout_seconds}, {"release", release},
            {"candidate_profile", options.candidate_profile.empty() ? llvm::json::Value(nullptr) : llvm::json::Value(options.candidate_profile)},
            {"mul_block_widths", options.mul_block_widths.empty() ? llvm::json::Value(nullptr) : llvm::json::Value(options.mul_block_widths)},
            {"add_limb_widths", options.add_limb_widths.empty() ? llvm::json::Value(nullptr) : llvm::json::Value(options.add_limb_widths)}
        };
        const auto request_path = output / "request.json";
        {
            std::ofstream stream(request_path);
            stream << llvm::formatv("{0:2}", llvm::json::Value(std::move(request))).str() << '\n';
            if (!stream) throw VulException("Cannot write auto-pipeline request");
        }
        const auto log = output / "search.log";
        const auto root_text = root.string(), request_text = request_path.string();
        // Pass paths as argv entries; source paths never enter a shell command.
        const int log_fd = open(log.c_str(), O_WRONLY | O_CREAT | O_TRUNC, 0666);
        if (log_fd < 0) throw VulException("Cannot open auto-pipeline log");
        const pid_t child = fork();
        if (child < 0) { close(log_fd); throw VulException("Cannot start auto-pipeline selector"); }
        if (child == 0) {
            if (dup2(log_fd, STDOUT_FILENO) < 0 || dup2(log_fd, STDERR_FILENO) < 0 || chdir(root_text.c_str()) != 0) _exit(126);
            close(log_fd);
            execlp("python3", "python3", "-B", "-m", "tools.autopipe.vul_entry", "--request", request_text.c_str(), static_cast<char *>(nullptr));
            _exit(127);
        }
        close(log_fd);
        int status = 0;
        pid_t waited;
        do { waited = waitpid(child, &status, 0); } while (waited < 0 && errno == EINTR);
        if (waited < 0 || !WIFEXITED(status) || WEXITSTATUS(status) != 0) {
            auto tail = contents(log);
            if (tail.size() > 3000) tail = tail.substr(tail.size() - 3000);
            throw VulException("Auto-pipeline selection failed; log: " + log.string() + "\n" + tail);
        }
        auto parsed = llvm::json::parse(contents(output / "result.json"));
        if (!parsed || !parsed->getAsObject()) throw VulException("Invalid auto-pipeline result");
        const auto &object = *parsed->getAsObject();
        auto values = object.getObject("output_reset_values");
        if (!values) throw VulException("Missing auto-pipeline output reset values");
        for (const auto &entry : *values) {
            auto words = entry.second.getAsArray();
            if (!words) throw VulException("Invalid auto-pipeline reset vector");
            for (const auto &word : *words) {
                auto text = word.getAsString();
                if (!text) throw VulException("Invalid auto-pipeline reset limb");
                result.output_reset_values[entry.first.str()].push_back(std::stoull(text->str(), nullptr, 16));
            }
        }
        result.rtl_text = contents(output / "instance.sv");
        result.rtl_module_definitions = contents(output / "selected-core.sv");
        result.arithmetic_report = contents(output / "result.json");
        auto summary = object.getString("summary");
        if (!summary) throw VulException("Missing auto-pipeline selection summary");
        result.debug_codelines.push_back("pipeline " + unit.name + ": " + summary->str() + "\n");
        result.ok = true;
    } catch (const std::exception &error) { result.error = error.what(); }
#endif
    return result;
}
