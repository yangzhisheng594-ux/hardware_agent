import argparse
import sys

try:
    from agent import run
except ImportError:
    from .agent import run


def main() -> int:
    parser = argparse.ArgumentParser(description="本地小模型驱动的硬件设计助手")
    parser.add_argument("--task", required=True, help="用户硬件设计需求")
    args = parser.parse_args()

    try:
        final_report_path = run(args.task)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"错误：执行硬件设计流程失败：{exc}", file=sys.stderr)
        return 1

    print(f"设计流程完成，最终报告已生成：{final_report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
