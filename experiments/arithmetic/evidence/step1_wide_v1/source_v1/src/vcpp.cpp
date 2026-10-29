// Copyright (c) 2025 Meng Chengzhen, in Shandong University
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#include "vcpp.hpp"

#include "vulcpp/project_parser.hpp"

VulStaticProject parseVcppStaticProject(
    const string &project_dir,
    const string &top_file_path,
    const string &main_file_path
) {
    return parseVcppStaticProjectImpl(project_dir, top_file_path, main_file_path);
}
