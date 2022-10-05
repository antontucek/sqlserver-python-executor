import argparse
import sys
import time


def main(cli_arguments=None):
    parser = argparse.ArgumentParser(prog='coreExecutorTest',
                                     description='Core test python script for unit tests')
    parser.add_argument('-r', '--return', required=False, type=int, default=0, action='store',
                        choices=range(0, 17), help='Exit code 0-16 to return, default 0')
    parser.add_argument('-s', '--sleep', required=False, type=int, default=0, action='store',
                        choices=range(0,16), help='Wait internal 0-15 in seconds, default 0')
    namespace, leftover = parser.parse_known_args(cli_arguments)
    if len(leftover) > 0:
        raise f"Unknown parameters found {leftover}"
    exit_code = vars(namespace)['return']
    sleep = vars(namespace)['sleep']
    if sleep > 0:
        print(f"Sleeping for {sleep} seconds...")
        time.sleep(sleep)
    print(f"Completed with exit code: {exit_code}")
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
