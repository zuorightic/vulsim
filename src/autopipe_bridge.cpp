#include "autopipe_bridge.hpp"

#include <llvm/Support/JSON.h>
#include <llvm/Support/FormatVariadic.h>
#include <cerrno>
#include <filesystem>
#include <fstream>
#include <sstream>
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
            {"timeout_s", options.timeout_seconds}, {"release", release}
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
