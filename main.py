from subprocess import check_output
from subprocess import CalledProcessError
from subprocess import Popen, PIPE
import os
import sys
import socket


def findGit():
    return check_output(["which", "git"]).decode("utf-8").strip()

GIT_PATH = findGit()
LOCAL_BRANCH = "localBox"
DEFAULT_ENV=os.environ.copy()

def git(*arg):
    gitArgs = [GIT_PATH]

    for a in arg:
        gitArgs.append(a)

    process = Popen(gitArgs, env=DEFAULT_ENV, stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()

    stdout = stdout.decode("utf-8").strip()
    stderr = stderr.decode("utf-8").strip()

    return stdout, stderr, process.returncode

def enterRepo():
    os.chdir(sys.argv[1])

def getBranch():
    output, err, code = git("branch")
    output = [ a for a in output.split("\n") if a.startswith("*") ]
    return output[0][2:]

def createBranch(name=""):
    name = LOCAL_BRANCH if not name else name

    git("branch", name)

def branchExists(name=""):
    name = LOCAL_BRANCH if not name else name

    output, err, code = git("branch")
    output = [ a.strip() for a in output.split("\n") if not a.startswith("*") ]
    output.append(getBranch())

    return name in output

def switchBranch(name=""):
    name = LOCAL_BRANCH if not name else name

    git("checkout", name)

def checkOnBranch(name=""):
    name = LOCAL_BRANCH if not name else name

    return getBranch() == name

def getCommitHash(name=""):
    name = LOCAL_BRANCH if not name else name

    output, err, code = git("rev-parse", name)
    return output

def isAncestor(ancestor, child):
    output, err, code = git("merge-base", "--is-ancestor", ancestor, child)
    return code == 0

def setBranchAt(branch, commit):
    git("branch", "-f", branch, commit)

def updateBranch(localBranch="", remoteBranch=""):
    localBranch = LOCAL_BRANCH if not localBranch else localBranch
    remoteBranch = LOCAL_BRANCH if not remoteBranch else remoteBranch

    remoteHash = getCommitHash(remoteBranch)
    localHash = getCommitHash(localBranch)

    if remoteHash == localHash:
        return True
    
    if not isAncestor(localHash, remoteHash):
        return False

    setBranchAt(localBranch, remoteHash)

    return True

def filesToCommit():
    output, err, code = git("status")
    return "nothing to commit" not in output

def commitAll():
    git("add", ".")

    git("commit", "-m", socket.gethostname())

def mergeIn(branch):
    git("merge", branch)

    return not filesToCommit()

def updateRemoteMaster():
    currentBranch = getBranch()

    remoteHash = getCommitHash("origin/master")
    localHash = getCommitHash("master")

    if not isAncestor(remoteHash, localHash):
        return False
    
    switchBranch("master")
    git("push")
    switchBranch(currentBranch)
    return True
    

def updateMasterWithLocal():
    currentBranch = getBranch()
    currentHash = getCommitHash("HEAD")
    updated = updateBranch("master", LOCAL_BRANCH)

    if updated:
        return True

    updated = mergeIn("master")

    if not updated:
        # merge conflict, print error
        setBranchAt(currentBranch, currentHash)
        git("clean", "--force")
        return False
    
    return updateBranch("master", LOCAL_BRANCH)

def updateLocalWithMaster():
    currentBranch = getBranch()
    currentHash = getCommitHash("HEAD")
    updated = updateBranch("master", "origin/master")

    if not updated:
        # print error
        return False
    
    updated = mergeIn("master")

    if not updated:
        # merge conflict, print error
        setBranchAt(currentBranch, currentHash)
        git("clean", "--force")
        return False

    return True

if len(sys.argv) <= 1 or len(sys.argv[1]) == 0:
    print("first arg must be git repo")
    exit()

enterRepo()

git("fetch")

if not branchExists():
    createBranch()

if getBranch() != LOCAL_BRANCH:
    switchBranch()

if filesToCommit():
    commitAll()
    updateMasterWithLocal()
    updateRemoteMaster()

if getCommitHash("HEAD") != getCommitHash("origin/master"):
    updateLocalWithMaster()
