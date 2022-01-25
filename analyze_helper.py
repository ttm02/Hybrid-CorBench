import json

input_fname_pattern = "[BENCH_BASE_DIR]/output/results_[TOOL].json"

## entry: name: [TP,TN,FP,FN,ERR,error_present,error_present_without_tool,case_id,full_case_name]
# True Positive, True Negative, False Positive, False negative,
# ERR=error in parsing the output or runnung case,
# error_present: if the error actually manifested during execution,
# case_id, full_case_name for later more in depth analysis refers to the dir_name

TP = 0
TN = 1
FP = 2
FN = 3
TW = 4
FW = 5
ERR = 6
error_present = 7
error_present_without_tool = 8
case_id = 9
full_case_name = 10
cflags_used = 11
exit_code_without_tool = 12

#categories = ['pt2pt', 'coll', 'usertypes', 'rma']
categories = ['pt2pt', 'coll', 'usertypes', 'rma', 'openmp/data_race','openmp/ordering','openmp/threading','openmp/memory']

# compile #'time, 'baseline_time','mem','baseline_mem' run#'time, 'baseline_time','mem','baseline_mem'
time_compile = 0
time_baseline_compile = 1
mem_compile = 2
mem_baseline_compile = 3
time_run = 4
time_baseline_run = 5
mem_run = 6
mem_baseline_run = 7

DEADLOCK_TIME=110.0


def get_category(this_case):
    name = this_case[full_case_name]

    category = None
    for canidate in categories:
        if canidate + "/" in name:
            # only one category
            assert category == None
            category = canidate
    if 'datatype/' in name:
        # only one category
        assert category == None
        category = 'usertypes'
    return category


def load_case_names(base_dir):
    omp_dir=base_dir+"/micro-benches/0-level/openmp/"
    filename = base_dir+"/micro-benches/0-level/openmp/case_numbering.txt"
    with open(filename) as file:
        lines = file.readlines()
        lines = [line.rstrip() for line in lines]

    case_names = {}

    for l in lines:
        name, number = l.split(" ")
        case_names[omp_dir+name]=int(number)

    return case_names

def is_correct_case(this_case):
    name = this_case[full_case_name]
    return "correct" in name


def read_tool_data():
    tools_result_data = {}
    jobs = 0
    # read all available input data
    for tool in TOOLS:
        tools_result_data[tool] = {}

        for test_dir in os.scandir(INPUT_DIR + "/" + tool):
            # only read the directories
            if not test_dir.is_dir():
                continue
                # exclude mini apps
            if test_dir.name == "kripke" or test_dir.name == "amg2013" or test_dir.name == "lulesh":
                continue

            jobs += 1

            job_id = test_dir.name
            # read the data from dir
            data = {}
            with open(test_dir.path + "/results.json", 'r') as f:
                data = json.load(f)
                tools_result_data[tool][job_id] = data
    print("Read Data from %i jobs" % (jobs))

    return tools_result_data

