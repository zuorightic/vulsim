#pragma once

#include "rtlgen.h"
#include "rtlzz_bridge.hpp"

// Select a frozen-model candidate and reuse only its core inside the VUL shell.
RTLzzLogicRTLResult generateAutoPipeline(
    const rtlgen::PipelineRTLUnit &unit,
    const std::string &source_file,
    const std::string &lib_include_dir,
    const std::map<std::string, std::vector<std::uint64_t>> &input_reset_values,
    const rtlgen::AutoPipelineOptions &options,
    bool release
);
