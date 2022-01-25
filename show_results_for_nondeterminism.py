import os
import argparse
import importlib.util
import json
from analyze_helper import *

## entry: name: [TP,TN,FP,FN,ERR,error_present,case_id,full_case_name]
# True Positive, True Negative, False Positive, False negative,
# ERR=error in parsing the output or runnung case,
# error_present: if the error actually manifested during execution,
# case_id, full_case_name for later more in depth analysis refers to the dir_name

TOOLS = ['MUST', 'ITAC']

openmp_categories= ['openmp/data_race','openmp/ordering','openmp/threading','openmp/memory']

# read env vars
BENCH_BASE_DIR = os.environ["MPI_CORRECTNESS_BM_DIR"];
INPUT_DIR = os.environ["MPI_CORRECTNESS_BM_EXPERIMENT_DIR"];

def add_cases(score, case):
    score[0] += case[0]
    score[1] += case[1]
    score[2] += case[2]
    score[3] += case[3]
    score[4] += case[4]
    score[5] += case[5]
    score[6] += case[6]
    score[7] += case[7]
    assert score[case_id] == case[case_id]
    assert score[full_case_name] == case[full_case_name]

    return score


def add_score_nondeterminism(score, case):
    score[0] += case[TN]
    score[1] += case[TP]
    score[2] += case[TW]
    score[3] += case[FP]
    score[3] += case[FW]
    score[4] += case[FN]
    score[5] += case[ERR]

    if score[6]!="_":
        assert score[6]== case[9]
    score[6]=case[9]

    if score[7]!="_":
        assert score[7]== case[10]
    score[7]=case[10]
    return score

def get_bufsize(case):
    return 10
    cflags = case[cflags_used]
    if "-DBUFFER_LENGTH_INT=1000000" in cflags:
        return 1000000
    elif "-DBUFFER_LENGTH_INT=10000" in cflags:
        return 10000
    elif "-DBUFFER_LENGTH_INT=10" in cflags:
        return 10
    else:
        assert False

def get_ordering(case):
    return 'false'
    cflags = case[cflags_used]
    if "-DUSE_DISTURBED_THREAD_ORDER" in cflags:
        return 'false'
    else:
        return 'correct'

def get_thread_num(case):
    return 8
    cflags = case[cflags_used]
    if "-DNUM_THREADS=8" in cflags:
        return 8
    elif "-DNUM_THREADS=4" in cflags:
        return 4
    elif "-DNUM_THREADS=2" in cflags:
        return 2
    elif "-DNUM_THREADS=1" in cflags:
        return 1
    else:
        assert False

def add_score_per_param(score, case):
    score[0] += int(case[TP])
    score[0] += int(case[TW])
    score[1] += int(case[FN])
    score[2] += int(case[ERR])

    return score

def parse_command_line_args():
    parser = argparse.ArgumentParser(
        description=(
            "Script that evaluates the report from a tool"
        )
    )

    # parser.add_argument('IN_DIR')
    parser.add_argument('TOOL', choices=['MUST', 'ITAC', 'MPI-Checker', 'PARCOACH', 'TODO_More_Tools'])
    parser.add_argument('case_id', type=int)
    # parser.add_argument('--BENCH_BASE_DIR', default=".")
    #parser.add_argument('--outfile', default="[BENCH_BASE_DIR]/output/results_[TOOL].json")

    args = parser.parse_args()
    return args

def print_jid_path(jid,case,tool):
    base_path = INPUT_DIR + "/" + tool
    print(base_path + "/job" + jid + "_" + str(case) + ".out")
    print(base_path + "/" + jid + "/" + str(case))


def main():
    ARGS = parse_command_line_args()

    tools_result_data = read_tool_data()

    naming = load_case_names(BENCH_BASE_DIR)
    naming["_"] = "-"

    # -1 as file starts at 1 and data at 0
    case_to_show = ARGS.case_id -1

    tool= ARGS.TOOL


    for case in next(iter(tools_result_data[TOOLS[0]].values())):
        # print(next(iter( tools_result_data[TOOLS[0]].values() ))[case][full_case_name])

        if case_to_show == int(case):

            found_jid=-1
            missed_jid=-1
            err_jid=-1
            case_data = list(tools_result_data[tool].values())[0][case]

            category = get_category(case_data)
            correct = is_correct_case(case_data)

            print("Case %i:"%(case_to_show+1))
            print(case_data[full_case_name])
            if correct:
                print("Correct Case")
                count =0
                for jid in tools_result_data[tool]:
                    case_data = tools_result_data[tool][jid][case]
                    count+= case_data[FP]
                print("False Positives: %d"%count)

            else:
                data_threads = {}
                data_threads[1] = [0,0,0]
                data_threads[2] = [0, 0, 0]
                data_threads[4] = [0, 0, 0]
                data_threads[8] = [0, 0, 0]
                data_buf_size={}
                data_buf_size[10] = [0, 0, 0]
                data_buf_size[10000] = [0, 0, 0]
                data_buf_size[1000000] = [0, 0, 0]
                data_order={}
                data_order['correct']=[0, 0, 0]
                data_order['false'] = [0, 0, 0]

            for jid in tools_result_data[tool]:
                case_data = tools_result_data[tool][jid][case]

                t_num = get_thread_num(case_data)
                data_threads[t_num] =add_score_per_param(data_threads[t_num],case_data)
                order = get_ordering(case_data)
                data_order[order]=add_score_per_param(data_order[order],case_data)
                bufsz = get_bufsize(case_data)
                data_buf_size[bufsz]= add_score_per_param(data_buf_size[bufsz],case_data)

                if case_data[TP] or case_data[TW]:
                    found_jid = jid
                if case_data[FN]:
                    missed_jid=jid
                if case_data[ERR]:
                    err_jid=jid

            print(data_order)
            print(data_buf_size)
            print(data_threads)
            print()
            if found_jid!=-1:
                print("Found:")
                print_jid_path(found_jid,case,tool)
            if missed_jid!=-1:
                print("Missed:")
                print_jid_path(missed_jid,case,tool)
            if err_jid!=-1:
                print("Crash:")
                print_jid_path(err_jid,case,tool)

if __name__ == '__main__':
    main()
