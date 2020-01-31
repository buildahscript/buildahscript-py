#!/usr/bin/python2
import os
import subprocess

subprocess.check_call(['docker', 'build', '-t', 'tester', '.ci'])

for script in os.listdir('demos'):
    subprocess.check_call([
        'docker', 'run', '--rm', '--init', '--privileged', 'tester', script,
    ])
