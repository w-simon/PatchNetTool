import os
import sys
import json
import getopt
import subprocess


class ConfigInfo:
    def __init__(self, config_file):
        with open(config_file, 'r') as f:
            data = json.loads(f.read())
            #print(data)
            self.begin_date = data['begin_date']
            self.end_date = data['end_date']
            self.linux_repo = data['linux_repo']
            self.linux_stable_repo = data['linux_stable_repo']
            self.branches = data['branches']
            self.git_log_dir = '/tmp/git_logs'

class LabelGenerator:
    def __init__(self, config):
            self.config = config

    def __collect_commits(self):
        current_path = os.getcwd()
        os.chdir(self.config.linux_repo)
        cmd='git log  --since=' + self.config.begin_date + ' --until=' + \
            self.config.end_date + ' --pretty=format:%H';
        lines = os.popen(cmd + " | awk '{printf $1 \"\\n\"}'").read()\
                .strip('\n')
        commits = lines.split('\n')
        os.chdir(current_path)
        return commits

    def __collect_git_logs(self):
        current_path = os.getcwd()
        os.chdir(self.config.linux_stable_repo)
        subprocess.run('rm -fr ' + self.config.git_log_dir + ' && mkdir -p ' + \
                        self.config.git_log_dir, shell=True)
        for branch in self.config.branches:
            subprocess.run('git checkout origin/linux-' + branch + '.y',
                            shell=True)
            subprocess.run('git log v' + branch + '^..HEAD^' +'> ' + \
                            self.config.git_log_dir + branch, shell=True)
        os.chdir(current_path)

    def __is_stable(self, commit):
        result = subprocess.call('grep -r -i ' + '\"' +
                                commit + ' upstream' + '\" ' + \
                                self.config.git_log_dir, shell=True)
        return result == 0

    def generate_label(self, output_file):
        commits = self.__collect_commits()
        self.__collect_git_logs()
        with open(output_file, 'w') as f:
            for commit in commits:
                if self.__is_stable(commit):
                    f.write(commit + ': ' + 'true\n')
                else:
                    f.write(commit + ': ' + 'false\n')

def usage():
    print ("Usage: generate_labelled_commits.py "
            " -c <config_file> "
            " -o <output_file>")

def main(argv):
    config_file = ''
    output_file = ''
    try:
        opts, args = getopt.getopt(argv,"hc:o:",
                                ["config_file=", "output_file="])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            usage()
            sys.exit()
        elif opt in ("-c", "--config_file"):
            config_file = arg
        elif opt in ("-o", "--output_file"):
            output_file = arg
        else:
            usage()
            sys.exit()

    generator = LabelGenerator(ConfigInfo(config_file))
    generator.generate_label(output_file)

if __name__ == "__main__":
    main(sys.argv[1:])
