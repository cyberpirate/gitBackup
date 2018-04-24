from subprocess import check_output
from subprocess import CalledProcessError
import os
import sys
import socket


def findGit():
    return check_output(["which", "git"]).decode("utf-8").strip()

GIT_PATH = findGit()
LOCAL_BRANCH = "localBox"

def enterRepo():
    os.chdir(sys.argv[1])

def gitFetch():
    check_output([GIT_PATH, "fetch"])

def getBranch():
    output = check_output([GIT_PATH, "branch"]).decode("utf-8").strip()
    output = [ a for a in output.split("\n") if a.startswith("*") ]
    return output[0][2:]

def createBranch(name=""):
    name = LOCAL_BRANCH if not name else name

    check_output([GIT_PATH, "branch", name])

def branchExists(name=""):
    name = LOCAL_BRANCH if not name else name

    output = check_output([GIT_PATH, "branch"]).decode("utf-8").strip()
    output = [ a.strip() for a in output.split("\n") if not a.startswith("*") ]
    output.append(getBranch())

    return name in output

def switchBranch(name=""):
    name = LOCAL_BRANCH if not name else name

    check_output([GIT_PATH, "checkout", name])

def checkOnBranch(name=""):
    name = LOCAL_BRANCH if not name else name

    return getBranch() == name

def getCommitHash(name=""):
    name = LOCAL_BRANCH if not name else name

    return check_output([GIT_PATH, "rev-parse", name]).decode("utf-8").strip()

def isAncestor(ancestor, child):
    try:
        check_output([GIT_PATH, "merge-base", "--is-ancestor", ancestor, child])
    except CalledProcessError as grepexc:
        return False
    return True

def setBranchAt(branch, commit):
    check_output([GIT_PATH, "branch", "-f", branch, commit])

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
    output = check_output([GIT_PATH, "status"]).decode("utf-8").strip()
    return "nothing to commit" not in output

def commitAll():
    check_output([GIT_PATH, "add", "."])

    check_output([GIT_PATH, "commit", "-m", socket.gethostname()])

def mergeIn(branch):
    check_output([GIT_PATH, "merge", branch])

    return not filesToCommit()

def updateRemoteMaster():
    currentBranch = getBranch()

    remoteHash = getCommitHash("origin/master")
    localHash = getCommitHash("master")

    if not isAncestor(remoteHash, localHash):
        return False
    
    switchBranch("master")
    check_output([GIT_PATH, "push"])
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
        check_output([GIT_PATH, "clean", "--force"])
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
        check_output([GIT_PATH, "clean", "--force"])
        return False

    return True

if len(sys.argv) <= 1 or len(sys.argv[1]) == 0:
    print("first arg must be git repo")
    exit()

enterRepo()

gitFetch()

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
